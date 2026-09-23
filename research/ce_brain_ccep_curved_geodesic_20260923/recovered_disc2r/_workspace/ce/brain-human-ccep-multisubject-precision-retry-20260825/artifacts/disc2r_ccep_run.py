"""BA-OBS-DISC2R linkage-only wrapper around the frozen DISC2 runner.

The predecessor scientific/numerical code is imported read-only.  This module
changes only trial provenance validation and redirects generated stage artifacts
to the retry run.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


NEW_ROOT = Path(__file__).resolve().parent.parent
NEW_ARTIFACTS = Path(__file__).resolve().parent
OLD_ROOT = NEW_ROOT.parent / "brain-human-ccep-multisubject-precision-20260825"
OLD_ARTIFACTS = OLD_ROOT / "artifacts"
OLD_RUN_LOCK_SHA256 = "2ea67d6728e1b1573d5efa15adef2e9f14ad0127bed458f43b265a3d376d9e6d"
OLD_FIXTURE_SHA256 = "f313ad0a5b9994d53533c4629a1b6f24a19319e3a0f78ad4c05fe4d8ec8e9341"

sys.path.insert(0, str(OLD_ARTIFACTS))
import disc2_ccep_run as base  # noqa: E402
from disc2_ccep_core import ApparatusError  # noqa: E402


# Redirect only mutable/generated run state.  Scientific source/split and the
# numerical implementation remain the exact predecessor bytes.
base.RUN_ROOT = NEW_ROOT
base.ARTIFACTS = NEW_ARTIFACTS
base.CONTRACT = NEW_ROOT / "00-contract.md"
base.SOURCE_MANIFEST = OLD_ARTIFACTS / "metadata-source-manifest.json"
base.SPLIT_MANIFEST = OLD_ARTIFACTS / "endpoint-blind-split-manifest.json"
base.RUN_LOCK = NEW_ROOT / "run-lock.json"
base.PREIMPLEMENTATION_AUDIT = NEW_ROOT / "preimplementation-audit-receipt.json"
base.FIXTURE_RECEIPT = OLD_ARTIFACTS / "pre-d0-fixture-receipt-v2.json"

_new_lock_verifier = base.verify_run_lock
_inherited_manifest_loader = base.load_and_verify_manifests
_sealed_sources: dict[tuple[str, str, str], Mapping[str, Any]] = {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_run_lock() -> tuple[dict[str, Any], str]:
    lock, lock_hash = _new_lock_verifier()
    old_lock_path = OLD_ROOT / "run-lock.json"
    if _sha256(old_lock_path) != OLD_RUN_LOCK_SHA256:
        raise RuntimeError("INHERITED_RUN_LOCK_HASH_MISMATCH")
    old_lock = json.loads(old_lock_path.read_text(encoding="utf-8"))
    for relative_path, expected_hash in old_lock["files"].items():
        path = OLD_ROOT / relative_path
        if not path.is_file() or _sha256(path) != expected_hash:
            raise RuntimeError(f"INHERITED_LOCK_FILE_MISMATCH::{relative_path}")
    return lock, lock_hash


def verify_fixture_receipt() -> dict[str, Any]:
    receipt_path = OLD_ARTIFACTS / "pre-d0-fixture-receipt-v2.json"
    if _sha256(receipt_path) != OLD_FIXTURE_SHA256:
        raise RuntimeError("INHERITED_FIXTURE_RECEIPT_HASH_MISMATCH")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("status") != "PASS"
        or receipt.get("final_fixture") is not True
        or int(receipt.get("null_replicates", -1)) != 64
        or int(receipt.get("null_false_selections", 65)) != 0
        or int(receipt.get("null_numerical_stops", 65)) != 0
    ):
        raise RuntimeError("INHERITED_FIXTURE_NOT_PASS")
    expected = {
        "contract_sha256": _sha256(OLD_ROOT / "00-contract.md"),
        "core_code_sha256": _sha256(OLD_ARTIFACTS / "disc2_ccep_core.py"),
        "runner_code_sha256": _sha256(OLD_ARTIFACTS / "disc2_ccep_run.py"),
        "fixture_code_sha256": _sha256(OLD_ARTIFACTS / "disc2_fixture.py"),
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise RuntimeError(f"INHERITED_FIXTURE_INTERNAL_HASH_MISMATCH::{key}")
    return receipt


def load_and_verify_manifests() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_manifest, split_manifest, records = _inherited_manifest_loader()
    sealed: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for participant in source_manifest.get("participants", []):
        subject = str(participant["subject"])
        for source in participant.get("sources", []):
            key = (subject, str(source["record_id"]), str(source["site_id"]))
            if key in sealed:
                raise ApparatusError(f"SOURCE_TRIAL_LINKAGE_STOP: duplicate source key {key}")
            sealed[key] = source
    if not sealed:
        raise ApparatusError("SOURCE_TRIAL_LINKAGE_STOP: no sealed sources")
    _sealed_sources.clear()
    _sealed_sources.update(sealed)
    return source_manifest, split_manifest, records


def _same_float(first: Any, second: Any) -> bool:
    return math.isclose(float(first), float(second), rel_tol=0.0, abs_tol=1.0e-15)


def ordered_trials(
    source: Mapping[str, Any], record: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], tuple[list[int], list[int]], dict[str, list[int]]]:
    expected_crosswalk = {"0": int(record.get("electrical_event_count", -1))}
    if record.get("event_sample_crosswalk") != expected_crosswalk:
        raise ApparatusError(
            "SOURCE_TRIAL_LINKAGE_STOP: record delta histogram is not exact zero"
        )

    key = (str(record["subject"]), str(record["record_id"]), str(source["site_id"]))
    sealed = _sealed_sources.get(key)
    if sealed is None:
        raise ApparatusError(f"SOURCE_TRIAL_LINKAGE_STOP: sealed source absent {key}")
    scalar_checks = (
        str(sealed["record_id"]) == str(source["record_id"]),
        list(sealed["contacts"]) == list(source["contacts"]),
        str(sealed["stimulation_type"]) == str(source["stimulation_type"]),
        _same_float(sealed["current_a"], source["current_a"]),
        _same_float(sealed["frequency_hz"], source["frequency_hz"]),
        _same_float(sealed["pulsewidth_s"], source["pulsewidth_s"]),
    )
    if not all(scalar_checks):
        raise ApparatusError("SOURCE_TRIAL_LINKAGE_STOP: source metadata mismatch")

    halves = source.get("temporal_repeatability_halves")
    if not isinstance(halves, dict) or set(halves) != {"A", "B"}:
        raise ApparatusError("SOURCE_TRIAL_LINKAGE_STOP: temporal halves missing")
    if len(halves["A"]) != 5 or len(halves["B"]) != 5:
        raise ApparatusError("SOURCE_TRIAL_LINKAGE_STOP: temporal halves are not 5/5")
    by_event: dict[int, dict[str, Any]] = {}
    for trial in halves["A"] + halves["B"]:
        event_index = int(trial["event_index"])
        normalized = {
            "event_index": event_index,
            "anchor_sample_zero_based": int(trial["anchor_sample_zero_based"]),
            "orientation_site": str(trial["orientation_site"]),
        }
        if event_index in by_event and by_event[event_index] != normalized:
            raise ApparatusError(
                "SOURCE_TRIAL_LINKAGE_STOP: duplicate event metadata differs"
            )
        by_event[event_index] = normalized
    if len(by_event) != 10:
        raise ApparatusError("SOURCE_TRIAL_LINKAGE_STOP: not ten unique trials")

    clean_by_event: dict[int, Mapping[str, Any]] = {}
    for trial in sealed.get("clean_trials", []):
        event_index = int(trial["event_index"])
        if event_index in clean_by_event:
            raise ApparatusError(
                "SOURCE_TRIAL_LINKAGE_STOP: duplicate clean-trial event"
            )
        clean_by_event[event_index] = trial
    for event_index, trial in by_event.items():
        clean = clean_by_event.get(event_index)
        if clean is None:
            raise ApparatusError(
                "SOURCE_TRIAL_LINKAGE_STOP: selected event absent from clean trials"
            )
        if (
            int(clean["anchor_sample_zero_based"])
            != trial["anchor_sample_zero_based"]
            or str(clean["orientation_site"]) != trial["orientation_site"]
        ):
            raise ApparatusError(
                "SOURCE_TRIAL_LINKAGE_STOP: trial anchor/orientation mismatch"
            )

    ordered = [by_event[index] for index in sorted(by_event)]
    position = {trial["event_index"]: index for index, trial in enumerate(ordered)}
    half_positions = (
        [position[int(trial["event_index"])] for trial in halves["A"]],
        [position[int(trial["event_index"])] for trial in halves["B"]],
    )

    orientation_positions: dict[str, list[int]] = {}
    for label, trials in (source.get("orientation_groups") or {}).items():
        indexes = [position[int(trial["event_index"])] for trial in trials]
        if len(indexes) not in (5, 10):
            raise ApparatusError(
                "SOURCE_TRIAL_LINKAGE_STOP: orientation group size invalid"
            )
        orientation_positions[str(label)] = indexes
    mode = source.get("orientation_mode")
    if mode == "two_orientation_5_by_5":
        if len(orientation_positions) != 2 or any(
            len(indexes) != 5 for indexes in orientation_positions.values()
        ):
            raise ApparatusError(
                "SOURCE_TRIAL_LINKAGE_STOP: two-orientation partition invalid"
            )
    elif mode == "single_orientation_temporal_only":
        if len(orientation_positions) != 1:
            raise ApparatusError(
                "SOURCE_TRIAL_LINKAGE_STOP: single-orientation group invalid"
            )
        orientation_positions = {}
    else:
        raise ApparatusError(f"SOURCE_TRIAL_LINKAGE_STOP: unknown mode {mode}")
    return ordered, half_positions, orientation_positions


# Install the narrow retry overrides in the inherited runner module.
base.verify_run_lock = verify_run_lock
base.verify_fixture_receipt = verify_fixture_receipt
base.load_and_verify_manifests = load_and_verify_manifests
base._ordered_trials = ordered_trials


def main(argv: Sequence[str] | None = None) -> int:
    return base.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
