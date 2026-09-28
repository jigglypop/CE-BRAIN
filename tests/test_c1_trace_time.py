import numpy as np

from research import c1_4_common_trace_time as c14


def synthetic(tau, bout_mean, events=1500, sessions=6, amplitude=0.2, seed=0):
    """Sessions of (θ_pre, lags, θ) whose alignment decays as amplitude·e^{−t/τ}, with exponential NREM bout lengths."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(sessions):
        found = []
        for _ in range(events // sessions):
            lags = np.arange(int(min(10 + rng.exponential(bout_mean), 480))) + 0.5
            pre = rng.uniform(-np.pi, np.pi)
            theta = np.where(rng.random(len(lags)) < amplitude * np.exp(-lags / tau), pre,
                             rng.uniform(-np.pi, np.pi, len(lags)))
            found.append((pre, lags, theta))
        out.append(found)
    return out


def test_common_tau_is_recovered_across_bout_lengths():
    r = c14.analyse([c14.cohort(synthetic(300, 200, seed=1)), c14.cohort(synthetic(300, 120, 4000, seed=2))])
    assert abs(np.log(r["common"]["tau"][0] / 300)) < np.log(1.5) and r["delta_chi2"] <= c14.COMMON


def test_different_taus_are_told_apart():
    r = c14.analyse([c14.cohort(synthetic(120, 200, seed=1)), c14.cohort(synthetic(600, 200, seed=2))])
    assert r["delta_chi2"] > c14.COMMON


def test_cohort_keeps_the_same_events_at_every_lag():
    s = c14.cohort(synthetic(300, 100, 300))
    assert all(lags[-1] >= c14.SPAN - 1 and lags.max() < c14.SPAN for found in s for _, lags, _ in found)
