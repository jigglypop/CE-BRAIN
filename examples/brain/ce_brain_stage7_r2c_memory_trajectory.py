"""Sealed R2C validation-selected memory-trajectory test on hc-3 ec016.233."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, hilbert, sosfiltfilt

from examples.brain import ce_brain_stage7_r1_memory_trajectory as r1

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_stage7_hc3"
ARCHIVE = DATA / "ec016.17" / "ec016.233.tar.gz"
PREFIX = DATA / "extracted" / "ec016.17" / "ec016.233" / "ec016.233"
DB = DATA / "metadata" / "hc3-metadata-tables" / "hc3-tables.db"
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE7_R2C_기억궤적_계약.md"
APPARATUS = ROOT / "artifacts" / "brain" / "ce_brain_stage7_r2b_apparatus" / "receipt.json"
APPARATUS_CODE = ROOT / "examples" / "brain" / "ce_brain_stage7_r2b_apparatus.py"
R1_CODE = ROOT / "examples" / "brain" / "ce_brain_stage7_r1_memory_trajectory.py"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage7_r2c_memory_trajectory.py"
ARTIFACT = ROOT / "artifacts" / "brain" / "ce_brain_stage7_r2c_memory_trajectory"
EXPECTED_MD5 = "9986ef9400e9862fb1142742455f95df"
CONFIGS = tuple((sigma, prior, dt) for sigma in (0.5, 1.0, 2.0, 3.0) for prior in ("occupancy", "uniform") for dt in (0.1, 0.2))


def configure_r1() -> None:
    r1.PREFIX = PREFIX
    r1.DB = DB
    r1.N_CHANNELS = 90


def load_units() -> tuple[list[np.ndarray], list[tuple[int, int]]]:
    connection = sqlite3.connect(DB)
    try:
        cells = [(int(e), int(c)) for e, c in connection.execute(
            "select ele,clu from cell where topdir=? and region='CA1' and cellType='p' order by ele,clu", ("ec016.17",)
        ).fetchall()]
    finally:
        connection.close()
    cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    units, identities = [], []
    for electrode, cluster in cells:
        if electrode not in cache:
            labels = np.loadtxt(Path(f"{PREFIX}.clu.{electrode}"), dtype=int, ndmin=1)[1:]
            times = np.loadtxt(Path(f"{PREFIX}.res.{electrode}"), dtype=int, ndmin=1)
            if len(labels) != len(times):
                raise RuntimeError("STAGE7_R2C_STOP: clu/res")
            cache[electrode] = labels, times
        labels, times = cache[electrode]
        if cluster in labels:
            units.append(times[labels == cluster].astype(float) / r1.SPIKE_RATE)
            identities.append((electrode, cluster))
    if len(units) != 75:
        raise RuntimeError(f"STAGE7_R2C_STOP: expected 75 present units, got {len(units)}")
    return units, identities


def place_fields(trace: dict[str, np.ndarray], units: list[np.ndarray], train: list[dict[str, Any]], sigma: float) -> tuple[np.ndarray, np.ndarray]:
    mask = r1.interval_mask(len(trace["time"]), train) & trace["valid"] & (trace["speed"] > 0.10)
    edges = np.linspace(0, 1, r1.POSITION_BINS + 1)
    occupancy, _ = np.histogram(trace["position"][mask], edges)
    occupancy = occupancy / r1.POSITION_RATE
    counts = np.zeros((len(units), r1.POSITION_BINS))
    for unit, spikes in enumerate(units):
        indices = np.clip(np.rint(spikes * r1.POSITION_RATE).astype(int), 0, len(mask) - 1)
        selected = indices[mask[indices]]
        counts[unit], _ = np.histogram(trace["position"][selected], edges)
    smooth_occupancy = gaussian_filter1d(occupancy.astype(float), sigma, mode="nearest")
    smooth_counts = gaussian_filter1d(counts, sigma, axis=1, mode="nearest")
    rates = np.maximum(smooth_counts / np.maximum(smooth_occupancy[None, :], 1e-6), 1e-4)
    return rates, smooth_occupancy / smooth_occupancy.sum()


def encoding(trace: dict[str, np.ndarray], units: list[np.ndarray], rates: np.ndarray, decode_prior: np.ndarray, baseline_prior: np.ndarray, rows: list[dict[str, Any]], dt: float) -> dict[str, float]:
    actual, decoded = [], []
    for row in rows:
        start, stop = trace["time"][row["start"]], trace["time"][row["stop"]]
        starts = np.arange(start, stop - dt, dt)
        if not len(starts):
            continue
        counts = r1.bin_counts(units, starts, starts + dt)
        estimate, _ = r1.decode(counts, rates, decode_prior, dt)
        indices = np.clip(np.rint((starts + dt / 2) * r1.POSITION_RATE).astype(int), 0, len(trace["position"]) - 1)
        valid = trace["valid"][indices]
        actual.extend(trace["position"][indices][valid]); decoded.extend(estimate[valid])
    actual_array, decoded_array = np.asarray(actual), np.asarray(decoded)
    if len(actual_array) < 100:
        raise RuntimeError("STAGE7_R2C_STOP: encoding coverage")
    centers = (np.arange(r1.POSITION_BINS) + 0.5) / r1.POSITION_BINS
    error = float(np.median(np.abs(actual_array - decoded_array)))
    baseline = float(np.median(np.abs(actual_array - np.sum(baseline_prior * centers))))
    return {"median_absolute_error": error, "static_baseline_error": baseline, "improvement": (baseline - error) / baseline, "samples": int(len(actual_array))}


def select_config(trace: dict[str, np.ndarray], units: list[np.ndarray], split: dict[str, list[dict[str, Any]]]) -> tuple[tuple[float, str, float], list[dict[str, Any]]]:
    receipts = []
    for sigma, prior_name, dt in CONFIGS:
        rates, occupancy = place_fields(trace, units, split["train"], sigma)
        decode_prior = occupancy if prior_name == "occupancy" else np.full(r1.POSITION_BINS, 1 / r1.POSITION_BINS)
        score = encoding(trace, units, rates, decode_prior, occupancy, split["validation"], dt)
        receipts.append({"sigma": sigma, "prior": prior_name, "dt": dt, **score})
    winner = min(receipts, key=lambda row: (row["median_absolute_error"], row["sigma"], row["prior"], row["dt"]))
    return (float(winner["sigma"]), str(winner["prior"]), float(winner["dt"])), receipts


def ripple_events(trace: dict[str, np.ndarray]) -> tuple[list[tuple[float, float]], dict[str, float]]:
    raw = np.memmap(Path(f"{PREFIX}.eeg"), dtype="<i2", mode="r").reshape(-1, 90)[:, 0].astype(float)
    envelope = np.abs(hilbert(sosfiltfilt(butter(4, [120, 250], btype="bandpass", fs=r1.LFP_RATE, output="sos"), raw)))
    index = np.clip(np.rint((np.arange(len(raw)) / r1.LFP_RATE) * r1.POSITION_RATE).astype(int), 0, len(trace["speed"]) - 1)
    immobile = trace["valid"][index] & (trace["speed"][index] < 0.02)
    baseline = envelope[immobile]; median = float(np.median(baseline)); scale = float(1.4826 * np.median(np.abs(baseline - median)))
    z = (envelope - median) / scale
    transitions = np.diff(np.r_[False, z >= 1.5, False].astype(int))
    starts, stops = np.flatnonzero(transitions == 1), np.flatnonzero(transitions == -1) - 1
    merged: list[list[int]] = []
    for start, stop in zip(starts, stops):
        if merged and start - merged[-1][1] - 1 < round(0.03 * r1.LFP_RATE): merged[-1][1] = int(stop)
        else: merged.append([int(start), int(stop)])
    events = []
    for start, stop in merged:
        duration = (stop - start + 1) / r1.LFP_RATE; center = (start + stop) // 2
        if 0.04 <= duration <= 0.4 and np.max(z[start:stop + 1]) >= 3.5 and immobile[center]: events.append((start / r1.LFP_RATE, (stop + 1) / r1.LFP_RATE))
    return events, {"robust_envelope_median": median, "robust_envelope_scale": scale, "raw_candidate_count": len(merged), "channel": 0}


def analyze() -> dict[str, Any]:
    configure_r1(); trace = r1.position_trace(); traversals = r1.detect_traversals(trace["position"], trace["valid"]); split = r1.split_traversals(traversals)
    units, identities = load_units(); selected, validation = select_config(trace, units, split)
    sigma, prior_name, dt = selected; rates, occupancy = place_fields(trace, units, split["train"], sigma)
    decode_prior = occupancy if prior_name == "occupancy" else np.full(r1.POSITION_BINS, 1 / r1.POSITION_BINS)
    test = encoding(trace, units, rates, decode_prior, occupancy, split["test"], dt)
    events, ripple = ripple_events(trace); replay = r1.replay_scores(events, units, rates, decode_prior)
    base = r1.decide(test, replay)
    decisions = {"DEVELOPMENT_MEMORY_TRAJECTORY_SUPPORTED": "DEVELOPMENT_MEMORY_TRAJECTORY_SUPPORTED_REPLICATED", "TRAJECTORY_MEMORY_NOT_ESTABLISHED": "TRAJECTORY_MEMORY_NOT_ESTABLISHED_REPLICATED", "ENCODING_TRAJECTORY_ONLY_REPLAY_NOT_ESTABLISHED": "ENCODING_TRAJECTORY_ONLY_REPLAY_NOT_ESTABLISHED_REPLICATED", "STAGE7_REPLAY_COVERAGE_STOP": "STAGE7_R2C_REPLAY_COVERAGE_STOP"}
    return {"decision": decisions[base], "claim_ceiling": "independent-topdir development replication; validation-selected decoder", "coverage": {"traversals": len(traversals), "train": len(split["train"]), "validation": len(split["validation"]), "test": len(split["test"]), "ca1_units": len(units), "first_unit": list(identities[0]), "last_unit": list(identities[-1]), "detected_ripples": len(events)}, "selected_config": {"sigma": sigma, "prior": prior_name, "dt": dt}, "validation_candidates": validation, "test_encoding": test, "ripple_detection": ripple, "replay": replay}


def files() -> tuple[Path, ...]:
    paths = [Path(__file__).resolve(), TEST_FILE, CONTRACT, APPARATUS_CODE, APPARATUS, R1_CODE, DB, Path(f"{PREFIX}.xml"), Path(f"{PREFIX}.whl")]
    for electrode in (1, 2, 3, 4, 7, 8, 9, 10): paths.extend((Path(f"{PREFIX}.clu.{electrode}"), Path(f"{PREFIX}.res.{electrode}")))
    return tuple(paths)


def seal(artifact: Path) -> dict[str, Any]:
    if r1.digest(ARCHIVE, "md5") != EXPECTED_MD5: raise RuntimeError("STAGE7_R2C_STOP: archive")
    manifest = {"files": {str(p.relative_to(ROOT)).replace("\\", "/"): r1.digest(p) for p in files()}, "archive_md5": EXPECTED_MD5, "eeg_sha256": r1.digest(Path(f"{PREFIX}.eeg")), "runtime": r1.runtime(), "scores_opened": False}
    manifest["manifest_sha256"] = r1.write_once(artifact / r1.MANIFEST, manifest); return manifest


def verify_manifest(artifact: Path) -> str:
    path = artifact / r1.MANIFEST; stored = json.loads(path.read_text(encoding="utf-8"))
    expected = {str(p.relative_to(ROOT)).replace("\\", "/"): r1.digest(p) for p in files()}
    if stored.get("files") != expected or stored.get("archive_md5") != EXPECTED_MD5 or stored.get("eeg_sha256") != r1.digest(Path(f"{PREFIX}.eeg")) or stored.get("runtime") != r1.runtime() or stored.get("scores_opened") is not False: raise RuntimeError("STAGE7_R2C_STOP: manifest mutation")
    return r1.digest(path)


def execute(artifact: Path) -> dict[str, Any]:
    result = analyze(); result["manifest_sha256"] = verify_manifest(artifact); result_hash = r1.write_once(artifact / r1.RESULT, result); return {"result_sha256": result_hash, **result}


def verify_result(artifact: Path) -> dict[str, Any]:
    stored_path = artifact / r1.RESULT; stored = json.loads(stored_path.read_text(encoding="utf-8")); fresh = analyze(); fresh["manifest_sha256"] = verify_manifest(artifact)
    if r1.canonical_bytes(stored) != r1.canonical_bytes(fresh): raise RuntimeError("STAGE7_R2C_STOP: raw recomputation mismatch")
    receipt = {"status": "PASS", "raw_recomputed": True, "decision": stored["decision"], "result_sha256": r1.digest(stored_path)}; receipt["validation_receipt_sha256"] = r1.write_once(artifact / r1.VALIDATION, receipt); return receipt


def main() -> None:
    parser = argparse.ArgumentParser(); group = parser.add_mutually_exclusive_group(required=True); group.add_argument("--seal", action="store_true"); group.add_argument("--execute", action="store_true"); group.add_argument("--verify-result", action="store_true"); parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT); args = parser.parse_args()
    value = seal(args.artifact_dir) if args.seal else execute(args.artifact_dir) if args.execute else verify_result(args.artifact_dir)
    print(json.dumps(value, sort_keys=True))


if __name__ == "__main__": main()
