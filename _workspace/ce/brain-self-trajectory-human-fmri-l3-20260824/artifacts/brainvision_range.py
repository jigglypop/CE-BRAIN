"""Fail-closed, byte-range-only apparatus for BA-SELF1 A1/A2.

This module deliberately records request receipts and QC summaries only.  It
never writes EEG byte payloads or decoded sample arrays to disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
from scipy.signal import firwin, lfilter

MANIFEST_SHA256 = "4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061"
A0_RECEIPT_SHA256 = "5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7"
CONTRACT_SHA256 = "2b08c0fd5eb69ae6f3d096a6542e248b6d2b69da985f90c7d06071e0690be50e"
SAMPLE_RATE = 5_000
CHANNELS = 64
ECG_INDEX = 31
WARMUP = 500
PRE_ANCHOR = 2_500
POST_ANCHOR = 500
SAMPLES_PER_WINDOW = PRE_ANCHOR + POST_ANCHOR + 1
DECIMATION = 20
USER_AGENT = "CE-BA-SELF1-A1-A2-range/1"


class ApparatusInvalid(RuntimeError):
    """An input or receipt condition failed; no scientific endpoint is allowed."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def dump_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def anchor_to_sample(anchor_s: float) -> int:
    sample = anchor_s * SAMPLE_RATE
    rounded = round(sample)
    if not math.isclose(sample, rounded, rel_tol=0.0, abs_tol=1e-6):
        raise ApparatusInvalid(f"anchor is not on the 5 kHz grid: {anchor_s!r}")
    return int(rounded)


def byte_geometry(anchor_sample: int) -> tuple[int, int, int, int]:
    first_sample = anchor_sample - PRE_ANCHOR
    last_sample = anchor_sample + POST_ANCHOR
    if first_sample < 0:
        raise ApparatusInvalid(f"negative first sample: {first_sample}")
    start = first_sample * CHANNELS * 4
    end = (last_sample + 1) * CHANNELS * 4 - 1
    return first_sample, last_sample, start, end


