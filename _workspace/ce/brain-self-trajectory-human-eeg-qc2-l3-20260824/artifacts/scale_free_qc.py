"""Fail-closed BA-SELF2 scale-free EEG apparatus.

The default command is an offline seal preflight.  Network access is possible
only with ``--execute`` and is restricted to the A1, A2, or D1-QC allocation.
This module deliberately contains no quotient, target, feature, loss, or model
code.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np

CONTRACT_SHA256 = "8eb85e4ce7218112c082b84e0f754ae3fa0afb1995374a9675c581164880517f"
MANIFEST_SHA256 = "4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061"
A0_RECEIPT_SHA256 = "5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7"
PREDECESSOR_BRAINVISION_SHA256 = "b075b9deb34c6a5e93ab58eabeb378a38c2e69045b4155d219252154baa3d559"
STAGES = ("A1", "A2", "D1-QC")


class ApparatusInvalid(RuntimeError):
    """A sealed input or QC domain condition failed."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def predecessor_default() -> Path:
    return Path(__file__).resolve().parents[1].with_name(
        "brain-self-trajectory-human-fmri-l3-20260824"
    ) / "artifacts" / "brainvision_range.py"


def unopened_splits(stage: str) -> list[str]:
    return {"A1": ["A2", "D1-QC", "D2", "C1", "C2", "C3"],
            "A2": ["D1-QC", "D2", "C1", "C2", "C3"],
            "D1-QC": ["D2", "C1", "C2", "C3"]}[stage]


def dump_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_predecessor(path: Path):
    if sha256_file(path) != PREDECESSOR_BRAINVISION_SHA256:
        raise ApparatusInvalid("predecessor BrainVision apparatus hash mismatch")
    spec = importlib.util.spec_from_file_location("ba_self1_brainvision_range", path)
    if spec is None or spec.loader is None:
        raise ApparatusInvalid("cannot load verified predecessor apparatus")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def robust_scale(values: np.ndarray) -> np.ndarray:
    median = np.median(values, axis=0)
    return 1.4826 * np.median(np.abs(values - median), axis=0)


def scale_free_qc(window: np.ndarray) -> dict:
    """Return the contract's Q_A/Q_D or reject every undefined window."""
    if window.ndim != 2 or window.shape[1] != 63 or window.shape[0] < 2:
        raise ApparatusInvalid(f"post-filter window shape mismatch: {window.shape}")
    if not np.isfinite(window).all():
        raise ApparatusInvalid("APPARATUS_INVALID_NONFINITE_WINDOW")
    residual = window - np.median(window, axis=0)
    difference = np.diff(window, axis=0)
    s = robust_scale(residual)
    r = robust_scale(difference)
    if not np.isfinite(s).all() or np.any(s <= 0.0):
        raise ApparatusInvalid("APPARATUS_INVALID_AMPLITUDE_CHANNEL_SCALE")
    if not np.isfinite(r).all() or np.any(r <= 0.0):
        raise ApparatusInvalid("APPARATUS_INVALID_DIFFERENCE_CHANNEL_SCALE")
    s_denominator, r_denominator = float(np.median(s)), float(np.median(r))
    if not math.isfinite(s_denominator) or s_denominator <= 0.0:
        raise ApparatusInvalid("APPARATUS_INVALID_AMPLITUDE_DENOMINATOR")
    if not math.isfinite(r_denominator) or r_denominator <= 0.0:
        raise ApparatusInvalid("APPARATUS_INVALID_DIFFERENCE_DENOMINATOR")
    qa = float(np.max(np.abs(residual)) / s_denominator)
    qd = float(np.max(np.abs(difference)) / r_denominator)
    if not math.isfinite(qa) or not math.isfinite(qd):
        raise ApparatusInvalid("APPARATUS_INVALID_NONFINITE_RATIO")
    return {
        "Q_A": qa,
        "Q_D": qd,
        "amplitude_scale_median": s_denominator,
        "difference_scale_median": r_denominator,
        "nonfinite_count": 0,
        "zero_amplitude_scale_channel_count": 0,
        "zero_difference_scale_channel_count": 0,
    }


