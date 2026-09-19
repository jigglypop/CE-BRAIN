import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('offset_sensitivity',Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys/recovery_offset_sensitivity.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_anchored_fit_matches_direct_constrained_least_squares():
    x = np.array([0.,.1,.5,1.])
    y = 25*x
    a,mse = module.fit_zero_offset(x,y,np.ones(4))
    assert a[0] == pytest.approx(25) and mse[0] < 1e-20
    a,mse = module.fit_zero_offset(x,-y,np.ones(4))
    assert a[0] == 0 and mse[0] == pytest.approx(np.mean(y*y))


def test_anchoring_cannot_silently_absorb_constant_shift():
    x = np.linspace(0.,1.,11)
    a,_ = module.fit_zero_offset(x,12+3*x,np.ones(11))
    expected = np.dot(x,12+3*x)/np.dot(x,x)
    assert a[0] == pytest.approx(expected) and a[0] != pytest.approx(3)


def test_zero_weight_outcomes_do_not_change_anchor_fit():
    x = np.arange(10.)
    y = x.copy()
    w = np.r_[np.ones(7),np.zeros(3)]
    before = module.fit_zero_offset(x,y,w)
    y[7:] += 1e9
    after = module.fit_zero_offset(x,y,w)
    np.testing.assert_array_equal(before[0],after[0])
    np.testing.assert_array_equal(before[1],after[1])
