import cefast
import numpy as np

from research import c1_1_common_equation as c11
from research import c1_5_common_equation_v2 as c15
from research import ring

SE = np.full(len(c15.INDEX), 0.012)  # 000056 정렬·자기상관 오차의 크기


def old_path(p, offsets, lengths, substeps, seed):
    theta = cefast.ring_trace(offsets, lengths, c11.SPAN, p["D"], p["A"], p["tau"], 0.0, c11.BETA, substeps, seed)
    events = [{"pre": d, "theta": row[:n], "head": d, "session": 0} for row, n, d in zip(theta, lengths, offsets)]
    with np.errstate(invalid="ignore", divide="ignore"):
        return c11.observe(c11.statistics(events), np.ones((1, len(events))))[0]


def test_gentle_well_agrees_with_the_old_euler_path():
    p = {"D": 0.3, "A": 2.5, "tau": 300.0}
    offsets = 0.8 * np.random.default_rng(0).standard_normal(2000)
    lengths = np.full(2000, c15.SPAN, np.int64)
    new = ring.observables(p, offsets, lengths, 3)[c15.INDEX]
    old = old_path(p, offsets, lengths, 200, 4)[c15.INDEX]
    assert np.max(np.abs(new - old) / SE) < 2.5  # 두 모의의 표본 잡음 수준


def test_steep_well_keeps_its_shape_against_a_fine_exact_integration():
    p = {"D": 3.8, "A": 4.0, "tau": 45.0}
    offsets = np.random.default_rng(1).standard_normal(2000)
    lengths = np.full(2000, c15.SPAN, np.int64)
    fine = cefast.ring_observe(offsets, lengths, p["D"], p["A"], p["tau"], c11.BETA, 1600, 5, ring.EDGES, ring.DELTAS, 8, 0)
    k, j = len(ring.EDGES) - 1, len(ring.DELTAS)
    with np.errstate(invalid="ignore", divide="ignore"):
        fine = np.r_[fine[:k] / fine[k:2 * k], fine[2 * k:2 * k + j] / fine[2 * k + j:], np.full(3, np.nan)][c15.INDEX]
    fast = ring.observables(p, offsets, lengths, 6)[c15.INDEX]
    rho = np.sum(fine[:5] * fast[:5]) / np.sum(fast[:5] ** 2)  # 관측 표본 수의 차이는 ρ가 흡수한다
    power = np.r_[np.ones(5), 2 * np.ones(5)]
    assert np.max(np.abs(fine - rho ** power * fast) / SE) < 1.5
