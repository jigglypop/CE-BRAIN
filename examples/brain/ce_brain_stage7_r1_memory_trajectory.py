"""Sealed Stage 7 R1 development test of trajectory-like CA1 replay."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sqlite3
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, hilbert, sosfiltfilt
from scipy.stats import binomtest, spearmanr

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_stage7_hc3"
PREFIX = DATA / "extracted" / "ec013.40" / "ec013.719" / "ec013.719"
DB = DATA / "metadata" / "hc3-metadata-tables" / "hc3-tables.db"
ARCHIVE = DATA / "ec013.40" / "ec013.719.tar.gz"
APPARATUS = ROOT / "artifacts" / "brain" / "ce_brain_stage7_hc3_apparatus" / "receipt.json"
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE7_R1_기억궤적_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage7_r1_memory_trajectory.py"
APPARATUS_CODE = ROOT / "examples" / "brain" / "ce_brain_stage7_hc3_apparatus.py"
ARTIFACT = ROOT / "artifacts" / "brain" / "ce_brain_stage7_r1_memory_trajectory"
SEED = 20_260_909
BOOTSTRAPS = 1_999
SHUFFLES = 199
POSITION_RATE = 39.0625
SPIKE_RATE = 20_000.0
LFP_RATE = 1_250.0
N_CHANNELS = 65
POSITION_BINS = 30
MANIFEST = "manifest.json"
RESULT = "result.json"
VALIDATION = "validation-receipt.json"
STOP = "STAGE7_R1_APPARATUS_STOP"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def write_once(path: Path, value: Any) -> str:
    if path.exists():
        raise RuntimeError(f"{STOP}: refusing overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return hashlib.sha256(payload).hexdigest()


def short_gap_interpolate(values: np.ndarray, valid: np.ndarray, limit: int) -> tuple[np.ndarray, np.ndarray]:
    result = values.astype(float).copy()
    accepted = valid.copy()
    missing = np.flatnonzero(~valid)
    if len(missing) == 0:
        return result, accepted
    starts = missing[np.r_[True, np.diff(missing) > 1]]
    ends = missing[np.r_[np.diff(missing) > 1, True]]
    for start, end in zip(starts, ends):
        if end - start + 1 <= limit and start > 0 and end + 1 < len(values) and valid[start - 1] and valid[end + 1]:
            fraction = np.arange(1, end - start + 2) / (end - start + 2)
            result[start : end + 1] = result[start - 1] + fraction[:, None] * (result[end + 1] - result[start - 1])
            accepted[start : end + 1] = True
    return result, accepted


def position_trace() -> dict[str, np.ndarray]:
    raw = np.loadtxt(Path(f"{PREFIX}.whl"))
    valid = np.all(raw >= 0, axis=1)
    centers = (raw[:, :2] + raw[:, 2:]) / 2
    centers, accepted = short_gap_interpolate(centers, valid, int(round(0.5 * POSITION_RATE)))
    filled = centers.copy()
    for column in range(2):
        indices = np.flatnonzero(accepted)
        filled[:, column] = np.interp(np.arange(len(filled)), indices, filled[indices, column])
        filled[:, column] = gaussian_filter1d(filled[:, column], 0.10 * POSITION_RATE, mode="nearest")
    centered = filled[accepted] - filled[accepted].mean(axis=0)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    projected = (filled - filled[accepted].mean(axis=0)) @ vt[0]
    low, high = np.quantile(projected[accepted], [0.01, 0.99])
    coordinate = np.clip((projected - low) / (high - low), 0, 1)
    speed = np.abs(np.gradient(coordinate) * POSITION_RATE)
    speed[~accepted] = np.nan
    return {"time": np.arange(len(raw)) / POSITION_RATE, "position": coordinate, "speed": speed, "valid": accepted}


def detect_traversals(position: np.ndarray, valid: np.ndarray) -> list[dict[str, Any]]:
    traversals: list[dict[str, Any]] = []
    index = 0
    maximum = int(30 * POSITION_RATE)
    minimum = int(1 * POSITION_RATE)
    while index < len(position):
        if valid[index] and (position[index] < 0.15 or position[index] > 0.85):
            direction = 1 if position[index] < 0.15 else -1
            target = position > 0.85 if direction == 1 else position < 0.15
            candidates = np.flatnonzero(target[index + minimum : min(len(position), index + maximum + 1)] & valid[index + minimum : min(len(position), index + maximum + 1)])
            if len(candidates):
                stop = index + minimum + int(candidates[0])
                fraction = float(np.mean(valid[index : stop + 1]))
                if fraction >= 0.8:
                    traversals.append({"start": index, "stop": stop, "direction": direction, "valid_fraction": fraction})
                    index = stop + 1
                    continue
        index += 1
    return traversals


def split_traversals(traversals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result = {"train": [], "validation": [], "test": []}
    for direction in (-1, 1):
        rows = [row for row in traversals if row["direction"] == direction]
        if len(rows) < 5:
            raise RuntimeError(f"{STOP}: only {len(rows)} traversals direction {direction}")
        train_end = max(1, int(np.floor(0.6 * len(rows))))
        validation_end = max(train_end + 1, int(np.floor(0.8 * len(rows))))
        result["train"].extend(rows[:train_end])
        result["validation"].extend(rows[train_end:validation_end])
        result["test"].extend(rows[validation_end:])
    if len(traversals) < 12:
        raise RuntimeError(f"{STOP}: traversal coverage")
    for rows in result.values():
        rows.sort(key=lambda row: row["start"])
    return result


def load_units() -> tuple[list[np.ndarray], list[tuple[int, int]]]:
    connection = sqlite3.connect(DB)
    try:
        cells = connection.execute(
            "select ele,clu from cell where topdir=? and region='CA1' and cellType='p' order by ele,clu", ("ec013.40",)
        ).fetchall()
    finally:
        connection.close()
    units = []
    identities = []
    cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for electrode, cluster in cells:
        electrode = int(electrode)
        if electrode not in cache:
            labels = np.loadtxt(Path(f"{PREFIX}.clu.{electrode}"), dtype=int, ndmin=1)[1:]
            times = np.loadtxt(Path(f"{PREFIX}.res.{electrode}"), dtype=int, ndmin=1)
            if len(labels) != len(times):
                raise RuntimeError(f"{STOP}: clu/res")
            cache[electrode] = labels, times
        labels, times = cache[electrode]
        units.append(times[labels == int(cluster)].astype(float) / SPIKE_RATE)
        identities.append((electrode, int(cluster)))
    if len(units) != 43:
        raise RuntimeError(f"{STOP}: CA1 unit count {len(units)}")
    return units, identities


def interval_mask(length: int, traversals: list[dict[str, Any]]) -> np.ndarray:
    mask = np.zeros(length, dtype=bool)
    for row in traversals:
        mask[row["start"] : row["stop"] + 1] = True
    return mask


def place_fields(trace: dict[str, np.ndarray], units: list[np.ndarray], train: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    mask = interval_mask(len(trace["time"]), train) & trace["valid"] & (trace["speed"] > 0.10)
    edges = np.linspace(0, 1, POSITION_BINS + 1)
    occupancy, _ = np.histogram(trace["position"][mask], edges)
    occupancy = occupancy / POSITION_RATE
    counts = np.zeros((len(units), POSITION_BINS))
    for unit, spikes in enumerate(units):
        indices = np.clip(np.rint(spikes * POSITION_RATE).astype(int), 0, len(mask) - 1)
        selected = indices[mask[indices]]
        counts[unit], _ = np.histogram(trace["position"][selected], edges)
    smooth_occupancy = gaussian_filter1d(occupancy.astype(float), 1, mode="nearest")
    smooth_counts = gaussian_filter1d(counts, 1, axis=1, mode="nearest")
    rates = smooth_counts / np.maximum(smooth_occupancy[None, :], 1e-6)
    rates = np.maximum(rates, 1e-4)
    prior = smooth_occupancy / smooth_occupancy.sum()
    return rates, prior


def bin_counts(units: list[np.ndarray], starts: np.ndarray, stops: np.ndarray) -> np.ndarray:
    output = np.empty((len(starts), len(units)), dtype=float)
    for unit, spikes in enumerate(units):
        output[:, unit] = np.searchsorted(spikes, stops, side="left") - np.searchsorted(spikes, starts, side="left")
    return output


def decode(counts: np.ndarray, rates: np.ndarray, prior: np.ndarray, dt: float) -> tuple[np.ndarray, np.ndarray]:
    log_likelihood = counts @ np.log(rates) - dt * rates.sum(axis=0)[None, :] + np.log(np.maximum(prior, 1e-12))[None, :]
    log_likelihood -= log_likelihood.max(axis=1, keepdims=True)
    posterior = np.exp(log_likelihood)
    posterior /= posterior.sum(axis=1, keepdims=True)
    centers = (np.arange(POSITION_BINS) + 0.5) / POSITION_BINS
    return posterior @ centers, posterior


def encoding_receipt(trace: dict[str, np.ndarray], units: list[np.ndarray], rates: np.ndarray, prior: np.ndarray, test: list[dict[str, Any]]) -> dict[str, float]:
    actual = []
    decoded = []
    for row in test:
        start_time = trace["time"][row["start"]]
        stop_time = trace["time"][row["stop"]]
        starts = np.arange(start_time, stop_time - 0.1, 0.1)
        if len(starts) == 0:
            continue
        counts = bin_counts(units, starts, starts + 0.1)
        estimate, _ = decode(counts, rates, prior, 0.1)
        indices = np.clip(np.rint((starts + 0.05) * POSITION_RATE).astype(int), 0, len(trace["position"]) - 1)
        valid = trace["valid"][indices]
        actual.extend(trace["position"][indices][valid])
        decoded.extend(estimate[valid])
    actual_array = np.asarray(actual)
    decoded_array = np.asarray(decoded)
    if len(actual_array) < 100:
        raise RuntimeError(f"{STOP}: encoding test coverage")
    error = float(np.median(np.abs(actual_array - decoded_array)))
    static = float(np.sum(prior * ((np.arange(POSITION_BINS) + 0.5) / POSITION_BINS)))
    baseline = float(np.median(np.abs(actual_array - static)))
    return {"median_absolute_error": error, "static_baseline_error": baseline, "improvement": (baseline - error) / baseline, "samples": int(len(actual_array))}


def ripple_events(trace: dict[str, np.ndarray]) -> tuple[list[tuple[float, float]], dict[str, float]]:
    raw = np.memmap(Path(f"{PREFIX}.eeg"), dtype="<i2", mode="r").reshape(-1, N_CHANNELS)[:, 32].astype(float)
    sos = butter(4, [120, 250], btype="bandpass", fs=LFP_RATE, output="sos")
    envelope = np.abs(hilbert(sosfiltfilt(sos, raw)))
    lfp_time = np.arange(len(raw)) / LFP_RATE
    position_index = np.clip(np.rint(lfp_time * POSITION_RATE).astype(int), 0, len(trace["speed"]) - 1)
    immobile = trace["valid"][position_index] & (trace["speed"][position_index] < 0.02)
    baseline = envelope[immobile]
    median = float(np.median(baseline))
    scale = float(1.4826 * np.median(np.abs(baseline - median)))
    if not np.isfinite(scale) or scale <= 0:
        raise RuntimeError(f"{STOP}: ripple scale")
    z = (envelope - median) / scale
    above = z >= 1.5
    transitions = np.diff(np.r_[False, above, False].astype(int))
    starts = np.flatnonzero(transitions == 1)
    stops = np.flatnonzero(transitions == -1) - 1
    merged: list[list[int]] = []
    gap = int(round(0.03 * LFP_RATE))
    for start, stop in zip(starts, stops):
        if merged and start - merged[-1][1] - 1 < gap:
            merged[-1][1] = int(stop)
        else:
            merged.append([int(start), int(stop)])
    events = []
    for start, stop in merged:
        duration = (stop - start + 1) / LFP_RATE
        center = (start + stop) // 2
        if 0.04 <= duration <= 0.4 and np.max(z[start : stop + 1]) >= 3.5 and immobile[center]:
            events.append((start / LFP_RATE, (stop + 1) / LFP_RATE))
    return events, {"robust_envelope_median": median, "robust_envelope_scale": scale, "raw_candidate_count": len(merged)}


def score_path(path: np.ndarray) -> tuple[float, float, float]:
    time = np.arange(len(path), dtype=float)
    order = spearmanr(time, path).statistic
    order = 0.0 if not np.isfinite(order) else abs(float(order))
    i, j = np.triu_indices(len(path), 1)
    distance = spearmanr(np.abs(i - j), np.abs(path[i] - path[j])).statistic
    distance = 0.0 if not np.isfinite(distance) else float(distance)
    jump = float(np.mean(np.abs(np.diff(path)))) if len(path) > 1 else 0.0
    return order, distance, jump


def bootstrap_difference(actual: np.ndarray, null: np.ndarray, offset: int) -> dict[str, float]:
    difference = actual - null
    rng = np.random.Generator(np.random.PCG64(SEED + offset))
    values = np.empty(BOOTSTRAPS)
    for i in range(BOOTSTRAPS):
        index = rng.integers(0, len(difference), len(difference))
        values[i] = np.median(difference[index])
    return {"difference": float(np.median(difference)), "lower_95": float(np.quantile(values, 0.025)), "median": float(np.median(values))}


def replay_scores(events: list[tuple[float, float]], units: list[np.ndarray], rates: np.ndarray, prior: np.ndarray) -> dict[str, Any]:
    rng = np.random.Generator(np.random.PCG64(SEED))
    actual_order, actual_distance, actual_jump = [], [], []
    time_order, time_distance, cell_order, cell_distance = [], [], [], []
    significant = []
    eligible = 0
    for start, stop in events:
        starts = np.arange(start, stop - 0.019999, 0.02)
        if len(starts) < 4:
            continue
        counts = bin_counts(units, starts, starts + 0.02)
        if np.sum(counts.sum(axis=0) > 0) < 5:
            continue
        path, _ = decode(counts, rates, prior, 0.02)
        order, distance, jump = score_path(path)
        t_order = np.empty(SHUFFLES)
        t_distance = np.empty(SHUFFLES)
        c_order = np.empty(SHUFFLES)
        c_distance = np.empty(SHUFFLES)
        for shuffle in range(SHUFFLES):
            shuffled_path = path[rng.permutation(len(path))]
            t_order[shuffle], t_distance[shuffle], _ = score_path(shuffled_path)
            cell_path, _ = decode(counts, rates[rng.permutation(len(units))], prior, 0.02)
            c_order[shuffle], c_distance[shuffle], _ = score_path(cell_path)
        actual_order.append(order)
        actual_distance.append(distance)
        actual_jump.append(jump)
        time_order.append(float(np.median(t_order)))
        time_distance.append(float(np.median(t_distance)))
        cell_order.append(float(np.median(c_order)))
        cell_distance.append(float(np.median(c_distance)))
        significant.append(bool(order > np.quantile(t_order, 0.95) and order > np.quantile(c_order, 0.95)))
        eligible += 1
    if eligible < 20:
        return {"eligible_events": eligible, "coverage_stop": True}
    ao, ad = np.asarray(actual_order), np.asarray(actual_distance)
    to, td = np.asarray(time_order), np.asarray(time_distance)
    co, cd = np.asarray(cell_order), np.asarray(cell_distance)
    fraction = float(np.mean(significant))
    pvalue = float(binomtest(sum(significant), eligible, 0.05, alternative="greater").pvalue)
    return {
        "eligible_events": eligible,
        "coverage_stop": False,
        "median_scores": {"actual_order": float(np.median(ao)), "time_order": float(np.median(to)), "cell_order": float(np.median(co)), "actual_distance": float(np.median(ad)), "time_distance": float(np.median(td)), "cell_distance": float(np.median(cd)), "actual_jump": float(np.median(actual_jump))},
        "comparisons": {"order_vs_time": bootstrap_difference(ao, to, 1), "order_vs_cell": bootstrap_difference(ao, co, 2), "distance_vs_time": bootstrap_difference(ad, td, 3), "distance_vs_cell": bootstrap_difference(ad, cd, 4)},
        "double_significant_events": int(sum(significant)),
        "double_significant_fraction": fraction,
        "binomial_p": pvalue,
    }


def decide(encoding: dict[str, float], replay: dict[str, Any]) -> str:
    encoding_pass = encoding["median_absolute_error"] <= 0.15 and encoding["improvement"] >= 0.20
    if not encoding_pass:
        return "TRAJECTORY_MEMORY_NOT_ESTABLISHED"
    if replay.get("coverage_stop"):
        return "STAGE7_REPLAY_COVERAGE_STOP"
    comparisons = replay["comparisons"]
    order_time, order_cell = comparisons["order_vs_time"], comparisons["order_vs_cell"]
    distance_time, distance_cell = comparisons["distance_vs_time"], comparisons["distance_vs_cell"]
    passed = (
        order_time["difference"] >= 0.10 and order_cell["difference"] >= 0.10
        and order_time["lower_95"] > 0 and order_cell["lower_95"] > 0
        and distance_time["lower_95"] > 0 and distance_cell["lower_95"] > 0
        and replay["double_significant_fraction"] >= 0.10 and replay["binomial_p"] < 0.01
    )
    return "DEVELOPMENT_MEMORY_TRAJECTORY_SUPPORTED" if passed else "ENCODING_TRAJECTORY_ONLY_REPLAY_NOT_ESTABLISHED"


def analyze() -> dict[str, Any]:
    trace = position_trace()
    traversals = detect_traversals(trace["position"], trace["valid"])
    split = split_traversals(traversals)
    units, identities = load_units()
    rates, prior = place_fields(trace, units, split["train"])
    encoding = encoding_receipt(trace, units, rates, prior, split["test"])
    events, ripple = ripple_events(trace)
    replay = replay_scores(events, units, rates, prior)
    result = {
        "claim_ceiling": "single familiar-track development session; observational ripple decoding",
        "coverage": {"traversals": len(traversals), "train_traversals": len(split["train"]), "validation_traversals": len(split["validation"]), "test_traversals": len(split["test"]), "ca1_pyramidal_units": len(units), "first_unit": list(identities[0]), "last_unit": list(identities[-1]), "detected_ripples": len(events)},
        "encoding": encoding,
        "ripple_detection": ripple,
        "replay": replay,
        "shuffle": {"repetitions": SHUFFLES, "seed": SEED},
        "bootstrap": {"repetitions": BOOTSTRAPS, "seed": SEED},
    }
    result["decision"] = decide(encoding, replay)
    return result


def runtime() -> dict[str, str]:
    return {"executable": sys.executable, "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}


def files() -> tuple[Path, ...]:
    paths = [Path(__file__).resolve(), TEST_FILE, CONTRACT, APPARATUS_CODE, APPARATUS, DB, Path(f"{PREFIX}.xml"), Path(f"{PREFIX}.whl")]
    for electrode in range(1, 9):
        paths.extend((Path(f"{PREFIX}.clu.{electrode}"), Path(f"{PREFIX}.res.{electrode}")))
    return tuple(paths)


def seal(artifact: Path) -> dict[str, Any]:
    apparatus = json.loads(APPARATUS.read_text(encoding="utf-8"))
    if apparatus.get("decision") != "STAGE7_HC3_APPARATUS_ELIGIBLE" or digest(ARCHIVE, "md5") != "32517ed8114e1b930df7925da6f2bb68":
        raise RuntimeError(f"{STOP}: apparatus")
    manifest = {"files": {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in files()}, "archive_md5": digest(ARCHIVE, "md5"), "eeg_sha256": digest(Path(f"{PREFIX}.eeg")), "runtime": runtime(), "scores_opened": False}
    manifest["manifest_sha256"] = write_once(artifact / MANIFEST, manifest)
    return manifest


def verify_manifest(artifact: Path) -> str:
    path = artifact / MANIFEST
    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected_files = {str(item.relative_to(ROOT)).replace("\\", "/"): digest(item) for item in files()}
    if manifest.get("files") != expected_files or manifest.get("archive_md5") != digest(ARCHIVE, "md5") or manifest.get("eeg_sha256") != digest(Path(f"{PREFIX}.eeg")) or manifest.get("runtime") != runtime() or manifest.get("scores_opened") is not False:
        raise RuntimeError(f"{STOP}: manifest mutation")
    return digest(path)


def execute(artifact: Path) -> dict[str, Any]:
    manifest_hash = verify_manifest(artifact)
    result = analyze()
    result["manifest_sha256"] = manifest_hash
    result_hash = write_once(artifact / RESULT, result)
    return {"result_sha256": result_hash, **result}


def verify_result(artifact: Path) -> dict[str, Any]:
    stored_path = artifact / RESULT
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    fresh = analyze()
    fresh["manifest_sha256"] = verify_manifest(artifact)
    if canonical_bytes(stored) != canonical_bytes(fresh):
        raise RuntimeError(f"{STOP}: raw recomputation mismatch")
    receipt = {"status": "PASS", "raw_recomputed": True, "decision": stored["decision"], "result_sha256": digest(stored_path)}
    receipt["validation_receipt_sha256"] = write_once(artifact / VALIDATION, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--seal", action="store_true")
    group.add_argument("--execute", action="store_true")
    group.add_argument("--verify-result", action="store_true")
    args = parser.parse_args()
    output = seal(args.artifact_dir) if args.seal else execute(args.artifact_dir) if args.execute else verify_result(args.artifact_dir)
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

