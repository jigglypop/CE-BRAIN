"""Endpoint-blind apparatus receipt for CE-BRAIN Stage 6 development data."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

DANDISET = "000021"
VERSION = "0.251116.2246"
API = f"https://api.dandiarchive.org/api/dandisets/{DANDISET}/versions/{VERSION}/assets/"
SALT = "CE-BRAIN-STAGE6-ALLEN-V1"


def fetch_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def collect_assets(fetch=fetch_json) -> list[dict[str, Any]]:
    url: str | None = f"{API}?page_size=100"
    rows: list[dict[str, Any]] = []
    while url:
        page = fetch(url)
        rows.extend(page["results"])
        url = page.get("next")
    return rows


def split_for(subject: str) -> str:
    value = int(hashlib.sha256(f"{SALT}|{subject}".encode()).hexdigest()[:8], 16) % 10
    return "development" if value < 6 else "calibration" if value < 8 else "confirmation"


def build_receipt(rows: list[dict[str, Any]]) -> dict[str, Any]:
    inventory = sorted(
        ({"asset_id": r["asset_id"], "path": r["path"], "size": int(r["size"])} for r in rows),
        key=lambda r: r["path"],
    )
    if len({r["asset_id"] for r in inventory}) != len(inventory):
        raise RuntimeError("STAGE6_APPARATUS_STOP: duplicate asset id")
    sessions = [r for r in inventory if "_probe-" not in r["path"]]
    probes = [r for r in inventory if "_probe-" in r["path"]]
    subjects = sorted({r["path"].split("/", 1)[0].removeprefix("sub-") for r in inventory})
    assignment = {subject: split_for(subject) for subject in subjects}
    counts = {name: sum(v == name for v in assignment.values()) for name in ("development", "calibration", "confirmation")}
    canonical = json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()
    return {
        "claim_ceiling": "metadata-only apparatus receipt; no neural endpoint opened",
        "dandiset": DANDISET,
        "version": VERSION,
        "asset_count": len(inventory),
        "subject_count": len(subjects),
        "session_asset_count": len(sessions),
        "probe_asset_count": len(probes),
        "total_bytes": sum(r["size"] for r in inventory),
        "inventory_sha256": hashlib.sha256(canonical).hexdigest(),
        "subject_split": assignment,
        "split_counts": counts,
        "confirmation_endpoint_opened": False,
        "dandi_001695_opened": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = build_receipt(collect_assets())
    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise RuntimeError(f"STAGE6_APPARATUS_STOP: refusing overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()

