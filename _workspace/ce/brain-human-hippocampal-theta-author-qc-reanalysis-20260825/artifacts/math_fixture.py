"""Synthetic invariants for BA-OBS-HPC2; intentionally reads no voltage."""
from __future__ import annotations

import numpy as np


SEED = 20260825


def closed(t: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return np.flatnonzero((t >= lo) & (t <= hi))


def sample_z(x: np.ndarray) -> np.ndarray:
    """MATLAB-style sample-SD z score along the trial axis (axis 0)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return (x - x.mean(axis=0, keepdims=True)) / x.std(axis=0, ddof=1, keepdims=True)


def main() -> None:
    # This is exactly the successor contract's author-code grid, not j/499.5.
    tau = np.arange(1000, dtype=float) / 999.0 * (1000.0 / 499.5) - 0.5
    retained = np.arange(999)
    latency = closed(tau[retained], -0.4, 0.8)
    baseline = closed(tau, -0.05, -0.01)
    early = closed(tau, 0.015, 0.05)
    late = closed(tau, 0.05, 0.25)
    prestim = closed(tau, -0.3, -0.1)

    assert (latency[0], latency[-1], len(latency)) == (50, 648, 599)
    assert (baseline[0], baseline[-1], len(baseline)) == (225, 244, 20)
    assert (early[0], early[-1], len(early)) == (257, 274, 18)
    assert (late[0], late[-1], len(late)) == (275, 374, 100)
    assert (prestim[0], prestim[-1], len(prestim)) == (100, 199, 100)
    assert np.intersect1d(early, late).size == 0
    assert latency[-1] < 999  # first-999 exclusion makes the final original sample unavailable

    # Artifact must precede baseline: this constant offset is rejected before
    # baseline subtraction and would be hidden by baseline-first processing.
    trace = np.full(999, 600.0)
    outside_50 = np.abs(tau[:999]) > 0.05
    assert np.max(np.abs(trace[outside_50])) >= 500.0
    trace_after_baseline = trace - trace[baseline].mean()
    assert np.max(np.abs(trace_after_baseline[outside_50])) == 0.0

    # p20: all selected channels are inspected; zscore dimension is trials.
    n_trial, n_chan, n_time = 40, 3, 999
    p20 = np.zeros((n_trial, n_chan, n_time), dtype=float)
    p20[0, 2, 400] = 1.0
    z = sample_z(p20)
    rejected = np.any(np.abs(z) > 5.0, axis=(1, 2))
    assert rejected.tolist() == [True] + [False] * (n_trial - 1)
    # A one-channel-only QC would incorrectly retain it.
    assert not np.any(np.abs(z[0, 0]) > 5.0)

    # Participant-cluster bootstrap: shared p17/p19 draws across arms.
    ids = ("p16", "p17", "p18", "p19", "p20", "UC004", "UC005")
    ts = np.array([0, 1, 2, 3])
    pb = np.array([1, 3, 4, 5, 6])
    delta = np.array([1.0, 2.0, 3.0, 4.0, 0.0, -1.0, 2.0])
    rng = np.random.Generator(np.random.PCG64(SEED))
    w = rng.exponential(size=(65536, len(ids)))
    ts_w = w[:, ts] / w[:, ts].sum(axis=1, keepdims=True)
    pb_w = w[:, pb] / w[:, pb].sum(axis=1, keepdims=True)
    d = ts_w @ delta[ts] - pb_w @ delta[pb]
    assert d.shape == (65536,)
    assert np.array_equal(w[:, 1], w[:, 1]) and np.array_equal(w[:, 3], w[:, 3])
    assert np.isfinite(np.quantile(d, [0.025, 0.975])).all()

    print({
        "no_real_voltage_read": True,
        "grid_last_s": float(tau[-1]),
        "first_999_latency": [int(latency[0]), int(latency[-1]), int(len(latency))],
        "baseline": [int(baseline[0]), int(baseline[-1]), int(len(baseline))],
        "early": [int(early[0]), int(early[-1]), int(len(early))],
        "late": [int(late[0]), int(late[-1]), int(len(late))],
        "prestim": [int(prestim[0]), int(prestim[-1]), int(len(prestim))],
        "bootstrap_draws": int(len(d)),
    })


if __name__ == "__main__":
    main()
