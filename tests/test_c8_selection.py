import numpy as np

from research import c8_1_selection as c8


def synthetic(kind, n=6000, events=120, seed=0):
    """Windows whose direction sits at one of two candidates 90–180° apart (selection) or at their midpoint (blend)."""
    rng = np.random.default_rng(seed)
    owner = np.repeat(np.arange(events), n // events)
    pre = rng.uniform(-np.pi, np.pi, events)[owner]
    head = pre + rng.choice([-1, 1], events)[owner] * rng.uniform(np.pi / 2, np.pi, events)[owner]
    mid = np.angle(np.exp(1j * pre) + np.exp(1j * head))
    center = np.where(rng.random(n) < 0.5, pre, head) if kind == "selection" else mid
    theta = np.where(rng.random(n) < 0.4, center + rng.vonmises(0, 3, n), rng.uniform(-np.pi, np.pi, n))
    return theta, {"pre": pre, "head": head, "mid": mid}, owner


def test_selection_and_blend_are_told_apart():
    s = c8.analyse(*synthetic("selection"), np.random.default_rng(0))
    assert s["selection_margin_p1"] > 0 and s["delta_aic"]["selection"] <= c8.AIC_MARGIN < s["delta_aic"]["blend"]
    b = c8.analyse(*synthetic("blend"), np.random.default_rng(0))
    assert b["selection_margin_p1"] <= 0 and b["delta_aic"]["blend"] <= c8.AIC_MARGIN < b["delta_aic"]["selection"]
