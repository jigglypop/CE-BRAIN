"""탐색 단계 X1·X2b의 계산 검사(자료 없이)."""

import math

import numpy as np

from research import x1_infinite_delta as x1
from research import x2b_fast_teacher_nlms as x2b


def cascade(x, K):
    """Pattern-Jet cascade: u_0 = x, u_k = lowpass_{2^k}(u_{k-1}), Δ_k = u_{k-1} − u_k."""
    prev, out = x.copy(), []
    for k in range(K):
        low = x1.lowpass(prev, 2.0 ** k)
        out.append(prev - low)
        prev = low
    return np.hstack(out)


def test_cascade_deltas_span_the_parallel_deltas():
    """D15: linear readout cannot tell the cascade from parallel lowpass deltas at the same scales."""
    rng = np.random.default_rng(0)
    x = np.cumsum(rng.standard_normal((60, 1)), 0)
    C = cascade(x, 6)
    P = np.hstack([x - x1.lowpass(x, 2.0 ** k) for k in range(6)])
    coef, *_ = np.linalg.lstsq(C, P, rcond=None)
    assert np.abs(C @ coef - P).max() < 1e-8 * np.abs(P).max()


def test_lowpass_matches_its_recursion_and_window_start():
    x = np.arange(12, dtype=float)[:, None]
    y = x1.lowpass(x, 2.0, start=3)
    a = math.exp(-0.5)
    assert np.allclose(y[:4], x[:4]) and np.isclose(y[4, 0], a * 3 + (1 - a) * 4)


def test_infinite_features_converge_with_quadrature():
    rng = np.random.default_rng(1)
    x = rng.standard_normal((40, 2))
    t = np.arange(10, 39)
    k = [x1.features(x, "inf", m, t) for m in (256, 1024)]
    gram = [f @ f.T for f in k]
    assert np.abs(gram[0] - gram[1]).max() < 0.01 * np.abs(gram[1]).max()


def test_delayed_scalar_recursion_follows_the_sine_law():
    """v_{n+1} = v_n − k v_{n−D} is stable iff k < 2 sin(π/(2(2D+1)))."""
    for delay in (0, 1, 2, 4, 8):
        bound = 2 * math.sin(math.pi / (2 * (2 * delay + 1)))
        for k, stable in ((0.97 * bound, True), (1.03 * bound, False)):
            v = [1.0] * (delay + 1)
            for _ in range(4000):
                v.append(v[-1] - k * v[-1 - delay])
            assert (abs(v[-1]) < 1.0) == stable, (delay, k)


def test_nlms_without_delay_is_stable_below_two_and_the_correction_restores_it():
    rng = np.random.default_rng(2)
    Z = np.hstack([np.ones((800, 1)), rng.standard_normal((800, 6))])
    Y = Z[:, 1:3] * 0.5 + 0.1 * rng.standard_normal((800, 2))
    assert not x2b.online(Z, Y, 1.8, 0)[1] and x2b.online(Z, Y, 3.0, 0)[1]  # ε = 1이라 실제 이득은 μ‖φ‖²/(1 + ‖φ‖²)
    assert x2b.limit(Z, Y, 8) < x2b.limit(Z, Y, 0)
    assert x2b.limit(Z, Y, 8, corrected=True) == x2b.limit(Z, Y, 0)