def fetch_exact_range(url: str, start: int, end: int, total: int, expected_etag: str) -> tuple[bytes, dict]:
    request = urllib.request.Request(
        url,
        headers={"Range": f"bytes={start}-{end}", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            status = response.status
            headers = {key.lower(): value for key, value in response.headers.items()}
    except Exception as error:  # receipt is still written by main
        raise ApparatusInvalid(f"range request failed: {type(error).__name__}: {error}") from error
    expected_range = f"bytes {start}-{end}/{total}"
    expected_length = end - start + 1
    received_range = headers.get("content-range")
    received_etag = headers.get("etag")
    if status != 206 or received_range != expected_range or len(body) != expected_length or received_etag != expected_etag:
        raise ApparatusInvalid(
            "range receipt mismatch: "
            f"status={status}, content_range={received_range!r}, bytes={len(body)}, etag={received_etag!r}"
        )
    return body, {
        "url": url,
        "status": status,
        "content_range": received_range,
        "etag": received_etag,
        "bytes": len(body),
        "sha256": sha256_bytes(body),
    }


def parse_multiplexed_float32(raw: bytes) -> np.ndarray:
    expected = SAMPLES_PER_WINDOW * CHANNELS * 4
    if len(raw) != expected:
        raise ApparatusInvalid(f"float payload byte count {len(raw)} != {expected}")
    values = np.frombuffer(raw, dtype="<f4")
    if values.size != SAMPLES_PER_WINDOW * CHANNELS:
        raise ApparatusInvalid("float payload value count mismatch")
    return values.reshape(SAMPLES_PER_WINDOW, CHANNELS)


def causal_filter_and_decimate(samples: np.ndarray) -> np.ndarray:
    if samples.shape != (SAMPLES_PER_WINDOW, CHANNELS):
        raise ApparatusInvalid(f"sample shape mismatch: {samples.shape}")
    scalp = np.delete(samples, ECG_INDEX, axis=1).astype(np.float64, copy=False)
    common_average = scalp - scalp.mean(axis=1, keepdims=True)
    taps = firwin(501, 45, fs=SAMPLE_RATE, window="hamming")
    filtered = lfilter(taps, [1.0], common_average, axis=0)
    retained = filtered[WARMUP:]
    # WARMUP=500 and the anchor's local index=2500 make anchor index 2000,
    # exactly divisible by 20; no delay compensation or future samples occur.
    if (PRE_ANCHOR - WARMUP) % DECIMATION:
        raise ApparatusInvalid("anchor cannot be aligned on decimation grid")
    return retained[::DECIMATION]


def window_qc(window: np.ndarray) -> dict:
    if window.ndim != 2 or window.shape[1] != CHANNELS - 1:
        raise ApparatusInvalid(f"post-filter shape mismatch: {window.shape}")
    finite = np.isfinite(window)
    median = np.median(window, axis=0)
    mad = np.median(np.abs(window - median), axis=0)
    first_difference = np.diff(window, axis=0)
    return {
        "nonfinite_count": int(window.size - finite.sum()),
        "zero_mad_channel_count": int(np.count_nonzero(mad == 0.0)),
        "max_abs_common_reference_amplitude": float(np.max(np.abs(window))),
        "max_abs_first_difference": float(np.max(np.abs(first_difference))),
        "samples_after_warmup_and_decimation": int(window.shape[0]),
        "scalp_channels": int(window.shape[1]),
    }


def qc_cutoffs(metrics: list[dict]) -> dict:
    if len(metrics) != 64:
        raise ApparatusInvalid(f"A2 must freeze QC from 64 windows, got {len(metrics)}")
    result = {}
    for name in ("max_abs_common_reference_amplitude", "max_abs_first_difference"):
        values = np.asarray([item[name] for item in metrics], dtype=np.float64)
        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        if not np.isfinite(median) or not np.isfinite(mad) or mad == 0.0:
            raise ApparatusInvalid(f"APPARATUS_INVALID_QC_SCALE: {name} MAD={mad!r}")
        result[name] = {"median": median, "mad": mad, "cutoff": median + 6.0 * mad}
    return result


def recording_for(a0: dict, subject: str, session: str) -> dict:
    matches = [item for item in a0["recordings"] if item["subject"] == subject and item["session"] == session]
    if len(matches) != 1:
        raise ApparatusInvalid(f"recording absent or duplicated: {subject}/{session}")
    record = matches[0]
    if record["content_length"] != record["header"]["data_points"] * CHANNELS * 4:
        raise ApparatusInvalid("A0 binary geometry linkage failed")
    if record["header"]["channels"][ECG_INDEX] != "ECG":
        raise ApparatusInvalid("A0 ECG index linkage failed")
    return record


def run(stage: str, manifest_path: Path, a0_path: Path) -> dict:
    manifest_bytes = manifest_path.read_bytes()
    a0_bytes = a0_path.read_bytes()
    if sha256_bytes(manifest_bytes) != MANIFEST_SHA256:
        raise ApparatusInvalid("manifest hash mismatch")
    if sha256_bytes(a0_bytes) != A0_RECEIPT_SHA256:
        raise ApparatusInvalid("A0 receipt hash mismatch")
    manifest = json.loads(manifest_bytes)
    a0 = json.loads(a0_bytes)
    if manifest.get("contract_sha256") != CONTRACT_SHA256 or a0.get("contract_sha256") != CONTRACT_SHA256:
        raise ApparatusInvalid("contract linkage mismatch")
    allowed = {"A1"} if stage == "A1" else {"A1", "A2"}
    selected = [item for item in manifest["trials"] if item["split"] in allowed]
    required_trials = 8 if stage == "A1" else 32
    if len(selected) != required_trials or any(item["subject"] != "sub-01" or item["session"] != "ses-02" for item in selected):
        raise ApparatusInvalid(f"{stage} manifest selection is not the sealed sub-01/ses-02 slice")
    record = recording_for(a0, "sub-01", "ses-02")
    rows = []
    for trial in selected:
        for condition, anchor_key in (("task", "task_anchor_s"), ("rest", "rest_anchor_s")):
            anchor = anchor_to_sample(float(trial[anchor_key]))
            first, last, start, end = byte_geometry(anchor)
            raw, receipt = fetch_exact_range(record["eeg_url"], start, end, record["content_length"], record["etag"])
            parsed = parse_multiplexed_float32(raw)
            filtered = causal_filter_and_decimate(parsed)
            row = {
                "trial_hash": trial["trial_hash"], "valid_ordinal": trial["valid_ordinal"], "split": trial["split"],
                "condition": condition, "anchor_s": trial[anchor_key], "anchor_sample": anchor,
                "first_sample": first, "last_sample": last, "request": receipt, "qc": window_qc(filtered),
            }
            rows.append(row)
    if len(rows) != required_trials * 2:
        raise ApparatusInvalid("window-count mismatch")
    if stage == "A1" and any(row["qc"]["nonfinite_count"] != 0 for row in rows):
        raise ApparatusInvalid("A1 finite-value check failed")
    output = {
        "schema": "BA-SELF1-brainvision-range-apparatus-v1", "stage": stage,
        "status": f"{stage}_APPARATUS_PASS", "contract_sha256": CONTRACT_SHA256,
        "manifest_sha256": MANIFEST_SHA256, "a0_receipt_sha256": A0_RECEIPT_SHA256,
        "scientific_endpoint_opened": False, "unopened_splits": ["D1", "D2", "C1", "C2", "C3"],
        "filter": {"kind": "causal scipy.signal.lfilter", "firwin_taps": 501, "cutoff_hz": 45, "window": "hamming", "zero_phase": False},
        "windows": rows,
    }
    if stage == "A2":
        cutoffs = qc_cutoffs([row["qc"] for row in rows])
        for row in rows:
            qc = row["qc"]
            row["qc"]["invalid_nonfinite_or_zero_mad"] = qc["nonfinite_count"] > 0 or qc["zero_mad_channel_count"] > 0
            row["qc"]["exceeds_amplitude_cutoff"] = any(qc[name] > values["cutoff"] for name, values in cutoffs.items())
        pairs = {}
        for row in rows:
            pairs.setdefault(row["trial_hash"], []).append(row)
        output["pair_qc"] = [
            {
                "trial_hash": trial_hash,
                "excluded": any(
                    row["qc"]["invalid_nonfinite_or_zero_mad"] or row["qc"]["exceeds_amplitude_cutoff"]
                    for row in pair
                ),
            }
            for trial_hash, pair in sorted(pairs.items())
        ]
        output["frozen_qc_cutoffs"] = cutoffs
        output["pair_exclusion_rule"] = "exclude both task/rest if either window is invalid or exceeds either frozen cutoff"
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("A1", "A2"), required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--a0-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    base = {"schema": "BA-SELF1-brainvision-range-apparatus-v1", "stage": args.stage,
            "scientific_endpoint_opened": False, "unopened_splits": ["D1", "D2", "C1", "C2", "C3"]}
    try:
        receipt = run(args.stage, args.manifest, args.a0_receipt)
    except ApparatusInvalid as error:
        receipt = {**base, "status": "APPARATUS_INVALID", "error": str(error)}
        dump_atomic(args.output, receipt)
        print(json.dumps({"status": receipt["status"], "error": receipt["error"]}, sort_keys=True))
        return 2
    dump_atomic(args.output, receipt)
    print(json.dumps({"status": receipt["status"], "windows": len(receipt["windows"]), "scientific_endpoint_opened": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
