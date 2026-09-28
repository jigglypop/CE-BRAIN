import cefast
import numpy as np
from scipy.optimize import brentq
from scipy.special import i0e, i1e

from research import c1_1_common_equation as c11
from research import c3_8_record_relocation as c38

V3 = {"D": 0.43, "A": 4.45, "tau": 45.0}
SLOW = {**V3, "tau": 743.0}


def events(p, n=870, seed=1):
    """Data-sized synthetic NREM events from the ring model, rotated per event, with ρ = 0.435 decoding noise."""
    rng = np.random.default_rng(seed)
    lengths = rng.integers(60, 481, n).astype(np.int64)
    theta = cefast.ring_trace(np.zeros(n), lengths, c11.SPAN, p["D"], p["A"], p["tau"], 0.0, c11.BETA, 200, seed)
    kappa = brentq(lambda k: i1e(k) / i0e(k) - 0.435, 0.05, 50)
    thetas = [row[:k] + rng.uniform(-np.pi, np.pi) + rng.vonmises(0, kappa, k) for row, k in zip(theta, lengths)]
    return thetas, np.arange(n) % 20, lengths


def test_single_clock_data_are_told_from_a_slow_clock():
    thetas, group, lengths = events(V3)
    data = c38.curve(thetas, group, np.random.default_rng(0))
    r, se = data["R"][c38.LONG], data["se"][c38.LONG]
    fast, slow = c38.model(V3, 0.435, lengths, 5)[c38.LONG], c38.model(SLOW, 0.435, lengths, 5)[c38.LONG]
    assert data["count"][c38.LONG] >= c38.MIN_EXCURSIONS
    assert abs(r - fast) / se <= c38.Z < abs(r - slow) / se