def freeze_cutoffs(metrics: list[dict]) -> dict:
    if len(metrics) != 64:
        raise ApparatusInvalid(f"A2 requires 64 windows, got {len(metrics)}")
    frozen = {}
    for key in ("Q_A", "Q_D"):
        values = np.asarray([item[key] for item in metrics], dtype=np.float64)
        if not np.isfinite(values).all():
            raise ApparatusInvalid(f"APPARATUS_INVALID_QC_SCALE: nonfinite {key}")
        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        if not math.isfinite(median) or not math.isfinite(mad) or mad <= 0.0:
            raise ApparatusInvalid(f"APPARATUS_INVALID_QC_SCALE: {key} MAD={mad!r}")
        frozen[key] = {"median": median, "mad": mad, "cutoff": median + 6.0 * mad}
    return frozen


def transfer_gate(pairs: list[dict]) -> tuple[bool, int, dict[str, int]]:
    if len(pairs) != 32:
        raise ApparatusInvalid(f"D1-QC pair count mismatch: {len(pairs)}")
    counts = {session: sum(bool(pair["accepted"]) and pair["session"] == session for pair in pairs)
              for session in ("ses-01", "ses-02")}
    accepted = sum(bool(pair["accepted"]) for pair in pairs)
    return accepted >= 24 and all(value >= 12 for value in counts.values()), accepted, counts


def window_reasons(metric: dict | None, cutoffs: dict | None, error: str | None = None) -> list[str]:
    if error is not None:
        return [error]
    assert metric is not None
    if cutoffs is None:
        return []
    return [f"{key}_EXCEEDS_CUTOFF" for key in ("Q_A", "Q_D") if metric[key] > cutoffs[key]["cutoff"]]


def select_trials(manifest: dict, stage: str) -> list[dict]:
    splits = {"A1": {"A1"}, "A2": {"A1", "A2"}, "D1-QC": {"D1"}}[stage]
    rows = [row for row in manifest["trials"] if row["split"] in splits]
    expected = {"A1": 8, "A2": 32, "D1-QC": 32}[stage]
    if len(rows) != expected:
        raise ApparatusInvalid(f"{stage} trial count mismatch: {len(rows)}")
    if stage in {"A1", "A2"} and any((r["subject"], r["session"]) != ("sub-01", "ses-02") for r in rows):
        raise ApparatusInvalid(f"{stage} allocation is not sealed sub-01/ses-02")
    if stage == "D1-QC":
        sessions = {session: sum(r["session"] == session for r in rows) for session in ("ses-01", "ses-02")}
        if any(value != 16 for value in sessions.values()) or any(r["subject"] != "sub-02" for r in rows):
            raise ApparatusInvalid("D1-QC allocation is not sealed 16/16 sub-02")
    return rows


def preflight(stage: str, manifest_path: Path, a0_path: Path, predecessor_path: Path, contract_path: Path) -> dict:
    if sha256_file(contract_path) != CONTRACT_SHA256:
        raise ApparatusInvalid("current contract hash mismatch")
    if sha256_file(manifest_path) != MANIFEST_SHA256:
        raise ApparatusInvalid("predecessor manifest hash mismatch")
    if sha256_file(a0_path) != A0_RECEIPT_SHA256:
        raise ApparatusInvalid("predecessor A0 receipt hash mismatch")
    predecessor = load_predecessor(predecessor_path)
    manifest, a0 = json.loads(manifest_path.read_bytes()), json.loads(a0_path.read_bytes())
    if manifest.get("contract_sha256") != predecessor.CONTRACT_SHA256 or a0.get("contract_sha256") != predecessor.CONTRACT_SHA256:
        raise ApparatusInvalid("predecessor contract linkage mismatch")
    selected = select_trials(manifest, stage)
    return {
        "schema": "BA-SELF2-scale-free-qc-v1",
        "stage": stage,
        "status": f"{stage}_PREFLIGHT_NOT_EXECUTED",
        "network_accessed": False,
        "scientific_endpoint_opened": False,
        "model_outcome_computed": False,
        "contract_sha256": CONTRACT_SHA256,
        "predecessor_brainvision_sha256": PREDECESSOR_BRAINVISION_SHA256,
        "manifest_sha256": MANIFEST_SHA256,
        "a0_receipt_sha256": A0_RECEIPT_SHA256,
        "selected_trials": len(selected),
        "unopened_splits": unopened_splits(stage),
    }


