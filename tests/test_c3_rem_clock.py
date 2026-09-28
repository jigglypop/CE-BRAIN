import numpy as np

from research import c3_7_rem_clock as c37
from tests.test_c3_wake_overwrite import synthetic


def test_preserving_rem_is_told_from_overwriting_rem():
    kept = c37.analyse(synthetic(743.0), 743.0, np.random.default_rng(0))
    assert kept["preserved_p1"] > 0 and kept["tau_star"] >= 743 / c37.SLOW
    assert kept["shortfall_trace"] <= c37.SHORTFALL < kept["shortfall_reset"]
    erased = c37.analyse(synthetic(20.0), 743.0, np.random.default_rng(0))
    assert erased["tau_star"] < 743 / c37.SLOW and erased["shortfall_trace"] > c37.SHORTFALL
