import numpy as np

from research import c1_5_common_equation_v2 as c15
from research import ring
from tests.test_c1_equation_v2 import synthetic


def test_single_short_clock_with_a_deep_well_is_fitted_and_not_confused_with_no_trace():
    p = {"D": 1.0, "A": 3.5, "tau": 45.0, "sigma0": 0.8}
    base = c15.Data(synthetic(p, events=120), np.random.default_rng(0))
    judge = ring.Model(base, *ring.JUDGE)
    dof = len(c15.INDEX) - 1
    assert judge.cost(p)[0] / dof <= 2 < judge.cost({**p, "A": 0.0})[0] / dof
