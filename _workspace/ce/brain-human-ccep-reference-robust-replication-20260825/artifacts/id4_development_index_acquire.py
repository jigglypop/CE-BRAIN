"""Injected-transport, metadata/index-only acquisition for BA-OBS-ID4."""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
import urllib.parse
import urllib.error
import csv
import io
import time
import shutil
import subprocess
from pathlib import Path
from typing import Callable
from typing import Any, Mapping, Protocol

from id4_ccep_apparatus import parse_tidx
from id4_development_range_plan import (DEVELOPMENT_SUBJECTS, FROZEN_SNAPSHOT, PRECISION_CONVENTION,
                                        PRECISION_CONVENTION_VERSION, SHARED_START_SAMPLE,
                                        prepare_development_channels, plan_development_channel)

COMMIT = "1bbd3a0696c56b7dfd87020bc61092644a702d0a"
RAW_PREFIX = f"https://raw.githubusercontent.com/OpenNeuroDatasets/ds004457/{COMMIT}/"
S3_PREFIX = "https://s3.amazonaws.com/openneuro.org/ds004457/"
TIMEOUT_SECONDS = 30
CONCURRENCY = 1
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (0.05, 0.10)
MAX_TSV_BYTES = 2_000_000
MAX_POINTER_BYTES = 16_384
MAX_TIDX_BYTES = 20_000_000
ANNEX = re.compile(r"SHA256E-s(?P<size>[1-9][0-9]*)--(?P<sha>[0-9a-f]{64})\.[^\s]+")
CHECKPOINT_SCHEMA = 5
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class Transport(Protocol):
    def get(self, url: str, *, timeout: int, max_bytes: int) -> bytes: ...
    def head(self, url: str, *, timeout: int) -> Mapping[str, str]: ...


class UrllibTransport:
    """Production transport, used only when a caller explicitly supplies it."""
    def __init__(self, *, opener: Callable[..., Any] | None = None, sleeper: Callable[[float], None] = time.sleep) -> None:
        self._opener = opener or urllib.request.urlopen
        self._sleeper = sleeper

    def _retry(self, operation: Callable[[], Any]) -> Any:
        for attempt in range(MAX_ATTEMPTS):
            try:
                return operation()
            except urllib.error.HTTPError:
                raise
            except (TimeoutError, urllib.error.URLError):
                if attempt + 1 == MAX_ATTEMPTS:
                    raise
                self._sleeper(BACKOFF_SECONDS[attempt])
        raise AssertionError("unreachable")

    def get(self, url: str, *, timeout: int, max_bytes: int) -> bytes:
        def operation() -> bytes:
            _validate_transport_url(url)
            with self._opener(url, timeout=timeout) as response:
                _validate_transport_url(response.geturl())
                body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:response cap")
            return body
        return self._retry(operation)

    def head(self, url: str, *, timeout: int) -> Mapping[str, str]:
        def operation() -> Mapping[str, str]:
            _validate_transport_url(url)
            with self._opener(urllib.request.Request(url, method="HEAD"), timeout=timeout) as response:
                _validate_transport_url(response.geturl())
                return {key: value for key, value in response.headers.items()}
        return self._retry(operation)


