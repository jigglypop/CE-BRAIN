import cefast
import numpy as np

from research import c1_1_common_equation as c11
from research import c1_5_common_equation_v2 as c15


def synthetic(p, events=60, sessions=4, rho=0.5, seed=7):
    """Events simulated by the v2 ring equation itself (another noise seed), with an onset offset and decoding noise."""
    rng = np.random.default_rng(seed)
    lengths = np.full(events, c15.SPAN, np.int64)
    delta = p["sigma0"] * rng.standard_normal(events)
    theta = cefast.ring_trace(delta, lengths, c11.SPAN, p["D"], p["A"], p["tau"], 0.0, c11.BETA, c11.SUBSTEPS, seed)
    kappa = 1.2 if rho == 0.5 else 2.0  # A1(1.2) ≈ 0.5
    turn = rng.uniform(-np.pi, np.pi, events)  # 사건마다 다른 방향(고리 식은 회전에 불변)
    return [{"pre": d + r, "theta": row[:n] + r + rng.vonmises(0, kappa, n), "head": np.nan, "session": i % sessions}
            for i, (row, n, d, r) in enumerate(zip(theta, lengths, delta, turn))]


def test_true_parameters_fit_and_the_trace_is_needed():
    p = {"D": 0.2, "A": 3.0, "tau": 700.0, "sigma0": 0.8}
    data = c15.Data(synthetic(p), np.random.default_rng(0))
    with_trace, _, _ = data.cost(p)
    without, _, _ = data.cost({**p, "A": 0.0})
    assert with_trace / (len(c15.INDEX) - 1) <= 2 < without / (len(c15.INDEX) - 1)
