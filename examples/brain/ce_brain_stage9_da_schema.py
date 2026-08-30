"""Download-verified, value-blind longitudinal schema audit for DANDI 001632."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

import h5py

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "artifacts" / "brain" / "ce_brain_stage9_da_apparatus" / "inventory.json"
DATA = ROOT / "data" / "external" / "ce_brain_stage9_da" / "schema"
SUBJECTS = {"30s": "sub-30s-F2", "60s": "sub-60s-F1", "300s": "sub-300s-F2", "600s": "sub-600s-F1"}
CHEMICAL_TERMS = ("photometry", "dopamine", "fluorescence", "fiber_photometry")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024): value.update(block)
    return value.hexdigest()


def detail(asset_id: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"https://api.dandiarchive.org/api/assets/{asset_id}/", timeout=30) as response: return json.load(response)


def ensure_asset(row: dict[str, Any]) -> Path:
    target = DATA / Path(row["path"]).name
    metadata = detail(row["asset_id"]); expected = metadata["digest"]["dandi:sha2-256"]
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".partial")
        urllib.request.urlretrieve(metadata["contentUrl"][1], temporary)
        temporary.replace(target)
    if target.stat().st_size != int(row["size"]) or digest(target) != expected: raise RuntimeError(f"STAGE9_DA_SCHEMA_STOP: hash {target.name}")
    return target


def schema(path: Path) -> dict[str, Any]:
    paths, shapes = [], {}
    with h5py.File(path, "r") as handle:
        def visit(name: str, item: h5py.Group | h5py.Dataset) -> None:
            if name.startswith("specifications/"): return
            paths.append(name)
            if isinstance(item, h5py.Dataset): shapes[name] = list(item.shape)
        handle.visititems(visit)
    lower = [name.lower() for name in paths]
    chemical = sorted(name for name, folded in zip(paths, lower) if any(term in folded for term in CHEMICAL_TERMS))
    behavior = "acquisition/eventLog" in paths
    return {"sha256": digest(path), "behavior_event_log": behavior, "chemical_instance_paths": chemical, "dataset_shapes": shapes}


def audit() -> dict[str, Any]:
    rows = json.loads(INVENTORY.read_text(encoding="utf-8")); sessions, condition_status = {}, {}
    for condition, subject in SUBJECTS.items():
        selected = [row for row in rows if row["path"].startswith(subject + "/")]
        selected.sort(key=lambda row: row["path"]); receipts = []
        for row in selected:
            path = ensure_asset(row); receipts.append({"path": row["path"], "asset_id": row["asset_id"], **schema(path)})
        sessions[condition] = receipts
        behavior_count = sum(item["behavior_event_log"] for item in receipts)
        chemical_count = sum(bool(item["chemical_instance_paths"]) for item in receipts)
        condition_status[condition] = {"sessions": len(receipts), "behavior_sessions": behavior_count, "chemical_sessions": chemical_count, "eligible": behavior_count >= 2 and chemical_count >= 1}
    passed = all(value["eligible"] for value in condition_status.values())
    return {"decision": "STAGE9_DA_LONGITUDINAL_SCHEMA_ELIGIBLE" if passed else "STAGE9_DA_LONGITUDINAL_SCHEMA_STOP", "subjects": SUBJECTS, "condition_status": condition_status, "sessions": sessions, "values_scored": False, "inventory_file_sha256": digest(INVENTORY)}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args(); result = audit()
    if args.output.exists(): raise RuntimeError("STAGE9_DA_SCHEMA_STOP: refusing overwrite")
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"); print(json.dumps({"decision": result["decision"], "condition_status": result["condition_status"]}, sort_keys=True))


if __name__ == "__main__": main()