class CurlTransport:
    """Windows curl.exe transport: argv-only, binary-safe GET and header-only HEAD."""
    TRANSIENT_EXIT_CODES = frozenset({6, 7, 18, 28, 52, 55, 56})

    def __init__(self, *, runner: Callable[[list[str]], Any] | None = None, sleeper: Callable[[float], None] = time.sleep,
                 curl_path: str | None = None) -> None:
        resolved = Path(curl_path or shutil.which("curl.exe") or "").resolve()
        if resolved.name.lower() != "curl.exe" or not resolved.is_file():
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:curl.exe unavailable")
        self._curl = str(resolved)
        self._runner = runner or (lambda argv: subprocess.run(argv, capture_output=True, check=False))
        self._sleeper = sleeper

    def _run(self, argv: list[str]) -> Any:
        for attempt in range(MAX_ATTEMPTS):
            result = self._runner(argv)
            if int(result.returncode) == 0:
                return result
            if int(result.returncode) not in self.TRANSIENT_EXIT_CODES or attempt + 1 == MAX_ATTEMPTS:
                raise ValueError(f"APPARATUS_INDEX_ACQUIRE_STOP:curl exit {result.returncode}")
            self._sleeper(BACKOFF_SECONDS[attempt])
        raise AssertionError("unreachable")

    def _argv(self, url: str, *, head: bool, max_bytes: int) -> list[str]:
        _validate_transport_url(url)
        argv = [self._curl, "-f", "-sS", "-L", "--connect-timeout", "10", "--max-time", str(TIMEOUT_SECONDS)]
        if head:
            argv.append("-I")
        else:
            argv.extend(("--max-filesize", str(max_bytes)))
        argv.extend(("-w", "%{stderr}%{url_effective}"))
        argv.append(url)
        return argv

    @staticmethod
    def _effective(result: Any) -> str:
        try:
            effective = bytes(result.stderr).decode("utf-8", errors="strict").strip()
        except UnicodeDecodeError as exc:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:curl effective URL") from exc
        _validate_transport_url(effective)
        return effective

    def get(self, url: str, *, timeout: int, max_bytes: int) -> bytes:
        # curl's max-time is bounded independently of caller timeout; reject expansion.
        if timeout > TIMEOUT_SECONDS or max_bytes <= 0:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:curl bounds")
        result = self._run(self._argv(url, head=False, max_bytes=max_bytes))
        self._effective(result)
        body = bytes(result.stdout)
        if len(body) > max_bytes:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:response cap")
        return body

    def get_range(self, url: str, *, start: int, end: int, timeout: int, max_bytes: int) -> bytes:
        """Fetch one inclusive byte range without ever requesting the full object."""
        return self.get_range_with_metadata(url, start=start, end=end, timeout=timeout, max_bytes=max_bytes)["body"]

    def get_range_with_metadata(self, url: str, *, start: int, end: int, timeout: int,
                                max_bytes: int) -> dict[str, Any]:
        """Fetch one inclusive range and bind its server-reported Content-Range."""
        if (type(start) is not int or type(end) is not int or start < 0 or end < start
                or timeout > TIMEOUT_SECONDS or max_bytes <= 0 or end - start + 1 > max_bytes):
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:curl range bounds")
        argv = self._argv(url, head=False, max_bytes=max_bytes)
        argv[1:1] = ["--range", f"{start}-{end}"]
        argv[argv.index("-w") + 1] = "%{stderr}%{url_effective}\n%header{content-range}"
        result = self._run(argv)
        try:
            effective, content_range = bytes(result.stderr).decode("utf-8", errors="strict").strip().splitlines()
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:curl range metadata") from exc
        _validate_transport_url(effective)
        body = bytes(result.stdout)
        if len(body) != end - start + 1 or len(body) > max_bytes:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:range cardinality")
        match = re.fullmatch(r"bytes ([0-9]+)-([0-9]+)/([1-9][0-9]*)", content_range.strip(), re.IGNORECASE)
        if match is None or (int(match.group(1)), int(match.group(2))) != (start, end) or int(match.group(3)) <= end:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:content range")
        return {"body": body, "content_range": content_range.strip(), "object_bytes": int(match.group(3))}

    def head(self, url: str, *, timeout: int) -> Mapping[str, str]:
        if timeout > TIMEOUT_SECONDS:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:curl bounds")
        result = self._run(self._argv(url, head=True, max_bytes=MAX_POINTER_BYTES))
        self._effective(result)
        raw = bytes(result.stdout)
        if len(raw) > MAX_POINTER_BYTES:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:header cap")
        blocks = [block for block in re.split(br"\r?\n\r?\n", raw) if block.strip()]
        if not blocks:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:curl headers")
        headers: dict[str, str] = {}
        for line in blocks[-1].splitlines()[1:]:
            if b":" in line:
                key, value = line.split(b":", 1)
                headers[key.decode("ascii", errors="strict")] = value.decode("utf-8", errors="strict").strip()
        return headers

def _url(prefix: str, relative: str) -> str:
    if not relative or relative.startswith("/") or ".." in relative.replace("\\", "/").split("/"):
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:unsafe relative path")
    return prefix + relative


def _validate_transport_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:unsafe transport URL")
    if not (url.startswith(RAW_PREFIX) or url.startswith(S3_PREFIX)):
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:unsafe transport URL")


