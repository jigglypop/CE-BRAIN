import numpy as np

from research import c8_2_window_selection as c82


def synthetic(kind, n=40000, events=200, seed=0):
    """Conflict windows of four 0.25 s vectors: anchored at a candidate, background, or a middle excess that is either
    two-and-two between the candidates (selection) or four at the midpoint (blend)."""
    rng = np.random.default_rng(seed)
    owner = rng.integers(0, events, n)
    pre = rng.uniform(-np.pi, np.pi, events)[owner]
    head = pre + rng.choice([-1, 1], events)[owner] * rng.uniform(np.pi / 2, 5 * np.pi / 6, events)[owner]
    mid = np.angle(np.exp(1j * pre) + np.exp(1j * head))
    kind_of = rng.choice(4, n, p=[0.25, 0.08, 0.07, 0.6])  # 과거, 현재, 중간 초과, 배경
    center = np.select([kind_of == 0, kind_of == 1, kind_of == 3],
                       [pre, head, rng.uniform(-np.pi, np.pi, n)], mid)[:, None].repeat(4, 1)
    if kind == "selection":
        split = rng.permuted(np.tile([0, 0, 1, 1], (n, 1)), axis=1).astype(bool)
        center = np.where((kind_of == 2)[:, None], np.where(split, pre[:, None], head[:, None]), center)
    z = rng.gamma(4, 1, (n, 4)) * np.exp(1j * (center + rng.vonmises(0, 4, (n, 4))))
    return z, pre, head, owner


def test_coherence_tells_selection_from_blend():
    s = c82.analyse(*synthetic("selection"), np.random.default_rng(0))
    assert s["excess_p1"] > 0 and abs(np.log(s["Q"] / s["Q_selection"])) <= c82.TOL
    assert s["Q_p99"] <= (s["Q_selection"] + 1) / 2
    b = c82.analyse(*synthetic("blend"), np.random.default_rng(0))
    assert b["excess_p1"] > 0 and abs(np.log(b["Q"])) <= c82.TOL < abs(np.log(b["Q"] / b["Q_selection"]))


def test_bins_do_not_overlap_up_to_150_degrees():
    pre = np.zeros(3)
    head = np.radians([90.0, 120.0, 150.0])
    mid = head / 2
    centers = np.stack([mid, 2 * pre - mid, 2 * head - mid, mid + np.pi, pre, head], 1)
    gaps = np.abs(np.angle(np.exp(1j * (centers[:, :, None] - centers[:, None, :]))))
    assert (gaps[:, ~np.eye(6, dtype=bool)] >= 2 * c82.HALF - 1e-9).all()
