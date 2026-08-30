"""P3 coordinates and coupling: does the fibre help predict the base?

Implements the P3 item pre-registered in
``13_실패한_계약의_분해와_후속_사전등록.md``.  Chapter 11's candidate assumes a
skew product, that is the base evolves on its own::

    M0:  z' = B z + d          y' = A_r y + C z + e

P3 opens the one coupling that assumption forbids::

    M1:  z' = B z + L y + d    y' = A_r y + C z + e

The two models share the fibre equation exactly, so the comparison isolates the
single question of whether the fibre carries information about the next base
state.  ``L`` costs 8 x 287 = 2296 coefficients, which equals the cost of four
extra ranks in the fibre autoregression (574 per rank), so the budget-matched
pair is M1 at rank r against M0 at rank r+4.

A delayed variant with p lags of the base and fibre is reported separately.
Window, split, unit retention, transform, basis and NMSE denominator reproduce
chapter 11 exactly, so the numbers here are comparable with chapter 12's.
"""

from __future__ import annotations

import hashlib
import json
import math
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
LATENT_DIMENSION = 8
MIN_TRAIN_RATE_HZ = 0.1
RIDGES = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0)
RANKS = (0, 2, 4, 8, 16, 32, 64)
RANK_OFFSET = 4
LAGS = (1, 2, 3)
BLOCK = 100
BOOTSTRAPS = 2000
SEED = 1701

HERE = Path(__file__).resolve().parent
MEC = "Entorhinal area medial part dorsal zone"


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


def ridge(x: np.ndarray, y: np.ndarray, lam: float) -> tuple[np.ndarray, np.ndarray]:
    x_mean, y_mean = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - x_mean, y - y_mean
    coefficient = np.linalg.solve(xc.T @ xc + lam * np.eye(x.shape[1]), xc.T @ yc)
    return coefficient, y_mean - x_mean @ coefficient


def reduced_rank(fitted: np.ndarray, coefficient: np.ndarray, rank: int) -> np.ndarray:
    """Classic reduced-rank projection of a fitted coefficient matrix."""
    if rank <= 0:
        return np.zeros_like(coefficient)
    if rank >= min(coefficient.shape):
        return coefficient
    _, _, vt = np.linalg.svd(fitted, full_matrices=False)
    projector = vt[:rank].T @ vt[:rank]
    return coefficient @ projector


