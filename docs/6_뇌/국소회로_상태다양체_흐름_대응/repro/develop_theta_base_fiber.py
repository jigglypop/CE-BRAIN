"""Development analysis: chapter 10's rotating base, instantiated on the data.

DEVELOPMENT ONLY, on the DANDI 001701 asset that chapters 11 and 12 consumed.

Chapter 17 argued that the dominant temporal structure of this recording is a
theta rotation and that the 100 ms counting window of chapters 11-16 removed it.
This script fits the candidate that chapter 17 pre-registered,

    y_{t+1} = A y_t + c(theta_t),
    c(theta) = c0 + sum_k a_k cos(k theta) + b_k sin(k theta),

where theta is the phase of the 6-10 Hz band of this session's local field
potential and y is the population Anscombe state.  Three comparisons are fixed
before scoring: the theta-free null y' = A y + c0, a circular shift of the phase
series, and a random permutation of the phase values.

Scoring is the held-out negative-binomial log likelihood on counts, per bin per
unit.  The whole comparison is repeated at 100 ms, which is chapter 17's own
falsifier: if theta helps as much at 100 ms as at 10 ms, the diagnosis is wrong.

The certificate is q = ||A||_2 alone, because a rotation of the circle is an
isometry and so the bunching factor kappa equals one.
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

PRIMARY_BIN = 0.01
FALSIFIER_BIN = 0.1
THETA_BAND = (6.0, 10.0)
HARMONICS = (1, 2, 3, 4)
RIDGES = (1e-1, 1.0, 10.0, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8)
MIN_TRAIN_RATE_HZ = 0.1
SHIFT_SECONDS = 30.0
BLOCK_SECONDS = 10.0
BOOTSTRAPS = 2000
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
    """Analytic-signal phase of one band, built from the FFT (no SciPy needed)."""
    spectrum = np.fft.fft(trace - trace.mean())
    frequency = np.fft.fftfreq(trace.size, 1 / fs)
    keep = (frequency >= low) & (frequency <= high)
    analytic = np.zeros_like(spectrum)
    analytic[keep] = 2.0 * spectrum[keep]
    return np.angle(np.fft.ifft(analytic))


def ridge(x: np.ndarray, y: np.ndarray, lam: float) -> tuple[np.ndarray, np.ndarray]:
    x_mean, y_mean = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - x_mean, y - y_mean
    coefficient = np.linalg.solve(xc.T @ xc + lam * np.eye(x.shape[1]), xc.T @ yc)
    return coefficient, y_mean - x_mean @ coefficient


class NegBinScorer:
    def __init__(self, counts: np.ndarray, train_rows: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> None:
        train_counts = counts[train_rows + 1]
        lam = np.maximum(train_counts.mean(axis=0), 1e-6)
        excess = np.mean((train_counts - lam) ** 2 - lam, axis=0)
        self.size = 1.0 / np.maximum(excess / np.maximum(lam ** 2, 1e-12), 1e-6)
        self.mean, self.scale, self.n_units = mean, scale, counts.shape[1]

    def prepare(self, counts: np.ndarray, rows: np.ndarray) -> None:
        self.target = counts[rows + 1]
        top = int(self.target.max())
        steps = np.log(self.size[None, :] + np.arange(top)[:, None]) if top else np.zeros((0, self.n_units))
        self.ladder = np.vstack((np.zeros((1, self.n_units)), np.cumsum(steps, axis=0)))
        self.log_factorial = np.concatenate(([0.0], np.cumsum(np.log(np.arange(1, top + 1))))) if top else np.array([0.0])
        self.index = self.target.astype(np.int64)

    def rowwise(self, state_prediction: np.ndarray) -> np.ndarray:
        rate = np.maximum((state_prediction * self.scale + self.mean) ** 2 - 0.375, 1e-6)
        term = (
            np.take_along_axis(self.ladder, self.index, axis=0)
            - self.log_factorial[self.index]
            + self.size * np.log(self.size / (self.size + rate))
            + self.target * np.log(rate / (self.size + rate))
        )
        return term.mean(axis=1)

    def score(self, state_prediction: np.ndarray) -> float:
        return float(self.rowwise(state_prediction).mean())


def harmonic_features(phase: np.ndarray, order: int) -> np.ndarray:
    blocks = [np.ones((phase.size, 1))]
    for k in range(1, order + 1):
        blocks.append(np.cos(k * phase)[:, None])
        blocks.append(np.sin(k * phase)[:, None])
    return np.hstack(blocks)


def block_bootstrap(difference: np.ndarray, block: int, rng: np.random.Generator) -> list[float]:
    n_blocks = max(difference.size // block, 2)
    means = difference[: n_blocks * block].reshape(n_blocks, block).mean(axis=1)
    draws = means[rng.integers(0, n_blocks, size=(BOOTSTRAPS, n_blocks))].mean(axis=1)
    return [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]


def invariant_graph_residual(a_matrix: np.ndarray, theta_coefficients: np.ndarray, order: int, omega: float, phase: np.ndarray, state: np.ndarray) -> float:
    """Closed-form graph h(theta) for a rigid rotation of mean advance omega."""
    size = a_matrix.shape[0]
    constant = theta_coefficients[0]
    graph = np.tile(np.linalg.solve(np.eye(size) - a_matrix, constant), (phase.size, 1))
    for k in range(1, order + 1):
        a_k = theta_coefficients[2 * k - 1]
        b_k = theta_coefficients[2 * k]
        z = a_k - 1j * b_k
        resolvent = np.linalg.solve(np.eye(size) - a_matrix * np.exp(-1j * k * omega), z)
        graph += np.real(np.exp(1j * k * (phase - omega))[:, None] * resolvent[None, :])
    return float(np.square(state - graph).sum() / np.square(state).sum())


def run(counts: np.ndarray, phase: np.ndarray, seconds: float, rng: np.random.Generator) -> dict:
    n_bins, n_units = counts.shape
    train_end, dev_end = int(math.floor(0.5 * n_bins)), int(math.floor(0.75 * n_bins))
    transformed = np.sqrt(counts + 0.375)
    mean = transformed[:train_end].mean(axis=0)
    scale = transformed[:train_end].std(axis=0)
    scale[scale == 0] = 1.0
    state = (transformed - mean) / scale

    train = np.arange(0, train_end - 1)
    dev = np.arange(train_end, dev_end - 1)
    test = np.arange(dev_end, n_bins - 1)
    scorer = NegBinScorer(counts, train, mean, scale)

    advance = np.diff(np.unwrap(phase))
    shift = int(round(SHIFT_SECONDS / seconds))
    variants = {
        "theta": phase,
        "shifted": np.roll(phase, shift),
        "permuted": rng.permutation(phase),
    }

    def fit_and_score(features: np.ndarray, lam: float, rows_fit: np.ndarray, rows_score: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        design = np.hstack([state[rows_fit], features[rows_fit]])
        coefficient, offset = ridge(design, state[rows_fit + 1], lam)
        estimate = np.hstack([state[rows_score], features[rows_score]]) @ coefficient + offset
        return coefficient, offset, estimate

    outcome: dict = {"bin_seconds": seconds, "n_bins": int(n_bins), "n_units": int(n_units),
                     "mean_phase_advance_rad": float(np.mean(advance)),
                     "phase_advance_sd_rad": float(np.std(advance)),
                     "implied_frequency_hz": float(np.mean(advance) / (2 * math.pi * seconds))}

    scorer.prepare(counts, dev)
    selection = {}
    for name, series in variants.items():
        best = None
        for order in HARMONICS:
            features = harmonic_features(series, order)
            for lam in RIDGES:
                _, _, estimate = fit_and_score(features, lam, train, dev)
                score = scorer.score(estimate)
                if best is None or score > best[0]:
                    best = (score, order, lam)
        selection[name] = {"development_loglik": best[0], "harmonics": best[1], "lambda": best[2]}
    best_null = None
    constant_features = np.ones((n_bins, 1))
    for lam in RIDGES:
        _, _, estimate = fit_and_score(constant_features, lam, train, dev)
        score = scorer.score(estimate)
        if best_null is None or score > best_null[0]:
            best_null = (score, lam)
    selection["null"] = {"development_loglik": best_null[0], "harmonics": 0, "lambda": best_null[1]}

    scorer.prepare(counts, test)
    rows: dict[str, np.ndarray] = {}
    results: dict[str, dict] = {}
    for name, choice in selection.items():
        features = constant_features if name == "null" else harmonic_features(variants[name], choice["harmonics"])
        coefficient, offset, estimate = fit_and_score(features, choice["lambda"], train, test)
        rows[name] = scorer.rowwise(estimate)
        entry = dict(choice)
        entry["test_loglik"] = float(rows[name].mean())
        entry["q"] = float(np.linalg.norm(coefficient[:n_units].T, 2))
        if name == "theta":
            a_matrix = coefficient[:n_units].T
            theta_block = coefficient[n_units:].copy()
            theta_block[0] += offset
            entry["invariant_graph_residual_test"] = invariant_graph_residual(
                a_matrix, theta_block, choice["harmonics"], float(np.mean(advance)), variants[name][test], state[test]
            )
        results[name] = entry

    baseline_rows = scorer.rowwise(np.broadcast_to(state[train + 1].mean(axis=0), (test.size, n_units)))
    baseline = float(baseline_rows.mean())
    results["train_mean"] = {"test_loglik": baseline}
    rows["train_mean"] = baseline_rows

    block = max(int(round(BLOCK_SECONDS / seconds)), 2)
    comparisons = {}
    for other in ("null", "shifted", "permuted", "train_mean"):
        difference = rows["theta"] - rows[other]
        comparisons[f"theta_minus_{other}"] = {
            "mean": float(difference.mean()),
            "bootstrap_ci95": block_bootstrap(difference, block, rng),
        }
    outcome["selection"] = results
    outcome["comparisons"] = comparisons
    outcome["theta_gain_over_train_mean"] = results["theta"]["test_loglik"] - baseline
    return outcome


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

        phase_full = band_phase(trace, fs, *THETA_BAND)
        starts = np.concatenate(([0], spike_index[:-1]))

        report = {"track": "DEVELOPMENT_ONLY", "theta_band_hz": list(THETA_BAND), "results": {}}
        for seconds in (PRIMARY_BIN, FALSIFIER_BIN):
            n_bins = int(math.floor((stop - start) / seconds))
            boundary = start + int(math.floor(0.5 * n_bins)) * seconds
            edges = start + seconds * np.arange(n_bins + 1)
            counts = np.empty((n_bins, spike_index.size), dtype=np.float32)
            prefix = np.empty(spike_index.size)
            for unit, (a, b) in enumerate(zip(starts, spike_index)):
                times = spike_times[a:b]
                counts[:, unit] = np.histogram(times, bins=edges)[0]
                prefix[unit] = np.searchsorted(times, boundary)
            counts = counts[:, (prefix / (boundary - start)) >= MIN_TRAIN_RATE_HZ].astype(np.float64)
            centres = start + seconds * (np.arange(n_bins) + 0.5)
            sample = np.clip(np.round((centres - start) * fs).astype(np.int64), 0, phase_full.size - 1)
            outcome = run(counts, phase_full[sample], seconds, rng)
            report["results"][f"{seconds:g}s"] = outcome
            gain = outcome["comparisons"]["theta_minus_null"]
            print(
                f"{seconds:g}s  units={outcome['n_units']}  freq={outcome['implied_frequency_hz']:.2f}Hz"
                f"  H={outcome['selection']['theta']['harmonics']}  q={outcome['selection']['theta']['q']:.4f}"
                f"  theta-null={gain['mean']:+.6f} ci={[round(v, 6) for v in gain['bootstrap_ci95']]}",
                flush=True,
            )

        primary = report["results"][f"{PRIMARY_BIN:g}s"]["comparisons"]["theta_minus_null"]["mean"]
        falsifier = report["results"][f"{FALSIFIER_BIN:g}s"]["comparisons"]["theta_minus_null"]["mean"]
        report["falsifier"] = {
            "gain_10ms": primary,
            "gain_100ms": falsifier,
            "ratio_100ms_over_10ms": falsifier / primary if primary else float("inf"),
            "diagnosis_holds_if_ratio_below": 0.2,
        }
        report["claim_ceiling"] = "Development measurement on a consumed asset; not a result about the recording family."
        report["source_receipt"] = receipt
        (HERE / "development-theta-base.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
        print(json.dumps(jsonable(report["falsifier"]), indent=2))
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
