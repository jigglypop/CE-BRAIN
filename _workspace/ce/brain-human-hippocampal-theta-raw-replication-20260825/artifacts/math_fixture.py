"""Synthetic-only checks for BA-OBS-HPC1 measurement and estimand semantics.

No dataset paths, files, or real voltage samples are read by this program.
Run:
  .codex/hooks/python.cmd python _workspace/ce/brain-human-hippocampal-theta-raw-replication-20260825/artifacts/math_fixture.py
"""
from __future__ import annotations

import json

import numpy as np
from scipy.signal import butter, sosfiltfilt

FS_HZ = 499.5
DT_MS = 1000.0 / FS_HZ
TIME_MS = np.arange(1000, dtype=float) * DT_MS - 500.0


def closed_mask(lo_ms: float, hi_ms: float) -> np.ndarray:
    return (TIME_MS >= lo_ms) & (TIME_MS <= hi_ms)


def p2p(x: np.ndarray, mask: np.ndarray) -> float:
    return float(np.max(x[mask]) - np.min(x[mask]))


def participant_bootstrap(ts: dict[str, float], pb: dict[str, float], draws: int = 65536):
    """Coupled Bayesian bootstrap: overlap subjects reuse exactly one Exp(1) draw."""
    rng = np.random.Generator(np.random.PCG64(20260825))
    everyone = sorted(set(ts) | set(pb))
    weights = rng.exponential(1.0, size=(draws, len(everyone)))
    lookup = {s: i for i, s in enumerate(everyone)}

    def weighted_arm(values: dict[str, float]) -> np.ndarray:
        names = list(values)
        w = weights[:, [lookup[s] for s in names]]
        v = np.array([values[s] for s in names])
        return (w * v).sum(axis=1) / w.sum(axis=1)

    return weighted_arm(ts) - weighted_arm(pb), weights, lookup


def main() -> None:
    early = closed_mask(15.0, 50.0)
    late = closed_mask(50.0, 250.0)
    prestim = closed_mask(-300.0, -100.0)
    assert np.isclose(DT_MS, 2.002002002002002)
    assert (np.flatnonzero(early)[[0, -1]].tolist(), early.sum()) == ([258, 274], 17)
    assert (np.flatnonzero(late)[[0, -1]].tolist(), late.sum()) == ([275, 374], 100)
    assert (np.flatnonzero(prestim)[[0, -1]].tolist(), prestim.sum()) == ([100, 199], 100)
    assert not np.any(early & late)

    seconds = TIME_MS / 1000.0
    x = 4.0 * np.sin(2 * np.pi * 20 * seconds) + 7.0 * np.cos(2 * np.pi * 60 * seconds)
    design = np.column_stack(
        [np.ones(1000)]
        + [f(2 * np.pi * hz * seconds) for hz in (60, 120, 180) for f in (np.sin, np.cos)]
    )
    cleaned = x - design[:, 1:] @ np.linalg.lstsq(design, x, rcond=None)[0][1:]
    assert abs(np.dot(cleaned, np.cos(2 * np.pi * 60 * seconds))) < 1e-8
    assert np.std(cleaned) > 1.0
    sos = butter(10, 80.0, btype="lowpass", fs=FS_HZ, output="sos")
    filtered = sosfiltfilt(sos, cleaned)
    assert filtered.shape == (1000,) and np.isfinite(filtered).all()

    a = np.zeros(1000)
    b = np.zeros(1000)
    a[300], a[350] = 10.0, -10.0
    b[300], b[350] = -10.0, 10.0
    assert p2p((a + b) / 2.0, late) == 0.0
    assert (p2p(a, late) + p2p(b, late)) / 2.0 == 20.0

    clinical = np.linspace(-3, 5, 1000)
    second = np.linspace(1, -1, 1000)
    assert np.allclose(clinical - second, clinical - second)

    ts = {"p16": 2.0, "p17": 5.0, "p18": 3.0, "p19": 4.0}
    pb = {"p17": 1.0, "p19": 2.0, "p20": 0.0, "UC004": -1.0, "UC005": 1.0}
    draws, weights, lookup = participant_bootstrap(ts, pb)
    assert draws.shape == (65536,)
    assert weights.shape[1] == 7 and {"p17", "p19"} <= set(lookup)
    unweighted_d = np.mean(list(ts.values())) - np.mean(list(pb.values()))
    paired = np.mean([ts["p17"] - pb["p17"], ts["p19"] - pb["p19"]])
    assert np.isclose(unweighted_d, 2.9)
    assert np.isclose(paired, 3.0)

    print(json.dumps({
        "dt_ms": DT_MS,
        "window_indices": {"early": [258, 274, 17], "late": [275, 374, 100], "prestim": [100, 199, 100]},
        "unweighted_primary_fixture": unweighted_d,
        "paired_fixture": paired,
        "coupled_bootstrap_equal_tail": np.quantile(draws, [0.025, 0.975]).tolist(),
        "no_real_voltage_read": True,
    }, indent=2))


if __name__ == "__main__":
    main()
