"""Score-blind apparatus audit for hc-3 ec016.17/ec016.233."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_stage7_hc3"
ARCHIVE = DATA / "ec016.17" / "ec016.233.tar.gz"
PREFIX = DATA / "extracted" / "ec016.17" / "ec016.233" / "ec016.233"
DB = DATA / "metadata" / "hc3-metadata-tables" / "hc3-tables.db"
EXPECTED_MD5 = "9986ef9400e9862fb1142742455f95df"
POSITION_RATE = 39.0625


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def audit() -> dict[str, object]:
    if digest(ARCHIVE, "md5") != EXPECTED_MD5:
        raise RuntimeError("STAGE7_R2B_APPARATUS_STOP: archive MD5")
    xml = ET.parse(Path(f"{PREFIX}.xml")).getroot()
    channels = int(xml.findtext("acquisitionSystem/nChannels"))
    spike_rate = int(xml.findtext("acquisitionSystem/samplingRate"))
    lfp_rate = int(xml.findtext("fieldPotentials/lfpSamplingRate"))
    eeg_duration = Path(f"{PREFIX}.eeg").stat().st_size / (2 * channels * lfp_rate)
    position = np.loadtxt(Path(f"{PREFIX}.whl"))
    position_duration = len(position) / POSITION_RATE
    position_valid = float(np.all(position >= 0, axis=1).mean())
    connection = sqlite3.connect(DB)
    try:
        metadata_duration = float(connection.execute(
            "select duration from session where topdir=? and session=?", ("ec016.17", "ec016.233")
        ).fetchone()[0])
        cells = [(int(e), int(c)) for e, c in connection.execute(
            "select ele,clu from cell where topdir=? and region='CA1' and cellType='p' order by ele,clu", ("ec016.17",)
        ).fetchall()]
    finally:
        connection.close()
    present = 0
    for electrode in sorted({electrode for electrode, _ in cells}):
        labels = np.loadtxt(Path(f"{PREFIX}.clu.{electrode}"), dtype=int, ndmin=1)[1:]
        times = np.loadtxt(Path(f"{PREFIX}.res.{electrode}"), dtype=int, ndmin=1)
        if len(labels) != len(times):
            raise RuntimeError(f"STAGE7_R2B_APPARATUS_STOP: clu/res {electrode}")
        present += sum(cluster in set(labels.tolist()) for e, cluster in cells if e == electrode)
    passed = bool(
        spike_rate == 20_000 and lfp_rate == 1_250
        and abs(eeg_duration - metadata_duration) < 0.1
        and abs(position_duration - eeg_duration) < 0.1
        and position_valid >= 0.90 and len(cells) == 84 and present == 84
    )
    return {
        "decision": "STAGE7_R2B_APPARATUS_ELIGIBLE" if passed else "STAGE7_R2B_APPARATUS_STOP",
        "archive_md5": EXPECTED_MD5,
        "archive_sha256": digest(ARCHIVE),
        "metadata_db_sha256": digest(DB),
        "channels": channels,
        "spike_sampling_rate_hz": spike_rate,
        "lfp_sampling_rate_hz": lfp_rate,
        "metadata_duration_seconds": metadata_duration,
        "lfp_duration_seconds": eeg_duration,
        "position_duration_seconds": position_duration,
        "position_rows": len(position),
        "position_valid_fraction": position_valid,
        "ca1_pyramidal_units": len(cells),
        "ca1_units_present": present,
        "ca1_electrodes": sorted({electrode for electrode, _ in cells}),
        "claim_ceiling": "apparatus eligibility only; ripple and replay scores unopened",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise RuntimeError(f"STAGE7_R2B_APPARATUS_STOP: refusing overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
