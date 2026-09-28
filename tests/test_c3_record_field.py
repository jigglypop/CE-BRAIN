import cefast
import numpy as np
from scipy.special import ive

from research import c1_1_common_equation as c11
from research import c1_5_common_equation_v2 as c15
from research import c3_9_record_field as c39


def test_a_gathered_record_gives_the_bump_shaped_well():
    x = np.linspace(-np.pi, np.pi, 361)
    well = ive(0, c11.BETA) + (c39.COEF[:, None] * np.cos(np.arange(1, c39.HARMONICS + 1)[:, None] * x)).sum(0)
    assert np.max(np.abs(well - np.exp(c11.BETA * (np.cos(x) - 1)))) < 1e-3


def test_true_field_parameters_fit_their_own_data_and_no_trace_does_not():
    p = {"D": 0.4, "A": 5.0, "tau": 60.0, "sigma0": 0.8}
    rng = np.random.default_rng(7)
    n = 150
    offsets = p["sigma0"] * rng.standard_normal(n)
    theta = c39.trajectories(p, np.full(n, c15.SPAN), 9)
    turn = rng.uniform(-np.pi, np.pi, n)
    events = [{"pre": d + t, "theta": row[:c15.SPAN] + t + rng.vonmises(0, 1.2, c15.SPAN), "head": np.nan, "session": i % 5}
              for i, (row, d, t) in enumerate(zip(theta, offsets, turn))]
    base = c15.Data(events, np.random.default_rng(0))
    judge = c39.Field(base, 8, 50)
    dof = len(c15.INDEX) - 1
    assert judge.cost(p)[0] / dof <= 2 < judge.cost({**p, "A": 0.0})[0] / dof
