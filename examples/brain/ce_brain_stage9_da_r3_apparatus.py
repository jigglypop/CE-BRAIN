"""Locked D-cohort schema gate for CE-BRAIN Stage 9."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from examples.brain.ce_brain_stage9_da_schema import digest, schema

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_stage9_da" / "dcohort"
INVENTORY = ROOT / "artifacts" / "brain" / "ce_brain_stage9_da_apparatus" / "inventory.json"
FILES = {
    "60sD": (DATA / "sub-60sD-F7_ses-day01.nwb", "14824eca5169143b8bd0eb87597d011064ec8c4bfdb646ae7cd12fa0716c62ce", "sub-60sD-F7"),
    "600sD": (DATA / "sub-600sD-F8_ses-day01.nwb", "47ef8735ec51e07d66cdc9b3b8b5a71c098b2178054400867bb5eaf5a1f8fa84", "sub-600sD-F8"),
}


def audit() -> dict[str, object]:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8")); receipts = {}; passed = True
    for condition, (path, expected, subject) in FILES.items():
        result = schema(path); next_days = sum(row["path"].startswith(subject + "/") for row in inventory)
        chemical_data = "processing/photometry/photometry_dff/data" in result["dataset_shapes"]
        chemical_time = "processing/photometry/photometry_dff/timestamps" in result["dataset_shapes"]
        eligible = digest(path) == expected and result["behavior_event_log"] and chemical_data and chemical_time and next_days >= 2
        passed &= eligible
        receipts[condition] = {"sha256": digest(path), "behavior_event_log": result["behavior_event_log"], "photometry_data_shape": result["dataset_shapes"].get("processing/photometry/photometry_dff/data"), "photometry_timestamp_shape": result["dataset_shapes"].get("processing/photometry/photometry_dff/timestamps"), "subject_sessions_in_inventory": next_days, "eligible": eligible}
    return {"decision": "STAGE9_DA_DCOHORT_SCHEMA_ELIGIBLE" if passed else "STAGE9_DA_DCOHORT_SCHEMA_STOP", "conditions": receipts, "chemical_values_scored": False, "confirmation_opened": False, "inventory_file_sha256": digest(INVENTORY)}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args(); result = audit()
    if args.output.exists(): raise RuntimeError("STAGE9_DA_DCOHORT_SCHEMA_STOP: refusing overwrite")
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"); print(json.dumps(result, sort_keys=True))


if __name__ == "__main__": main()
