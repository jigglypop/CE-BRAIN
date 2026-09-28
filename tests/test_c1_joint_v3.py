import numpy as np

from research import c1_5_common_equation_v2 as c15
from research import ring
from tests.test_c1_equation_v2 import synthetic


def test_one_well_depth_with_own_clocks_fits_and_no_trace_does_not():
    truths = [{"D": 0.4, "A": 3.5, "tau": 45.0, "sigma0": 0.8}, {"D": 1.2, "A": 3.5, "tau": 12.0, "sigma0": 1.2}]
    bases = [c15.Data(synthetic(p, events=100, seed=s), np.random.default_rng(0)) for s, p in enumerate(truths, 7)]
    fitted = {"params": truths}
    none = {"params": [{**p, "A": 0.0} for p in truths]}
    assert ring.judged(bases, fitted, 7)["chi2_dof"] <= 2 < ring.judged(bases, none, 4)["chi2_dof"]
