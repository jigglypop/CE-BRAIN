"""Endpoint-blind selector for an independent CE-BRAIN Stage 7 hc-3 session."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_stage7_hc3"
DB = DATA / "metadata" / "hc3-metadata-tables" / "hc3-tables.db"
FILELIST = DATA / "filelist.txt"
CHECKSUMS = DATA / "checksums.md5"
EXCLUDED_TOPDIRS = ("ec013.40",)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def select() -> dict[str, object]:
    connection = sqlite3.connect(DB)
    try:
        rows = connection.execute(
            """
            select s.topdir, s.session, s.familiarity, s.duration, f.size, f.video_type,
                   (select count(*) from cell c where c.topdir=s.topdir and c.region='CA1' and c.cellType='p') ca1p
            from session s join file f on f.topdir=s.topdir and f.session=s.session
            where s.behavior='linear' and s.duration>=600 and f.video_type is not null
            """
        ).fetchall()
    finally:
        connection.close()
    eligible = [row for row in rows if row[0] not in EXCLUDED_TOPDIRS and int(row[6]) >= 30]
    if not eligible:
        raise RuntimeError("STAGE7_R2_SELECTION_STOP: no eligible session")
    best_units = max(int(row[6]) for row in eligible)
    topdir = sorted({str(row[0]) for row in eligible if int(row[6]) == best_units})[0]
    selected = min((row for row in eligible if row[0] == topdir), key=lambda row: (int(row[4]), str(row[1])))
    checksum_key = f"{selected[0]}/{selected[1]}.tar.gz"
    checksum = next((line.split()[0] for line in CHECKSUMS.read_text(encoding="utf-8").splitlines() if line.endswith(checksum_key)), None)
    if checksum is None:
        raise RuntimeError("STAGE7_R2_SELECTION_STOP: checksum missing")
    return {
        "decision": "STAGE7_R2_ENDPOINT_BLIND_SESSION_SELECTED",
        "topdir": selected[0],
        "session": selected[1],
        "familiarity": int(selected[2]),
        "duration_seconds": float(selected[3]),
        "archive_bytes": int(selected[4]),
        "video_type": selected[5],
        "ca1_pyramidal_units": int(selected[6]),
        "archive_md5": checksum,
        "selection_rule": "exclude R1 topdir; linear >=600 s; video; >=30 CA1 pyramidal; maximize units by topdir, then minimize archive bytes",
        "endpoint_opened": False,
        "metadata_sha256": digest(DB),
        "filelist_sha256": digest(FILELIST),
        "checksums_sha256": digest(CHECKSUMS),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = select()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise RuntimeError(f"STAGE7_R2_SELECTION_STOP: refusing overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
