"""Sealed stage runner for BA-OBS-DISC2 actual human CCEP validation.

The runner separates endpoint opening from fitting.  ``open-stage`` writes an
exclusive stage-open marker before the first byte request and never stores raw
waveforms.  ``fit-stage`` can only consume the already sealed endpoint file.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence

for _thread_variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(_thread_variable, "1")

import numpy as np
import requests
from scipy.stats import spearmanr

from disc2_ccep_core import (
    ApparatusError,
    BIN_CENTERS_X,
    FitError,
    ProfileError,
    SourceData,
    candidate_mean,
    canonical_sha256,
    compute_source_endpoints,
    decode_selected_channels,
    equal_weight_objective,
    fetch_locked_range,
    fit_candidate,
    huber_loss,
    make_range_spec,
    participant_bootstrap,
    participant_improvements,
    profiled_huber_location,
    source_profile_and_loss,
)


RUN_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = Path(__file__).resolve().parent
CONTRACT = RUN_ROOT / "00-contract.md"
SOURCE_MANIFEST = ARTIFACTS / "metadata-source-manifest.json"
SPLIT_MANIFEST = ARTIFACTS / "endpoint-blind-split-manifest.json"
RUN_LOCK = RUN_ROOT / "run-lock.json"
PREIMPLEMENTATION_AUDIT = RUN_ROOT / "preimplementation-audit-receipt.json"
FIXTURE_RECEIPT = ARTIFACTS / "pre-d0-fixture-receipt-v2.json"
STAGES = ("D0", "D1", "D2", "D3")
CANDIDATES = ("SC", "SAC", "SH0", "SHA0")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
    ).encode("utf-8") + b"\n"
    if exclusive:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        return
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def verify_run_lock() -> tuple[dict[str, Any], str]:
    if not RUN_LOCK.is_file():
        raise RuntimeError("RUN_LOCK_MISSING")
    lock = load_json(RUN_LOCK)
    if lock.get("schema") != "BA-OBS-DISC2-run-lock-v1" or lock.get("status") != "LOCKED":
        raise RuntimeError("RUN_LOCK_INVALID")
    files = lock.get("files")
    if not isinstance(files, dict) or not files:
        raise RuntimeError("RUN_LOCK_FILES_INVALID")
    for relative_path, expected_hash in sorted(files.items()):
        path = RUN_ROOT / relative_path
        if not path.is_file():
            raise RuntimeError(f"RUN_LOCK_FILE_MISSING::{relative_path}")
        actual_hash = file_sha256(path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"RUN_LOCK_HASH_MISMATCH::{relative_path}::{actual_hash}::{expected_hash}"
            )
    return lock, file_sha256(RUN_LOCK)


def verify_preimplementation_audit(lock_hash: str) -> dict[str, Any]:
    if not PREIMPLEMENTATION_AUDIT.is_file():
        raise RuntimeError("PREIMPLEMENTATION_AUDIT_MISSING")
    receipt = load_json(PREIMPLEMENTATION_AUDIT)
    if receipt.get("verdict") != "PASS":
        raise RuntimeError("PREIMPLEMENTATION_AUDIT_NOT_PASS")
    if receipt.get("run_lock_sha256") != lock_hash:
        raise RuntimeError("PREIMPLEMENTATION_AUDIT_LOCK_MISMATCH")
    return receipt


def verify_fixture_receipt() -> dict[str, Any]:
    if not FIXTURE_RECEIPT.is_file():
        raise RuntimeError("PRE_D0_FIXTURE_RECEIPT_MISSING")
    receipt = load_json(FIXTURE_RECEIPT)
    if receipt.get("status") != "PASS" or receipt.get("final_fixture") is not True:
        raise RuntimeError("PRE_D0_FIXTURE_NOT_PASS")
    if int(receipt.get("null_replicates", -1)) != 64:
        raise RuntimeError("PRE_D0_FIXTURE_REPLICATE_MISMATCH")
    if int(receipt.get("null_false_selections", 65)) > 2:
        raise RuntimeError("PRE_D0_FIXTURE_FALSE_SELECTION_STOP")
    expected = {
        "contract_sha256": file_sha256(CONTRACT),
        "core_code_sha256": file_sha256(ARTIFACTS / "disc2_ccep_core.py"),
        "runner_code_sha256": file_sha256(Path(__file__)),
        "fixture_code_sha256": file_sha256(ARTIFACTS / "disc2_fixture.py"),
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise RuntimeError(f"PRE_D0_FIXTURE_HASH_MISMATCH::{key}")
    return receipt


def result_path(stage: str) -> Path:
    return ARTIFACTS / f"{stage.lower()}-result.json"


def endpoint_path(stage: str) -> Path:
    return ARTIFACTS / f"{stage.lower()}-endpoints.json"


def endpoint_receipt_path(stage: str) -> Path:
    return ARTIFACTS / f"{stage.lower()}-endpoint-receipt.json"


def range_receipt_path(stage: str) -> Path:
    return ARTIFACTS / f"{stage.lower()}-range-receipt.json"


def opened_path(stage: str) -> Path:
    return ARTIFACTS / f"{stage.lower()}-opened.json"


def failure_path(stage: str) -> Path:
    return ARTIFACTS / f"{stage.lower()}-failure.json"


def expected_predecessor(stage: str) -> tuple[str, str] | None:
    if stage == "D0":
        return None
    previous = STAGES[STAGES.index(stage) - 1]
    required = {
        "D1": "PASS_SELECTION_ONLY",
        "D2": "PASS_INTERMEDIATE",
        "D3": "PASS_INTERMEDIATE",
    }[stage]
    return previous, required


def verify_stage_barrier(stage: str, lock_hash: str, *, opening: bool) -> dict[str, Any]:
    if stage not in STAGES:
        raise RuntimeError(f"UNKNOWN_STAGE::{stage}")
    audit = verify_preimplementation_audit(lock_hash)
    fixture = verify_fixture_receipt()
    predecessor = expected_predecessor(stage)
    predecessor_receipt = None
    if predecessor is not None:
        previous, required_status = predecessor
        previous_path = result_path(previous)
        if not previous_path.is_file():
            raise RuntimeError(f"PREDECESSOR_RESULT_MISSING::{previous}")
        predecessor_receipt = load_json(previous_path)
        if predecessor_receipt.get("status") != required_status:
            raise RuntimeError(
                f"PREDECESSOR_STATUS_STOP::{previous}::{predecessor_receipt.get('status')}"
            )
        if predecessor_receipt.get("run_lock_sha256") != lock_hash:
            raise RuntimeError("PREDECESSOR_LOCK_MISMATCH")
    if opening:
        if opened_path(stage).exists() or endpoint_path(stage).exists():
            raise RuntimeError(f"STAGE_ALREADY_OPENED::{stage}")
    else:
        if not opened_path(stage).is_file() or not endpoint_path(stage).is_file():
            raise RuntimeError(f"STAGE_ENDPOINT_MISSING::{stage}")
        if result_path(stage).exists():
            raise RuntimeError(f"STAGE_ALREADY_FIT::{stage}")
    return {"audit": audit, "fixture": fixture, "predecessor": predecessor_receipt}


def _record_map(source_manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    records = source_manifest.get("recordings")
    if not isinstance(records, list):
        raise ApparatusError("source manifest recordings must be a list")
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        record_id = str(record.get("record_id"))
        if not record_id or record_id in result:
            raise ApparatusError("record_id is missing or duplicated")
        result[record_id] = record
    return result


def load_and_verify_manifests() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_manifest = load_json(SOURCE_MANIFEST)
    split_manifest = load_json(SPLIT_MANIFEST)
    if source_manifest.get("scientific_endpoint_opened") is not False:
        raise ApparatusError("source manifest endpoint-open flag is not false")
    if split_manifest.get("scientific_endpoint_opened") is not False:
        raise ApparatusError("split manifest endpoint-open flag is not false")
    source_hash = file_sha256(SOURCE_MANIFEST)
    if split_manifest.get("source_manifest_sha256") != source_hash:
        raise ApparatusError("split/source manifest SHA linkage failed")
    return source_manifest, split_manifest, _record_map(source_manifest)


def stage_subjects(split_manifest: Mapping[str, Any], stage: str) -> list[Mapping[str, Any]]:
    selected = [subject for subject in split_manifest.get("subjects", []) if subject.get("stage") == stage]
    expected = {"D0": 24, "D1": 8, "D2": 12, "D3": 30}[stage]
    if len(selected) != expected or len({subject.get("subject") for subject in selected}) != expected:
        raise ApparatusError(f"stage participant count mismatch for {stage}")
    if any(len(subject.get("sources", [])) != 8 for subject in selected):
        raise ApparatusError("each selected participant must have eight sources")
    return selected


def _ordered_trials(
    source: Mapping[str, Any], record: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], tuple[list[int], list[int]], dict[str, list[int]]]:
    halves = source.get("temporal_repeatability_halves")
    if not isinstance(halves, dict) or set(halves) != {"A", "B"}:
        raise ApparatusError("temporal halves are missing")
    if len(halves["A"]) != 5 or len(halves["B"]) != 5:
        raise ApparatusError("temporal halves are not 5/5")
    by_event: dict[int, dict[str, Any]] = {}
    for trial in halves["A"] + halves["B"]:
        event_index = int(trial["event_index"])
        normalized = {
            "event_index": event_index,
            "anchor_sample_zero_based": int(trial["anchor_sample_zero_based"]),
            "orientation_site": str(trial["orientation_site"]),
        }
        if event_index in by_event and by_event[event_index] != normalized:
            raise ApparatusError("duplicate event has inconsistent trial metadata")
        by_event[event_index] = normalized
    if len(by_event) != 10:
        raise ApparatusError("source does not have ten unique trials")
    ordered = [by_event[index] for index in sorted(by_event)]
    position = {trial["event_index"]: index for index, trial in enumerate(ordered)}
    half_positions = (
        [position[int(trial["event_index"])] for trial in halves["A"]],
        [position[int(trial["event_index"])] for trial in halves["B"]],
    )

    crosswalk = record.get("event_sample_crosswalk")
    if not isinstance(crosswalk, dict):
        raise ApparatusError("record event/sample crosswalk is missing")
    for trial in ordered:
        event_key = str(trial["event_index"])
        if event_key not in crosswalk or int(crosswalk[event_key]) != trial["anchor_sample_zero_based"]:
            raise ApparatusError("sealed event/sample crosswalk mismatch")

    orientation_positions: dict[str, list[int]] = {}
    groups = source.get("orientation_groups") or {}
    for label, trials in groups.items():
        indexes = [position[int(trial["event_index"])] for trial in trials]
        if len(indexes) not in (5, 10):
            raise ApparatusError("orientation group must have five or ten trials")
        orientation_positions[str(label)] = indexes
    mode = source.get("orientation_mode")
    if mode == "two_orientation_5_by_5":
        if len(orientation_positions) != 2 or any(
            len(indexes) != 5 for indexes in orientation_positions.values()
        ):
            raise ApparatusError("two-orientation source is not a sealed 5/5 partition")
    elif mode == "single_orientation_temporal_only":
        if len(orientation_positions) != 1:
            raise ApparatusError("single-orientation source has inconsistent groups")
        # A ten-trial single orientation is not a polarity comparison.  It is
        # intentionally absent from the orientation endpoint/control.
        orientation_positions = {}
    else:
        raise ApparatusError(f"unknown orientation mode: {mode}")
    return ordered, half_positions, orientation_positions


def _selected_contact_plan(
    source: Mapping[str, Any], record: Mapping[str, Any]
) -> tuple[list[str], dict[str, tuple[int, int]], list[Mapping[str, Any]]]:
    targets = list(source.get("anchors", [])) + list(source.get("evaluation", []))
    if len(source.get("anchors", [])) != 4 or len(source.get("evaluation", [])) != 12:
        raise ApparatusError("source anchor/query count is not 4/12")
    target_ids = [str(target["site_id"]) for target in targets]
    if len(set(target_ids)) != 16:
        raise ApparatusError("target site IDs are duplicated")
    source_contacts = set(str(value) for value in source.get("contacts", []))
    contact_names: list[str] = []
    for target in targets:
        contacts = [str(value) for value in target.get("contacts", [])]
        if len(contacts) != 2 or contacts[0] == contacts[1]:
            raise ApparatusError("receiver target is not a distinct contact pair")
        if source_contacts.intersection(contacts):
            raise ApparatusError("receiver overlaps stimulation-source contact")
        contact_names.extend(contacts)
    contact_names = list(dict.fromkeys(contact_names))
    channels = record.get("channels")
    if not isinstance(channels, dict):
        raise ApparatusError("record channel map is missing")
    for contact in contact_names:
        if contact not in channels:
            raise ApparatusError(f"selected contact missing from source record: {contact}")
        channel = channels[contact]
        if channel.get("type") != "ECOG" or channel.get("status") != "good":
            raise ApparatusError(f"selected contact is not good ECoG: {contact}")
        if not math.isfinite(float(channel.get("resolution"))) or float(channel["resolution"]) <= 0.0:
            raise ApparatusError(f"selected contact resolution is invalid: {contact}")
    selected_position = {contact: index for index, contact in enumerate(contact_names)}
    target_pairs = {
        str(target["site_id"]): (
            selected_position[str(target["contacts"][0])],
            selected_position[str(target["contacts"][1])],
        )
        for target in targets
    }
    return contact_names, target_pairs, targets


def _request_with_retry(url: str, **kwargs: Any) -> requests.Response:
    delay = 0.5
    last_error: BaseException | None = None
    for attempt in range(5):
        try:
            response = requests.get(url, **kwargs)
            if response.status_code < 500:
                return response
            last_error = ApparatusError(f"transient HTTP {response.status_code}")
        except requests.RequestException as error:
            last_error = error
        if attempt < 4:
            time.sleep(delay)
            delay *= 2.0
    raise ApparatusError(f"range request exhausted retries: {last_error}")


def process_source(
    *,
    stage: str,
    subject: Mapping[str, Any],
    source: Mapping[str, Any],
    record: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if record.get("record_id") != source.get("record_id"):
        raise ApparatusError("source/record ID mismatch")
    if record.get("subject") != subject.get("subject"):
        raise ApparatusError("source record crosses participant boundary")
    if not str(source.get("site_id", "")).startswith(f"{record.get('session')}|"):
        raise ApparatusError("source site/session mismatch")

    trials, temporal_positions, orientation_positions = _ordered_trials(source, record)
    contact_names, target_pairs, targets = _selected_contact_plan(source, record)
    channels = record["channels"]
    channel_indexes = [int(channels[name]["index"]) for name in contact_names]
    if len(set(channel_indexes)) != len(channel_indexes):
        raise ApparatusError("selected contacts map to duplicate recording indexes")
    resolutions = [float(channels[name]["resolution"]) for name in contact_names]
    units = [str(channels[name]["units"]) for name in contact_names]

    sampling_frequency = float(record["authoritative_sampling_frequency_hz"])
    channel_count = int(record["header"]["number_of_channels"])
    sample_count = int(record["sample_count"])
    source_identity = record["source"]

    def fetch_trial(trial: Mapping[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
        spec = make_range_spec(
            sampling_frequency,
            channel_count,
            int(trial["anchor_sample_zero_based"]),
            sample_count,
        )
        payload, receipt = fetch_locked_range(
            _request_with_retry,
            locked_url=str(source_identity["locked_url"]),
            etag=str(source_identity["etag"]),
            version_id=str(source_identity["version_id"]),
            content_length=int(source_identity["content_length"]),
            spec=spec,
        )
        selected = decode_selected_channels(
            payload, spec, channel_indexes, resolutions, units
        )
        receipt.update(
            {
                "stage": stage,
                "subject": str(subject["subject"]),
                "record_id": str(record["record_id"]),
                "source_id": str(source["site_id"]),
                "event_index": int(trial["event_index"]),
                "anchor_sample_zero_based": int(trial["anchor_sample_zero_based"]),
                "cache_key": [
                    stage,
                    str(subject["subject"]),
                    str(record["record_id"]),
                    int(trial["event_index"]),
                ],
            }
        )
        return selected, receipt

    with ThreadPoolExecutor(max_workers=10) as executor:
        fetched = list(executor.map(fetch_trial, trials))
    trial_arrays = np.stack([item[0] for item in fetched], axis=0)
    range_receipts = [item[1] for item in fetched]
    spec = make_range_spec(
        sampling_frequency,
        channel_count,
        int(trials[0]["anchor_sample_zero_based"]),
        sample_count,
    )
    endpoints = compute_source_endpoints(
        trial_arrays,
        spec,
        target_pairs,
        temporal_positions,
        orientation_positions,
    )

    source_center = np.asarray(source["center_xyz_mm"], dtype=np.float64)
    rows = []
    anchor_ids = {str(target["site_id"]) for target in source["anchors"]}
    for target in targets:
        target_id = str(target["site_id"])
        target_center = np.asarray(target["center_xyz_mm"], dtype=np.float64)
        delta = (target_center - source_center) / 50.0
        rows.append(
            {
                "role": "anchor" if target_id in anchor_ids else "query",
                "site_id": target_id,
                "site": str(target["site"]),
                "contacts": [str(value) for value in target["contacts"]],
                "center_xyz_mm": target_center.tolist(),
                "distance_mm": float(target["distance_mm"]),
                "distance_stratum": int(target["distance_stratum"]),
                "delta_over_50mm": delta.tolist(),
                "endpoint": endpoints[target_id],
            }
        )
    source_result = {
        "subject": str(subject["subject"]),
        "stage": stage,
        "d0_fold": subject.get("d0_fold"),
        "age_years": float(subject["age_years"]),
        "source_id": str(source["site_id"]),
        "source_site": str(source["site"]),
        "source_contacts": [str(value) for value in source["contacts"]],
        "source_center_xyz_mm": source_center.tolist(),
        "record_id": str(record["record_id"]),
        "sampling_frequency_hz": sampling_frequency,
        "orientation_mode": str(source["orientation_mode"]),
        "targets": rows,
    }
    return source_result, range_receipts


def _pooled_spearman(first: Sequence[float], second: Sequence[float]) -> float:
    if len(first) != len(second) or len(first) < 2:
        return float("nan")
    statistic = float(spearmanr(first, second).statistic)
    return statistic


def apparatus_metrics(stage: str, sources: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    temporal_first: list[float] = []
    temporal_second: list[float] = []
    orientation_first: list[float] = []
    orientation_second: list[float] = []
    post_pre_ratios: list[float] = []
    orientation_sources = 0
    orientation_participants: set[str] = set()
    target_count = 0
    for source in sources:
        if len(source["targets"]) != 16:
            raise ApparatusError("source endpoint target count is not 16")
        for target in source["targets"]:
            endpoint = target["endpoint"]
            if not math.isfinite(float(endpoint["baseline_sigma_uv"])) or float(
                endpoint["baseline_sigma_uv"]
            ) <= 0.0:
                raise ApparatusError("endpoint baseline scale is invalid")
            half = endpoint["temporal_half_energy"]
            temporal_first.extend(float(value) for value in half[0])
            temporal_second.extend(float(value) for value in half[1])
            post = np.asarray(endpoint["energy"], dtype=np.float64)
            pre = np.asarray(endpoint["pre_energy"], dtype=np.float64)
            if np.any(pre <= 0.0) or not np.isfinite(post).all() or not np.isfinite(pre).all():
                raise ApparatusError("post/pre endpoint energy is invalid")
            post_pre_ratios.extend((post / pre).tolist())
            target_count += 1
        if source["orientation_mode"] == "two_orientation_5_by_5":
            orientation_sources += 1
            orientation_participants.add(str(source["subject"]))
            for target in source["targets"]:
                groups = target["endpoint"]["orientation_energy"]
                if len(groups) != 2:
                    raise ApparatusError("two-orientation endpoint is missing groups")
                labels = sorted(groups)
                orientation_first.extend(float(value) for value in groups[labels[0]])
                orientation_second.extend(float(value) for value in groups[labels[1]])

    temporal_rho = _pooled_spearman(temporal_first, temporal_second)
    orientation_rho = _pooled_spearman(orientation_first, orientation_second)
    median_ratio = float(np.median(np.asarray(post_pre_ratios, dtype=np.float64)))
    metrics = {
        "stage": stage,
        "source_count": len(sources),
        "target_count": target_count,
        "temporal_repeatability_pooled_spearman": temporal_rho,
        "orientation_source_count": orientation_sources,
        "orientation_participant_count": len(orientation_participants),
        "orientation_specific_pooled_spearman": orientation_rho,
        "median_paired_post_over_pre_energy_ratio": median_ratio,
    }
    if stage == "D0":
        checks = {
            "source_count_192": len(sources) == 192,
            "target_count_3072": target_count == 192 * 16,
            "temporal_repeatability_at_least_0_30": math.isfinite(temporal_rho)
            and temporal_rho >= 0.30,
            "orientation_source_at_least_32": orientation_sources >= 32,
            "orientation_participant_at_least_4": len(orientation_participants) >= 4,
            "orientation_repeatability_at_least_0_20": math.isfinite(orientation_rho)
            and orientation_rho >= 0.20,
            "post_over_pre_at_least_1_25": math.isfinite(median_ratio)
            and median_ratio >= 1.25,
        }
        metrics["checks"] = checks
        metrics["status"] = "PASS" if all(checks.values()) else "APPARATUS_STOP"
    else:
        metrics["status"] = "PASS_INTEGRITY"
    return metrics


def open_stage(stage: str) -> dict[str, Any]:
    lock, lock_hash = verify_run_lock()
    barrier = verify_stage_barrier(stage, lock_hash, opening=True)
    source_manifest, split_manifest, records = load_and_verify_manifests()
    subjects = stage_subjects(split_manifest, stage)
    marker = {
        "schema": "BA-OBS-DISC2-stage-open-v1",
        "stage": stage,
        "opened_at_utc": utc_now(),
        "run_lock_sha256": lock_hash,
        "contract_sha256": file_sha256(CONTRACT),
        "source_manifest_sha256": file_sha256(SOURCE_MANIFEST),
        "split_manifest_sha256": file_sha256(SPLIT_MANIFEST),
        "preimplementation_audit_sha256": file_sha256(PREIMPLEMENTATION_AUDIT),
        "pre_d0_fixture_receipt_sha256": file_sha256(FIXTURE_RECEIPT),
        "predecessor_result_sha256": (
            file_sha256(result_path(STAGES[STAGES.index(stage) - 1]))
            if stage != "D0"
            else None
        ),
        "status": "OPENED_IRREVERSIBLY",
    }
    atomic_write_json(opened_path(stage), marker, exclusive=True)

    source_results: list[dict[str, Any]] = []
    range_receipts: list[dict[str, Any]] = []
    seen_cache_keys: set[tuple[Any, ...]] = set()
    try:
        total_sources = len(subjects) * 8
        completed = 0
        for subject in subjects:
            for source in subject["sources"]:
                record_id = str(source["record_id"])
                if record_id not in records:
                    raise ApparatusError(f"source record is absent: {record_id}")
                source_result, receipts = process_source(
                    stage=stage,
                    subject=subject,
                    source=source,
                    record=records[record_id],
                )
                for receipt in receipts:
                    key = tuple(receipt["cache_key"])
                    if key in seen_cache_keys:
                        raise ApparatusError(f"range cache-key collision: {key}")
                    seen_cache_keys.add(key)
                range_receipts.extend(receipts)
                source_results.append(source_result)
                completed += 1
                if completed % 8 == 0 or completed == total_sources:
                    print(
                        json.dumps(
                            {
                                "stage": stage,
                                "endpoint_sources_complete": completed,
                                "endpoint_sources_total": total_sources,
                            }
                        ),
                        flush=True,
                    )

        expected_ranges = total_sources * 10
        if len(range_receipts) != expected_ranges:
            raise ApparatusError(
                f"range receipt count mismatch: {len(range_receipts)} != {expected_ranges}"
            )
        range_document = {
            "schema": "BA-OBS-DISC2-range-receipt-v1",
            "stage": stage,
            "run_lock_sha256": lock_hash,
            "raw_payload_persisted": False,
            "range_count": len(range_receipts),
            "ranges": range_receipts,
            "status": "PASS",
        }
        atomic_write_json(range_receipt_path(stage), range_document)
        endpoints_document = {
            "schema": "BA-OBS-DISC2-endpoints-v1",
            "stage": stage,
            "run_lock_sha256": lock_hash,
            "endpoint_definition": "baseline-subtracted bipolar; pooled-baseline 1.4826 MAD; ten-trial mean; five-bin dimensionless RMS; log(E+1e-6)",
            "bin_centers_x": BIN_CENTERS_X.tolist(),
            "source_count": len(source_results),
            "sources": source_results,
        }
        atomic_write_json(endpoint_path(stage), endpoints_document)
        metrics = apparatus_metrics(stage, source_results)
        receipt = {
            "schema": "BA-OBS-DISC2-endpoint-receipt-v1",
            "stage": stage,
            "run_lock_sha256": lock_hash,
            "range_receipt_sha256": file_sha256(range_receipt_path(stage)),
            "endpoint_sha256": file_sha256(endpoint_path(stage)),
            "raw_payload_persisted": False,
            "apparatus": metrics,
            "status": metrics["status"],
        }
        atomic_write_json(endpoint_receipt_path(stage), receipt)
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True), flush=True)
        return receipt
    except BaseException as error:
        failure = {
            "schema": "BA-OBS-DISC2-stage-failure-v1",
            "stage": stage,
            "run_lock_sha256": lock_hash,
            "failed_at_utc": utc_now(),
            "error_type": type(error).__name__,
            "error": str(error),
            "status": "IRREVERSIBLE_STAGE_FAILURE",
        }
        atomic_write_json(failure_path(stage), failure)
        raise


def endpoint_sources(path: Path, endpoint_field: str = "z") -> list[SourceData]:
    document = load_json(path)
    result = []
    for source in document["sources"]:
        anchors = [target for target in source["targets"] if target["role"] == "anchor"]
        queries = [target for target in source["targets"] if target["role"] == "query"]
        if len(anchors) != 4 or len(queries) != 12:
            raise FitError("endpoint source does not have 4/12 anchor/query rows")
        result.append(
            SourceData(
                subject=str(source["subject"]),
                source_id=str(source["source_id"]),
                age_tilde=(float(source["age_years"]) - 20.0) / 20.0,
                anchor_delta=np.asarray(
                    [target["delta_over_50mm"] for target in anchors], dtype=np.float64
                ),
                query_delta=np.asarray(
                    [target["delta_over_50mm"] for target in queries], dtype=np.float64
                ),
                anchor_z=np.asarray(
                    [target["endpoint"][endpoint_field] for target in anchors],
                    dtype=np.float64,
                ),
                query_z=np.asarray(
                    [target["endpoint"][endpoint_field] for target in queries],
                    dtype=np.float64,
                ),
            ).validated()
        )
    return result


def _equal_weight_loss_from_map(
    sources: Sequence[SourceData], losses: Mapping[tuple[str, str], float]
) -> float:
    by_subject: dict[str, list[float]] = {}
    for source in sources:
        by_subject.setdefault(source.subject, []).append(
            float(losses[(source.subject, source.source_id)])
        )
    return float(np.mean([np.mean(values) for values in by_subject.values()]))


def d0_cross_validated_selection(
    sources: Sequence[SourceData], fold_by_subject: Mapping[str, int]
) -> dict[str, Any]:
    if set(fold_by_subject.values()) != set(range(6)):
        raise FitError("D0 fold map must contain folds zero through five")
    by_candidate: dict[str, dict[str, Any]] = {
        name: {"folds": [], "admissible": True} for name in ("S0",) + CANDIDATES
    }
    for fold in range(6):
        training = [source for source in sources if fold_by_subject[source.subject] != fold]
        testing = [source for source in sources if fold_by_subject[source.subject] == fold]
        if len({source.subject for source in testing}) != 4:
            raise FitError(f"D0 fold {fold} does not contain four held-out participants")
        fitted: dict[str, Any] = {}
        for name in ("S0",) + CANDIDATES:
            try:
                fit = fit_candidate(training, name)
                losses = {
                    (source.subject, source.source_id): source_profile_and_loss(
                        source, name, fit.parameters
                    )[1]
                    for source in testing
                }
                test_loss = _equal_weight_loss_from_map(testing, losses)
            except (FitError, ProfileError, FloatingPointError) as error:
                by_candidate[name]["admissible"] = False
                by_candidate[name]["folds"].append(
                    {"fold": fold, "status": "NUMERICAL_STOP", "error": str(error)}
                )
                continue
            fitted[name] = {"fit": fit, "test_loss": test_loss}
            by_candidate[name]["folds"].append(
                {
                    "fold": fold,
                    "status": "PASS",
                    "test_loss": test_loss,
                    "fit": fit.as_dict(),
                }
            )
        if "S0" not in fitted:
            raise FitError(f"D0_S0_NUMERICAL_STOP::{fold}")
        baseline_loss = fitted["S0"]["test_loss"]
        for name in CANDIDATES:
            if name in fitted:
                fold_receipt = by_candidate[name]["folds"][-1]
                fold_receipt["relative_improvement"] = 1.0 - (
                    fitted[name]["test_loss"] / baseline_loss
                )
                fold_receipt["beats_s0"] = fitted[name]["test_loss"] < baseline_loss

    baseline_folds = by_candidate["S0"]["folds"]
    if not by_candidate["S0"]["admissible"] or len(baseline_folds) != 6:
        raise FitError("D0_S0_NUMERICAL_STOP")
    baseline_mean = float(np.mean([fold["test_loss"] for fold in baseline_folds]))
    survivors = []
    for name in CANDIDATES:
        entry = by_candidate[name]
        passed_folds = [fold for fold in entry["folds"] if fold.get("status") == "PASS"]
        if len(passed_folds) != 6:
            entry.update(
                {
                    "cv_mean_loss": None,
                    "cv_relative_improvement": None,
                    "fold_wins": sum(bool(fold.get("beats_s0")) for fold in passed_folds),
                    "survives": False,
                }
            )
            continue
        mean_loss = float(np.mean([fold["test_loss"] for fold in passed_folds]))
        improvement = 1.0 - mean_loss / baseline_mean
        fold_wins = sum(bool(fold["beats_s0"]) for fold in passed_folds)
        survives = bool(
            entry["admissible"] and improvement >= 0.005 and fold_wins >= 4
        )
        entry.update(
            {
                "cv_mean_loss": mean_loss,
                "cv_relative_improvement": improvement,
                "fold_wins": fold_wins,
                "survives": survives,
            }
        )
        if survives:
            geometry_dof = 1 if name in ("SC", "SH0") else 3
            survivors.append((name, improvement, geometry_dof))
    survivors.sort(key=lambda row: (-row[1], row[2], row[0]))
    winner = None
    if survivors:
        best_improvement = survivors[0][1]
        tied = [row for row in survivors if best_improvement - row[1] <= 0.005]
        tied.sort(key=lambda row: (row[2], row[0]))
        winner = tied[0][0]
    return {
        "baseline_cv_mean_loss": baseline_mean,
        "candidates": by_candidate,
        "survivors": [row[0] for row in survivors],
        "winner": winner,
        "status": "PASS_SELECTION_ONLY"
        if winner is not None
        else "D0_NO_GEOMETRIC_EQUATION_SURVIVED",
    }


def _fold_map_from_split() -> dict[str, int]:
    split = load_json(SPLIT_MANIFEST)
    result = {
        str(subject["subject"]): int(subject["d0_fold"])
        for subject in split["subjects"]
        if subject["stage"] == "D0"
    }
    if len(result) != 24:
        raise FitError("D0 fold map does not contain 24 participants")
    return result


def geometry_permutation_test(
    sources: Sequence[SourceData],
    baseline_parameters: np.ndarray,
    winner_name: str,
    winner_parameters: np.ndarray,
    *,
    stage: str,
    contract_hash: str,
    replicates: int,
) -> dict[str, Any]:
    participant, _ = participant_improvements(
        sources, baseline_parameters, winner_name, winner_parameters
    )
    observed = float(np.mean(list(participant.values())))
    baseline_loss_by_source: dict[tuple[str, str], float] = {}
    winner_anchor_offset: dict[tuple[str, str], float] = {}
    winner_temporal_geometry: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]] = {}
    for source in sources:
        key = (source.subject, source.source_id)
        _, baseline_loss, _ = source_profile_and_loss(source, "S0", baseline_parameters)
        baseline_loss_by_source[key] = baseline_loss
        anchor_mean = candidate_mean(
            winner_name, winner_parameters, source.age_tilde, source.anchor_delta
        )
        winner_anchor_offset[key] = profiled_huber_location(source.anchor_z - anchor_mean)
        winner_temporal_geometry[key] = (
            source.query_z,
            source.query_delta,
        )

    exceedances = 0
    permutation_hash = hashlib.sha256()
    for replicate in range(replicates):
        by_subject: dict[str, list[float]] = {}
        for source in sources:
            key = (source.subject, source.source_id)
            seed = (
                f"BA-OBS-DISC2::geometry-permutation::{contract_hash}::{stage}::"
                f"{replicate}::{source.subject}::{source.source_id}"
            )
            raw_seed = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big")
            generator = np.random.Generator(np.random.PCG64(raw_seed))
            permutation = generator.permutation(12)
            permutation_hash.update(permutation.astype("<i8", copy=False).tobytes())
            response, geometry = winner_temporal_geometry[key]
            prediction = candidate_mean(
                winner_name,
                winner_parameters,
                source.age_tilde,
                geometry[permutation],
            ) + winner_anchor_offset[key]
            winner_loss = float(np.mean(huber_loss(response - prediction)))
            improvement = baseline_loss_by_source[key] - winner_loss
            by_subject.setdefault(source.subject, []).append(improvement)
        permuted_mean = float(
            np.mean([np.mean(values) for values in by_subject.values()])
        )
        if permuted_mean >= observed:
            exceedances += 1
    return {
        "replicates": replicates,
        "observed_mean_improvement": observed,
        "exceedances": exceedances,
        "p_value": (1.0 + exceedances) / (replicates + 1.0),
        "permutation_index_sha256": permutation_hash.hexdigest(),
    }


def _prior_stage_sources(stage: str, endpoint_field: str = "z") -> list[SourceData]:
    current_index = STAGES.index(stage)
    result: list[SourceData] = []
    for prior in STAGES[:current_index]:
        result.extend(endpoint_sources(endpoint_path(prior), endpoint_field))
    return result


def evaluate_fixed_structure(
    *,
    training: Sequence[SourceData],
    testing: Sequence[SourceData],
    winner_name: str,
    stage: str,
    endpoint_label: str,
) -> dict[str, Any]:
    baseline_fit = fit_candidate(training, "S0")
    winner_fit = fit_candidate(training, winner_name)
    participant, source_improvement = participant_improvements(
        testing, baseline_fit.parameters, winner_name, winner_fit.parameters
    )
    bootstrap_quantile = {"D1": 0.20, "D2": 0.20, "D3": 0.025}[stage]
    contract_hash = file_sha256(CONTRACT)
    bootstrap = participant_bootstrap(
        participant,
        replicates=8192,
        seed_material=(
            f"BA-OBS-DISC2::participant-bootstrap::{contract_hash}::"
            f"{stage}::{endpoint_label}"
        ),
        lower_quantile=bootstrap_quantile,
    )
    permutation_replicates = {"D1": 511, "D2": 1023, "D3": 4095}[stage]
    permutation = geometry_permutation_test(
        testing,
        baseline_fit.parameters,
        winner_name,
        winner_fit.parameters,
        stage=f"{stage}::{endpoint_label}",
        contract_hash=contract_hash,
        replicates=permutation_replicates,
    )
    mean_improvement = float(np.mean(list(participant.values())))
    positive = int(sum(value > 0.0 for value in participant.values()))
    if stage == "D1":
        passed = (
            mean_improvement > 0.0
            and positive >= 6
            and permutation["p_value"] <= 0.20
        )
    elif stage == "D2":
        passed = (
            bootstrap["lower_bound"] > 0.0
            and positive >= 8
            and permutation["p_value"] <= 0.10
        )
    else:
        passed = (
            bootstrap["lower_bound"] > 0.0
            and positive >= 20
            and permutation["p_value"] <= 0.025
        )
    return {
        "endpoint_label": endpoint_label,
        "baseline_fit": baseline_fit.as_dict(),
        "winner_fit": winner_fit.as_dict(),
        "participant_improvements": participant,
        "source_improvements": {
            f"{key[0]}::{key[1]}": value
            for key, value in source_improvement.items()
        },
        "mean_improvement": mean_improvement,
        "positive_participants": positive,
        "bootstrap": bootstrap,
        "geometry_permutation": permutation,
        "passes_stage_gate": passed,
    }


def fit_stage(stage: str) -> dict[str, Any]:
    _, lock_hash = verify_run_lock()
    barrier = verify_stage_barrier(stage, lock_hash, opening=False)
    endpoint_receipt = load_json(endpoint_receipt_path(stage))
    if endpoint_receipt.get("run_lock_sha256") != lock_hash:
        raise RuntimeError("ENDPOINT_RECEIPT_LOCK_MISMATCH")
    if endpoint_receipt.get("endpoint_sha256") != file_sha256(endpoint_path(stage)):
        raise RuntimeError("ENDPOINT_RECEIPT_HASH_MISMATCH")
    if stage == "D0" and endpoint_receipt.get("status") != "PASS":
        result = {
            "schema": "BA-OBS-DISC2-stage-result-v1",
            "stage": stage,
            "run_lock_sha256": lock_hash,
            "endpoint_receipt_sha256": file_sha256(endpoint_receipt_path(stage)),
            "status": "APPARATUS_STOP",
            "apparatus": endpoint_receipt.get("apparatus"),
        }
        atomic_write_json(result_path(stage), result)
        return result

    current = endpoint_sources(endpoint_path(stage), "z")
    if stage == "D0":
        selection = d0_cross_validated_selection(current, _fold_map_from_split())
        result = {
            "schema": "BA-OBS-DISC2-stage-result-v1",
            "stage": stage,
            "run_lock_sha256": lock_hash,
            "endpoint_receipt_sha256": file_sha256(endpoint_receipt_path(stage)),
            **selection,
        }
        atomic_write_json(result_path(stage), result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
        return result

    predecessor = barrier["predecessor"]
    winner_name = str(predecessor.get("winner"))
    if winner_name not in CANDIDATES:
        raise FitError("predecessor winner is absent or unknown")
    training = _prior_stage_sources(stage, "z")
    primary = evaluate_fixed_structure(
        training=training,
        testing=current,
        winner_name=winner_name,
        stage=stage,
        endpoint_label="bipolar_poststimulus",
    )
    passed = bool(primary["passes_stage_gate"])
    status = (
        "PASS_INTERMEDIATE"
        if passed and stage in ("D1", "D2")
        else "PASS_FINAL"
        if passed and stage == "D3"
        else "NOT_CONFIRMED"
        if stage == "D3"
        else "KILLED_INTERMEDIATE"
    )
    controls: dict[str, Any] = {}
    reference_classification = None
    if stage == "D3" and passed:
        pre_control = evaluate_fixed_structure(
            training=_prior_stage_sources(stage, "pre_z"),
            testing=endpoint_sources(endpoint_path(stage), "pre_z"),
            winner_name=winner_name,
            stage=stage,
            endpoint_label="bipolar_prestimulus_negative_control",
        )
        contact_control = evaluate_fixed_structure(
            training=_prior_stage_sources(stage, "contact_mean_z"),
            testing=endpoint_sources(endpoint_path(stage), "contact_mean_z"),
            winner_name=winner_name,
            stage=stage,
            endpoint_label="contact_mean_poststimulus_diagnostic",
        )
        controls = {
            "prestimulus_negative_control": pre_control,
            "contact_mean_diagnostic": contact_control,
        }
        if pre_control["passes_stage_gate"]:
            status = "NEGATIVE_CONTROL_FAIL / NOT_CONFIRMED"
        reference_classification = (
            "REFERENCE_CONCORDANT"
            if contact_control["passes_stage_gate"]
            else "REFERENCE_SENSITIVE"
        )

    result = {
        "schema": "BA-OBS-DISC2-stage-result-v1",
        "stage": stage,
        "run_lock_sha256": lock_hash,
        "endpoint_receipt_sha256": file_sha256(endpoint_receipt_path(stage)),
        "winner": winner_name,
        "primary": primary,
        "controls": controls,
        "reference_classification": reference_classification,
        "status": status,
    }
    atomic_write_json(result_path(stage), result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    return result


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.set_defaults(handler=lambda args: verify_run_lock())
    open_parser = subparsers.add_parser("open-stage")
    open_parser.add_argument("stage", choices=STAGES)
    open_parser.set_defaults(handler=lambda args: open_stage(args.stage))
    fit_parser = subparsers.add_parser("fit-stage")
    fit_parser.add_argument("stage", choices=STAGES)
    fit_parser.set_defaults(handler=lambda args: fit_stage(args.stage))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        result = args.handler(args)
    except BaseException as error:
        print(
            json.dumps(
                {"status": "STOP", "error_type": type(error).__name__, "error": str(error)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
            flush=True,
        )
        return 2
    if args.command == "verify":
        print(json.dumps({"status": "PASS", "run_lock_sha256": result[1]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
