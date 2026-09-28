import numpy as np

from research import c4_4_ring_diffusion as c44
from research import c5_3_detailed_balance as c53


def test_turning_runs_follow_the_head_angular_velocity():
    t = np.arange(0, 30, 0.02)
    w = np.where((t > 5) & (t < 8), 2.0, np.where((t > 15) & (t < 17), -2.0, 0.0))  # rad/s
    angle = np.cumsum(w) * 0.02
    runs = c53.turning(t, angle, [(0, 30)])
    (ps, pe), (ns, ne) = runs["positive"], runs["negative"]
    assert len(ps) == 1 and abs(ps[0] - 5) < 0.3 and abs(pe[0] - 8) < 0.3
    assert len(ns) == 1 and abs(ns[0] - 15) < 0.3 and abs(ne[0] - 17) < 0.3


def test_directed_index_changes_sign_with_the_rotation():
    lag = (np.arange(2 * c44.HALF + 1) - c44.HALF) * c44.BIN
    psi = (np.arange(c44.PSI) + 0.5) * 2 * np.pi / c44.PSI

    def correlogram(v):  # 봉우리가 속도 v로 돌면 차 ψ인 쌍은 지연 ψ/v에서 함께 켜진다
        shift = np.angle(np.exp(1j * (psi[:, None] - v * lag[None])))
        return 1 + 5 * np.exp(4 * (np.cos(shift) - 1)) * np.exp(-np.abs(lag)[None] / 0.3)

    expected = np.ones(c44.PSI)
    d = lambda v: np.divide(*c53.directed(correlogram(v), expected))
    assert d(2.0) * d(-2.0) < 0 and abs(d(0.0)) < 1e-9
