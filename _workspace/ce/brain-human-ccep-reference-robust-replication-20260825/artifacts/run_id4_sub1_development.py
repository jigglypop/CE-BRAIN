"""Run every frozen sub-1 development site with reusable verified metadata."""
from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import http.client
import io
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import numpy as np

import id4_ccep_apparatus as apparatus
import id4_development_endpoint as endpoint
import id4_development_index_acquire as acquire
import id4_development_range_plan as planner
import id4_development_signal as signal


SUBJECT = "sub-1"
PLAN_SHA256 = "cdb3385fcd936e6835e9e0ac2dd36d8af6c40f0be44f5307d5fdf1753d16be2b"
FIRST_SITE_SHA256 = "faf27f45524fad15fb6d5c55b3632464ee69b141a93d78d74eaca891d12ed520"
STOP = "APPARATUS_SUBJECT_DEVELOPMENT_STOP"
AMENDMENT_V1 = "id4-subject-development-signal-concurrency-v1"
AMENDMENT_ID = "id4-subject-development-signal-concurrency-v2"
V1_SITES = frozenset({"LB1-LB2", "LB11-LB12", "LB12-LB13", "LB13-LB14", "LB2-LB3"})
SIGNAL_WORKERS = 8
MAX_SITE_TRIALS = 23


