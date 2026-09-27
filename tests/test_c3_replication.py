import numpy as np

from research import c3_2_trace_replication as c3
from research.store import Session
from tests.test_c3_trace import simulate


def session(**kwargs):
    """The C3-1 simulator in the session format, with its true preferred directions."""
    spikes, states, phi = simulate(**kwargs)
    start, stop, label = map(np.array, zip(*states))
    return Session({"spikes": np.concatenate([np.sort(x) for x in spikes]), "ends": np.cumsum([len(x) for x in spikes]),
                    "states_start": start.astype(float), "states_stop": stop.astype(float),
                    "states_label": label}), phi


def test_trace_is_recovered_through_the_session_format():
    s, phi = session(events=200)
    r = c3.analyse([c3.events(s, phi, "states", "wake", "nrem")], 0)
    assert r["alignment"][0] > r["null_top"] and 40 < r["fits"]["exp"]["params"][1] < 90
    assert r["fits"]["exp"]["chi2_dof"] <= c3.CHI2 < min(r["fits"]["none"]["chi2_dof"], r["fits"]["constant"]["chi2_dof"])


def test_floor_and_no_trace():
    rng = np.random.default_rng(3)
    lags = np.arange(0.5, 480, 1.0)

    def fake(level):
        pre = rng.uniform(0, 2 * np.pi, 300)
        keep = rng.random((300, len(lags))) < level(lags)
        theta = np.where(keep, pre[:, None], rng.uniform(0, 2 * np.pi, (300, len(lags))))
        return [[(p, lags, th) for p, th in zip(pre[i::3], theta[i::3])] for i in range(3)]

    floor = c3.analyse(fake(lambda t: 0.2 * np.exp(-t / 50) + 0.05), 0)["fits"]
    assert floor["exp"]["chi2"] - floor["exp_floor"]["chi2"] > c3.SELECT
    assert 30 < floor["exp_floor"]["params"][1] < 80 and 0.03 < floor["exp_floor"]["params"][2] < 0.07
    none = c3.analyse(fake(lambda t: 0 * t), 0)
    assert none["alignment"][0] <= none["null_top"] or none["fits"]["none"]["chi2_dof"] <= c3.CHI2
