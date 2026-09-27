import numpy as np

from research import c4_2_anisotropic_metric as c42


def population(seed=0, jitter=0.0, gain=0.0, cells=30, minutes=30):
    """Window-level Poisson counts whose bump is shifted by jitter (rad) or scaled by gain noise."""
    rng = np.random.default_rng(seed)
    w = int(minutes * 60 / c42.T)
    angle = np.cumsum(rng.normal(0, 0.15, w)) % (2 * np.pi)
    preferred = rng.vonmises(0, 1.5, cells) % (2 * np.pi)
    shifted = angle + jitter * rng.normal(size=w)
    rate = 0.5 + 30 * np.exp(3 * (np.cos(shifted[:, None] - preferred[None, :]) - 1))
    scale = np.clip(1 + gain * rng.normal(size=w), 0.05, None)
    return rng.poisson(scale[:, None] * rate * c42.T), angle, np.arange(w) * c42.T


def test_jitter_along_the_manifold_is_recovered():
    r = c42.evaluate(*population(jitter=np.radians(15)))
    assert r["rms"]["jitter"] < 0.2 and r["rms"]["jitter"] < r["rms"]["gain"] and r["rms"]["fixed"] > 0.35
    assert 10 < r["sigma_deg"] < 20 and r["cross"] < 0.3


def test_gain_noise_is_not_mistaken_for_jitter():
    r = c42.evaluate(*population(gain=0.3))
    assert r["rms"]["gain"] < r["rms"]["jitter"]


def test_poisson_population_has_no_jitter():
    r = c42.evaluate(*population())
    assert r["sigma_deg"] < 5 and 0.8 < r["a"] < 1.2