class _PersistentS3Transport:
    """One connection, one channel at a time; never requests a complete TDAT object."""

    def __init__(self) -> None:
        self._connection: http.client.HTTPSConnection | None = None

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @staticmethod
    def _path(url: str) -> str:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "s3.amazonaws.com" or not parsed.path.startswith("/"):
            raise ValueError(f"{STOP}:persistent transport URL")
        return parsed.path + (("?" + parsed.query) if parsed.query else "")

    def _request(self, method: str, url: str, *, timeout: int,
                 headers: dict[str, str] | None = None) -> http.client.HTTPResponse:
        path = self._path(url)
        for attempt in range(3):
            try:
                if self._connection is None:
                    self._connection = http.client.HTTPSConnection("s3.amazonaws.com", timeout=timeout)
                self._connection.request(method, path, headers=headers or {})
                return self._connection.getresponse()
            except (OSError, http.client.HTTPException):
                self.close()
                if attempt == 2:
                    raise
        raise AssertionError("unreachable")

    def get_range_with_metadata(self, url: str, *, start: int, end: int, timeout: int,
                                max_bytes: int) -> dict[str, Any]:
        if (type(start) is not int or type(end) is not int or start < 0 or end < start
                or end - start + 1 > max_bytes or timeout > acquire.TIMEOUT_SECONDS):
            raise ValueError(f"{STOP}:persistent range bounds")
        response = self._request("GET", url, timeout=timeout, headers={"Range": f"bytes={start}-{end}"})
        try:
            body = response.read(max_bytes + 1)
            content_range = response.getheader("Content-Range", "")
        finally:
            response.close()
        if response.status != 206 or len(body) != end - start + 1:
            raise RuntimeError(f"{STOP}:persistent range response")
        match = re.fullmatch(r"bytes ([0-9]+)-([0-9]+)/([1-9][0-9]*)", content_range, re.IGNORECASE)
        if match is None or (int(match.group(1)), int(match.group(2))) != (start, end):
            raise RuntimeError(f"{STOP}:persistent content range")
        return {"body": body, "content_range": content_range, "object_bytes": int(match.group(3))}

    def head(self, url: str, *, timeout: int) -> dict[str, str]:
        response = self._request("HEAD", url, timeout=timeout)
        try:
            response.read(1)
            headers = {name: value for name, value in response.getheaders()}
        finally:
            response.close()
        if response.status != 200:
            raise RuntimeError(f"{STOP}:persistent HEAD")
        return headers


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _write_receipt(path: Path, payload: dict[str, Any]) -> str:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_suffix(".json.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return _sha(body)


def _metadata_job(job: tuple[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    channel, provenance = job
    metadata = signal.acquire_channel_metadata(
        subject=SUBJECT, channel=channel, expected=provenance, transport=acquire.CurlTransport()
    )
    return channel, metadata


def _decode_job(job: tuple[str, dict[str, Any], list[dict[str, Any]]]) -> tuple[str, np.ndarray, dict[str, Any], int, int]:
    channel, metadata, events = job
    started = time.monotonic_ns()
    transport = _PersistentS3Transport()
    try:
        values, receipt = signal.process_eligible_event_windows(
            metadata, events, transport=transport,
            processor=lambda transient, _events: transient.copy(),
        )
    finally:
        transport.close()
    return channel, values, receipt, started, time.monotonic_ns()


def _observed_max_concurrency(intervals: list[tuple[int, int]]) -> int:
    active = maximum = 0
    for _, delta in sorted((point, delta) for start, end in intervals for point, delta in ((start, 1), (end, -1))):
        active += delta
        maximum = max(maximum, active)
    return maximum


def _resumable_site_receipt(payload: dict[str, Any], *, site: str, channels: int) -> bool:
    receipts = payload.get("channel_receipts")
    amendment = payload.get("amendment_id")
    configured = payload.get("max_signal_concurrency")
    version_matches = (
        (site in V1_SITES and amendment == AMENDMENT_V1 and configured == 4)
        or (site not in V1_SITES and amendment == AMENDMENT_ID and configured == SIGNAL_WORKERS)
    )
    return bool(
        payload.get("status") == "PASS_DEVELOPMENT_SITE_ENDPOINT"
        and payload.get("subject") == SUBJECT and payload.get("stimulation_site") == site
        and version_matches and payload.get("plan_sha256") == PLAN_SHA256
        and payload.get("channels") == channels and isinstance(receipts, list) and len(receipts) == channels
        and len({row.get("channel") for row in receipts}) == channels
        and all(row.get("cleanup") is True and row.get("persistent_raw_bytes") == 0 for row in receipts)
        and 1 <= payload.get("observed_max_concurrency", 0) <= configured
        and payload.get("persistent_raw_bytes") == 0 and payload.get("raw_tile_disposed") is True
        and payload.get("cross_site_signal_cache") is False
        and payload.get("decoded_value_cache_after_copy") is False
    )


def _source_texts(plan: dict[str, Any]) -> dict[str, str]:
    transport = acquire.CurlTransport()
    texts: dict[str, str] = {}
    for name, path in acquire._tsv_paths(SUBJECT).items():
        body = transport.get(
            acquire._url(acquire.RAW_PREFIX, path), timeout=acquire.TIMEOUT_SECONDS,
            max_bytes=acquire.MAX_TSV_BYTES,
        )
        if _sha(body) != plan["tsv_sha256"][name]:
            raise RuntimeError(f"{STOP}:TSV")
        texts[name] = body.decode("utf-8")
    return texts


def _channels(texts: dict[str, str]) -> list[str]:
    rows = list(csv.DictReader(io.StringIO(texts["channels"]), delimiter="\t"))
    return [
        row["name"].strip() for row in rows
        if row.get("name", "").strip()
        and row.get("status", "").strip().lower() == "good"
        and row.get("type", "").strip().lower() in {"ieeg", "seeg", "ecog"}
    ]


def _acquire_metadata(plan: dict[str, Any], channels: list[str], *, workers: int) -> dict[str, dict[str, Any]]:
    provenance = {row["channel"]: row for row in plan["channel_provenance"]}
    if set(channels) != set(provenance):
        raise RuntimeError(f"{STOP}:channel population")
    output: dict[str, dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_metadata_job, (channel, dict(provenance[channel]))) for channel in channels]
        for future in concurrent.futures.as_completed(futures):
            channel, metadata = future.result()
            output[channel] = metadata
            print(f"METADATA {len(output)}/{len(channels)} {channel}", flush=True)
    return output


def _registered_receivers(metadata_plan: dict[str, Any], site: str, order: dict[str, int]) -> dict[str, tuple[int, int]]:
    nodes: set[str] = set()
    for pair in metadata_plan["pairs"]:
        if pair["allocation"] != "development_apparatus":
            continue
        if pair["a"] == site:
            nodes.add(pair["b"])
        elif pair["b"] == site:
            nodes.add(pair["a"])
    return {
        node: (order[node.split("-")[0]], order[node.split("-")[1]])
        for node in sorted(nodes)
    }


def _run_site(
    site: str, events: list[dict[str, Any]], channels: list[str],
    metadata: dict[str, dict[str, Any]], metadata_plan: dict[str, Any], *, workers: int,
) -> dict[str, Any]:
    if workers != SIGNAL_WORKERS:
        raise ValueError(f"{STOP}:bounded signal concurrency")
    site_events = [row for row in events if row["node"] == site]
    if not site_events or len(site_events) > MAX_SITE_TRIALS:
        raise RuntimeError(f"{STOP}:site events")
    tile_shape = (len(site_events), len(channels), endpoint.WINDOW_SAMPLES)
    tile = np.empty(tile_shape, dtype=np.float64)
    receipts: list[dict[str, Any]] = []
    intervals: list[tuple[int, int]] = []
    order = {channel: index for index, channel in enumerate(channels)}
    try:
        jobs = [(channel, metadata[channel], site_events) for channel in channels]
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_decode_job, job) for job in jobs]
            for future in concurrent.futures.as_completed(futures):
                channel_name, values, receipt, started, ended = future.result()
                try:
                    tile[:, order[channel_name], :] = values
                finally:
                    values.fill(np.nan)
                intervals.append((started, ended))
                receipts.append({
                    "channel": channel_name, "payload_bytes": receipt["payload_bytes"],
                    "ranges": receipt["ranges"], "range_sha256": receipt["range_sha256"],
                    "tdat_sha256": metadata[channel_name]["identities"]["tdat"]["sha256"],
                    "tdat_bytes": metadata[channel_name]["identities"]["tdat"]["bytes"],
                    "tmet_sha256": metadata[channel_name]["identities"]["tmet"]["sha256"],
                    "cleanup": receipt["cleanup"], "persistent_raw_bytes": receipt["persistent_raw_bytes"],
                })
                print(f"SITE {site} {len(receipts)}/{len(channels)} {channel_name}", flush=True)
        if len(receipts) != len(channels) or {row["channel"] for row in receipts} != set(channels):
            raise RuntimeError(f"{STOP}:incomplete channel population")
        receivers = _registered_receivers(metadata_plan, site, order)
        if not receivers:
            raise RuntimeError(f"{STOP}:registered receivers")
        result = endpoint.site_endpoints(
            tile, stimulated=tuple(order[name] for name in site.split("-")),
            halves=[row["half"] for row in site_events], receiver_contacts=receivers,
        )
    finally:
        tile.fill(np.nan)
        del tile
    observed = _observed_max_concurrency(intervals)
    if observed > SIGNAL_WORKERS or observed < 1:
        raise RuntimeError(f"{STOP}:observed concurrency")
    return {
        "status": "PASS_DEVELOPMENT_SITE_ENDPOINT", "snapshot": planner.FROZEN_SNAPSHOT,
        "amendment_id": AMENDMENT_ID, "plan_sha256": PLAN_SHA256,
        "subject": SUBJECT, "stimulation_site": site, "trials": len(site_events),
        "channels": len(channels), "registered_receivers": len(receivers),
        "endpoints": result["endpoints"], "selected_car75_per_trial": result["selected_per_trial"],
        "payload_bytes": sum(row["payload_bytes"] for row in receipts),
        "channel_receipt_set_sha256": _sha(
            repr(sorted(receipts, key=lambda row: row["channel"])).encode()
        ),
        "metadata_cache_bytes": sum(
            len(row["tmet"]) + len(row["tidx"]) for row in metadata.values()
        ),
        "max_signal_concurrency": SIGNAL_WORKERS, "observed_max_concurrency": observed,
        "tile_shape": list(tile_shape), "tile_dtype": "float64",
        "site_tile_max_bytes": len(site_events) * len(channels) * endpoint.WINDOW_SAMPLES * 8,
        "extra_decoded_max_bytes": SIGNAL_WORKERS * len(site_events) * endpoint.WINDOW_SAMPLES * 8,
        "channel_receipts": sorted(receipts, key=lambda row: row["channel"]),
        "cross_site_signal_cache": False, "decoded_value_cache_after_copy": False,
        "persistent_raw_bytes": 0, "raw_tile_disposed": True, "endpoint_evidence": True,
        "development_gate_computed": False, "confirmation_opened": False,
    }


