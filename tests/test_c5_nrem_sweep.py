import numpy as np

from research import c1_5_common_equation_v2 as c15
from research import c5_2_nrem_sweep as c52


def test_true_sweep_parameters_fit_their_own_data_and_no_trace_does_not():
    p = {"D": 0.2, "A": 5.0, "tau": 60.0, "sigma0": 0.8, "speed": 3.19, "tau_w": 0.3}
    rng = np.random.default_rng(7)
    n = 150
    offsets = p["sigma0"] * rng.standard_normal(n)
    theta = c52.trajectories(p, np.full(n, c15.SPAN), 9)
    turn = rng.uniform(-np.pi, np.pi, n)
    events = [{"pre": d + t, "theta": row[:c15.SPAN] + t + rng.vonmises(0, 1.2, c15.SPAN), "head": np.nan, "session": i % 5}
              for i, (row, d, t) in enumerate(zip(theta, offsets, turn))]
    base = c15.Data(events, np.random.default_rng(0))
    judge = c52.Sweep(base, 8, 50)
    dof = len(c15.INDEX) - 1
    assert judge.cost(p)[0] / dof <= 2 < judge.cost({**p, "A": 0.0})[0] / dof
