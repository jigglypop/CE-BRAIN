"""Fail-closed BA-SELF3 channelwise-affine EEG apparatus only.

This file intentionally has no quotient, target, feature, loss, or model
implementation.  It opens signal only for A1/A2/B1 when ``--execute`` is
present; allocation is metadata-only and is deterministic.
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

CONTRACT_SHA256 = "765c54ee2b20006619b3059c68ec3a5d1a3f007381f6d89593c597015ac41fce"
MANIFEST_SHA256 = "4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061"
A0_RECEIPT_SHA256 = "5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7"
SELF2_SHA256 = "9740d04ab8198a403d94d9c825b1a8f7279c159854fb6403f84da8c4a48685a4"
SELF1_BRAINVISION_SHA256 = "b075b9deb34c6a5e93ab58eabeb378a38c2e69045b4155d219252154baa3d559"
SOURCE_MANIFEST_CONTRACT_SHA256 = "2b08c0fd5eb69ae6f3d096a6542e248b6d2b69da985f90c7d06071e0690be50e"
B1_PREFIX = "BA-SELF3-B1-v1:"
STAGES = ("A0-ALLOCATION", "A1", "A2", "B1")


class ApparatusInvalid(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def dump_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def predecessor_default() -> Path:
    return Path(__file__).resolve().parents[1].with_name(
        "brain-self-trajectory-human-eeg-qc2-l3-20260824"
    ) / "artifacts" / "scale_free_qc.py"


def unopened_splits(stage: str) -> list[str]:
    return {
        "A0-ALLOCATION": ["A1", "A2", "B1", "D2-M", "C1", "C2", "C3"],
        "A1": ["A2", "B1", "D2-M", "C1", "C2", "C3"],
        "A2": ["B1", "D2-M", "C1", "C2", "C3"],
        "B1": ["D2-M", "C1", "C2", "C3"],
    }[stage]


def load_self2(path: Path):
    if sha256_file(path) != SELF2_SHA256:
        raise ApparatusInvalid("BA-SELF2 apparatus hash mismatch")
    spec = importlib.util.spec_from_file_location("ba_self2_scale_free_qc", path)
    if spec is None or spec.loader is None:
        raise ApparatusInvalid("cannot load verified BA-SELF2 apparatus")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_apparatus_modules(path: Path):
    """Return verified SELF1 range apparatus and SELF2 R1 diagnostic module."""
    self2 = load_self2(path)
    # SELF2 verifies the frozen SELF1 hash before returning this nested module.
    br = self2.load_predecessor(self2.predecessor_default())
    return br, self2


def channelwise_qc(window: np.ndarray) -> dict:
    """Exact R2 QA/QD, invariant only to finite channelwise affine maps."""
    if window.ndim != 2 or window.shape[1] != 63 or window.shape[0] < 2:
        raise ApparatusInvalid(f"post-filter window shape mismatch: {window.shape}")
    if not np.isfinite(window).all():
        raise ApparatusInvalid("APPARATUS_INVALID_NONFINITE_WINDOW")
    centre = np.median(window, axis=0)
    residual = window - centre
    difference = np.diff(window, axis=0)
    s = 1.4826 * np.median(np.abs(residual), axis=0)
    d_centre = np.median(difference, axis=0)
    r = 1.4826 * np.median(np.abs(difference - d_centre), axis=0)
    if not np.isfinite(s).all() or np.any(s <= 0):
        raise ApparatusInvalid("APPARATUS_INVALID_AMPLITUDE_CHANNEL_SCALE")
    if not np.isfinite(r).all() or np.any(r <= 0):
        raise ApparatusInvalid("APPARATUS_INVALID_DIFFERENCE_CHANNEL_SCALE")
    qa = float(np.max(np.abs(residual / s[None, :])))
    qd = float(np.max(np.abs(difference / r[None, :])))
    if not math.isfinite(qa) or not math.isfinite(qd):
        raise ApparatusInvalid("APPARATUS_INVALID_NONFINITE_RATIO")
    return {"Q_A": qa, "Q_D": qd, "nonfinite_count": 0,
            "zero_amplitude_scale_channel_count": 0,
            "zero_difference_scale_channel_count": 0}


def freeze_cutoffs(metrics: list[dict]) -> dict:
    if len(metrics) != 64:
        raise ApparatusInvalid(f"A2 requires 64 windows, got {len(metrics)}")
    result = {}
    for key in ("Q_A", "Q_D"):
        values = np.asarray([item[key] for item in metrics], dtype=float)
        median, mad = float(np.median(values)), float(np.median(np.abs(values - np.median(values))))
        if not np.isfinite(values).all() or not math.isfinite(mad) or mad <= 0:
            raise ApparatusInvalid(f"APPARATUS_INVALID_QC_SCALE: {key}")
        result[key] = {"median": median, "mad": mad, "cutoff": median + 6 * mad}
    return result


def allocation(manifest: dict) -> dict:
    rows = [dict(row) for row in manifest["trials"] if row["split"] == "D2"]
    if len(rows) != 132:
        raise ApparatusInvalid(f"sealed D2 allocation count mismatch: {len(rows)}")
    by_session = {session: [] for session in ("ses-01", "ses-02")}
    for row in rows:
        if row["subject"] != "sub-02" or row["session"] not in by_session:
            raise ApparatusInvalid("D2 allocation is not sealed sub-02 sessions")
        row["allocation_key"] = sha256_bytes((B1_PREFIX + row["trial_hash"]).encode("utf-8"))
        by_session[row["session"]].append(row)
    assigned = []
    for session, group in by_session.items():
        if len(group) not in (59, 73):
            raise ApparatusInvalid(f"unexpected D2 session count {session}: {len(group)}")
        group.sort(key=lambda r: (r["allocation_key"], r["trial_hash"]))
        for index, row in enumerate(group):
            row["old_split"] = row["split"]
            row["new_split"] = "B1" if index < 16 else "D2-M"
            assigned.append(row)
    counts = {split: sum(r["new_split"] == split for r in assigned) for split in ("B1", "D2-M")}
    session_counts = {session: {split: sum(r["session"] == session and r["new_split"] == split for r in assigned)
                                for split in ("B1", "D2-M")} for session in by_session}
    if counts != {"B1": 32, "D2-M": 100} or session_counts != {"ses-01": {"B1": 16, "D2-M": 57}, "ses-02": {"B1": 16, "D2-M": 43}}:
        raise ApparatusInvalid("B1/D2-M allocation counts mismatch")
    coverage = {session: sorted({r["word"] for r in assigned if r["session"] == session and r["new_split"] == "D2-M"}) for session in by_session}
    if any(len(words) != 8 for words in coverage.values()):
        raise ApparatusInvalid("D2-M does not retain all eight word levels per session")
    return {"schema": "BA-SELF3-B1-allocation-v1", "status": "A0_ALLOCATION_PASS", "signal_accessed": False,
            "scientific_endpoint_opened": False, "model_outcome_opened": False, "model_outcome_computed": False,
            "manifest_sha256": MANIFEST_SHA256, "self1_brainvision_sha256": SELF1_BRAINVISION_SHA256,
            "filter_geometry": {"raw_samples": 3001, "fir_taps": 501, "decimation": 20, "postfilter_shape": [126, 63]},
            "allocation_prefix": B1_PREFIX,
            "trials": sorted(assigned, key=lambda r: (r["session"], r["allocation_key"], r["trial_hash"])),
            "counts": counts, "session_counts": session_counts, "d2m_word_coverage": coverage,
            "unopened_splits": unopened_splits("A0-ALLOCATION")}


def preflight(stage: str, manifest_path: Path, a0_path: Path, predecessor_path: Path, contract_path: Path) -> dict:
    if sha256_file(contract_path) != CONTRACT_SHA256: raise ApparatusInvalid("current contract hash mismatch")
    if sha256_file(manifest_path) != MANIFEST_SHA256: raise ApparatusInvalid("manifest hash mismatch")
    if sha256_file(a0_path) != A0_RECEIPT_SHA256: raise ApparatusInvalid("A0 receipt hash mismatch")
    br, _self2 = load_apparatus_modules(predecessor_path)
    manifest, a0 = json.loads(manifest_path.read_bytes()), json.loads(a0_path.read_bytes())
    if (manifest.get("contract_sha256") != SOURCE_MANIFEST_CONTRACT_SHA256
            or a0.get("contract_sha256") != SOURCE_MANIFEST_CONTRACT_SHA256):
        raise ApparatusInvalid("predecessor contract linkage mismatch")
    return {"schema": "BA-SELF3-channelwise-qc-v1", "stage": stage,
            "status": f"{stage}_PREFLIGHT_NOT_EXECUTED", "network_accessed": False,
            "scientific_endpoint_opened": False, "model_outcome_opened": False, "model_outcome_computed": False,
            "contract_sha256": CONTRACT_SHA256, "manifest_sha256": MANIFEST_SHA256,
            "a0_receipt_sha256": A0_RECEIPT_SHA256, "self2_apparatus_sha256": SELF2_SHA256,
            "self1_brainvision_sha256": SELF1_BRAINVISION_SHA256,
            "filter_geometry": {"raw_samples": 3001, "fir_taps": 501, "decimation": 20, "postfilter_shape": [126, 63]},
            "unopened_splits": unopened_splits(stage)}


def selected_calibration(manifest: dict, stage: str) -> list[dict]:
    labels = {"A1": {"A1"}, "A2": {"A1", "A2"}}[stage]
    rows = [r for r in manifest["trials"] if r["split"] in labels]
    expected = {"A1": 8, "A2": 32}[stage]
    if len(rows) != expected or any((r["subject"], r["session"]) != ("sub-01", "ses-02") for r in rows):
        raise ApparatusInvalid(f"{stage} calibration allocation mismatch")
    return rows


def window_row(br, self2, a0: dict, trial: dict, condition: str, cutoffs: dict | None) -> dict:
    anchor_key = f"{condition}_anchor_s"; record = br.recording_for(a0, trial["subject"], trial["session"])
    anchor = br.anchor_to_sample(float(trial[anchor_key])); first, last, start, end = br.byte_geometry(anchor)
    raw, request = br.fetch_exact_range(record["eeg_url"], start, end, record["content_length"], record["etag"])
    window = br.causal_filter_and_decimate(br.parse_multiplexed_float32(raw))
    # These legacy values are explicitly receipt diagnostics, never gates.
    try:
        absolute = br.window_qc(window)
    except Exception as error:
        absolute = {"diagnostic_error": f"{type(error).__name__}: {error}"}
    try:
        r1 = self2.scale_free_qc(window)
    except Exception as error:
        r1 = {"diagnostic_error": f"{type(error).__name__}: {error}"}
    try:
        metric = channelwise_qc(window); reasons = [] if cutoffs is None else [key + "_EXCEEDS_CUTOFF" for key in ("Q_A", "Q_D") if metric[key] > cutoffs[key]["cutoff"]]
    except ApparatusInvalid as error:
        metric, reasons = None, [str(error)]
    return {"condition": condition, "anchor_s": trial[anchor_key], "anchor_sample": anchor, "first_sample": first, "last_sample": last,
            "request": request, "channelwise_qc": metric, "matched_absolute_diagnostic": absolute,
            "matched_self2_r1_diagnostic": r1, "rejection_reasons": reasons}


def execute_calibration(stage: str, manifest_path: Path, a0_path: Path, predecessor_path: Path, contract_path: Path) -> dict:
    receipt = preflight(stage, manifest_path, a0_path, predecessor_path, contract_path)
    br, self2 = load_apparatus_modules(predecessor_path)
    manifest, a0 = json.loads(manifest_path.read_bytes()), json.loads(a0_path.read_bytes())
    windows = []
    for trial in selected_calibration(manifest, stage):
        for condition in ("task", "rest"):
            row = window_row(br, self2, a0, trial, condition, None); row["trial_hash"] = trial["trial_hash"]; windows.append(row)
    hard = [r for r in windows if r["rejection_reasons"]]
    if hard: raise ApparatusInvalid(f"{stage} channelwise hard-domain failures: {len(hard)}")
    receipt.update({"network_accessed": True, "windows": windows, "status": f"{stage}_APPARATUS_PASS"})
    if stage == "A2": receipt["frozen_qc_cutoffs"] = freeze_cutoffs([r["channelwise_qc"] for r in windows])
    return receipt


def transfer_gate(pairs: list[dict]) -> tuple[bool, int, dict[str, int]]:
    if len(pairs) != 32: raise ApparatusInvalid(f"B1 pair count mismatch: {len(pairs)}")
    per = {s: sum(p["accepted"] and p["session"] == s for p in pairs) for s in ("ses-01", "ses-02")}
    total = sum(p["accepted"] for p in pairs)
    return total >= 24 and all(v >= 12 for v in per.values()), total, per


def execute_b1(manifest_path: Path, a0_path: Path, predecessor_path: Path, contract_path: Path, allocation_path: Path, a2_path: Path) -> dict:
    receipt = preflight("B1", manifest_path, a0_path, predecessor_path, contract_path)
    allocation_receipt, a2 = json.loads(allocation_path.read_bytes()), json.loads(a2_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    expected_allocation = allocation(manifest)
    if (allocation_receipt.get("manifest_sha256") != MANIFEST_SHA256
            or allocation_receipt.get("contract_sha256") != CONTRACT_SHA256
            or allocation_receipt.get("status") != "A0_ALLOCATION_PASS"
            or allocation_receipt.get("signal_accessed") is not False
            or allocation_receipt.get("scientific_endpoint_opened") is not False
            or allocation_receipt.get("model_outcome_opened") is not False
            or allocation_receipt.get("model_outcome_computed") is not False
            or allocation_receipt.get("counts") != expected_allocation["counts"]
            or allocation_receipt.get("session_counts") != expected_allocation["session_counts"]
            or allocation_receipt.get("d2m_word_coverage") != expected_allocation["d2m_word_coverage"]
            or allocation_receipt.get("trials") != expected_allocation["trials"]):
        raise ApparatusInvalid("allocation linkage or deterministic-content mismatch")
    if (a2.get("stage") != "A2" or a2.get("status") != "A2_APPARATUS_PASS" or a2.get("network_accessed") is not True
            or len(a2.get("windows", [])) != 64 or a2.get("scientific_endpoint_opened") is not False
            or a2.get("model_outcome_opened") is not False
            or a2.get("model_outcome_computed") is not False or a2.get("contract_sha256") != CONTRACT_SHA256
            or a2.get("manifest_sha256") != MANIFEST_SHA256 or a2.get("a0_receipt_sha256") != A0_RECEIPT_SHA256
            or set(a2.get("frozen_qc_cutoffs", {})) != {"Q_A", "Q_D"}):
        raise ApparatusInvalid("A2 cutoff linkage mismatch")
    rows = [r for r in allocation_receipt["trials"] if r["new_split"] == "B1"]
    if len(rows) != 32 or {r["session"] for r in rows} != {"ses-01", "ses-02"}: raise ApparatusInvalid("B1 allocation mismatch")
    br, self2 = load_apparatus_modules(predecessor_path)
    a0 = json.loads(a0_path.read_bytes())
    pairs = []
    for trial in rows:
        windows = [window_row(br, self2, a0, trial, condition, a2["frozen_qc_cutoffs"]) for condition in ("task", "rest")]
        reasons = sorted({reason for row in windows for reason in row["rejection_reasons"]})
        pairs.append({"trial_hash": trial["trial_hash"], "session": trial["session"], "word": trial["word"], "accepted": not reasons, "rejection_reasons": reasons, "windows": windows})
    passed, accepted, by_session = transfer_gate(pairs)
    receipt.update({"network_accessed": True, "allocation_sha256": sha256_file(allocation_path), "a2_receipt_sha256": sha256_file(a2_path),
                    "frozen_qc_cutoffs": a2["frozen_qc_cutoffs"], "pairs": pairs, "accepted_pairs": accepted,
                    "rejected_pairs": 32 - accepted, "accepted_pairs_by_session": by_session,
                    "status": "B1_APPARATUS_PASS" if passed else "APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER"})
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--stage", required=True, choices=STAGES)
    parser.add_argument("--manifest", required=True, type=Path); parser.add_argument("--a0-receipt", required=True, type=Path); parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--predecessor", default=predecessor_default(), type=Path); parser.add_argument("--allocation", type=Path); parser.add_argument("--a2-receipt", type=Path); parser.add_argument("--output", required=True, type=Path); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(); code = 0
    try:
        if args.stage == "A0-ALLOCATION":
            preflight(args.stage, args.manifest, args.a0_receipt, args.predecessor, args.contract)
            receipt = allocation(json.loads(args.manifest.read_bytes())); receipt.update({"contract_sha256": CONTRACT_SHA256, "a0_receipt_sha256": A0_RECEIPT_SHA256, "self2_apparatus_sha256": SELF2_SHA256, "self1_brainvision_sha256": SELF1_BRAINVISION_SHA256, "filter_geometry": {"raw_samples": 3001, "fir_taps": 501, "decimation": 20, "postfilter_shape": [126, 63]}})
        elif not args.execute:
            receipt = preflight(args.stage, args.manifest, args.a0_receipt, args.predecessor, args.contract)
        elif args.stage == "B1":
            if args.allocation is None or args.a2_receipt is None: raise ApparatusInvalid("B1 requires --allocation and --a2-receipt")
            receipt = execute_b1(args.manifest, args.a0_receipt, args.predecessor, args.contract, args.allocation, args.a2_receipt)
        else:
            receipt = execute_calibration(args.stage, args.manifest, args.a0_receipt, args.predecessor, args.contract)
    except Exception as error:
        receipt = {"schema": "BA-SELF3-channelwise-qc-v1", "stage": args.stage, "status": "APPARATUS_INVALID", "error": f"{type(error).__name__}: {error}", "scientific_endpoint_opened": False, "model_outcome_opened": False, "model_outcome_computed": False, "self1_brainvision_sha256": SELF1_BRAINVISION_SHA256, "unopened_splits": unopened_splits(args.stage)}; code = 2
    else:
        if receipt["status"] == "APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER": code = 2
    dump_atomic(args.output, receipt); print(json.dumps({"status": receipt["status"], "network_accessed": receipt.get("network_accessed", False)}, sort_keys=True)); return code


if __name__ == "__main__":
    raise SystemExit(main())
