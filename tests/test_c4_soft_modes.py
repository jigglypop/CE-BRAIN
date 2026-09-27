import numpy as np

from research import c4_3_soft_modes as c43


def environment(rng, preferred, jitter=0.0, gain=0.0, fixed=None, minutes=30):
    """Window-level Poisson counts with bump jitter (rad), gain noise, or a fixed-axis log-rate modulation."""
    w = int(minutes * 60 / c43.T)
    angle = np.cumsum(rng.normal(0, 0.15, w)) % (2 * np.pi)
    shifted = angle + jitter * rng.normal(size=w)
    rate = 0.5 + 30 * np.exp(3 * (np.cos(shifted[:, None] - preferred[None, :]) - 1))
    rate *= np.clip(1 + gain * rng.normal(size=w), 0.05, None)[:, None]
    if fixed is not None:
        rate *= np.exp(np.outer(rng.normal(size=w), fixed))
    return c43.session(rng.poisson(rate * c43.T), angle, np.arange(w) * c43.T)


def pair(seed=0, cells=30, **noise):
    """The same cells in two environments; preferred directions rotate coherently by 40°."""
    rng = np.random.default_rng(seed)
    preferred = rng.vonmises(0, 1.5, cells) % (2 * np.pi)
    return environment(rng, preferred, **noise), environment(rng, (preferred + np.radians(40)) % (2 * np.pi), **noise)


def test_soft_modes_transfer_across_environments():
    r = c43.transfer(*pair(jitter=np.radians(12), gain=0.2))
    assert r["soft"] < 0.2 < r["fixed"] and r["cross"] < 0.3
    assert 9 < np.degrees(r["spread"]["position"]) < 15 and 0.12 < r["spread"]["amplitude"] < 0.28


def test_state_independent_noise_does_not_pass_the_reverse_proof():
    for noise in ({"fixed": np.random.default_rng(1).normal(0, 0.3, 30)}, {}):
        assert c43.transfer(*pair(**noise))["fixed"] <= c43.TOL
