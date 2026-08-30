"""Development analysis: the dimension curve and the slowest time constant.

DEVELOPMENT ONLY, on the DANDI 001701 asset that chapters 11 and 12 consumed.

Chapter 16 left two empirical questions that survive corollary 16.1.  This
script measures both on the development asset so that a successor contract can
fix thresholds that are known to be reachable.

Dimension curve.  If the population state lived on a low-dimensional attracting
manifold, held-out likelihood should peak at some modest retained dimension.
The script truncates the fitted one-step operator to its m slowest eigenmodes,
for m from one up to the full dimension, and scores each truncation by held-out
negative-binomial log likelihood on counts.  The location of the maximum is the
measurement.

Time constant.  If the linear description is right, the slowest time constant
tau = -bin / log|lambda| is a property of the process and must not depend on the
bin width used to estimate it.  The script repeats the whole fit at five bin
widths and reports the resulting time constants.
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

BIN_WIDTHS = (0.025, 0.05, 0.1, 0.2, 0.4)
PRIMARY_BIN = 0.1
MIN_TRAIN_RATE_HZ = 0.1
RIDGES = (1e-2, 1e-1, 1.0, 10.0, 1e2, 1e3, 1e4)
DIMENSION_GRID = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256)

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


class NegBinScorer:
    """Held-out negative-binomial scoring of a predicted Anscombe state."""

    def __init__(self, counts: np.ndarray, train_rows: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> None:
        train_counts = counts[train_rows + 1]
        lam = np.maximum(train_counts.mean(axis=0), 1e-6)
        excess = np.mean((train_counts - lam) ** 2 - lam, axis=0)
        alpha = np.maximum(excess / np.maximum(lam ** 2, 1e-12), 1e-6)
        self.size = 1.0 / alpha
        self.mean, self.scale = mean, scale
        self.n_units = counts.shape[1]

    def prepare(self, counts: np.ndarray, rows: np.ndarray) -> None:
        self.target = counts[rows + 1]
        top = int(self.target.max())
        steps = np.log(self.size[None, :] + np.arange(top)[:, None]) if top else np.zeros((0, self.n_units))
        self.ladder = np.vstack((np.zeros((1, self.n_units)), np.cumsum(steps, axis=0)))
        self.log_factorial = np.concatenate(([0.0], np.cumsum(np.log(np.arange(1, top + 1))))) if top else np.array([0.0])
        self.index = self.target.astype(np.int64)

    def score(self, state_prediction: np.ndarray) -> float:
        rate = np.maximum((state_prediction * self.scale + self.mean) ** 2 - 0.375, 1e-6)
        term = (
            np.take_along_axis(self.ladder, self.index, axis=0)
            - self.log_factorial[self.index]
            + self.size * np.log(self.size / (self.size + rate))
            + self.target * np.log(rate / (self.size + rate))
        )
        return float(term.mean())


def pair_safe_dimensions(values: np.ndarray, grid: tuple[int, ...], n_units: int) -> list[int]:
    """Snap each requested dimension up so complex conjugate pairs stay together."""
    order = np.argsort(np.abs(values))[::-1]
    boundaries = []
    index = 0
    while index < order.size:
        k = order[index]
        index += 2 if abs(values[k].imag) > 1e-12 else 1
        boundaries.append(min(index, n_units))
    allowed = sorted(set(boundaries))
    chosen = []
    for m in grid:
        if m > n_units:
            continue
        candidate = next((b for b in allowed if b >= m), None)
        if candidate is not None:
            chosen.append(candidate)
    if n_units not in chosen:
        chosen.append(n_units)
    return sorted(set(chosen))


def analyse(counts: np.ndarray, seconds: float) -> dict:
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
    best = None
    for lam in RIDGES:
        coefficient, offset = ridge(state[train], state[train + 1], lam)
        scorer.prepare(counts, dev)
        score = scorer.score(state[dev] @ coefficient + offset)
        if best is None or score > best[0]:
            best = (score, lam, coefficient, offset)
    dev_score, selected_lambda, operator, offset = best

    r_matrix = operator.T
    values, vectors = np.linalg.eig(r_matrix)
    inverse = np.linalg.inv(vectors)
    order = np.argsort(np.abs(values))[::-1]
    moduli = np.abs(values)[order]
    with np.errstate(divide="ignore"):
        constants = -seconds / np.log(np.maximum(moduli, 1e-300))

    scorer.prepare(counts, dev)
    dev_scores = {}
    scorer_dev_state = state[dev]
    for m in pair_safe_dimensions(values, DIMENSION_GRID, n_units):
        keep = np.zeros(n_units, dtype=complex)
        keep[order[:m]] = values[order[:m]]
        reduced = np.real(vectors @ np.diag(keep) @ inverse)
        dev_scores[m] = scorer.score(scorer_dev_state @ reduced.T + offset)

    scorer.prepare(counts, test)
    test_scores = {}
    baseline = scorer.score(np.broadcast_to(state[train + 1].mean(axis=0), (test.size, n_units)))
    for m in dev_scores:
        keep = np.zeros(n_units, dtype=complex)
        keep[order[:m]] = values[order[:m]]
        reduced = np.real(vectors @ np.diag(keep) @ inverse)
        test_scores[m] = scorer.score(state[test] @ reduced.T + offset)
    full_score = scorer.score(state[test] @ operator + offset)

    best_dev_m = max(dev_scores, key=dev_scores.get)
    return {
        "bin_seconds": seconds,
        "n_bins": int(n_bins),
        "n_units": int(n_units),
        "selected_lambda": selected_lambda,
        "development_loglik": dev_score,
        "mean_count_per_bin": float(counts.mean()),
        "top_moduli": moduli[:10].tolist(),
        "top_time_constants_seconds": constants[:10].tolist(),
        "slowest_time_constant_seconds": float(constants[0]),
        "moduli_above_half": int((moduli > 0.5).sum()),
        "eigenvector_condition": float(np.linalg.cond(vectors)),
        "train_mean_loglik": baseline,
        "full_operator_loglik": full_score,
        "dimension_curve_development": dev_scores,
        "dimension_curve_test": test_scores,
        "development_selected_dimension": best_dev_m,
        "test_loglik_at_selected": test_scores[best_dev_m],
        "argmax_test_dimension": max(test_scores, key=test_scores.get),
    }


def main() -> None:
    path, receipt, temporary = resolve_asset()
    try:
        with h5py.File(path, "r") as nwb:
            lfp = nwb["processing/probe_0_channel_160/LFP/LFP"]
            rate_hz = float(lfp["starting_time"].attrs["rate"])
            start = float(lfp["starting_time"][()])
            stop = start + lfp["data"].shape[0] / rate_hz
            spike_times = nwb["units/spike_times"][:]
            spike_index = nwb["units/spike_times_index"][:]

        starts = np.concatenate(([0], spike_index[:-1]))
        report = {"track": "DEVELOPMENT_ONLY", "window_seconds": [start, stop], "results": {}}
        for seconds in BIN_WIDTHS:
            n_bins = int(math.floor((stop - start) / seconds))
            boundary = start + int(math.floor(0.5 * n_bins)) * seconds
            edges = start + seconds * np.arange(n_bins + 1)
            counts = np.empty((n_bins, spike_index.size))
            prefix = np.empty(spike_index.size)
            for unit, (a, b) in enumerate(zip(starts, spike_index)):
                times = spike_times[a:b]
                counts[:, unit] = np.histogram(times, bins=edges)[0]
                prefix[unit] = np.searchsorted(times, boundary)
            counts = counts[:, (prefix / (boundary - start)) >= MIN_TRAIN_RATE_HZ]
            outcome = analyse(counts, seconds)
            report["results"][f"{seconds:g}s"] = outcome
            print(
                f"{seconds:g}s  lam={outcome['selected_lambda']:g}  |lam|max={outcome['top_moduli'][0]:.4f}"
                f"  tau={outcome['slowest_time_constant_seconds']:.4f}s"
                f"  dev-argmax m={outcome['development_selected_dimension']}"
                f"  test-argmax m={outcome['argmax_test_dimension']} of {outcome['n_units']}",
                flush=True,
            )

        primary = report["results"][f"{PRIMARY_BIN:g}s"]
        constants = [report["results"][f"{s:g}s"]["slowest_time_constant_seconds"] for s in BIN_WIDTHS]
        report["timescale_invariance"] = {
            "bin_widths": list(BIN_WIDTHS),
            "slowest_time_constants": constants,
            "ratio_max_over_min": max(constants) / min(constants),
        }
        report["primary"] = {
            "bin": f"{PRIMARY_BIN:g}s",
            "development_selected_dimension": primary["development_selected_dimension"],
            "n_units": primary["n_units"],
            "fraction_of_full": primary["development_selected_dimension"] / primary["n_units"],
        }
        report["claim_ceiling"] = "Development measurement on a consumed asset; not a result about the recording family."
        report["source_receipt"] = receipt
        (HERE / "development-dimension-timescale.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
        print(json.dumps(jsonable({k: v for k, v in report.items() if k not in ("results", "source_receipt")}), indent=2))
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
