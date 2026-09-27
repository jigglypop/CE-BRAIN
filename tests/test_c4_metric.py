import numpy as np

from research import c4_1_metric_hd as c4


def poisson_population(seed=0, cells=30, minutes=30, dt=0.01):
    """Poisson head-direction cells whose preferred directions crowd one side, so g(θ) varies."""
    rng = np.random.default_rng(seed)
    t = np.arange(0, minutes * 60, dt)
    angle = np.cumsum(rng.normal(0, 0.06, len(t))) % (2 * np.pi)
    preferred = rng.vonmises(0, 1.5, cells) % (2 * np.pi)
    rate = 0.5 + 30 * np.exp(3 * (np.cos(angle[:, None] - preferred[None, :]) - 1))
    counts = rng.poisson(rate * dt)
    spikes = [np.repeat(t, counts[:, i]) + rng.uniform(0, dt, counts[:, i].sum()) for i in range(cells)]
    return spikes, t, angle


def test_fisher_metric_recovers_poisson_precision():
    result = c4.evaluate(*c4.windows(*poisson_population()))
    assert result["rms"]["A"] < 0.2 < 0.35 < result["rms"]["B"]
    assert 0.6 < result["scale_A"] < 1.6
