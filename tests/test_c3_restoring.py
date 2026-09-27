import numpy as np

from research import c3_3_restoring as c3


def synthetic(kind, events=400, sessions=4, seed=0, noise=0.8):
    """Events whose NREM direction diffuses freely from θ_pre, or is pulled back to it (OU); the actual head
    is θ_pre plus an offset, so past and present differ."""
    rng = np.random.default_rng(seed)
    lags = np.arange(0.5, 480, 1.0)
    out = [{"events": []} for _ in range(sessions)]
    for i in range(events):
        pre = rng.uniform(0, 2 * np.pi)
        head = pre + rng.normal(0, 1.0)
        x = np.zeros(len(lags))
        for k in range(1, len(lags)):
            target = {"restoring": 0.0, "present": head - pre}.get(kind)
            pull = 0 if target is None else -0.05 * np.angle(np.exp(1j * (x[k - 1] - target)))
            x[k] = x[k - 1] + pull + rng.normal(0, 0.35)
        theta = pre + x + rng.vonmises(0, 1 / noise ** 2, len(lags))
        out[i % sessions]["events"].append({"pre": pre, "lags": lags, "theta": theta, "head": np.full(len(lags), head)})
    return out


def test_free_diffusion_stays_under_the_bound():
    r = c3.analyse(synthetic("free"), np.random.default_rng(1))
    assert r["excess_long_p1"] <= 0 and abs(r["excess_long"]) < 0.02


def test_restoring_exceeds_the_bound_and_past_wins():
    r = c3.analyse(synthetic("restoring"), np.random.default_rng(1))
    assert r["excess_long_p1"] > 0 and r["chi2_free"] > c3.CHI2
    assert r["past_minus_present_p1"] > 0 and r["alpha"][0] > 0.2 and abs(r["beta"][0]) < 0.1


def test_pull_to_the_present_head_is_not_called_past():
    r = c3.analyse(synthetic("present"), np.random.default_rng(1))
    assert r["past_minus_present_p1"] <= 0 and r["beta"][0] > r["alpha"][0]
