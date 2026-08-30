"""Metadata-only inventory lock for DANDI 001632 Stage 9 dopamine apparatus."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://api.dandiarchive.org/api/dandisets/001632/versions/draft"
CORE = ("30s", "60s", "300s", "600s")
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE9_DA_장치계약.md"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def condition(subject: str) -> str:
    return re.sub(r"-[FM]\d+$", "", subject.removeprefix("sub-"))


def split_subjects(subjects: list[str]) -> dict[str, list[str]]:
    ordered = sorted(subjects, key=lambda item: hashlib.sha256(f"CE-BRAIN-STAGE9|{item}".encode()).hexdigest())
    n = len(ordered); dev_end = max(1, math.floor(0.6 * n)); cal_end = max(dev_end + 1, math.floor(0.8 * n)); cal_end = min(cal_end, n - 1)
    return {"development": ordered[:dev_end], "calibration": ordered[dev_end:cal_end], "confirmation": ordered[cal_end:]}


def fetch_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def fetch_inventory() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    metadata = fetch_json(f"{BASE}/")
    url: str | None = f"{BASE}/assets/?page_size=100"
    assets = []
    while url:
        page = fetch_json(url); assets.extend(page["results"]); url = page["next"]
    rows = [{key: row[key] for key in ("asset_id", "path", "size", "created", "modified")} for row in assets]
    rows.sort(key=lambda row: row["path"])
    return metadata, rows


def audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    metadata, rows = fetch_inventory()
    subjects = sorted({row["path"].split("/")[0] for row in rows})
    groups = {name: [subject for subject in subjects if condition(subject) == name] for name in CORE}
    splits = {name: split_subjects(group) for name, group in groups.items()}
    selected = {}
    for name in CORE:
        subject = sorted(splits[name]["development"])[0]
        candidates = [row for row in rows if row["path"].startswith(subject + "/") and "ses-day01" in row["path"]]
        if not candidates:
            raise RuntimeError(f"STAGE9_DA_APPARATUS_STOP: no day01 {subject}")
        selected[name] = min(candidates, key=lambda row: (row["size"], row["path"]))
    receipt = {
        "decision": "STAGE9_DA_METADATA_LOCKED_SCHEMA_PENDING",
        "dandiset": "001632",
        "version": "draft",
        "asset_count": len(rows),
        "total_bytes": sum(int(row["size"]) for row in rows),
        "subject_count": len(subjects),
        "inventory_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
        "metadata_sha256": hashlib.sha256(canonical(metadata)).hexdigest(),
        "core_condition_counts": {name: len(groups[name]) for name in CORE},
        "splits": splits,
        "schema_assets": selected,
        "endpoint_opened": False,
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
    }
    return receipt, rows


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, required=True); args = parser.parse_args()
    receipt, rows = audit(); args.output_dir.mkdir(parents=True, exist_ok=True)
    inventory_path, receipt_path = args.output_dir / "inventory.json", args.output_dir / "metadata-receipt.json"
    if inventory_path.exists() or receipt_path.exists(): raise RuntimeError("STAGE9_DA_APPARATUS_STOP: refusing overwrite")
    inventory_path.write_bytes(canonical(rows) + b"\n"); receipt["inventory_file_sha256"] = hashlib.sha256(inventory_path.read_bytes()).hexdigest(); receipt_path.write_bytes(canonical(receipt) + b"\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__": main()
