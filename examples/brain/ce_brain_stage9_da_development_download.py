"""Download and hash-lock only Stage 9 dopamine development animals."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from examples.brain.ce_brain_stage9_da_schema import DATA as UNUSED_DATA, digest, ensure_asset

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "artifacts" / "brain" / "ce_brain_stage9_da_apparatus" / "inventory.json"
TARGET = ROOT / "data" / "external" / "ce_brain_stage9_da" / "development"
DEVELOPMENT = ("sub-60sD-F7", "sub-60sD-F11", "sub-60sD-F8", "sub-600sD-F8", "sub-600sD-F10", "sub-600sD-F7", "sub-600sD-M8")


def selected_rows() -> list[dict[str, object]]:
    rows = json.loads(INVENTORY.read_text(encoding="utf-8"))
    selected = [row for row in rows if row["path"].split("/")[0] in DEVELOPMENT]
    selected.sort(key=lambda row: row["path"])
    counts = {subject: sum(row["path"].startswith(subject + "/") for row in selected) for subject in DEVELOPMENT}
    if len(selected) != 57 or counts.get("sub-60sD-F8") != 9 or any(counts[subject] != 8 for subject in DEVELOPMENT if subject != "sub-60sD-F8"): raise RuntimeError("STAGE9_DA_DOWNLOAD_STOP: expected 57 locked assets")
    return selected


def download() -> dict[str, object]:
    import examples.brain.ce_brain_stage9_da_schema as helper
    helper.DATA = TARGET
    receipts = []
    for row in selected_rows():
        path = ensure_asset(row); receipts.append({"path": row["path"], "asset_id": row["asset_id"], "bytes": path.stat().st_size, "sha256": digest(path)})
    return {"decision": "STAGE9_DA_DEVELOPMENT_LOCKED", "subjects": list(DEVELOPMENT), "assets": receipts, "asset_count": len(receipts), "total_bytes": sum(item["bytes"] for item in receipts), "confirmation_opened": False, "inventory_file_sha256": digest(INVENTORY)}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args(); result = download()
    if args.output.exists(): raise RuntimeError("STAGE9_DA_DOWNLOAD_STOP: refusing overwrite")
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"); print(json.dumps({key: result[key] for key in ("decision", "asset_count", "total_bytes", "confirmation_opened")}, sort_keys=True))


if __name__ == "__main__": main()
