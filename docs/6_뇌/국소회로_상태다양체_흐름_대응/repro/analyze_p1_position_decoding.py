"""P1 apparatus sanity: movement position decoding from the frozen 001701 asset.

This script implements exactly the P1 item pre-registered in
``13_실패한_계약의_분해와_후속_사전등록.md``.  It reuses chapter 11's observation
chain (100 ms counts, Anscombe transform, train-block standardisation, 0.1 Hz
train-prefix unit selection, half/quarter/quarter split) and asks a single
question: can that chain decode position during movement?

Endpoint: median Euclidean test error, in centimetres, over movement bins.
Pass requires BOTH (a) error <= 0.7 * constant-baseline error and (b) error <
circularly shifted control error.  Region-restricted vectors are reported as
secondary indicators without thresholds.

Only aggregate JSON is written.  The NWB file is verified against the frozen
receipt and never persisted inside the repository.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import h5py
import numpy as np
import requests

DANDISET = "001701"
VERSION = "0.260120.0303"
ASSET_ID = "3f3d0b16-9b3e-42ac-a5e6-327829df1116"
EXPECTED_SIZE = 12_967_760
EXPECTED_SHA256 = "5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3"

BIN_SECONDS = 0.1
MIN_TRAIN_RATE_HZ = 0.1
SPEED_SMOOTH_SECONDS = 0.42
MOVEMENT_THRESHOLDS_CM_S = (2.0, 5.0)
RIDGES = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0)
CONTROL_SHIFT_SECONDS = 300.0
PASS_BASELINE_RATIO = 0.7

HERE = Path(__file__).resolve().parent


def text(value) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def jsonable(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def resolve_asset() -> tuple[Path, dict, bool]:
    cached = os.environ.get("CE_DANDI_001701_CACHE")
    if cached:
        path = Path(cached)
        if path.exists() and path.stat().st_size == EXPECTED_SIZE:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest == EXPECTED_SHA256:
                return path, {"source": "verified_cache", "sha256": digest, "bytes": path.stat().st_size}, False
    api = f"https://api.dandiarchive.org/api/dandisets/{DANDISET}/versions/{VERSION}/assets/{ASSET_ID}/"
    meta = requests.get(api, timeout=60)
    meta.raise_for_status()
    url = meta.json()["contentUrl"][0]
    handle, name = tempfile.mkstemp(suffix=".nwb")
    os.close(handle)
    path = Path(name)
    digest = hashlib.sha256()
    received = 0
    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with path.open("wb") as sink:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    sink.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
    actual = digest.hexdigest()
    if received != EXPECTED_SIZE or actual != EXPECTED_SHA256:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"receipt mismatch: bytes={received}, sha256={actual}")
    return path, {"source": "download", "sha256": actual, "bytes": received, "asset_api": api}, True


def boxcar(values: np.ndarray, width: int) -> np.ndarray:
    kernel = np.ones(width) / width
    padded = np.pad(values, width, mode="edge")
    return np.convolve(padded, kernel, mode="same")[width:-width]


def ridge_fit(x: np.ndarray, y: np.ndarray, lam: float) -> tuple[np.ndarray, np.ndarray]:
    x_mean, y_mean = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - x_mean, y - y_mean
    gram = xc.T @ xc + lam * np.eye(x.shape[1])
    coefficient = np.linalg.solve(gram, xc.T @ yc)
    return coefficient, y_mean - x_mean @ coefficient


def median_error(truth: np.ndarray, estimate: np.ndarray) -> float:
    return float(np.median(np.linalg.norm(truth - estimate, axis=1)))


def decode(features: np.ndarray, target: np.ndarray, train: np.ndarray, dev: np.ndarray, test: np.ndarray) -> dict:
    scores = {}
    for lam in RIDGES:
        coefficient, intercept = ridge_fit(features[train], target[train], lam)
        scores[lam] = median_error(target[dev], features[dev] @ coefficient + intercept)
    best = min(scores, key=scores.get)
    coefficient, intercept = ridge_fit(features[train], target[train], best)
    constant = np.median(target[train], axis=0)
    return {
        "lambda": best,
        "development_median_error_cm": scores[best],
        "test_median_error_cm": median_error(target[test], features[test] @ coefficient + intercept),
        "baseline_median_error_cm": median_error(target[test], np.broadcast_to(constant, target[test].shape)),
        "n_train": int(train.size),
        "n_development": int(dev.size),
        "n_test": int(test.size),
    }


def main() -> None:
    path, receipt, temporary = resolve_asset()
    try:
        with h5py.File(path, "r") as nwb:
            locations = np.array([text(v) for v in nwb["general/extracellular_ephys/electrodes/location"][:]])
            units = nwb["units"]
            spike_times = units["spike_times"][:]
            spike_index = units["spike_times_index"][:]
            unit_location = locations[units["electrodes"][:]]

            series = nwb["processing/behavior/Position/position"]
            hz = float(series["starting_time"].attrs["rate"])
            t0 = float(series["starting_time"][()])
            raw = series["data"][:]

        n_samples = raw.shape[0]
        sample_time = t0 + np.arange(n_samples) / hz
        gap = ~np.isfinite(raw).all(axis=1)
        filled = raw.copy()
        index = np.arange(n_samples)
        for column in range(2):
            good = np.isfinite(filled[:, column])
            filled[:, column] = np.interp(index, index[good], filled[good, column])
        step = np.linalg.norm(np.diff(filled, axis=0), axis=1) * hz
        speed = boxcar(np.concatenate(([step[0]], step)), int(round(SPEED_SMOOTH_SECONDS * hz)))

        start = max(sample_time[0], float(spike_times.min()))
        stop = min(sample_time[-1], float(spike_times.max()))
        n_bins = int(np.floor((stop - start) / BIN_SECONDS))
        edges = start + BIN_SECONDS * np.arange(n_bins + 1)

        starts = np.concatenate(([0], spike_index[:-1]))
        counts = np.empty((n_bins, spike_index.size), dtype=np.float64)
        for unit, (a, b) in enumerate(zip(starts, spike_index)):
            counts[:, unit] = np.histogram(spike_times[a:b], bins=edges)[0]

        which = np.clip(((sample_time - start) / BIN_SECONDS).astype(np.int64), -1, n_bins)
        inside = (which >= 0) & (which < n_bins)
        position = np.full((n_bins, 2), np.nan)
        bin_speed = np.full(n_bins, np.nan)
        bin_gap = np.zeros(n_bins, dtype=bool)
        totals = np.bincount(which[inside], minlength=n_bins).astype(np.float64)
        for column in range(2):
            position[:, column] = np.bincount(which[inside], weights=filled[inside, column], minlength=n_bins) / np.maximum(totals, 1)
        bin_speed = np.bincount(which[inside], weights=speed[inside], minlength=n_bins) / np.maximum(totals, 1)
        bin_gap = np.bincount(which[inside], weights=gap[inside].astype(float), minlength=n_bins) > 0
        usable = (totals > 0) & ~bin_gap

        train_end, dev_end = n_bins // 2, (3 * n_bins) // 4
        train_block = np.arange(0, train_end)
        prefix_rate = counts[train_block].sum(axis=0) / (train_block.size * BIN_SECONDS)
        retained = prefix_rate >= MIN_TRAIN_RATE_HZ

        anscombe = np.sqrt(counts + 0.375)
        mean = anscombe[train_block].mean(axis=0)
        scale = anscombe[train_block].std(axis=0)
        scale[scale == 0] = 1.0
        features_all = (anscombe - mean) / scale

        shift_bins = int(round(CONTROL_SHIFT_SECONDS / BIN_SECONDS))
        shifted_position = np.roll(position, shift_bins, axis=0)
        shifted_speed = np.roll(bin_speed, shift_bins)
        shifted_usable = np.roll(usable, shift_bins)

        groups = {
            "all_retained": retained,
            "mec_only": retained & (unit_location == "Entorhinal area medial part dorsal zone"),
            "visual_only": retained & np.isin(unit_location, ["Posterolateral visual area", "Primary visual area"]),
        }

        report: dict = {
            "item": "P1",
            "window_seconds": [start, stop],
            "n_bins": n_bins,
            "bin_seconds": BIN_SECONDS,
            "blocks": {"train": [0, train_end], "development": [train_end, dev_end], "test": [dev_end, n_bins]},
            "usable_bins": int(usable.sum()),
            "unit_counts": {name: int(mask.sum()) for name, mask in groups.items()},
            "control_shift_seconds": CONTROL_SHIFT_SECONDS,
            "thresholds": {"pass_baseline_ratio": PASS_BASELINE_RATIO},
            "results": {},
        }

        for threshold in MOVEMENT_THRESHOLDS_CM_S:
            moving = usable & (bin_speed > threshold)
            shifted_moving = shifted_usable & (shifted_speed > threshold)
            per_threshold: dict = {"moving_bins": int(moving.sum()), "moving_fraction_of_usable": float(moving.sum() / usable.sum())}
            for name, mask in groups.items():
                features = features_all[:, mask]
                split = [np.flatnonzero(moving[lo:hi]) + lo for lo, hi in ((0, train_end), (train_end, dev_end), (dev_end, n_bins))]
                per_threshold[name] = decode(features, position, *split)
                shifted_split = [np.flatnonzero(shifted_moving[lo:hi]) + lo for lo, hi in ((0, train_end), (train_end, dev_end), (dev_end, n_bins))]
                per_threshold[name]["shifted_control"] = decode(features, shifted_position, *shifted_split)
            primary = per_threshold["all_retained"]
            ratio = primary["test_median_error_cm"] / primary["baseline_median_error_cm"]
            per_threshold["primary_ratio_to_baseline"] = ratio
            per_threshold["passes_baseline_condition"] = bool(ratio <= PASS_BASELINE_RATIO)
            per_threshold["passes_shift_condition"] = bool(primary["test_median_error_cm"] < primary["shifted_control"]["test_median_error_cm"])
            per_threshold["status"] = "PASS" if per_threshold["passes_baseline_condition"] and per_threshold["passes_shift_condition"] else "FAIL"
            report["results"][f"speed_gt_{threshold:g}"] = per_threshold

        report["status"] = report["results"][f"speed_gt_{MOVEMENT_THRESHOLDS_CM_S[0]:g}"]["status"]
        report["claim_ceiling"] = "Apparatus check only; no biological, manifold, metric, or causal claim."
        report["source_receipt"] = receipt
        (HERE / "p1-result.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
        print(json.dumps(jsonable(report), indent=2))
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
