"""Development analysis: the extended update equation (19.11).

DEVELOPMENT ONLY, on the DANDI 001701 asset that chapters 11 and 12 consumed.

Chapter 19 extends chapter 7's fibre map in three directions: the fibre
coefficients may depend on the base, the recursion may carry several lags, and
an exogenous input may enter.  This script fits the resulting predictor

    y_hat[i, t+1] = b_i
                  + sum_l sum_k ( alpha[i,l,k] . s[t-l] cos(k theta_t)
                                + beta [i,l,k] . s[t-l] sin(k theta_t) )
                  + sum_h ( a[i,h] cos(h theta_t) + b[i,h] sin(h theta_t) )
                  + d_i . phi(u_t)

where s = W' y are the top-r train principal components of the population
Anscombe state, theta is the local field potential theta phase, and phi(u)
carries position, head direction and speed.

Nested variants isolate what each added term buys:

    V1  constant + one lag, no theta             (chapter 18's null, in latent form)
    V2  + theta forcing c(theta)                 (chapter 18's candidate)
    V3  + several lags                           (corollary 19.5)
    V4  + base-dependent coefficients A_l(theta) (theorem 19.3)
    V5  + behaviour input                        (proposition 19.6)

Scoring is held-out negative-binomial log likelihood on counts.  The
certificate is the exponential growth rate of the companion cocycle of
equation (19.8), computed along the session's own phase trajectory, which is
what theorem 19.4 requires instead of an operator norm.

The design matrix is built once in single precision and the normal equations
are accumulated once in double precision, so every nested variant is a
sub-block solve rather than a fresh pass over the data.
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
MAX_LAG = 16
LAG_CHOICES = (2, 4, 8, 12, 16)
MAX_COEFFICIENT_HARMONIC = 2
COEFFICIENT_CHOICES = (1, 2)
FORCING_HARMONIC = 3
RIDGES = (1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8)
MIN_TRAIN_RATE_HZ = 0.1
SHIFT_SECONDS = 30.0
BLOCK_SECONDS = 10.0
BOOTSTRAPS = 2000
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

    def rowwise(self, prediction: np.ndarray) -> np.ndarray:
        rate = np.maximum((prediction * self.scale + self.mean) ** 2 - 0.375, 1e-6)
        term = (
            np.take_along_axis(self.ladder, self.index, axis=0)
            - self.log_factorial[self.index]
            + self.size * np.log(self.size / (self.size + rate))
            + self.target * np.log(rate / (self.size + rate))
        )
        return term.mean(axis=1)

    def score(self, prediction: np.ndarray) -> float:
        return float(self.rowwise(prediction).mean())


def block_bootstrap(difference: np.ndarray, block: int, rng: np.random.Generator) -> list[float]:
    n_blocks = max(difference.size // block, 2)
    means = difference[: n_blocks * block].reshape(n_blocks, block).mean(axis=1)
    draws = means[rng.integers(0, n_blocks, size=(BOOTSTRAPS, n_blocks))].mean(axis=1)
    return [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]


def cocycle_exponent(lag_blocks: list[np.ndarray], harmonic_blocks: list[list[tuple[np.ndarray, np.ndarray]]], phase: np.ndarray) -> dict:
    """Top exponential growth rate of the companion cocycle along the observed phases."""
    lags = len(lag_blocks)
    r = lag_blocks[0].shape[0]
    size = r * lags
    matrix = np.eye(size)
    accumulated = 0.0
    steps = 0
    for position, angle in enumerate(phase):
        # The companion matrix is dense only in its top block row, so the product
        # costs r*size^2 rather than size^3: the lower rows are a plain shift.
        top = np.zeros((r, size))
        for l in range(lags):
            block = lag_blocks[l]
            for k, (cosine, sine) in enumerate(harmonic_blocks[l], start=1):
                block = block + cosine * math.cos(k * angle) + sine * math.sin(k * angle)
            top += block @ matrix[l * r : (l + 1) * r, :]
        matrix = np.vstack((top, matrix[: (lags - 1) * r, :])) if lags > 1 else top
        steps += 1
        norm = float(np.linalg.norm(matrix, 2))
        if norm == 0.0:
            return {"per_step_factor": 0.0, "steps": steps, "degenerate": True}
        if norm > 1e6 or norm < 1e-6 or position % 50 == 49:
            accumulated += math.log(norm)
            matrix = matrix / norm
    accumulated += math.log(max(float(np.linalg.norm(matrix, 2)), 1e-300))
    rate = accumulated / steps
    return {"per_step_factor": math.exp(rate), "log_rate_per_step": rate, "steps": steps, "degenerate": False}


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
        sample = np.clip(np.round((centres - start) * fs).astype(np.int64), 0, phase_full.size - 1)
        phase = phase_full[sample]

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
        behaviour = np.c_[
            filled[pick], np.sin(head[pick]), np.cos(head[pick]), velocity[pick],
            np.linalg.norm(velocity[pick], axis=1),
        ]
        reference = behaviour[:train_end][inside[:train_end]]
        behaviour = (behaviour - reference.mean(axis=0)) / np.where(reference.std(axis=0) == 0, 1.0, reference.std(axis=0))
        behaviour = behaviour.astype(np.float32)

        transformed = np.sqrt(counts + 0.375)
        mean = transformed[:train_end].mean(axis=0)
        scale = transformed[:train_end].std(axis=0)
        scale[scale == 0] = 1.0
        state = (transformed - mean) / scale
        basis = np.linalg.svd(state[:train_end], full_matrices=False)[2].T[:, :LATENT]
        latent = (state @ basis).astype(np.float32)

        def valid(lo: int, hi: int) -> np.ndarray:
            rows = np.arange(max(lo, MAX_LAG), min(hi, n_bins - 1))
            return rows[inside[rows]]

        train, dev, test = valid(0, train_end), valid(train_end, dev_end), valid(dev_end, n_bins)
        scorer = NegBinScorer(counts, train, mean, scale)

        n_history = MAX_LAG * (2 * MAX_COEFFICIENT_HARMONIC + 1) * LATENT
        n_forcing = 2 * FORCING_HARMONIC
        n_behaviour = behaviour.shape[1]
        n_features = 1 + n_history + n_forcing + n_behaviour

        history_map: dict = {}
        cursor = 1
        for l in range(MAX_LAG):
            for k in range(MAX_COEFFICIENT_HARMONIC + 1):
                for tag in (("c",) if k == 0 else ("c", "s")):
                    history_map[(l, k, tag)] = (cursor, cursor + LATENT)
                    cursor += LATENT
        forcing_span = (cursor, cursor + n_forcing)
        cursor += n_forcing
        behaviour_span = (cursor, cursor + n_behaviour)

        def build(rows: np.ndarray, angles: np.ndarray, behave: np.ndarray) -> np.ndarray:
            design = np.empty((rows.size, n_features), dtype=np.float32)
            design[:, 0] = 1.0
            angle = angles[rows]
            for l in range(MAX_LAG):
                history = latent[rows - l]
                for k in range(MAX_COEFFICIENT_HARMONIC + 1):
                    if k == 0:
                        lo, hi = history_map[(l, 0, "c")]
                        design[:, lo:hi] = history
                    else:
                        lo, hi = history_map[(l, k, "c")]
                        design[:, lo:hi] = history * np.cos(k * angle)[:, None].astype(np.float32)
                        lo, hi = history_map[(l, k, "s")]
                        design[:, lo:hi] = history * np.sin(k * angle)[:, None].astype(np.float32)
            lo, _ = forcing_span
            for h in range(1, FORCING_HARMONIC + 1):
                design[:, lo + 2 * (h - 1)] = np.cos(h * angle)
                design[:, lo + 2 * (h - 1) + 1] = np.sin(h * angle)
            lo, hi = behaviour_span
            design[:, lo:hi] = behave[rows]
            return design

        def gram_cross(design: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            gram = np.zeros((design.shape[1], design.shape[1]))
            cross = np.zeros((design.shape[1], target.shape[1]))
            for lo in range(0, design.shape[0], CHUNK):
                block = design[lo : lo + CHUNK].astype(np.float64)
                gram += block.T @ block
                cross += block.T @ target[lo : lo + CHUNK]
            return gram, cross

        def columns(lags: int, harmonics: int, forcing: bool, behave: bool) -> np.ndarray:
            selected = [0]
            for l in range(lags):
                for k in range(harmonics + 1):
                    for tag in (("c",) if k == 0 else ("c", "s")):
                        lo, hi = history_map[(l, k, tag)]
                        selected += list(range(lo, hi))
            if forcing:
                selected += list(range(*forcing_span))
            if behave:
                selected += list(range(*behaviour_span))
            return np.array(sorted(selected))

        target_train = state[train + 1]
        design_train = build(train, phase, behaviour)
        gram_full, cross_full = gram_cross(design_train, target_train)
        del design_train

        def solve(gram: np.ndarray, cross: np.ndarray, cols: np.ndarray, lam: float) -> np.ndarray:
            block = gram[np.ix_(cols, cols)] + lam * np.eye(cols.size)
            block[0, 0] -= lam
            return np.linalg.solve(block, cross[cols])

        design_dev = build(dev, phase, behaviour)
        scorer.prepare(counts, dev)

        def sweep(cols: np.ndarray) -> tuple[float, float]:
            projected = design_dev[:, cols]
            best = None
            for lam in RIDGES:
                score = scorer.score(projected @ solve(gram_full, cross_full, cols, lam))
                if best is None or score > best[0]:
                    best = (score, lam)
            return best

        results: dict = {}
        specs = {
            "V1_one_lag_no_theta": {"lags": 1, "harmonics": 0, "forcing": False, "behave": False},
            "V2_plus_forcing": {"lags": 1, "harmonics": 0, "forcing": True, "behave": False},
        }
        for lags in LAG_CHOICES:
            specs[f"V3_lags{lags}"] = {"lags": lags, "harmonics": 0, "forcing": True, "behave": False}
        for name, spec in specs.items():
            cols = columns(**spec)
            score, lam = sweep(cols)
            results[name] = {**spec, "n_features": int(cols.size), "development_loglik": score, "lambda": lam}

        best_lag = max(LAG_CHOICES, key=lambda l: results[f"V3_lags{l}"]["development_loglik"])
        for harmonics in COEFFICIENT_CHOICES:
            spec = {"lags": best_lag, "harmonics": harmonics, "forcing": True, "behave": False}
            cols = columns(**spec)
            score, lam = sweep(cols)
            results[f"V4_harmonics{harmonics}"] = {**spec, "n_features": int(cols.size), "development_loglik": score, "lambda": lam}
        best_harmonic = max(COEFFICIENT_CHOICES, key=lambda k: results[f"V4_harmonics{k}"]["development_loglik"])

        spec = {"lags": best_lag, "harmonics": best_harmonic, "forcing": True, "behave": True}
        cols = columns(**spec)
        score, lam = sweep(cols)
        results["V5_plus_behaviour"] = {**spec, "n_features": int(cols.size), "development_loglik": score, "lambda": lam}

        # Behaviour added to the lag model directly, so that its contribution is not
        # confounded with whatever the base-dependent coefficients cost.
        spec = {"lags": best_lag, "harmonics": 0, "forcing": True, "behave": True}
        cols = columns(**spec)
        score, lam = sweep(cols)
        results["V6_lags_plus_behaviour"] = {**spec, "n_features": int(cols.size), "development_loglik": score, "lambda": lam}
        del design_dev

        design_test = build(test, phase, behaviour)
        scorer.prepare(counts, test)
        rows_store: dict[str, np.ndarray] = {}
        baseline_rows = scorer.rowwise(np.broadcast_to(state[train + 1].mean(axis=0), (test.size, n_units)))
        rows_store["train_mean"] = baseline_rows
        selected_beta = selected_cols = None
        for name, entry in results.items():
            cols = columns(entry["lags"], entry["harmonics"], entry["forcing"], entry["behave"])
            beta = solve(gram_full, cross_full, cols, entry["lambda"])
            rows_store[name] = scorer.rowwise(design_test[:, cols] @ beta)
            entry["test_loglik"] = float(rows_store[name].mean())
            entry["gain_over_train_mean"] = entry["test_loglik"] - float(baseline_rows.mean())
            if name == "V5_plus_behaviour":
                selected_beta, selected_cols = beta, cols
        del design_test, gram_full, cross_full

        shift = int(round(SHIFT_SECONDS / BIN_SECONDS))
        entry = results["V5_plus_behaviour"]
        for control, angles, behave in (
            ("phase_shifted", np.roll(phase, shift), behaviour),
            ("behaviour_shifted", phase, np.roll(behaviour, shift, axis=0)),
        ):
            control_train = build(train, angles, behave)
            gram_c, cross_c = gram_cross(control_train, target_train)
            del control_train
            beta_c = solve(gram_c, cross_c, selected_cols, entry["lambda"])
            del gram_c, cross_c
            control_test = build(test, angles, behave)
            rows_store[control] = scorer.rowwise(control_test[:, selected_cols] @ beta_c)
            del control_test

        block_bins = max(int(round(BLOCK_SECONDS / BIN_SECONDS)), 2)
        order = ["train_mean", "V1_one_lag_no_theta", "V2_plus_forcing",
                 f"V3_lags{best_lag}", f"V4_harmonics{best_harmonic}", "V5_plus_behaviour"]
        comparisons = {}
        for previous, current in zip(order, order[1:]):
            difference = rows_store[current] - rows_store[previous]
            comparisons[f"{current}_minus_{previous}"] = {
                "mean": float(difference.mean()),
                "bootstrap_ci95": block_bootstrap(difference, block_bins, rng),
            }
        for control in ("phase_shifted", "behaviour_shifted"):
            difference = rows_store["V5_plus_behaviour"] - rows_store[control]
            comparisons[f"V5_minus_{control}"] = {
                "mean": float(difference.mean()),
                "bootstrap_ci95": block_bootstrap(difference, block_bins, rng),
            }
        for left, right in (("V6_lags_plus_behaviour", f"V3_lags{best_lag}"),
                            ("V5_plus_behaviour", f"V3_lags{best_lag}"),
                            ("V5_plus_behaviour", "V6_lags_plus_behaviour")):
            difference = rows_store[left] - rows_store[right]
            comparisons[f"{left}_minus_{right}"] = {
                "mean": float(difference.mean()),
                "bootstrap_ci95": block_bootstrap(difference, block_bins, rng),
            }

        position_map = {c: i for i, c in enumerate(selected_cols)}
        lag_blocks, harmonic_blocks = [], []
        for l in range(entry["lags"]):
            lo, hi = history_map[(l, 0, "c")]
            take = [position_map[c] for c in range(lo, hi)]
            lag_blocks.append(basis.T @ selected_beta[take].T)
            per_harmonic = []
            for k in range(1, entry["harmonics"] + 1):
                pair = []
                for tag in ("c", "s"):
                    lo_k, hi_k = history_map[(l, k, tag)]
                    take_k = [position_map[c] for c in range(lo_k, hi_k)]
                    pair.append(basis.T @ selected_beta[take_k].T)
                per_harmonic.append((pair[0], pair[1]))
            harmonic_blocks.append(per_harmonic)
        certificate = cocycle_exponent(lag_blocks, harmonic_blocks, phase[test])

        report = {
            "track": "DEVELOPMENT_ONLY",
            "bin_seconds": BIN_SECONDS,
            "n_units": int(n_units),
            "latent_dimension": LATENT,
            "rows": {"train": int(train.size), "development": int(dev.size), "test": int(test.size)},
            "selected_lags": best_lag,
            "selected_coefficient_harmonics": best_harmonic,
            "variants": results,
            "train_mean_loglik": float(baseline_rows.mean()),
            "controls": {name: float(rows_store[name].mean()) for name in ("phase_shifted", "behaviour_shifted")},
            "comparisons": comparisons,
            "cocycle_certificate": certificate,
            "claim_ceiling": "Development measurement on a consumed asset; not a result about the recording family.",
            "source_receipt": receipt,
        }
        (HERE / "development-cocycle.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
        for name in order:
            if name == "train_mean":
                print(f"  {name:24s} loglik={float(baseline_rows.mean()):.6f}")
            else:
                e = results[name]
                print(f"  {name:24s} feats={e['n_features']:5d} lam={e['lambda']:8g} test={e['test_loglik']:.6f} gain={e['gain_over_train_mean']:+.6f}")
        print(json.dumps(jsonable({"comparisons": comparisons, "certificate": certificate}), indent=2))
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
