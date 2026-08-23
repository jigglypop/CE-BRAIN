"""Deterministic status-only classification derived from frozen BA-SRM8 v2 receipts."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
F0 = ROOT / "f0-receipt-v2.json"
F1 = ROOT / "f1-receipt-v2.json"
OUT = ROOT / "f0f1-classification-receipt.json"
EXPECTED = {
    "f0": "4a71893a420c054bf39ac8661e21e7c71655ffeb53fe04c9d6f2e211f06ffb33",
    "f1": "3ba86b48892991406f593b5ffd0c818faa65ec8b5bdb0fad5acd924a8aa63c26",
    "core": "e685568ad4836dab1f301f69afa2e9c9a4d8fcecd7a1a64fb2bdba830a5ebc65",
    "runner": "168de51dcf133bb4fc3075ac5c0a9beea998462dac0d81c7e20cf68e6b36bbd4",
    "manifest": "58280bb9759549b9f285e95135b5320e44f1d317adf347a065319f367a3e6a0c",
}


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def count(rows: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        out[row["status"]] = out.get(row["status"], 0) + 1
    return dict(sorted(out.items()))


def projection(rows: list[dict]) -> str:
    """All candidate fields except the only authorized status/reason fields."""
    return digest_bytes(canonical([{key: value for key, value in row.items() if key not in {"status", "reason"}} for row in rows]))


def main() -> None:
    f0_bytes, f1_bytes = F0.read_bytes(), F1.read_bytes()
    if digest_bytes(f0_bytes) != EXPECTED["f0"] or digest_bytes(f1_bytes) != EXPECTED["f1"]:
        raise ValueError("frozen source receipt hash mismatch")
    f0, f1 = json.loads(f0_bytes), json.loads(f1_bytes)
    if f0["input_hashes"]["core_sha256"] != EXPECTED["core"] or f0["input_hashes"]["runner_sha256"] != EXPECTED["runner"]:
        raise ValueError("frozen code hash mismatch")
    if f0["input_hashes"]["manifest_sha256"] != EXPECTED["manifest"]:
        raise ValueError("manifest hash mismatch")
    target = []
    for row in f0["candidates"]:
        identifier = row["id"]
        family_match = identifier.startswith("EXP_theta2__") or identifier.startswith("COMPACT_L4__")
        if family_match and row["status"] == "INVALID_KILL" and row["reason"] == "invalid calibration scale terms":
            target.append(identifier)
    if len(target) != 12 or len(set(target)) != 12:
        raise ValueError("expected exact 12 classification targets")
    f1_by_id = {row["id"]: row for row in f1["candidates"]}
    if any(f1_by_id[item]["status"] != "INVALID_KILL" or f1_by_id[item]["reason"] != "F0_INVALID_KILL" for item in target):
        raise ValueError("F1 source status mapping mismatch")
    f0_after = [{**row, **({"status": "ABSTAIN", "reason": "ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF"} if row["id"] in target else {})} for row in f0["candidates"]]
    f1_after = [{**row, **({"status": "ABSTAIN", "reason": "ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF"} if row["id"] in target else {})} for row in f1["candidates"]]
    if projection(f0["candidates"]) != projection(f0_after) or projection(f1["candidates"]) != projection(f1_after):
        raise ValueError("unauthorized candidate-field mutation")
    promoted = f1["promoted_ids"]
    receipt = {
        "all_source_hashes": EXPECTED,
        "attempt_00_promotion_valid": False,
        "behavior_loaded": False,
        "before_after_counts": {"f0": {"after": count(f0_after), "before": count(f0["candidates"])}, "f1": {"after": count(f1_after), "before": count(f1["candidates"])}},
        "canonical_promotion_ids_sha256": digest_bytes(canonical(promoted)),
        "classification_valid": True,
        "deterministic_status_only": True,
        "invariant_projection_sha256": {"f0_after": projection(f0_after), "f0_before": projection(f0["candidates"]), "f1_after": projection(f1_after), "f1_before": projection(f1["candidates"])},
        "mapped_ids": target,
        "mapping": {"f0": {"from": {"reason": "invalid calibration scale terms", "status": "INVALID_KILL"}, "to": {"reason": "ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF", "status": "ABSTAIN"}}, "f1": {"from": {"reason": "F0_INVALID_KILL", "status": "INVALID_KILL"}, "to": {"reason": "ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF", "status": "ABSTAIN"}}},
        "model_fit": False,
        "numerical_rerun": False,
        "promoted_ids": promoted,
        "schema": "BA-SRM8-F0F1-classification-v1",
    }
    data = canonical(receipt)
    with OUT.open("wb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    if OUT.read_bytes() != data:
        raise ValueError("receipt persistence mismatch")
    print(json.dumps({"hash": digest_bytes(data), "mapped": len(target), "promotion_hash": receipt["canonical_promotion_ids_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