def block_bootstrap(difference: np.ndarray, rng: np.random.Generator) -> list[float]:
    n_blocks = max(difference.size // BLOCK, 2)
    means = difference[: n_blocks * BLOCK].reshape(n_blocks, BLOCK).mean(axis=1)
    draws = means[rng.integers(0, n_blocks, size=(BOOTSTRAPS, n_blocks))].mean(axis=1)
    return [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]


def evaluate(state: np.ndarray, label: str, rng: np.random.Generator) -> dict:
    n_bins, n_units = state.shape
    train_end, dev_end = int(math.floor(0.5 * n_bins)), int(math.floor(0.75 * n_bins))
    train = np.arange(0, train_end - 1)
    dev = np.arange(train_end, dev_end - 1)
    test = np.arange(dev_end, n_bins - 1)

    _, _, vt = np.linalg.svd(state[:train_end], full_matrices=False)
    basis = vt.T
    d = LATENT_DIMENSION
    z, y = state @ basis[:, :d], state @ basis[:, d:]
    base_map, fibre_map = basis[:, :d].T, basis[:, d:].T

    train_bin_mean = state[:train_end].mean(axis=0)
    denominator = float(np.square(state[test + 1] - train_bin_mean).sum())

    def rows_error(rows: np.ndarray, next_z: np.ndarray, next_y: np.ndarray) -> np.ndarray:
        estimate = next_z @ base_map + next_y @ fibre_map
        return np.square(state[rows + 1] - estimate).sum(axis=1)

    fits: dict[tuple[str, int, float], dict] = {}
    for lam in RIDGES:
        b, b0 = ridge(z[train], z[train + 1], lam)
        bl, bl0 = ridge(np.c_[z[train], y[train]], z[train + 1], lam)
        fibre_coefficient, fibre_intercept = ridge(np.c_[y[train], z[train]], y[train + 1], lam)
        a_full, c_block = fibre_coefficient[: y.shape[1]], fibre_coefficient[y.shape[1] :]
        residual_fit = y[train] @ a_full
        for rank in RANKS:
            a_rank = reduced_rank(residual_fit, a_full, rank)
            packed = np.vstack((a_rank, c_block))
            for name, next_z_of in (
                ("skew", lambda rows: z[rows] @ b + b0),
                ("feedback", lambda rows: np.c_[z[rows], y[rows]] @ bl + bl0),
            ):
                errors = {}
                for split_name, rows in (("development", dev), ("test", test)):
                    next_y = np.c_[y[rows], z[rows]] @ packed + fibre_intercept
                    errors[split_name] = rows_error(rows, next_z_of(rows), next_y)
                parameters = d * d + d + 574 * rank + d * y.shape[1] + y.shape[1]
                if name == "feedback":
                    parameters += d * y.shape[1]
                fits[(name, rank, lam)] = {
                    "development_nmse": float(errors["development"].sum() / denominator),
                    "test_errors": errors["test"],
                    "parameters": parameters,
                }

    def select(name: str, rank: int) -> tuple[float, dict]:
        best = min(RIDGES, key=lambda lam: fits[(name, rank, lam)]["development_nmse"])
        return best, fits[(name, rank, best)]

    grid = []
    for rank in RANKS:
        for name in ("skew", "feedback"):
            lam, fit = select(name, rank)
            grid.append({
                "model": name,
                "rank": rank,
                "lambda": lam,
                "parameters": fit["parameters"],
                "development_nmse": fit["development_nmse"],
                "test_nmse": float(fit["test_errors"].sum() / denominator),
            })

    chosen_rank = min(RANKS, key=lambda rank: select("feedback", rank)[1]["development_nmse"])
    matched_rank = chosen_rank + RANK_OFFSET
    if matched_rank not in RANKS:
        matched_lam, matched_fit = None, None
        for lam in RIDGES:
            b, b0 = ridge(z[train], z[train + 1], lam)
            fibre_coefficient, fibre_intercept = ridge(np.c_[y[train], z[train]], y[train + 1], lam)
            a_full, c_block = fibre_coefficient[: y.shape[1]], fibre_coefficient[y.shape[1] :]
            a_rank = reduced_rank(y[train] @ a_full, a_full, matched_rank)
            packed = np.vstack((a_rank, c_block))
            errors = {}
            for split_name, rows in (("development", dev), ("test", test)):
                errors[split_name] = rows_error(rows, z[rows] @ b + b0, np.c_[y[rows], z[rows]] @ packed + fibre_intercept)
            score = float(errors["development"].sum() / denominator)
            if matched_fit is None or score < matched_fit["development_nmse"]:
                matched_lam = lam
                matched_fit = {
                    "development_nmse": score,
                    "test_errors": errors["test"],
                    "parameters": d * d + d + 574 * matched_rank + d * y.shape[1] + y.shape[1],
                }
    else:
        matched_lam, matched_fit = select("skew", matched_rank)

    feedback_lam, feedback_fit = select("feedback", chosen_rank)
    difference = (matched_fit["test_errors"] - feedback_fit["test_errors"]) / denominator * test.size
    interval = block_bootstrap(difference, rng)
    improvement = float(matched_fit["test_errors"].sum() / denominator) - float(feedback_fit["test_errors"].sum() / denominator)

    delay = []
    for lag in LAGS:
        rows_offset = lag - 1
        train_l = train[train >= rows_offset]
        dev_l = dev[dev >= rows_offset]
        test_l = test[test >= rows_offset]
        history_z = np.concatenate([z[rows_offset:] if k == 0 else z[rows_offset - k : -k] for k in range(lag)], axis=1)
        history_y = np.concatenate([y[rows_offset:] if k == 0 else y[rows_offset - k : -k] for k in range(lag)], axis=1)
        shift = rows_offset
        best_score, best_entry = math.inf, None
        for lam in RIDGES:
            bz, bz0 = ridge(history_z[train_l - shift], z[train_l + 1], lam)
            by, by0 = ridge(np.c_[history_y[train_l - shift], history_z[train_l - shift]], y[train_l + 1], lam)
            score_rows = {}
            for split_name, rows in (("development", dev_l), ("test", test_l)):
                next_z = history_z[rows - shift] @ bz + bz0
                next_y = np.c_[history_y[rows - shift], history_z[rows - shift]] @ by + by0
                score_rows[split_name] = np.square(state[rows + 1] - (next_z @ base_map + next_y @ fibre_map)).sum(axis=1)
            score = float(score_rows["development"].sum() / denominator)
            if score < best_score:
                best_score = score
                best_entry = {
                    "lag": lag,
                    "lambda": lam,
                    "development_nmse": score,
                    "test_nmse": float(score_rows["test"].sum() / denominator),
                    "test_rows": int(test_l.size),
                    "parameters": lag * d * d + d + lag * y.shape[1] * y.shape[1] + lag * d * y.shape[1] + y.shape[1],
                }
        delay.append(best_entry)

    return {
        "label": label,
        "n_units": int(n_units),
        "n_bins": int(n_bins),
        "rows": {"train": int(train.size), "development": int(dev.size), "test": int(test.size)},
        "nmse_denominator": denominator,
        "grid": grid,
        "budget_matched": {
            "feedback": {"rank": chosen_rank, "lambda": feedback_lam, "parameters": feedback_fit["parameters"], "test_nmse": float(feedback_fit["test_errors"].sum() / denominator)},
            "skew": {"rank": matched_rank, "lambda": matched_lam, "parameters": matched_fit["parameters"], "test_nmse": float(matched_fit["test_errors"].sum() / denominator)},
            "improvement_nmse": improvement,
            "bootstrap_ci95": interval,
            "status": "PASS" if improvement > 0 and interval[0] > 0 else "FAIL",
        },
        "delay": delay,
    }


def main() -> None:
    path, receipt, temporary = resolve_asset()
    rng = np.random.default_rng(SEED)
    try:
        with h5py.File(path, "r") as nwb:
            lfp = nwb["processing/probe_0_channel_160/LFP/LFP"]
            rate = float(lfp["starting_time"].attrs["rate"])
            start = float(lfp["starting_time"][()])
            stop = start + lfp["data"].shape[0] / rate
            units = nwb["units"]
            spike_times = units["spike_times"][:]
            spike_index = units["spike_times_index"][:]
            locations = np.array([v.decode() if isinstance(v, bytes) else str(v) for v in nwb["general/extracellular_ephys/electrodes/location"][:]])
            unit_location = locations[units["electrodes"][:]]

        n_bins = int(math.floor((stop - start) / BIN_SECONDS))
        train_boundary = start + math.floor(0.5 * n_bins) * BIN_SECONDS
        edges = start + BIN_SECONDS * np.arange(n_bins + 1)
        starts = np.concatenate(([0], spike_index[:-1]))
        counts = np.empty((n_bins, spike_index.size))
        prefix = np.empty(spike_index.size)
        for unit, (a, b) in enumerate(zip(starts, spike_index)):
            times = spike_times[a:b]
            counts[:, unit] = np.histogram(times, bins=edges)[0]
            prefix[unit] = np.searchsorted(times, train_boundary)
        retained = (prefix / (train_boundary - start)) >= MIN_TRAIN_RATE_HZ

        report = {
            "item": "P3",
            "window_seconds": [start, stop],
            "n_bins": n_bins,
            "retained_units": int(retained.sum()),
            "rank_offset": RANK_OFFSET,
            "results": {},
        }
        for label, mask in (("all_retained", retained), ("mec_only", retained & (unit_location == MEC))):
            selected = counts[:, mask]
            train_end = int(math.floor(0.5 * n_bins))
            transformed = np.sqrt(selected + 0.375)
            mean = transformed[:train_end].mean(axis=0)
            scale = transformed[:train_end].std(axis=0)
            scale[scale == 0] = 1.0
            report["results"][label] = evaluate((transformed - mean) / scale, label, rng)
            summary = report["results"][label]["budget_matched"]
            print(f"{label}: feedback rank={summary['feedback']['rank']} nmse={summary['feedback']['test_nmse']:.7f} vs skew rank={summary['skew']['rank']} nmse={summary['skew']['test_nmse']:.7f} -> {summary['status']}", flush=True)

        report["status"] = report["results"]["all_retained"]["budget_matched"]["status"]
        report["claim_ceiling"] = "Coordinate/coupling comparison only; no biological, manifold, metric, or causal claim."
        report["source_receipt"] = receipt
        (HERE / "p3-result.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
