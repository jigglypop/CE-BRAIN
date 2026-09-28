import numpy as np

from research import c1_5_common_equation_v2 as c15
from research import c1_6_common_equation_precise as c16
from tests.test_c1_equation_v2 import synthetic


def test_fresh_noise_keeps_the_true_parameters_and_rejects_no_trace():
    p = {"D": 0.2, "A": 3.0, "tau": 700.0, "sigma0": 0.8}
    base = c15.Data(synthetic(p), np.random.default_rng(0))
    dof = len(c15.INDEX) - 1
    for replicas, seed in (c16.FIT, c16.JUDGE):
        judge = c16.Precise(base, replicas, seed)
        assert judge.cost(p)[0] / dof <= 2 < judge.cost({**p, "A": 0.0})[0] / dof
