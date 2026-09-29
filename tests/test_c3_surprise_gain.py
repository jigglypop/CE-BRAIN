import cefast
import numpy as np
from scipy.optimize import brentq
from scipy.special import i0e, i1e

from research import c1_1_common_equation as c11
from research import c1_5_common_equation_v2 as c15
from research import c3_8_record_relocation as c38
from research import c3_11_surprise_gain as c311
from research import ring
from research.c3_1_sleep_trace import LAGS

V3 = {"D": 0.43, "A": 4.45, "tau": 45.25, "sigma0": 1.0, "lam": 0.0}
GAIN = {**V3, "lam": 0.3}


def test_zero_gain_is_the_old_kernel_bit_for_bit():
    rng = np.random.default_rng(0)
    edges, deltas = LAGS.astype(float), np.asarray(c11.DELTAS, np.int64)
    offsets, lengths = rng.normal(size=40), np.full(40, 240, np.int64)
    for scheme in (0, 1):
        old = cefast.ring_observe(offsets, lengths, 0.43, 4.45, 45.25, c11.BETA, 100, 7, edges, deltas, 1, scheme)
        new = cefast.ring_observe_gain(offsets, lengths, 0.43, 4.45, 45.25, c11.BETA, 100, 7, edges, deltas, 1, scheme, 0.0)
        assert np.array_equal(old, new)
    runs = rng.integers(60, 481, 30).astype(np.int64)
    old = cefast.ring_trace(np.zeros(30), runs, c11.SPAN, 0.43, 4.45, 45.25, 0.0, c11.BETA, 200, 3)
    new = cefast.ring_trace_gain(np.zeros(30), runs, c11.SPAN, 0.43, 4.45, 45.25, 0.0, c11.BETA, 200, 3, 0.0)
    assert np.array_equal(old, new, equal_nan=True)


def test_vectorised_relocation_is_the_paper_code():
    rng = np.random.default_rng(1)
    for _ in range(100):
        th = np.cumsum(rng.normal(0, 0.6, rng.integers(40, 300)))
        centre = np.angle(np.exp(1j * th[:c38.EARLY]).sum())
        run, cos = c311.excursions(th, centre)
        assert [(int(a), float(b)) for a, b in zip(run, cos)] == [(a, float(b)) for a, b in c38.excursions(th, centre)]
    lengths = rng.integers(60, 481, 60)
    paper = c38.model(V3, 0.435, lengths, 5)
    ours, _ = c311.relocation(V3, 0.435, lengths, 5, c38.REPLICAS, 100)
    assert np.allclose(paper, ours, atol=1e-12)


def synthetic(p, n=870, seed=3):
    """Data-sized NREM events of the surprise-gain model: the C1-5 cohort, the C3-8 excursion R and the event lengths."""
    rng = np.random.default_rng(seed)
    lengths = rng.integers(60, 481, n).astype(np.int64)
    steps = int(max(100, np.ceil(p["D"] * c11.BETA * p["A"] / 0.05)))
    theta = cefast.ring_trace_gain(np.zeros(n), lengths, c11.SPAN, p["D"], p["A"], p["tau"], 0.0, c11.BETA, steps, seed, p["lam"])
    kappa = brentq(lambda k: i1e(k) / i0e(k) - 0.435, 0.05, 50)
    turn, offset = rng.uniform(-np.pi, np.pi, n), p["sigma0"] * rng.standard_normal(n)
    thetas = [row[:k] + t + rng.vonmises(0, kappa, k) for row, k, t in zip(theta, lengths, turn)]
    group = np.arange(n) % 20
    events = [{"pre": d + t, "theta": th[:c15.SPAN], "head": np.nan, "session": g}
              for th, d, t, g in zip(thetas, offset, turn, group) if len(th) >= c15.SPAN]
    data = c38.curve(thetas, group, np.random.default_rng(0))
    return c15.Data(events, np.random.default_rng(0)), lengths, np.array(data["R"]), np.array(data["se"])


def test_the_gain_is_told_apart_at_data_size():
    for truth, other in ((V3, GAIN), (GAIN, V3)):
        base, lengths, r, se = synthetic(truth)
        joint = c311.Joint(base, lengths, r, se, (4, 1, 2, 11, 5))
        assert joint.cost(other)[0] - joint.cost(truth)[0] >= c311.NEEDED
    assert ring.SCHEME == 1
