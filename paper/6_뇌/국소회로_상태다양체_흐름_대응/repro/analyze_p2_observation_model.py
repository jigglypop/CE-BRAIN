"""P2 observation model: point-process versus Anscombe-Gauss on the same features.

Implements the P2 item pre-registered in
``13_실패한_계약의_분해와_후속_사전등록.md``.  All three models share one design
matrix -- the intercept plus the top eight train-block principal components of
the standardised Anscombe counts at time ``t`` -- and predict the counts at
``t+1``.  They differ only in observation distribution and link:

  gauss    identity link on the Anscombe scale, per-unit residual variance;
           the count probability is recovered by the Anscombe change of
           variables over the interval that maps to the observed integer
  poisson  log link on counts, fitted by ridge-penalised IRLS
  negbin   the same log-link mean with a per-unit dispersion fitted by moments
           on the train block

Endpoint: held-out mean log-likelihood per bin per unit, in nats, on counts.
The primary timescale is 100 ms; the others are reported without thresholds.
Uncertainty uses a non-overlapping 10-second block bootstrap on the per-bin
paired difference.  Only aggregate JSON is written; the verified NWB file is
never persisted inside the repository.
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

TIMESCALES_SECONDS = (0.1, 0.05, 0.025, 0.01, 0.002)
PRIMARY_TIMESCALE = 0.1
LATENT_DIMENSION = 8
MIN_TRAIN_RATE_HZ = 0.1
RIDGE = 10.0
IRLS_STEPS = 30
IRLS_TOLERANCE = 1e-9
BLOCK_SECONDS = 10.0
BOOTSTRAPS = 2000
ROW_CHUNK = 60_000
SEED = 1701

HERE = Path(__file__).resolve().parent
ERFC = np.frompyfunc(math.erfc, 1, 1)
ROOT_TWO = math.sqrt(2.0)


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


def upper_tail(z: np.ndarray) -> np.ndarray:
    """Standard normal upper tail probability, accurate in the far tail."""
    return 0.5 * ERFC(z / ROOT_TWO).astype(np.float64)


def gauss_count_logprob(counts: np.ndarray, mean: np.ndarray, sigma: float) -> np.ndarray:
    """Log probability the Anscombe-scale Gaussian assigns to each observed count."""
    zb = (np.sqrt(counts + 0.875) - mean) / sigma
    za = np.where(counts > 0, (np.sqrt(np.maximum(counts - 0.125, 0.0)) - mean) / sigma, -np.inf)
    tail_za, tail_zb = upper_tail(za), upper_tail(zb)
    tail_neg_za, tail_neg_zb = upper_tail(-za), upper_tail(-zb)
    probability = np.where(
        za >= 0.0,
        tail_za - tail_zb,
        np.where(zb <= 0.0, tail_neg_zb - tail_neg_za, 1.0 - tail_zb - tail_neg_za),
    )
    return np.log(np.maximum(probability, 1e-300))


def fit_irls(design: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, bool]:
    """Poisson log-link IRLS with step halving.

    The undamped Newton step diverges for the very sparse counts that appear at
    the fine timescales, so every step is accepted only if it does not decrease
    the penalised log-likelihood; otherwise it is halved.  The intercept is
    unpenalised and the remaining columns carry RIDGE.
    """
    penalty = RIDGE * np.eye(design.shape[1])
    penalty[0, 0] = 0.0

    def objective(coefficients: np.ndarray) -> float:
        eta = np.clip(design @ coefficients, -30.0, 20.0)
        return float((target * eta - np.exp(eta)).sum() - 0.5 * coefficients @ penalty @ coefficients)

    beta = np.zeros(design.shape[1])
    beta[0] = math.log(max(target.mean(), 1e-8))
    value = objective(beta)
    converged = False
    for _ in range(IRLS_STEPS):
        eta = np.clip(design @ beta, -30.0, 20.0)
        rate = np.exp(eta)
        gradient = design.T @ (target - rate) - penalty @ beta
        hessian = design.T @ (design * rate[:, None]) + penalty + 1e-9 * np.eye(design.shape[1])
        step = np.linalg.solve(hessian, gradient)
        scale = 1.0
        for _ in range(30):
            candidate = beta + scale * step
            proposed = objective(candidate)
            if proposed >= value:
                break
            scale *= 0.5
        else:
            converged = True
            break
        movement = float(np.max(np.abs(scale * step)))
        beta, value = candidate, proposed
        if movement < IRLS_TOLERANCE:
            converged = True
            break
    return beta, converged


def block_bootstrap(difference: np.ndarray, block: int, rng: np.random.Generator) -> list[float]:
    n_blocks = max(difference.size // block, 2)
    trimmed = difference[: n_blocks * block].reshape(n_blocks, block).mean(axis=1)
    draws = trimmed[rng.integers(0, n_blocks, size=(BOOTSTRAPS, n_blocks))].mean(axis=1)
    return [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]


def bin_counts(spike_times: np.ndarray, spike_index: np.ndarray, edges: np.ndarray) -> np.ndarray:
    starts = np.concatenate(([0], spike_index[:-1]))
    out = np.zeros((edges.size - 1, spike_index.size), dtype=np.uint16)
    for unit, (a, b) in enumerate(zip(starts, spike_index)):
        out[:, unit] = np.histogram(spike_times[a:b], bins=edges)[0]
    return out


def latent_coordinates(counts: np.ndarray, train_end: int) -> np.ndarray:
    n_bins, n_units = counts.shape
    mean = np.zeros(n_units)
    second = np.zeros(n_units)
    for lo in range(0, train_end, ROW_CHUNK):
        hi = min(lo + ROW_CHUNK, train_end)
        block = np.sqrt(counts[lo:hi].astype(np.float64) + 0.375)
        mean += block.sum(axis=0)
        second += (block ** 2).sum(axis=0)
    mean /= train_end
    scale = np.sqrt(np.maximum(second / train_end - mean ** 2, 0.0))
    scale[scale <= 0] = 1.0

    gram = np.zeros((n_units, n_units))
    for lo in range(0, train_end, ROW_CHUNK):
        hi = min(lo + ROW_CHUNK, train_end)
        block = (np.sqrt(counts[lo:hi].astype(np.float64) + 0.375) - mean) / scale
        gram += block.T @ block
    _, vectors = np.linalg.eigh(gram / max(train_end - 1, 1))
    basis = vectors[:, ::-1][:, :LATENT_DIMENSION]

    latent = np.empty((n_bins, LATENT_DIMENSION))
    for lo in range(0, n_bins, ROW_CHUNK):
        hi = min(lo + ROW_CHUNK, n_bins)
        block = (np.sqrt(counts[lo:hi].astype(np.float64) + 0.375) - mean) / scale
        latent[lo:hi] = block @ basis
    return latent


def analyse(counts: np.ndarray, seconds: float, rng: np.random.Generator) -> dict:
    n_bins = counts.shape[0]
    train_end, dev_end = n_bins // 2, (3 * n_bins) // 4
    prefix_rate = counts[:train_end].sum(axis=0, dtype=np.int64) / (train_end * seconds)
    retained = prefix_rate >= MIN_TRAIN_RATE_HZ
    counts = np.ascontiguousarray(counts[:, retained])
    n_units = int(retained.sum())

    latent = latent_coordinates(counts, train_end)
    design = np.c_[np.ones(n_bins), latent]
    rows_train = np.arange(0, train_end - 1)
    rows_test = np.arange(dev_end, n_bins - 1)
    x_train = design[rows_train]
    x_test = design[rows_test]

    gram = x_train.T @ x_train + RIDGE * np.eye(design.shape[1])
    gram[0, 0] -= RIDGE

    totals = {"gauss": 0.0, "poisson": 0.0, "negbin": 0.0}
    poisson_gap = np.zeros(rows_test.size)
    negbin_gap = np.zeros(rows_test.size)
    dispersions = np.empty(n_units)
    convergence = np.zeros(n_units, dtype=bool)
    peak_eta = np.zeros(n_units)

    for unit in range(n_units):
        train_counts = counts[rows_train + 1, unit].astype(np.float64)
        test_counts = counts[rows_test + 1, unit].astype(np.float64)
        max_count = int(test_counts.max())
        log_factorial = np.concatenate(([0.0], np.cumsum(np.log(np.arange(1, max_count + 1))))) if max_count else np.array([0.0])
        test_index = test_counts.astype(np.int64)

        anscombe_train = np.sqrt(train_counts + 0.375)
        beta = np.linalg.solve(gram, x_train.T @ anscombe_train)
        sigma = max(float((anscombe_train - x_train @ beta).std()), 1e-6)
        gauss = gauss_count_logprob(test_counts, x_test @ beta, sigma)

        coefficient, converged = fit_irls(x_train, train_counts)
        convergence[unit] = converged
        eta_test = x_test @ coefficient
        peak_eta[unit] = float(np.max(np.abs(eta_test)))
        rate_test = np.exp(np.clip(eta_test, -30.0, 20.0))
        poisson = test_counts * np.log(rate_test) - rate_test - log_factorial[test_index]

        rate_train = np.exp(np.clip(x_train @ coefficient, -30.0, 20.0))
        excess = float(np.mean((train_counts - rate_train) ** 2 - rate_train))
        denominator = float(np.mean(rate_train ** 2))
        alpha = max(excess / denominator, 1e-8) if denominator > 0 else 1e-8
        size = 1.0 / alpha
        dispersions[unit] = alpha
        ladder = np.concatenate(([0.0], np.cumsum(np.log(size + np.arange(max_count))))) if max_count else np.array([0.0])
        negbin = (
            ladder[test_index]
            - log_factorial[test_index]
            + size * np.log(size / (size + rate_test))
            + test_counts * np.log(rate_test / (size + rate_test))
        )

        totals["gauss"] += float(gauss.mean())
        totals["poisson"] += float(poisson.mean())
        totals["negbin"] += float(negbin.mean())
        poisson_gap += poisson - gauss
        negbin_gap += negbin - gauss

    per_bin = {name: value / n_units for name, value in totals.items()}
    block = max(int(round(BLOCK_SECONDS / seconds)), 2)
    result = {
        "bin_seconds": seconds,
        "n_bins": int(n_bins),
        "retained_units": n_units,
        "test_rows": int(rows_test.size),
        "mean_count_per_bin": float(counts.mean()),
        "bootstrap_block_bins": block,
        "median_dispersion_alpha": float(np.median(dispersions)),
        "irls_converged_units": int(convergence.sum()),
        "max_abs_test_eta": float(peak_eta.max()),
        "loglik_per_bin_per_unit_nats": per_bin,
        "loglik_per_second_per_unit_nats": {name: value / seconds for name, value in per_bin.items()},
    }
    for name, gap in (("poisson", poisson_gap), ("negbin", negbin_gap)):
        difference = gap / n_units
        result[f"{name}_minus_gauss"] = {
            "mean_nats_per_bin_per_unit": float(difference.mean()),
            "bootstrap_ci95": block_bootstrap(difference, block, rng),
        }
    return result


def main() -> None:
    path, receipt, temporary = resolve_asset()
    rng = np.random.default_rng(SEED)
    try:
        with h5py.File(path, "r") as nwb:
            units = nwb["units"]
            spike_times = units["spike_times"][:]
            spike_index = units["spike_times_index"][:]
            series = nwb["processing/behavior/Position/position"]
            hz = float(series["starting_time"].attrs["rate"])
            t0 = float(series["starting_time"][()])
            n_samples = series["data"].shape[0]

        start = max(t0, float(spike_times.min()))
        stop = min(t0 + (n_samples - 1) / hz, float(spike_times.max()))

        report = {
            "item": "P2",
            "window_seconds": [start, stop],
            "latent_dimension": LATENT_DIMENSION,
            "ridge": RIDGE,
            "block_seconds": BLOCK_SECONDS,
            "bootstraps": BOOTSTRAPS,
            "results": {},
        }
        for seconds in TIMESCALES_SECONDS:
            n_bins = int(np.floor((stop - start) / seconds))
            edges = start + seconds * np.arange(n_bins + 1)
            counts = bin_counts(spike_times, spike_index, edges)
            outcome = analyse(counts, seconds, rng)
            report["results"][f"{seconds:g}s"] = outcome
            print(f"{seconds:g}s ->", json.dumps(jsonable(outcome["loglik_per_bin_per_unit_nats"])), flush=True)
            del counts

        primary = report["results"][f"{PRIMARY_TIMESCALE:g}s"]
        best = max(("poisson", "negbin"), key=lambda name: primary[f"{name}_minus_gauss"]["mean_nats_per_bin_per_unit"])
        improvement = primary[f"{best}_minus_gauss"]
        report["primary_timescale"] = f"{PRIMARY_TIMESCALE:g}s"
        report["best_point_process_model"] = best
        report["status"] = "PASS" if improvement["mean_nats_per_bin_per_unit"] > 0 and improvement["bootstrap_ci95"][0] > 0 else "FAIL"
        report["claim_ceiling"] = "Observation-model comparison only; no biological, manifold, metric, or causal claim."
        report["source_receipt"] = receipt
        (HERE / "p2-result.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
        print(json.dumps(jsonable({k: v for k, v in report.items() if k != "results"}), indent=2))
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
