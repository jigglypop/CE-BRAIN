"""Development analysis: fitting in the scoring space, and the pullback attractor.

DEVELOPMENT ONLY, on the DANDI 001701 asset that chapters 11 and 12 consumed.

Chapters 18 and 20 fit by least squares on the Anscombe scale and then scored by
negative-binomial likelihood on counts, mapping a predicted Anscombe value back
to a rate by inverting the transform.  That bridge is a defect: the estimator
optimises one loss and the endpoint measures another, and at 10 ms the inverse
map is steep near zero counts.  This script removes the bridge by fitting the
same features (equation 19.11 with the rejected base-dependent terms dropped)
as a Poisson log-link generalised linear model, by damped iteratively reweighted
least squares, and scoring the result with the same negative-binomial endpoint.

It also measures the object the theory is actually about.  Proposition 19.6 says
that with an exogenous input the invariant graph is replaced by a pullback
attractor, reachable by running the model's own recursion forward from any
initial condition.  The script runs that recursion along the held-out trajectory
and reports how far the observed latent state sits from it.

Two further corrections are applied to both models equally and declared here:
the negative-binomial dispersion is re-estimated from each model's fitted rate
rather than from a constant-rate model, and the ridge grid is swept on a seeded
subsample of units before the full fit, because a per-unit sweep over all units
is not affordable.
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

BIN_SECONDS = 0.01
THETA_BAND = (6.0, 10.0)
LATENT = 24
LAGS = 12
FORCING_HARMONIC = 3
GAUSSIAN_RIDGE = 1e5
GLM_RIDGES = (1e2, 1e3, 1e4)
GLM_STEPS = 8
GLM_TOLERANCE = 1e-8
SELECTION_UNITS = 60
MIN_TRAIN_RATE_HZ = 0.1
BLOCK_SECONDS = 10.0
BOOTSTRAPS = 2000
BURN_IN = 500
CHUNK = 8192
SEED = 1701

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


def band_phase(trace: np.ndarray, fs: float, low: float, high: float) -> np.ndarray:
    spectrum = np.fft.fft(trace - trace.mean())
    frequency = np.fft.fftfreq(trace.size, 1 / fs)
    keep = (frequency >= low) & (frequency <= high)
    analytic = np.zeros_like(spectrum)
    analytic[keep] = 2.0 * spectrum[keep]
    return np.angle(np.fft.ifft(analytic))


def negbin_loglik(target: np.ndarray, rate: np.ndarray, size: float) -> np.ndarray:
    top = int(target.max())
    ladder = np.concatenate(([0.0], np.cumsum(np.log(size + np.arange(top))))) if top else np.array([0.0])
    log_factorial = np.concatenate(([0.0], np.cumsum(np.log(np.arange(1, top + 1))))) if top else np.array([0.0])
    index = target.astype(np.int64)
    return (
        ladder[index]
        - log_factorial[index]
        + size * np.log(size / (size + rate))
        + target * np.log(rate / (size + rate))
    )


def dispersion_from_fit(target: np.ndarray, rate: np.ndarray) -> float:
    """Moment estimate of the negative-binomial dispersion around a fitted rate."""
    excess = float(np.mean((target - rate) ** 2 - rate))
    denominator = float(np.mean(rate ** 2))
    if denominator <= 0:
        return 1e-6
    return max(excess / denominator, 1e-6)


def poisson_irls(design: np.ndarray, target: np.ndarray, lam: float) -> np.ndarray:
    penalty = lam * np.eye(design.shape[1])
    penalty[0, 0] = 0.0

    def objective(beta: np.ndarray) -> float:
        eta = np.clip(design @ beta, -30.0, 15.0)
        return float((target * eta - np.exp(eta)).sum() - 0.5 * beta @ penalty @ beta)

    beta = np.zeros(design.shape[1])
    beta[0] = math.log(max(target.mean(), 1e-8))
    value = objective(beta)
    for _ in range(GLM_STEPS):
        eta = np.clip(design @ beta, -30.0, 15.0)
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
            break
        moved = float(np.max(np.abs(scale * step)))
        beta, value = candidate, proposed
        if moved < GLM_TOLERANCE:
            break
    return beta


def block_bootstrap(difference: np.ndarray, block: int, rng: np.random.Generator) -> list[float]:
    n_blocks = max(difference.size // block, 2)
    means = difference[: n_blocks * block].reshape(n_blocks, block).mean(axis=1)
    draws = means[rng.integers(0, n_blocks, size=(BOOTSTRAPS, n_blocks))].mean(axis=1)
    return [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]


def main() -> None:
    path, receipt, temporary = resolve_asset()
    rng = np.random.default_rng(SEED)
    try:
        with h5py.File(path, "r") as nwb:
            lfp = nwb["processing/probe_0_channel_160/LFP/LFP"]
            fs = float(lfp["starting_time"].attrs["rate"])
            start = float(lfp["starting_time"][()])
            trace = lfp["data"][:, 0].astype(np.float64)
            stop = start + trace.size / fs
            spike_times = nwb["units/spike_times"][:]
            spike_index = nwb["units/spike_times_index"][:]
            series = nwb["processing/behavior/Position/position"]
            behaviour_hz = float(series["starting_time"].attrs["rate"])
            behaviour_t0 = float(series["starting_time"][()])
            position_raw = series["data"][:]
            head_raw = nwb["processing/behavior/CompassDirection/head direction"]["data"][:]

        phase_full = band_phase(trace, fs, *THETA_BAND)
        n_bins = int(math.floor((stop - start) / BIN_SECONDS))
        train_end, dev_end = int(math.floor(0.5 * n_bins)), int(math.floor(0.75 * n_bins))
        boundary = start + train_end * BIN_SECONDS
        edges = start + BIN_SECONDS * np.arange(n_bins + 1)
        starts = np.concatenate(([0], spike_index[:-1]))
        counts = np.empty((n_bins, spike_index.size), dtype=np.float32)
        prefix = np.empty(spike_index.size)
        for unit, (a, b) in enumerate(zip(starts, spike_index)):
            times = spike_times[a:b]
            counts[:, unit] = np.histogram(times, bins=edges)[0]
            prefix[unit] = np.searchsorted(times, boundary)
        counts = counts[:, (prefix / (boundary - start)) >= MIN_TRAIN_RATE_HZ].astype(np.float64)
        n_units = counts.shape[1]

        centres = start + BIN_SECONDS * (np.arange(n_bins) + 0.5)
        phase = phase_full[np.clip(np.round((centres - start) * fs).astype(np.int64), 0, phase_full.size - 1)]

        gap = ~np.isfinite(position_raw).all(axis=1)
        filled = position_raw.copy()
        index = np.arange(filled.shape[0])
        for column in range(2):
            good = np.isfinite(filled[:, column])
            filled[:, column] = np.interp(index, index[good], filled[good, column])
        head = np.where(np.isfinite(head_raw), head_raw, 0.0)
        velocity = np.vstack((np.zeros((1, 2)), np.diff(filled, axis=0) * behaviour_hz))
        behaviour_time = behaviour_t0 + np.arange(filled.shape[0]) / behaviour_hz
        pick = np.clip(np.round((centres - behaviour_t0) * behaviour_hz).astype(np.int64), 0, filled.shape[0] - 1)
        inside = (centres >= behaviour_time[0]) & (centres <= behaviour_time[-1]) & ~gap[pick]
        behaviour = np.c_[filled[pick], np.sin(head[pick]), np.cos(head[pick]), velocity[pick],
                          np.linalg.norm(velocity[pick], axis=1)]
        reference = behaviour[:train_end][inside[:train_end]]
        behaviour = (behaviour - reference.mean(axis=0)) / np.where(reference.std(axis=0) == 0, 1.0, reference.std(axis=0))

        transformed = np.sqrt(counts + 0.375)
        mean = transformed[:train_end].mean(axis=0)
        scale = transformed[:train_end].std(axis=0)
        scale[scale == 0] = 1.0
        state = (transformed - mean) / scale
        basis = np.linalg.svd(state[:train_end], full_matrices=False)[2].T[:, :LATENT]
        latent = state @ basis

        def valid(lo: int, hi: int) -> np.ndarray:
            rows = np.arange(max(lo, LAGS), min(hi, n_bins - 1))
            return rows[inside[rows]]

        train, dev, test = valid(0, train_end), valid(train_end, dev_end), valid(dev_end, n_bins)

        def build(rows: np.ndarray) -> np.ndarray:
            blocks = [np.ones((rows.size, 1))]
            for l in range(LAGS):
                blocks.append(latent[rows - l])
            angle = phase[rows]
            harmonics = np.empty((rows.size, 2 * FORCING_HARMONIC))
            for h in range(1, FORCING_HARMONIC + 1):
                harmonics[:, 2 * (h - 1)] = np.cos(h * angle)
                harmonics[:, 2 * (h - 1) + 1] = np.sin(h * angle)
            blocks.append(harmonics)
            blocks.append(behaviour[rows])
            return np.hstack(blocks)

        design_train, design_dev, design_test = build(train), build(dev), build(test)
        n_features = design_train.shape[1]

        # Gaussian fit on the Anscombe scale, exactly as in chapter 20.
        gram = design_train.T @ design_train + GAUSSIAN_RIDGE * np.eye(n_features)
        gram[0, 0] -= GAUSSIAN_RIDGE
        gaussian_beta = np.linalg.solve(gram, design_train.T @ state[train + 1])
        gaussian_test = design_test @ gaussian_beta
        gaussian_rate_test = np.maximum((gaussian_test * scale + mean) ** 2 - 0.375, 1e-6)
        gaussian_rate_train = np.maximum(((design_train @ gaussian_beta) * scale + mean) ** 2 - 0.375, 1e-6)

        # Poisson log-link fit of the same features, with the ridge chosen on a
        # seeded subsample of units because a full per-unit sweep is unaffordable.
        chosen = rng.choice(n_units, size=min(SELECTION_UNITS, n_units), replace=False)
        selection = {}
        for lam in GLM_RIDGES:
            total = 0.0
            for unit in chosen:
                beta = poisson_irls(design_train, counts[train + 1, unit], lam)
                rate = np.exp(np.clip(design_dev @ beta, -30.0, 15.0))
                size = 1.0 / dispersion_from_fit(counts[train + 1, unit], np.exp(np.clip(design_train @ beta, -30.0, 15.0)))
                total += float(negbin_loglik(counts[dev + 1, unit], rate, size).mean())
            selection[lam] = total / chosen.size
            print(f"  glm ridge {lam:g}: development {selection[lam]:.6f}", flush=True)
        glm_ridge = max(selection, key=selection.get)

        glm_rows = np.zeros(test.size)
        gaussian_rows = np.zeros(test.size)
        constant_rows = np.zeros(test.size)
        glm_rate_test = np.empty((test.size, n_units))
        for unit in range(n_units):
            target_train = counts[train + 1, unit]
            target_test = counts[test + 1, unit]

            beta = poisson_irls(design_train, target_train, glm_ridge)
            rate_train = np.exp(np.clip(design_train @ beta, -30.0, 15.0))
            rate_test = np.exp(np.clip(design_test @ beta, -30.0, 15.0))
            glm_rate_test[:, unit] = rate_test
            glm_rows += negbin_loglik(target_test, rate_test, 1.0 / dispersion_from_fit(target_train, rate_train))

            gaussian_rows += negbin_loglik(
                target_test, gaussian_rate_test[:, unit],
                1.0 / dispersion_from_fit(target_train, gaussian_rate_train[:, unit]),
            )
            constant = max(target_train.mean(), 1e-6)
            constant_rows += negbin_loglik(
                target_test, np.full(test.size, constant),
                1.0 / dispersion_from_fit(target_train, np.full(target_train.size, constant)),
            )
            if unit % 50 == 0:
                print(f"  unit {unit}/{n_units}", flush=True)
        glm_rows /= n_units
        gaussian_rows /= n_units
        constant_rows /= n_units

        # Pullback attractor of proposition 19.6, run forward in the latent space.
        lag_blocks = [basis.T @ gaussian_beta[1 + l * LATENT : 1 + (l + 1) * LATENT].T for l in range(LAGS)]
        drive_columns = np.concatenate(([0], np.arange(1 + LAGS * LATENT, n_features)))
        drive = basis.T @ gaussian_beta[drive_columns].T @ design_test[:, drive_columns].T
        history = np.zeros((LAGS, LATENT))
        residual_numerator = 0.0
        residual_denominator = 0.0
        for position in range(test.size):
            nxt = drive[:, position].copy()
            for l in range(LAGS):
                nxt += lag_blocks[l] @ history[l]
            history = np.vstack((nxt, history[:-1]))
            if position >= BURN_IN:
                difference = latent[test[position] + 1] - nxt
                residual_numerator += float(difference @ difference)
                residual_denominator += float(latent[test[position] + 1] @ latent[test[position] + 1])
        attractor_residual = residual_numerator / residual_denominator

        block = max(int(round(BLOCK_SECONDS / BIN_SECONDS)), 2)
        report = {
            "track": "DEVELOPMENT_ONLY",
            "n_units": int(n_units),
            "n_features": int(n_features),
            "lags": LAGS,
            "latent_dimension": LATENT,
            "rows": {"train": int(train.size), "development": int(dev.size), "test": int(test.size)},
            "glm_ridge_selection": selection,
            "glm_ridge": glm_ridge,
            "test_loglik": {
                "constant_rate": float(constant_rows.mean()),
                "gaussian_fit_bridged": float(gaussian_rows.mean()),
                "poisson_glm_fit": float(glm_rows.mean()),
            },
            "comparisons": {
                "glm_minus_gaussian": {
                    "mean": float((glm_rows - gaussian_rows).mean()),
                    "bootstrap_ci95": block_bootstrap(glm_rows - gaussian_rows, block, rng),
                },
                "glm_minus_constant": {
                    "mean": float((glm_rows - constant_rows).mean()),
                    "bootstrap_ci95": block_bootstrap(glm_rows - constant_rows, block, rng),
                },
                "gaussian_minus_constant": {
                    "mean": float((gaussian_rows - constant_rows).mean()),
                    "bootstrap_ci95": block_bootstrap(gaussian_rows - constant_rows, block, rng),
                },
            },
            "pullback_attractor_residual_test": attractor_residual,
            "burn_in_bins": BURN_IN,
            "claim_ceiling": "Development measurement on a consumed asset; not a result about the recording family.",
            "source_receipt": receipt,
        }
        (HERE / "development-glm-attractor.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
        print(json.dumps(jsonable({k: v for k, v in report.items() if k != "source_receipt"}), indent=2))
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