def execute(stage: str, manifest_path: Path, a0_path: Path, predecessor_path: Path, contract_path: Path) -> dict:
    preflight_receipt = preflight(stage, manifest_path, a0_path, predecessor_path, contract_path)
    br = load_predecessor(predecessor_path)
    manifest, a0 = json.loads(manifest_path.read_bytes()), json.loads(a0_path.read_bytes())
    trials = select_trials(manifest, stage)
    cutoffs = None
    if stage == "D1-QC":
        raise ApparatusInvalid("D1-QC requires --a2-receipt")
    rows = []
    for trial in trials:
        record = br.recording_for(a0, trial["subject"], trial["session"])
        for condition, anchor_key in (("task", "task_anchor_s"), ("rest", "rest_anchor_s")):
            anchor = br.anchor_to_sample(float(trial[anchor_key]))
            first, last, start, end = br.byte_geometry(anchor)
            raw, request = br.fetch_exact_range(record["eeg_url"], start, end, record["content_length"], record["etag"])
            window = br.causal_filter_and_decimate(br.parse_multiplexed_float32(raw))
            old = br.window_qc(window)
            try:
                metric, reasons = scale_free_qc(window), []
            except ApparatusInvalid as error:
                metric, reasons = None, [str(error)]
            rows.append({"trial_hash": trial["trial_hash"], "session": trial["session"], "condition": condition,
                         "anchor_s": trial[anchor_key], "anchor_sample": anchor, "first_sample": first,
                         "last_sample": last, "request": request, "scale_free_qc": metric,
                         "matched_absolute_diagnostic": old, "rejection_reasons": reasons})
    output = {**preflight_receipt, "network_accessed": True, "windows": rows,
              "status": f"{stage}_APPARATUS_PASS"}
    hard_errors = [row for row in rows if row["rejection_reasons"]]
    if hard_errors:
        raise ApparatusInvalid(f"{stage} scale-free QC hard-domain failure in {len(hard_errors)} window(s)")
    if stage == "A2":
        cutoffs = freeze_cutoffs([row["scale_free_qc"] for row in rows if not row["rejection_reasons"]])
        if len(rows) != 64:
            raise ApparatusInvalid("A2 window count mismatch")
        output["frozen_qc_cutoffs"] = cutoffs
    return output


