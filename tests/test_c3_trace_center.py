import numpy as np
from scipy.signal import lfilter

from research import c3_5_trace_center as c35


def synthetic(centre, tau=500.0, sessions=6, events=60, history=3000, seed=0):
    """Events whose NREM directions sit near arg h_τ of their own wandering 1 s history ('trace') or near θ_pre ('pre')."""
    rng = np.random.default_rng(seed)
    taus = np.r_[c35.TAUS, tau]
    out = []
    for _ in range(sessions):
        found = []
        for _ in range(events):
            step = rng.normal(0, 0.05, history) + np.where(rng.random(history) < 0.003, rng.uniform(-np.pi, np.pi, history), 0)
            x = np.exp(1j * np.cumsum(step))
            h = np.array([lfilter([1.0], [1.0, -np.exp(-1 / t)], x)[-1] for t in taus])
            pre = np.angle(x[-10:].mean())
            target = np.angle(h[-1]) if centre == "trace" else pre
            theta = np.where(rng.random(100) < 0.3, target + rng.vonmises(0, 2, 100), rng.uniform(-np.pi, np.pi, 100))
            found.append({"m": np.exp(1j * theta).mean(), "pre": pre, "h": h})
        out.append(found)
    return out


def test_integration_time_and_centre_are_recovered():
    r = c35.summarise(c35.analyse(synthetic("trace"), np.random.default_rng(0)))
    assert abs(np.log(r["tau_star"] / 500)) <= np.log(c35.AGREE) and r["gain_p1"] > 0
    assert r["shortfall_trace"] <= c35.SHORTFALL < r["shortfall_pre"]


def test_pre_sleep_centre_gives_no_gain():
    r = c35.summarise(c35.analyse(synthetic("pre"), np.random.default_rng(0)))
    assert r["gain_p1"] < 0 and r["tau_star"] < 100
