"""Development analysis: reduced-rank fibre skew products on the consumed asset.

DEVELOPMENT ONLY.  This script runs on the DANDI 001701 asset that chapters 11
and 12 already opened and scored.  Nothing here is a confirmation, and no
threshold reported by this script may be read as a result about the recording
family.  Its purpose is to measure what a rank-restricted fibre does to the two
things chapter 11 required at once -- held-out superiority and a contraction
certificate -- so that a successor contract can be written with thresholds that
are known to be reachable.

Window, split, unit retention, transform, basis and NMSE denominator reproduce
chapter 11 exactly, so every number is comparable with chapter 12's.

For each latent dimension d, ridge lambda and fibre rank r it reports:

  test/development NMSE            against chapter 11's denominator
  q     = ||A_r||_2                chapter 11's Euclidean contraction check
  rho   = spectral radius of A_r   the coordinate-free stability quantity
  ||A_r||_P                        the Lyapunov-metric norm of lemma 13.1
  kappa = ||B^-1||_2, q*kappa      chapter 11's bunching check
  invariant residual               chapter 11's secondary graph residual
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
MIN_TRAIN_RATE_HZ = 0.1
LATENT_DIMENSIONS = (2, 4, 8, 16, 32)
RIDGES = (1e-2, 1e-1, 1.0, 10.0, 1e2, 1e3, 1e4)
RANKS = (0, 2, 4, 8, 12, 16, 24, 32, 48, 64)
LYAPUNOV_STEPS = 40
LYAPUNOV_TOLERANCE = 1e-10

HERE = Path(__file__).resolve().parent


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


def lyapunov_norm(a: np.ndarray) -> tuple[float, bool]:
    """Return ||A||_P for the Lyapunov metric of lemma 13.1, and whether it converged.

    Solves A^T P A - P = -I by the doubling iteration P <- P + A^T P A,
    A <- A^2, which converges quadratically when the spectral radius is below
    one.  Returns infinity when the iteration diverges.
    """
    size = a.shape[0]
    p = np.eye(size)
    power = a.copy()
    for _ in range(LYAPUNOV_STEPS):
        increment = power.T @ p @ power
        p = p + increment
        if not np.all(np.isfinite(p)):
            return math.inf, False
        if np.linalg.norm(increment, 2) < LYAPUNOV_TOLERANCE * np.linalg.norm(p, 2):
            eigenvalues = np.linalg.eigvalsh(p)
            if eigenvalues.min() <= 0:
                return math.inf, False
            factor = np.linalg.cholesky(p)
            return float(np.linalg.norm(factor.T @ a @ np.linalg.inv(factor.T), 2)), True
        power = power @ power
        if not np.all(np.isfinite(power)):
            return math.inf, False
    return math.inf, False


def main() -> None:
    path, receipt, temporary = resolve_asset()
    try:
        with h5py.File(path, "r") as nwb:
            lfp = nwb["processing/probe_0_channel_160/LFP/LFP"]
            rate = float(lfp["starting_time"].attrs["rate"])
            start = float(lfp["starting_time"][()])
            stop = start + lfp["data"].shape[0] / rate
            units = nwb["units"]
            spike_times = units["spike_times"][:]
            spike_index = units["spike_times_index"][:]

        n_bins = int(math.floor((stop - start) / BIN_SECONDS))
        train_end, dev_end = int(math.floor(0.5 * n_bins)), int(math.floor(0.75 * n_bins))
        train_boundary = start + train_end * BIN_SECONDS
        edges = start + BIN_SECONDS * np.arange(n_bins + 1)
        starts = np.concatenate(([0], spike_index[:-1]))
        counts = np.empty((n_bins, spike_index.size))
        prefix = np.empty(spike_index.size)
        for unit, (a, b) in enumerate(zip(starts, spike_index)):
            times = spike_times[a:b]
            counts[:, unit] = np.histogram(times, bins=edges)[0]
            prefix[unit] = np.searchsorted(times, train_boundary)
        retained = (prefix / (train_boundary - start)) >= MIN_TRAIN_RATE_HZ
        counts = counts[:, retained]

        transformed = np.sqrt(counts + 0.375)
        mean = transformed[:train_end].mean(axis=0)
        scale = transformed[:train_end].std(axis=0)
        scale[scale == 0] = 1.0
        state = (transformed - mean) / scale

        train = np.arange(0, train_end - 1)
        dev = np.arange(train_end, dev_end - 1)
        test = np.arange(dev_end, n_bins - 1)
        _, _, vt = np.linalg.svd(state[:train_end], full_matrices=False)
        basis = vt.T
        train_bin_mean = state[:train_end].mean(axis=0)
        denominator = float(np.square(state[test + 1] - train_bin_mean).sum())

        full_var = {}
        for lam in RIDGES:
            coefficient, intercept = ridge(state[train], state[train + 1], lam)
            full_var[lam] = {
                "development_nmse": float(np.square(state[dev + 1] - (state[dev] @ coefficient + intercept)).sum() / denominator),
                "test_nmse": float(np.square(state[test + 1] - (state[test] @ coefficient + intercept)).sum() / denominator),
            }
        best_full_lambda = min(RIDGES, key=lambda lam: full_var[lam]["development_nmse"])

        entries = []
        for d in LATENT_DIMENSIONS:
            z, y = state @ basis[:, :d], state @ basis[:, d:]
            base_map, fibre_map = basis[:, :d].T, basis[:, d:].T
            n_fibre = y.shape[1]
            for lam in RIDGES:
                b_matrix, b_intercept = ridge(z[train], z[train + 1], lam)
                fibre_coefficient, fibre_intercept = ridge(np.c_[y[train], z[train]], y[train + 1], lam)
                a_full, c_block = fibre_coefficient[:n_fibre], fibre_coefficient[n_fibre:]
                _, _, fibre_vt = np.linalg.svd(y[train] @ a_full, full_matrices=False)
                try:
                    kappa = float(np.linalg.norm(np.linalg.inv(b_matrix), 2))
                except np.linalg.LinAlgError:
                    kappa = math.inf
                for rank in RANKS:
                    if rank > min(a_full.shape):
                        continue
                    if rank == 0:
                        a_rank = np.zeros_like(a_full)
                    elif rank >= min(a_full.shape):
                        a_rank = a_full
                    else:
                        projector = fibre_vt[:rank].T @ fibre_vt[:rank]
                        a_rank = a_full @ projector
                    packed = np.vstack((a_rank, c_block))
                    scores = {}
                    for name, rows in (("development", dev), ("test", test)):
                        next_z = z[rows] @ b_matrix + b_intercept
                        next_y = np.c_[y[rows], z[rows]] @ packed + fibre_intercept
                        scores[name] = float(np.square(state[rows + 1] - (next_z @ base_map + next_y @ fibre_map)).sum() / denominator)
                    q = float(np.linalg.norm(a_rank, 2))
                    rho = float(np.max(np.abs(np.linalg.eigvals(a_rank)))) if rank > 0 else 0.0
                    norm_p, converged = (0.0, True) if rank == 0 else lyapunov_norm(a_rank)
                    entries.append({
                        "d": d,
                        "lambda": lam,
                        "rank": rank,
                        "parameters": d * d + d + 2 * n_fibre * rank + d * n_fibre + n_fibre,
                        "development_nmse": scores["development"],
                        "test_nmse": scores["test"],
                        "q": q,
                        "rho": rho,
                        "norm_p": norm_p,
                        "lyapunov_converged": bool(converged),
                        "kappa": kappa,
                        "q_kappa": q * kappa,
                    })
            print(f"d={d} done, entries={len(entries)}", flush=True)

        selected = min(entries, key=lambda item: item["development_nmse"])
        report = {
            "track": "DEVELOPMENT_ONLY",
            "asset": "sub-BaggySweatpants/sub-BaggySweatpants_ses-BaggySweatpants-DY15-g1_behavior+ecephys.nwb",
            "n_bins": int(n_bins),
            "retained_units": int(retained.sum()),
            "rows": {"train": int(train.size), "development": int(dev.size), "test": int(test.size)},
            "nmse_denominator": denominator,
            "full_var": {"selected_lambda": best_full_lambda, **full_var[best_full_lambda], "grid": full_var},
            "development_selected": selected,
            "entries": entries,
            "claim_ceiling": "Development measurement on a consumed asset; not a result about the recording family.",
            "source_receipt": receipt,
        }
        (HERE / "development-reduced-rank.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
        print(json.dumps(jsonable({"full_var": report["full_var"]["test_nmse"], "selected": selected}), indent=2))
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
