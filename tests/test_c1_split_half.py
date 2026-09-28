import numpy as np
from scipy.signal import lfilter

from research import c1_10_split_half as c110


def synthetic(slow_share, sessions=8, events=40, length=240, seed=0):
    """Events of (full, half A, half B) directions: a persistent drifting state, a half-dependent bias of the state,
    and independent half noises that are a fast part plus a slow part (φ 0.964 per window) with the given variance share."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(sessions):
        found = []
        for _ in range(events):
            state = rng.uniform(-np.pi, np.pi) + np.cumsum(rng.normal(0, 0.02, length))
            halves = []
            for bias in (0.3, -0.2):
                slow = lfilter([np.sqrt(1 - 0.964 ** 2)], [1, -0.964], rng.standard_normal(length))
                noise = 0.8 * (np.sqrt(slow_share) * slow + np.sqrt(1 - slow_share) * rng.standard_normal(length))
                halves.append(state + bias * np.sin(state) + noise)
            found.append(np.stack([state + rng.normal(0, 0.3, length), *halves], 1))
        out.append(found)
    return out


def test_slow_noise_share_is_told_apart():
    none = c110.analyse(synthetic(0.0), np.random.default_rng(1))["bias_removed"]
    slow = c110.analyse(synthetic(0.41), np.random.default_rng(1))["bias_removed"]
    assert none["C_p99"][c110.KEY] < c110.LIMIT <= slow["C"][c110.KEY]
