"""One-channel-at-a-time, raw-free MEF3 development window acquisition."""
from __future__ import annotations

import hashlib
import math
import os
import tempfile
import warnings
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence
from unittest.mock import patch

import numpy as np

import id4_development_index_acquire as acquire
from id4_ccep_apparatus import parse_tidx
from id4_development_range_plan import EXPECTED_FS_HZ
from id4_sample_index_decoder import read_exact_sample_window

STOP = "APPARATUS_DEVELOPMENT_SIGNAL_STOP"
MAX_EVENT_SAMPLES = 1127


class RangeTransport(Protocol):
    def get(self, url: str, *, timeout: int, max_bytes: int) -> bytes: ...
    def head(self, url: str, *, timeout: int) -> Mapping[str, str]: ...
    def get_range_with_metadata(self, url: str, *, start: int, end: int, timeout: int,
                                max_bytes: int) -> Mapping[str, Any]: ...


def _paths(subject: str, channel: str) -> dict[str, str]:
    pair = acquire._channel_paths(subject, channel)
    stem = pair["tidx"][:-5]
    return {"tmet": stem + ".tmet", **pair}


def _merge(ranges: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    output: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if not output or start > output[-1][1]:
            output.append((start, end))
        else:
            output[-1] = (output[-1][0], max(output[-1][1], end))
    return output


def executable_ranges(rows: Sequence[Mapping[str, int]], windows: Sequence[Sequence[int]], *,
                      tdat_bytes: int) -> list[tuple[int, int]]:
    """TDAT header plus blocks touched by pymef's observed inclusive-end inspection."""
    if not rows or not windows or type(tdat_bytes) is not int or tdat_bytes <= 1024:
        raise ValueError(f"{STOP}:range inputs")
    selected: list[tuple[int, int]] = [(0, 1024)]
    total_samples = int(rows[-1]["start_sample"]) + int(rows[-1]["sample_count"])
    for window in windows:
        if (len(window) != 2 or any(type(value) is not int for value in window)
                or window[0] < 0 or window[1] <= window[0] or window[1] > total_samples
                or window[1] - window[0] > MAX_EVENT_SAMPLES):
            raise ValueError(f"{STOP}:window")
        touched: list[Mapping[str, int]] = []
        for row in rows:
            sample_start = int(row["start_sample"])
            sample_end = sample_start + int(row["sample_count"])
            if sample_end > window[0] and sample_start <= window[1]:
                touched.append(row)
        if (not touched or int(touched[0]["start_sample"]) > window[0]
                or int(touched[-1]["start_sample"]) + int(touched[-1]["sample_count"]) < window[1]):
            raise ValueError(f"{STOP}:uncovered window")
        for previous, current in zip(touched, touched[1:]):
            if (int(current["start_sample"]) != int(previous["start_sample"]) + int(previous["sample_count"])
                    or bool(current.get("discontinuity", True))):
                raise ValueError(f"{STOP}:sample discontinuity")
        for row in touched:
            start = int(row["tdat_offset"]); end = start + int(row["block_bytes"])
            if start < 1024 or end > tdat_bytes:
                raise ValueError(f"{STOP}:tdat span")
            selected.append((start, end))
    return _merge(selected)


def acquire_channel_metadata(*, subject: str, channel: str, expected: Mapping[str, Any],
                             transport: RangeTransport) -> dict[str, Any]:
    """Fetch and verify one channel's tmet/tidx plus TDAT object identity, no signal range."""
    if subject not in {"sub-1", "sub-5"} or expected.get("channel") != channel:
        raise ValueError(f"{STOP}:development source")
    paths = _paths(subject, channel)
    identities: dict[str, dict[str, Any]] = {}
    bodies: dict[str, bytes] = {}
    for extension in ("tmet", "tidx", "tdat"):
        pointer = transport.get(acquire._url(acquire.RAW_PREFIX, paths[extension]),
                                timeout=acquire.TIMEOUT_SECONDS, max_bytes=acquire.MAX_POINTER_BYTES)
        sha256, size = acquire._annex(pointer)
        identities[extension] = {"sha256": sha256, "bytes": size,
                                 "pointer_sha256": hashlib.sha256(pointer).hexdigest()}
    for extension, cap in (("tmet", 16_384), ("tidx", acquire.MAX_TIDX_BYTES)):
        body = transport.get(acquire._url(acquire.S3_PREFIX, paths[extension]),
                             timeout=acquire.TIMEOUT_SECONDS, max_bytes=cap)
        identity = identities[extension]
        if len(body) != identity["bytes"] or hashlib.sha256(body).hexdigest() != identity["sha256"]:
            raise RuntimeError(f"{STOP}:{extension} identity")
        bodies[extension] = body
    if ((expected.get("tmet_sha256") is not None
            and identities["tmet"]["sha256"] != expected.get("tmet_sha256"))
            or (expected.get("tmet_bytes") is not None
                and identities["tmet"]["bytes"] != expected.get("tmet_bytes"))
            or identities["tidx"]["sha256"] != expected.get("tidx_sha256")
            or identities["tidx"]["bytes"] != expected.get("tidx_bytes")
            or identities["tdat"]["sha256"] != expected.get("tdat_sha256")
            or identities["tdat"]["bytes"] != expected.get("tdat_bytes")):
        raise RuntimeError(f"{STOP}:frozen plan identity")
    headers = transport.head(acquire._url(acquire.S3_PREFIX, paths["tdat"]), timeout=acquire.TIMEOUT_SECONDS)
    if (int(acquire._header(headers, "Content-Length")) != identities["tdat"]["bytes"]
            or acquire._header(headers, "ETag") != expected.get("etag")
            or acquire._header(headers, "x-amz-version-id") != expected.get("version_id")):
        raise RuntimeError(f"{STOP}:tdat HEAD identity")
    return {"subject": subject, "channel": channel, "paths": paths, "identities": identities,
            "tmet": bodies["tmet"], "tidx": bodies["tidx"], "rows": parse_tidx(bodies["tidx"]),
            "tdat_headers": dict(headers)}


def decode_channel_windows(metadata: Mapping[str, Any], windows: Sequence[Sequence[int]], *,
                           transport: RangeTransport) -> tuple[np.ndarray, dict[str, Any]]:
    """Fetch exact executable ranges, decode physical values, then delete all raw bytes."""
    subject = str(metadata["subject"]); channel = str(metadata["channel"])
    paths = metadata["paths"]; identities = metadata["identities"]; rows = metadata["rows"]
    ranges = executable_ranges(rows, windows, tdat_bytes=int(identities["tdat"]["bytes"]))
    fetched: list[dict[str, Any]] = []
    payloads: list[tuple[int, bytes]] = []
    for start, end in ranges:
        response = transport.get_range_with_metadata(acquire._url(acquire.S3_PREFIX, paths["tdat"]),
                                                     start=start, end=end - 1, timeout=acquire.TIMEOUT_SECONDS,
                                                     max_bytes=end - start)
        body = bytes(response["body"])
        if int(response["object_bytes"]) != identities["tdat"]["bytes"]:
            raise RuntimeError(f"{STOP}:range object identity")
        payloads.append((start, body))
        fetched.append({"start": start, "end": end, "bytes": len(body),
                        "content_range": str(response["content_range"]),
                        "sha256": hashlib.sha256(body).hexdigest()})
    after = transport.head(acquire._url(acquire.S3_PREFIX, paths["tdat"]), timeout=acquire.TIMEOUT_SECONDS)
    for name in ("Content-Length", "ETag", "x-amz-version-id"):
        if acquire._header(after, name) != acquire._header(metadata["tdat_headers"], name):
            raise RuntimeError(f"{STOP}:source changed")
    cleanup = False
    with tempfile.TemporaryDirectory(prefix="ce-development-channel-") as temporary:
        root = Path(temporary)
        session = root / f"{subject}_ses-ieeg01_task-ccep_run-01_ieeg.mefd"
        segment = session / f"{channel}.timd" / f"{channel}-000000.segd"
        segment.mkdir(parents=True)
        stem = segment / f"{channel}-000000"
        stem.with_suffix(".tmet").write_bytes(bytes(metadata["tmet"]))
        stem.with_suffix(".tidx").write_bytes(bytes(metadata["tidx"]))
        with stem.with_suffix(".tdat").open("wb") as handle:
            handle.truncate(int(identities["tdat"]["bytes"]))
            for start, body in payloads:
                handle.seek(start); handle.write(body)
        with patch.dict(os.environ, {"LOCALAPPDATA": temporary}), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import mef3io
            import pymef

            mef = pymef.MefSession(str(session), "", check_all_passwords=True)
            with mef3io.Reader(str(session), n_threads=1, cache=None) as reader:
                info = reader.info(channel)
            if (float(info["sampling_frequency"]) != EXPECTED_FS_HZ
                    or str(info["units_description"]).strip().lower() != "microvolts"):
                raise RuntimeError(f"{STOP}:sample time unit")
            decoded = [read_exact_sample_window(session, channel, int(start), int(end), allowed_channels=[channel],
                                                total_samples=int(rows[-1]["start_sample"]) + int(rows[-1]["sample_count"]),
                                                max_window_samples=MAX_EVENT_SAMPLES)
                       for start, end in windows]
            warning_text = [str(item.message) for item in caught]
            if warning_text:
                raise RuntimeError(f"{STOP}:decoder warning:{warning_text[0]}")
        output = np.asarray(decoded, dtype=np.float64)
        if output.shape != (len(windows), MAX_EVENT_SAMPLES) or not np.all(np.isfinite(output)):
            raise RuntimeError(f"{STOP}:decoded window identity")
        cleanup = True
    if not cleanup or session.exists():
        raise RuntimeError(f"{STOP}:cleanup")
    receipt = {"subject": subject, "channel": channel, "windows": len(windows), "ranges": fetched,
               "range_sha256": hashlib.sha256(str(fetched).encode()).hexdigest(),
               "payload_bytes": sum(row["bytes"] for row in fetched),
               "transient_tdat_logical_bytes": identities["tdat"]["bytes"], "persistent_raw_bytes": 0,
               "fs_hz": EXPECTED_FS_HZ, "units": "microvolts", "warnings": [], "cleanup": cleanup}
    return output, receipt


def process_eligible_event_windows(metadata: Mapping[str, Any], events: Sequence[Mapping[str, Any]], *,
                                   transport: RangeTransport,
                                   processor: Callable[[np.ndarray, Sequence[Mapping[str, Any]]], Any]) -> tuple[Any, dict[str, Any]]:
    """Bind windows to frozen event records, reduce them in-callback, then erase the channel tile."""
    if not events or not callable(processor):
        raise ValueError(f"{STOP}:eligible event processor")
    identities: set[tuple[str, int]] = set()
    windows: list[list[int]] = []
    previous: tuple[str, int, int] | None = None
    for event in events:
        try:
            node = str(event["node"]); center = int(event["center_sample"]); source_row = int(event["source_row"])
            trial_index = int(event["trial_index"]); half = str(event["half"]); acquisition_window = list(event["acquisition"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{STOP}:eligible event binding") from exc
        if (not node or type(event["center_sample"]) is not int or type(event["source_row"]) is not int
                or type(event["trial_index"]) is not int or half != ("A" if trial_index % 2 == 0 else "B")
                or acquisition_window != [center - 1024, center + 103] or (node, center) in identities):
            raise ValueError(f"{STOP}:eligible event binding")
        order = (node, center, source_row)
        if previous is not None and order < previous:
            raise ValueError(f"{STOP}:eligible event order")
        previous = order; identities.add((node, center)); windows.append(acquisition_window)
    values, receipt = decode_channel_windows(metadata, windows, transport=transport)
    try:
        compact = processor(values, events)
    finally:
        values.fill(np.nan)
    receipt["eligible_event_table_bound"] = True
    receipt["derived_output_disposed_after_callback"] = True
    return compact, receipt