def execute_d1(manifest_path: Path, a0_path: Path, predecessor_path: Path, contract_path: Path, a2_path: Path) -> dict:
    preflight_receipt = preflight("D1-QC", manifest_path, a0_path, predecessor_path, contract_path)
    a2 = json.loads(a2_path.read_bytes())
    if (a2.get("stage") != "A2" or a2.get("status") != "A2_APPARATUS_PASS"
            or a2.get("network_accessed") is not True or len(a2.get("windows", [])) != 64
            or set(a2.get("frozen_qc_cutoffs", {})) != {"Q_A", "Q_D"}):
        raise ApparatusInvalid("sealed A2 scale-free cutoffs unavailable")
    if (a2.get("contract_sha256") != CONTRACT_SHA256 or a2.get("manifest_sha256") != MANIFEST_SHA256
            or a2.get("a0_receipt_sha256") != A0_RECEIPT_SHA256):
        raise ApparatusInvalid("A2 receipt seal linkage mismatch")
    br = load_predecessor(predecessor_path)
    manifest, a0 = json.loads(manifest_path.read_bytes()), json.loads(a0_path.read_bytes())
    pairs = []
    for trial in select_trials(manifest, "D1-QC"):
        record, windows = br.recording_for(a0, trial["subject"], trial["session"]), []
        for condition, anchor_key in (("task", "task_anchor_s"), ("rest", "rest_anchor_s")):
            anchor = br.anchor_to_sample(float(trial[anchor_key])); first, last, start, end = br.byte_geometry(anchor)
            raw, request = br.fetch_exact_range(record["eeg_url"], start, end, record["content_length"], record["etag"])
            window = br.causal_filter_and_decimate(br.parse_multiplexed_float32(raw)); old = br.window_qc(window)
            try:
                metric = scale_free_qc(window); reasons = window_reasons(metric, a2["frozen_qc_cutoffs"])
            except ApparatusInvalid as error:
                metric, reasons = None, [str(error)]
            windows.append({"condition": condition, "anchor_s": trial[anchor_key], "anchor_sample": anchor,
                            "first_sample": first, "last_sample": last,
                            "Q_A": None if metric is None else metric["Q_A"],
                            "Q_D": None if metric is None else metric["Q_D"], "scale_free_qc": metric,
                            "matched_absolute_diagnostic": old, "request": request, "rejection_reasons": reasons})
        reasons = sorted({reason for row in windows for reason in row["rejection_reasons"]})
        pairs.append({"trial_hash": trial["trial_hash"], "session": trial["session"], "accepted": not reasons,
                      "rejection_reasons": reasons, "windows": windows})
    passed, accepted, accepted_by_session = transfer_gate(pairs)
    return {**preflight_receipt, "network_accessed": True, "a2_receipt_sha256": sha256_file(a2_path),
            "frozen_qc_cutoffs": a2["frozen_qc_cutoffs"], "pairs": pairs, "accepted_pairs": accepted,
            "rejected_pairs": len(pairs) - accepted, "accepted_pairs_by_session": accepted_by_session,
            "status": "D1_QC_APPARATUS_PASS" if passed else "APPARATUS_INVALID_CROSS_SUBJECT_SCALE_FREE_QC",
            "scientific_endpoint_opened": False, "model_outcome_computed": False, "unopened_splits": unopened_splits("D1-QC")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=STAGES); parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--a0-receipt", required=True, type=Path); parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--predecessor", default=predecessor_default(), type=Path); parser.add_argument("--a2-receipt", type=Path)
    parser.add_argument("--output", required=True, type=Path); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        if not args.execute:
            receipt = preflight(args.stage, args.manifest, args.a0_receipt, args.predecessor, args.contract)
        elif args.stage == "D1-QC":
            if args.a2_receipt is None:
                raise ApparatusInvalid("D1-QC requires --a2-receipt")
            receipt = execute_d1(args.manifest, args.a0_receipt, args.predecessor, args.contract, args.a2_receipt)
        else:
            receipt = execute(args.stage, args.manifest, args.a0_receipt, args.predecessor, args.contract)
    except Exception as error:
        receipt = {"schema": "BA-SELF2-scale-free-qc-v1", "stage": args.stage, "status": "APPARATUS_INVALID",
                   "error": f"{type(error).__name__}: {error}", "scientific_endpoint_opened": False,
                   "model_outcome_computed": False, "unopened_splits": unopened_splits(args.stage)}
        code = 2
    else:
        code = 2 if receipt["status"] == "APPARATUS_INVALID_CROSS_SUBJECT_SCALE_FREE_QC" else 0
    # This serializes receipts only; raw payloads and decoded windows remain in memory.
    dump_atomic(args.output, receipt)
    print(json.dumps({"status": receipt["status"], "network_accessed": receipt.get("network_accessed", False)}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