def _tsv_paths(subject: str) -> dict[str, str]:
    base = f"{subject}/ses-ieeg01/ieeg"
    stem = f"{subject}_ses-ieeg01_task-ccep_run-01"
    return {"events": f"{base}/{stem}_events.tsv", "channels": f"{base}/{stem}_channels.tsv",
            "electrodes": f"{base}/{subject}_ses-ieeg01_electrodes.tsv"}


def _channel_paths(subject: str, channel: str) -> dict[str, str]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", channel):
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:unsafe channel name")
    base = f"{subject}/ses-ieeg01/ieeg/{subject}_ses-ieeg01_task-ccep_run-01_ieeg.mefd/{channel}.timd/{channel}-000000.segd/{channel}-000000"
    return {"tidx": base + ".tidx", "tdat": base + ".tdat"}


def _annex(pointer: bytes) -> tuple[str, int]:
    match = ANNEX.search(pointer.decode("utf-8", errors="strict"))
    if match is None:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:invalid annex pointer")
    return match.group("sha"), int(match.group("size"))


def _header(headers: Mapping[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower() and str(value).strip():
            return str(value).strip()
    raise ValueError(f"APPARATUS_INDEX_ACQUIRE_STOP:missing {name}")


def _channel_digest(channels: set[str]) -> str:
    return hashlib.sha256("\n".join(sorted(channels)).encode()).hexdigest()


def _checkpoint_write(path: Path, payload: Mapping[str, Any]) -> None:
    payload = dict(payload); payload.pop("checkpoint_sha256", None)
    payload["checkpoint_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    temporary.replace(path)


def _checkpoint_read(path: Path, identity: Mapping[str, Any], channels: set[str]) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint schema")
    digest = loaded.pop("checkpoint_sha256", None)
    if not isinstance(digest, str) or not SHA256.fullmatch(digest) or hashlib.sha256(json.dumps(loaded, sort_keys=True, separators=(",", ":")).encode()).hexdigest() != digest:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint digest")
    loaded["checkpoint_sha256"] = digest
    allowed_keys = set(identity) | {"status", "shared_first_uutc", "completed", "checkpoint_sha256"}
    if set(loaded) != allowed_keys:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint schema")
    if loaded.get("status") != "IN_PROGRESS" or any(loaded.get(key) != value for key, value in identity.items()):
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint identity")
    completed = loaded.get("completed")
    if not isinstance(completed, list) or type(loaded.get("shared_first_uutc")) is not int:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint schema")
    names = [entry.get("channel") for entry in completed if isinstance(entry, dict)]
    if (len(names) != len(completed) or not all(isinstance(name, str) and name for name in names)
            or len(set(names)) != len(names) or not set(names).issubset(channels)):
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint completed channels")
    entry_keys = {"channel", "provenance", "range_sha256", "range_count", "planned_tdat_bytes", "block_count", "pointer_bytes"}
    provenance_keys = {"channel", "tidx_sha256", "tidx_bytes", "tdat_sha256", "tdat_bytes", "etag", "version_id"}
    for entry in completed:
        provenance = entry["provenance"]
        if set(entry) != entry_keys or not isinstance(provenance, dict) or set(provenance) != provenance_keys or entry["channel"] != provenance["channel"]:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint entry schema")
        if (not all(type(entry[key]) is int and entry[key] > 0 for key in ("range_count", "planned_tdat_bytes", "block_count", "pointer_bytes"))
                or entry["planned_tdat_bytes"] < 1024 or entry["range_count"] > entry["block_count"]):
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint entry values")
        if not SHA256.fullmatch(str(entry["range_sha256"])) or not SHA256.fullmatch(str(provenance["tidx_sha256"])) or not SHA256.fullmatch(str(provenance["tdat_sha256"])):
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint entry hashes")
        if (not all(type(provenance[key]) is int and provenance[key] > 0 for key in ("tidx_bytes", "tdat_bytes"))
                or entry["planned_tdat_bytes"] > provenance["tdat_bytes"]
                or not all(isinstance(provenance[key], str) and provenance[key].strip() for key in ("etag", "version_id"))):
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:checkpoint provenance")
    return loaded


def acquire_development_index(
    *, snapshot: str, subject: str, expected_tsv_sha256: Mapping[str, str], transport: Transport, fs_hz: int = 2048,
    tsv_paths: Mapping[str, str] | None = None, channel_paths: Mapping[str, Mapping[str, str]] | None = None,
    progress: Callable[[int, int, str], None] | None = None, checkpoint_path: str | Path | None = None,
) -> dict[str, Any]:
    """Acquire TSV/pointer/tidx and tdat HEAD metadata only; never tdat body bytes."""
    if snapshot != FROZEN_SNAPSHOT or subject not in DEVELOPMENT_SUBJECTS:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:source or confirmation subject")
    derived_tsv_paths = _tsv_paths(subject)
    if tsv_paths is not None and dict(tsv_paths) != derived_tsv_paths:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:TSV path authority")
    if set(expected_tsv_sha256) != set(derived_tsv_paths):
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:TSV contract")
    tsv: dict[str, bytes] = {}
    for name in sorted(derived_tsv_paths):
        body = transport.get(_url(RAW_PREFIX, derived_tsv_paths[name]), timeout=TIMEOUT_SECONDS, max_bytes=MAX_TSV_BYTES)
        if hashlib.sha256(body).hexdigest() != expected_tsv_sha256[name]:
            raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:TSV hash")
        tsv[name] = body
    channels_text = tsv["channels"].decode("utf-8")
    channel_rows = list(csv.DictReader(io.StringIO(channels_text), delimiter="\t"))
    if not channel_rows or not channel_rows[0].keys() >= {"name", "type", "status"}:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:channels columns")
    names = [str(row.get("name", "")).strip() for row in channel_rows]
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name) for name in names) or len(set(names)) != len(names):
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:unsafe or duplicate channel")
    good = {str(row["name"]).strip() for row in channel_rows if str(row.get("status", "")).strip().lower() == "good"
            and str(row.get("type", "")).strip().lower() in {"ieeg", "seeg", "ecog"}}
    derived_channel_paths = {channel: _channel_paths(subject, channel) for channel in good}
    if channel_paths is not None and {key: dict(value) for key, value in channel_paths.items()} != derived_channel_paths:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:channel path authority")
    if not good:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:no good channels")
    if channel_paths is not None and set(channel_paths) != good:
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:all good channel paths required")
    good, retained_nodes = prepare_development_channels(snapshot=snapshot, subject=subject, events_tsv=tsv["events"].decode("utf-8"), channels_tsv=channels_text, electrodes_tsv=tsv["electrodes"].decode("utf-8"), fs_hz=fs_hz)
    if good != set(derived_channel_paths):
        raise ValueError("APPARATUS_INDEX_ACQUIRE_STOP:planner/channel disagreement")
    identity = {"schema": CHECKPOINT_SCHEMA, "snapshot": snapshot, "commit": COMMIT, "subject": subject,
                "tsv_sha256": {name: hashlib.sha256(body).hexdigest() for name, body in tsv.items()}, "fs_hz": fs_hz,
                "good_channel_set_sha256": _channel_digest(good), "precision_convention": PRECISION_CONVENTION,
                "precision_convention_version": PRECISION_CONVENTION_VERSION, "shared_start_sample": SHARED_START_SAMPLE}
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else None
    state: dict[str, Any] = {**identity, "status": "IN_PROGRESS", "shared_first_uutc": None, "completed": []}
    if checkpoint is not None and checkpoint.exists():
        state = _checkpoint_read(checkpoint, identity, good)
    completed = {entry["channel"]: entry for entry in state["completed"]}
    pointer_bytes = sum(int(entry["pointer_bytes"]) for entry in completed.values())
    verified_tidx_bytes = sum(int(entry["provenance"]["tidx_bytes"]) for entry in completed.values())
    for channel in sorted(derived_channel_paths):
        if channel in completed:
            continue
        paths = derived_channel_paths[channel]
        method = "pointer"
        try:
            tidx_pointer = transport.get(_url(RAW_PREFIX, paths["tidx"]), timeout=TIMEOUT_SECONDS, max_bytes=MAX_POINTER_BYTES)
            tdat_pointer = transport.get(_url(RAW_PREFIX, paths["tdat"]), timeout=TIMEOUT_SECONDS, max_bytes=MAX_POINTER_BYTES)
            tidx_sha, tidx_expected_size = _annex(tidx_pointer); tdat_sha, tdat_expected_size = _annex(tdat_pointer)
            method = "tidx_get"; tidx = transport.get(_url(S3_PREFIX, paths["tidx"]), timeout=TIMEOUT_SECONDS, max_bytes=MAX_TIDX_BYTES)
            if len(tidx) != tidx_expected_size or hashlib.sha256(tidx).hexdigest() != tidx_sha: raise ValueError("tidx identity")
            method = "tdat_head"; headers = transport.head(_url(S3_PREFIX, paths["tdat"]), timeout=TIMEOUT_SECONDS)
            if int(_header(headers, "Content-Length")) != tdat_expected_size: raise ValueError("tdat size")
            first_row = parse_tidx(tidx)[0]
            if first_row["start_sample"] != SHARED_START_SAMPLE: raise ValueError("start sample")
            if state["shared_first_uutc"] is None: state["shared_first_uutc"] = first_row["start_uutc"]
            result = plan_development_channel(snapshot=snapshot, subject=subject, events_tsv=tsv["events"].decode("utf-8"), channels_tsv=channels_text, retained_nodes=retained_nodes, shared_first_uutc=state["shared_first_uutc"], tidx_bytes=tidx, tdat_size=tdat_expected_size, fs_hz=fs_hz)
            provenance = {"channel": channel, "tidx_sha256": tidx_sha, "tidx_bytes": len(tidx), "tdat_sha256": tdat_sha,
                          "tdat_bytes": tdat_expected_size, "etag": _header(headers, "ETag"), "version_id": _header(headers, "x-amz-version-id")}
        except Exception as exc:
            raise RuntimeError(f"APPARATUS_INDEX_ACQUIRE_STOP:channel={channel} method={method}") from exc
        entry = {"channel": channel, "provenance": provenance, "range_sha256": hashlib.sha256(json.dumps(result["ranges"], separators=(",", ":")).encode()).hexdigest(),
                 "range_count": len(result["ranges"]), "planned_tdat_bytes": result["bytes"], "block_count": result["block_count"],
                 "pointer_bytes": len(tidx_pointer) + len(tdat_pointer)}
        completed[channel] = entry; state["completed"] = [completed[name] for name in sorted(completed)]
        pointer_bytes += entry["pointer_bytes"]; verified_tidx_bytes += provenance["tidx_bytes"]
        if checkpoint is not None: _checkpoint_write(checkpoint, state)
        if progress is not None:
            progress(len(completed), len(derived_channel_paths), channel)
    if set(completed) != good: raise RuntimeError("APPARATUS_INDEX_ACQUIRE_STOP:incomplete all-good gate")
    compact_channels = [completed[channel] for channel in sorted(completed)]
    if checkpoint is not None:
        final = {**state, "status": "COMPLETE"}; _checkpoint_write(checkpoint, final)
    return {"snapshot": snapshot, "commit": COMMIT, "subject": subject,
            "precision_convention": PRECISION_CONVENTION, "precision_convention_version": PRECISION_CONVENTION_VERSION,
            "shared_first_uutc": state["shared_first_uutc"],
            "shared_start_sample": SHARED_START_SAMPLE,
            "tsv_sha256": identity["tsv_sha256"], "channel_provenance": [entry["provenance"] for entry in compact_channels], "planned_ranges": compact_channels,
            "aggregate": {"verified_unique_tsv_bytes": sum(map(len, tsv.values())), "verified_unique_pointer_bytes": pointer_bytes,
                          "verified_unique_tidx_bytes": verified_tidx_bytes, "planned_tdat_bytes": sum(entry["planned_tdat_bytes"] for entry in compact_channels),
                          "planned_persistent_raw_bytes": 0, "wire_transfer_bytes_status": "NOT_CLAIMED_RETRIES_AND_RESUME"},
            "signal_accessed": False, "development_index_opened": True,
            "development_signal_opened": False, "confirmation_opened": False, "concurrency": CONCURRENCY,
            "retry_policy": {"max_attempts": MAX_ATTEMPTS, "transient_only": True,
                             "backoff_seconds": list(BACKOFF_SECONDS)}}
