"""Endpoint-blind apparatus audit for the CE-BRAIN Stage 7 hc-3 session."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_stage7_hc3"
ARCHIVE = DATA / "ec013.40" / "ec013.719.tar.gz"
SESSION = DATA / "extracted" / "ec013.40" / "ec013.719"
PREFIX = SESSION / "ec013.719"
DB = DATA / "metadata" / "hc3-metadata-tables" / "hc3-tables.db"
EXPECTED_MD5 = "32517ed8114e1b930df7925da6f2bb68"


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def load_vector(path: Path, dtype=float) -> np.ndarray:
    return np.loadtxt(path, dtype=dtype, ndmin=1)


def cluster_receipt(prefix: Path, electrode: int) -> dict[str, int]:
    clusters = load_vector(Path(f"{prefix}.clu.{electrode}"), int)
    times = load_vector(Path(f"{prefix}.res.{electrode}"), int)
    declared = int(clusters[0])
    labels = clusters[1:]
    if len(labels) != len(times):
        raise RuntimeError(f"STAGE7_APPARATUS_STOP: electrode {electrode} clu/res mismatch")
    return {"declared_clusters": declared, "spikes": int(len(times)), "observed_labels": int(len(np.unique(labels)))}


def audit() -> dict[str, Any]:
    if digest(ARCHIVE, "md5") != EXPECTED_MD5:
        raise RuntimeError("STAGE7_APPARATUS_STOP: archive MD5")
    xml = ET.parse(Path(f"{PREFIX}.xml")).getroot()
    channels = int(xml.findtext("acquisitionSystem/nChannels"))
    sampling_rate = int(xml.findtext("acquisitionSystem/samplingRate"))
    lfp_rate = int(xml.findtext("fieldPotentials/lfpSamplingRate"))
    eeg_bytes = Path(f"{PREFIX}.eeg").stat().st_size
    if eeg_bytes % (2 * channels):
        raise RuntimeError("STAGE7_APPARATUS_STOP: EEG shape")
    eeg_samples = eeg_bytes // (2 * channels)
    whl = np.loadtxt(Path(f"{PREFIX}.whl"))
    valid = np.all(whl >= 0, axis=1)
    connection = sqlite3.connect(DB)
    try:
        session = connection.execute(
            "select behavior,familiarity,duration from session where topdir=? and session=?",
            ("ec013.40", "ec013.719"),
        ).fetchone()
        cells = connection.execute(
            "select ele,clu,region,cellType from cell where topdir=? order by ele,clu", ("ec013.40",)
        ).fetchall()
        epos = connection.execute("select * from epos where topdir=?", ("ec013.40",)).fetchone()
    finally:
        connection.close()
    if session is None or epos is None:
        raise RuntimeError("STAGE7_APPARATUS_STOP: metadata")
    ca1_pyramidal = [(int(ele), int(clu)) for ele, clu, region, cell_type in cells if region == "CA1" and cell_type == "p"]
    clusters = {str(electrode): cluster_receipt(PREFIX, electrode) for electrode in range(1, 9)}
    duration = eeg_samples / lfp_rate
    valid_schema = bool(
        session[0] == "linear"
        and len(ca1_pyramidal) >= 30
        and valid.mean() >= 0.9
        and abs(duration - float(session[2])) < 0.1
        and sampling_rate == 20_000
        and lfp_rate == 1_250
    )
    return {
        "decision": "STAGE7_HC3_APPARATUS_ELIGIBLE" if valid_schema else "STAGE7_APPARATUS_STOP",
        "archive_md5": EXPECTED_MD5,
        "archive_sha256": digest(ARCHIVE),
        "metadata_db_sha256": digest(DB),
        "topdir": "ec013.40",
        "session": "ec013.719",
        "behavior": session[0],
        "familiarity": int(session[1]),
        "duration_seconds": float(session[2]),
        "channels": channels,
        "spike_sampling_rate_hz": sampling_rate,
        "lfp_sampling_rate_hz": lfp_rate,
        "eeg_samples": int(eeg_samples),
        "position_rows": int(len(whl)),
        "position_valid_fraction": float(valid.mean()),
        "ca1_pyramidal_units": len(ca1_pyramidal),
        "ca1_electrodes": sorted({electrode for electrode, _ in ca1_pyramidal}),
        "cluster_receipts": clusters,
        "claim_ceiling": "apparatus eligibility only; no ripple or replay endpoint opened",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise RuntimeError(f"STAGE7_APPARATUS_STOP: refusing overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()