def _directed(site_results: dict[str, dict[str, Any]], metadata_plan: dict[str, Any]) -> tuple[dict[str, Any], int]:
    directed: dict[str, Any] = {}
    held_out = 0
    for pair in metadata_plan["pairs"]:
        if pair["allocation"] != "development_apparatus":
            held_out += 1
            continue
        for source, target in ((pair["a"], pair["b"]), (pair["b"], pair["a"])):
            cell = site_results[source]["endpoints"][target]
            directed[f"{source}->{target}"] = {
                half: {
                    "mean_early": cell[half]["mean"]["early"],
                    "mean_prestim": cell[half]["mean"]["prestim"],
                    "bip_early": cell[half]["bip"]["early"],
                    "bip_prestim": cell[half]["bip"]["prestim"],
                }
                for half in ("A", "B")
            }
    return directed, held_out


def main() -> None:
    root = Path(__file__).parent
    plan_path = root / "development-index-plan-sub-1-v4.json"
    if _sha(plan_path.read_bytes()) != PLAN_SHA256:
        raise RuntimeError(f"{STOP}:plan hash")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    texts = _source_texts(plan)
    events = planner.development_event_table(
        snapshot=planner.FROZEN_SNAPSHOT, subject=SUBJECT, events_tsv=texts["events"],
        channels_tsv=texts["channels"], electrodes_tsv=texts["electrodes"], fs_hz=2048,
    )
    channels = _channels(texts)
    metadata_plan = apparatus.canonical_metadata_plan(
        texts["channels"], texts["electrodes"], texts["events"],
        snapshot=planner.FROZEN_SNAPSHOT, subject=SUBJECT,
    )
    metadata = _acquire_metadata(plan, channels, workers=8)
    sites = sorted({row["node"] for row in events})
    results: dict[str, dict[str, Any]] = {}
    first = root / "development-first-site-sub-1.json"
    if first.exists() and _sha(first.read_bytes()) == FIRST_SITE_SHA256:
        payload = json.loads(first.read_text(encoding="utf-8"))
        results[payload["stimulation_site"]] = payload
    for site in sites:
        output = root / f"development-site-sub-1-{site}.json"
        if site in results:
            print(f"REUSE {site} {FIRST_SITE_SHA256}", flush=True)
            continue
        if output.exists():
            payload = json.loads(output.read_text(encoding="utf-8"))
            if _resumable_site_receipt(payload, site=site, channels=len(channels)):
                results[site] = payload
                print(f"RESUME {site} {_sha(output.read_bytes())}", flush=True)
                continue
        payload = _run_site(site, events, channels, metadata, metadata_plan, workers=SIGNAL_WORKERS)
        digest = _write_receipt(output, payload)
        results[site] = payload
        print(f"SITE_RESULT {site} {digest}", flush=True)
    directed, held_out = _directed(results, metadata_plan)
    gate = endpoint.development_gate(directed, held_out_pairs=held_out)
    receipt = {
        "status": gate["status"], "snapshot": planner.FROZEN_SNAPSHOT, "subject": SUBJECT,
        "sites": len(results), "events": len(events), "channels": len(channels),
        "site_receipts": {
            site: _sha((root / f"development-site-sub-1-{site}.json").read_bytes())
            if (root / f"development-site-sub-1-{site}.json").exists() else FIRST_SITE_SHA256
            for site in sites
        },
        "gate": gate, "persistent_raw_bytes": 0, "confirmation_opened": False,
    }
    digest = _write_receipt(root / "development-gate-sub-1.json", receipt)
    print(f"SUBJECT_GATE {gate['status']} {digest}", flush=True)
    print(json.dumps(gate, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
