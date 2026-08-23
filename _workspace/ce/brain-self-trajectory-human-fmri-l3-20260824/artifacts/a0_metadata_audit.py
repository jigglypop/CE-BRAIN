"""Metadata-only A0 audit for OpenNeuro ds006033 v1.0.1.

This program never issues GET or Range requests to a .eeg object.  It reads
only public text metadata and uses HEAD for the multi-GB binary objects.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import tempfile
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path


DOI = "10.18112/openneuro.ds006033.v1.0.1"
TAG = "1.0.1"
TAG_OBJECT = "3af0502b0664b80dacf015e76c436c9ba371527c"
CONTRACT_SHA256 = "2b08c0fd5eb69ae6f3d096a6542e248b6d2b69da985f90c7d06071e0690be50e"
SEED = "BA-SELF1-v1"
RAW_BASE = f"https://raw.githubusercontent.com/OpenNeuroDatasets/ds006033/{TAG}"
S3_BASE = "https://s3.amazonaws.com/openneuro.org/ds006033"
USER_AGENT = "CE-BA-SELF1-A0-metadata-audit/1"

CHANNELS = [
    "Fp1", "Fp2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2",
    "F7", "F8", "T7", "T8", "P7", "P8", "Fz", "Cz", "Pz", "Oz",
    "FC1", "FC2", "CP1", "CP2", "FC5", "FC6", "CP5", "CP6", "TP9",
    "TP10", "POz", "ECG", "F1", "F2", "C1", "C2", "P1", "P2",
    "AF3", "AF4", "FC3", "FC4", "CP3", "CP4", "PO3", "PO4", "F5",
    "F6", "C5", "C6", "P5", "P6", "AF7", "AF8", "FT7", "FT8",
    "TP7", "TP8", "PO7", "PO8", "FT9", "FT10", "Fpz", "CPz",
]

RECORDINGS = [
    ("sub-01", "ses-02", 8_992_173, 2_301_996_288, 125),
    ("sub-02", "ses-01", 6_842_855, 1_751_770_880, 89),
    ("sub-02", "ses-02", 5_398_776, 1_382_086_656, 75),
    ("sub-03", "ses-01", 9_114_213, 2_333_238_528, 125),
    ("sub-03", "ses-02", 9_042_659, 2_314_920_704, 125),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request(url: str, *, method: str = "GET", byte_range: str | None = None):
    headers = {"User-Agent": USER_AGENT}
    if byte_range is not None:
        headers["Range"] = byte_range
    req = urllib.request.Request(url, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read() if method != "HEAD" else b""
        return response.status, {k.lower(): v for k, v in response.headers.items()}, body


def get_text(url: str) -> tuple[str, dict]:
    status, headers, body = request(url)
    if status != 200:
        raise RuntimeError(f"GET status {status}: {url}")
    return body.decode("utf-8-sig"), {
        "url": url,
        "bytes": len(body),
        "sha256": sha256_bytes(body),
        "etag": headers.get("etag"),
    }


def parse_vhdr(text: str) -> dict:
    values: dict[str, str] = {}
    channels: dict[int, str] = {}
    history = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("; Data created from history path:"):
            history = stripped[2:].strip()
        if "=" in stripped and not stripped.startswith(";"):
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
        match = re.match(r"Ch(\d+)=([^,]+)", stripped)
        if match:
            channels.setdefault(int(match.group(1)), match.group(2).strip())
    ordered = [channels.get(i) for i in range(1, 65)]
    return {
        "number_of_channels": int(values["NumberOfChannels"]),
        "data_points": int(values["DataPoints"]),
        "sampling_interval_us": int(values["SamplingInterval"]),
        "data_orientation": values["DataOrientation"],
        "binary_format": values["BinaryFormat"],
        "channels": ordered,
        "history": history,
    }


def canonical_hash(subject: str, session: str, onset_text: str, word: str) -> str:
    payload = json.dumps(
        [DOI, subject, session, onset_text, word, SEED],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(payload)


def assign_splits(trials: list[dict]) -> None:
    by_subject: dict[str, list[dict]] = defaultdict(list)
    for trial in trials:
        by_subject[trial["subject"]].append(trial)

    plans = {
        "sub-01": [(8, "A1"), (24, "A2")],
        "sub-02": [(32, "D1"), (132, "D2")],
        "sub-03": [(25, "C1"), (50, "C2"), (175, "C3")],
    }
    for subject, subject_trials in by_subject.items():
        strata: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for trial in subject_trials:
            strata[(trial["session"], trial["word"])].append(trial)
        for values in strata.values():
            values.sort(key=lambda item: item["trial_hash"])
            for rank, item in enumerate(values):
                item["stratum_rank"] = rank
        ordered = sorted(
            subject_trials,
            key=lambda item: (
                item["stratum_rank"], item["session"], item["word"], item["trial_hash"]
            ),
        )
        cursor = 0
        for count, split in plans[subject]:
            for item in ordered[cursor : cursor + count]:
                item["split"] = split
            cursor += count
        for item in ordered[cursor:]:
            item["split"] = "UNUSED_SEALED"


def dump_atomic(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    sources: dict[str, dict] = {}
    description_text, sources["dataset_description"] = get_text(f"{RAW_BASE}/dataset_description.json")
    description = json.loads(description_text)
    changes_text, sources["changes"] = get_text(f"{RAW_BASE}/CHANGES")

    api_url = f"https://api.github.com/repos/OpenNeuroDatasets/ds006033/git/ref/tags/{TAG}"
    _, _, api_body = request(api_url)
    tag_object_observed = json.loads(api_body.decode("utf-8"))["object"]["sha"]

    recordings_receipt = []
    trials: list[dict] = []
    for subject, session, expected_points, expected_size, expected_valid in RECORDINGS:
        stem = f"{subject}_{session}_task-innerspeech"
        rel = f"{subject}/{session}/eeg"
        vhdr_url = f"{S3_BASE}/{rel}/{stem}_eeg.vhdr"
        sidecar_url = f"{RAW_BASE}/{rel}/{stem}_eeg.json"
        events_url = f"{RAW_BASE}/{rel}/{stem}_events.tsv"
        eeg_url = f"{S3_BASE}/{rel}/{stem}_eeg.eeg"

        vhdr_text, vhdr_source = get_text(vhdr_url)
        sidecar_text, sidecar_source = get_text(sidecar_url)
        events_text, events_source = get_text(events_url)
        sources[f"{subject}_{session}_vhdr"] = vhdr_source
        sources[f"{subject}_{session}_sidecar"] = sidecar_source
        sources[f"{subject}_{session}_events"] = events_source

        header = parse_vhdr(vhdr_text)
        sidecar = json.loads(sidecar_text)
        head_status, head_headers, _ = request(eeg_url, method="HEAD")
        observed_size = int(head_headers["content-length"])
        geometry_size = header["data_points"] * header["number_of_channels"] * 4

        if head_status != 200:
            raise RuntimeError(f"HEAD status {head_status}: {eeg_url}")
        if header["number_of_channels"] != 64 or header["channels"] != CHANNELS:
            raise RuntimeError(f"header channel schema mismatch: {subject}/{session}")
        if header["channels"][31] != "ECG":
            raise RuntimeError(f"ECG is not channel 32: {subject}/{session}")
        if header["data_points"] != expected_points:
            raise RuntimeError(f"DataPoints mismatch: {subject}/{session}")
        if observed_size != expected_size or geometry_size != expected_size:
            raise RuntimeError(f"binary byte geometry mismatch: {subject}/{session}")
        if header["sampling_interval_us"] != 200:
            raise RuntimeError(f"sampling interval mismatch: {subject}/{session}")
        if header["data_orientation"] != "MULTIPLEXED" or header["binary_format"] != "IEEE_FLOAT_32":
            raise RuntimeError(f"binary layout mismatch: {subject}/{session}")
        if not header["history"] or "Scanner Artifact Correction" not in header["history"]:
            raise RuntimeError(f"scanner correction history missing: {subject}/{session}")
        if "Pulse Artifact Correction" not in header["history"]:
            raise RuntimeError(f"pulse correction history missing: {subject}/{session}")

        rows = list(csv.DictReader(io.StringIO(events_text), delimiter="\t"))
        valid = []
        word_ordinal = 0
        for row in rows:
            if row["trial_type"] not in {"rest", "fixation"}:
                word_ordinal += 1
            duration = float(row["duration"])
            onset = float(row["onset"])
            if onset < 10.0 or duration < 1.9 or duration > 2.1:
                continue
            if row["trial_type"] in {"rest", "fixation"}:
                continue
            onset_text = row["onset"]
            valid.append((onset, onset_text, row["trial_type"], word_ordinal))
        valid.sort(key=lambda item: item[0])
        if len(valid) != expected_valid:
            raise RuntimeError(f"valid event count mismatch: {subject}/{session}")
        for ordinal, (onset, onset_text, word, source_ordinal) in enumerate(valid, start=1):
            trials.append({
                "subject": subject,
                "session": session,
                "run": "innerspeech",
                "onset": onset,
                "onset_text": onset_text,
                "word": word,
                "source_word_ordinal": source_ordinal,
                "valid_ordinal": ordinal,
                "task_anchor_s": onset + 1.2,
                "rest_anchor_s": onset + 7.2,
                "block_id": f"{subject}/{session}/b{(ordinal - 1) // 5:03d}",
                "trial_hash": canonical_hash(subject, session, onset_text, word),
            })

        recordings_receipt.append({
            "subject": subject,
            "session": session,
            "eeg_url": eeg_url,
            "content_length": observed_size,
            "etag": head_headers.get("etag"),
            "accept_ranges": head_headers.get("accept-ranges"),
            "header": header,
            "sidecar_counts": {
                "EEGChannelCount": sidecar.get("EEGChannelCount"),
                "ECGChannelCount": sidecar.get("ECGChannelCount"),
                "MiscChannelCount": sidecar.get("MiscChannelCount"),
            },
            "sidecar_count_sum": sum(
                int(sidecar.get(key, 0))
                for key in ("EEGChannelCount", "ECGChannelCount", "MiscChannelCount")
            ),
            "valid_trials": len(valid),
            "word_counts": dict(sorted(Counter(item[2] for item in valid).items())),
        })

    assign_splits(trials)
    split_counts = Counter(trial["split"] for trial in trials)
    recording_counts = Counter(f"{trial['subject']}/{trial['session']}" for trial in trials)
    expected_split_counts = {
        "A1": 8, "A2": 24, "D1": 32, "D2": 132,
        "C1": 25, "C2": 50, "C3": 175, "UNUSED_SEALED": 93,
    }
    if len(trials) != 539 or dict(split_counts) != expected_split_counts:
        raise RuntimeError(f"manifest arithmetic mismatch: {dict(split_counts)}")

    # Range semantics are tested only on a text metadata object, never on .eeg.
    range_url = f"{S3_BASE}/sub-01/ses-02/eeg/sub-01_ses-02_task-innerspeech_eeg.vhdr"
    range_status, range_headers, range_body = request(range_url, byte_range="bytes=0-63")
    if range_status != 206 or len(range_body) != 64 or not range_headers.get("content-range", "").startswith("bytes 0-63/"):
        raise RuntimeError("S3 metadata range semantics failed")

    manifest = {
        "schema": "BA-SELF1-A0-trial-manifest-v1",
        "contract_sha256": CONTRACT_SHA256,
        "dataset_doi": DOI,
        "hash_canonicalization": "json.dumps([DOI,subject,session,onset_text,word,seed],ensure_ascii=False,separators=(',',':')) UTF-8",
        "trials": sorted(trials, key=lambda item: (item["subject"], item["session"], item["onset"])),
    }
    dump_atomic(args.manifest, manifest)
    manifest_bytes = args.manifest.read_bytes()

    receipt = {
        "schema": "BA-SELF1-A0-metadata-receipt-v1",
        "status": "A0_METADATA_PASS_WITH_DECLARED_SIDECAR_DEFECT",
        "signal_values_opened": False,
        "eeg_get_requests": 0,
        "contract_sha256": CONTRACT_SHA256,
        "dataset": {
            "doi_expected": DOI,
            "doi_observed": description.get("DatasetDOI", "").removeprefix("doi:"),
            "tag": TAG,
            "tag_object_expected": TAG_OBJECT,
            "tag_object_observed": tag_object_observed,
            "license": description.get("License"),
            "bids_version": description.get("BIDSVersion"),
            "changes_contains_1_0_1": "1.0.1" in changes_text,
        },
        "recordings": recordings_receipt,
        "known_metadata_defect": {
            "description": "Each sidecar count sum is 66 while each vhdr/binary has 64 total channels and names ECG at index 32.",
            "sidecar_schema_used_for_binary": False,
            "binary_schema_authority": "BrainVision vhdr exact names/order plus Content-Length geometry",
        },
        "event_counts": dict(sorted(recording_counts.items())),
        "total_valid_trials": len(trials),
        "split_counts": dict(sorted(split_counts.items())),
        "allocated_scientific_or_apparatus": len(trials) - split_counts["UNUSED_SEALED"],
        "unused_sealed": split_counts["UNUSED_SEALED"],
        "manifest": {
            "path": str(args.manifest).replace("\\", "/"),
            "bytes": len(manifest_bytes),
            "sha256": sha256_bytes(manifest_bytes),
        },
        "metadata_range_test": {
            "url": range_url,
            "status": range_status,
            "bytes": len(range_body),
            "content_range": range_headers.get("content-range"),
            "sha256": sha256_bytes(range_body),
            "eeg_signal_object_tested": False,
        },
        "sources": sources,
        "checks": {
            "canonical_identity": description.get("DatasetDOI", "").removeprefix("doi:") == DOI and tag_object_observed == TAG_OBJECT,
            "five_recordings": len(recordings_receipt) == 5,
            "header_binary_geometry": all(item["content_length"] == item["header"]["data_points"] * 64 * 4 for item in recordings_receipt),
            "header_channel_order": all(item["header"]["channels"] == CHANNELS for item in recordings_receipt),
            "ecg_index_32": all(item["header"]["channels"][31] == "ECG" for item in recordings_receipt),
            "artifact_history": all(
                "Scanner Artifact Correction" in item["header"]["history"]
                and "Pulse Artifact Correction" in item["header"]["history"]
                for item in recordings_receipt
            ),
            "declared_sidecar_defect_reproduced": all(item["sidecar_count_sum"] == 66 for item in recordings_receipt),
            "valid_event_total_539": len(trials) == 539,
            "split_arithmetic_446_plus_93": sum(split_counts[name] for name in expected_split_counts if name != "UNUSED_SEALED") == 446 and split_counts["UNUSED_SEALED"] == 93,
            "metadata_range_206": range_status == 206,
        },
    }
    if not all(receipt["checks"].values()):
        raise RuntimeError(f"A0 check failed: {receipt['checks']}")
    dump_atomic(args.output, receipt)
    print(json.dumps({
        "status": receipt["status"],
        "total_valid_trials": len(trials),
        "split_counts": dict(sorted(split_counts.items())),
        "manifest_sha256": receipt["manifest"]["sha256"],
        "signal_values_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
