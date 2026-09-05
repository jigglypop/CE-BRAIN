import importlib.util
from pathlib import Path
import sys

import numpy as np

MODULE_DIR=Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric"
sys.path.insert(0,str(MODULE_DIR))
spec=importlib.util.spec_from_file_location("periodic_channel_association",MODULE_DIR/"electrical_star_periodic_channel_association.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_command_guard_covers_full_real_and_shifted_windows():
    commands=[(.1,.102)]
    assert not m.clear_of_commands(.13,.15,commands)
    assert m.clear_of_commands(.132,.15,commands)
    assert m.clear_of_commands(.05,.1,commands)
    assert not m.clear_of_commands(.099,.101,commands)


def test_window_center_and_baselines_use_separate_recorded_times():
    raw=np.full((1,7,2250),20.)
    raw[:,:,0:1000]=10.
    raw[:,:,500]=-90.
    raw[:,:,1750]=-180.
    actual,control=m.center_windows(raw,1e-12,0.)
    np.testing.assert_allclose(actual[:,:,500],-200.)
    np.testing.assert_allclose(control[:,:,500],-100.)
    assert np.max(abs(actual[:,:,:350]))<1e-12


def test_concurrent_prediction_and_one_sided_shift_are_distinct():
    actual=np.zeros((4,7,1000));control=np.zeros_like(actual)
    shape=-np.exp(-((m.TIME_MS-.1)/.3)**2)*100
    for e in range(4):
        actual[e,-1]=shape*(e+1)
        for c in range(6):actual[e,c]=actual[e,-1]*(c+1)*.1
    beta=m.coefficients(actual,np.array([True,True,False,False]))
    np.testing.assert_allclose(beta,np.arange(1,7)*.1)
    pred=beta[2]*actual[2:,-1][:,m.PRIMARY]
    real=m.score(actual[2:,2][:,m.PRIMARY],pred)
    shifted=m.score(control[2:,2][:,m.PRIMARY],pred)
    assert real['RMSE_over_zero']<1e-12
    assert real['gain_over_zero_pA2']>0
    assert shifted['gain_over_zero_pA2']<0
    assert shifted['RMSE_over_zero'] is None


def test_derivative_units_and_svd_recover_two_observation_coefficients():
    from electrical_star_periodic_derivative import design,fit
    actual=np.zeros((3,7,1000))
    for event in range(3):actual[event,-1]=(event+1)*(-80*np.exp(-(m.TIME_MS/.4)**2))
    x=design(actual)
    expected=(actual[:,-1,2:]-actual[:,-1,:-2])/.04
    np.testing.assert_allclose(x[...,1],expected[:,np.flatnonzero(m.PRIMARY)-1])
    y=.02*x[...,0]-.003*x[...,1]
    fitted=fit(x[:2],y[:2],[0,1])
    np.testing.assert_allclose(fitted['coefficients'],[.02,-.003],rtol=1e-10,atol=1e-12)
    assert fitted['rank']==2
    np.testing.assert_allclose(x[2]@np.array(fitted['coefficients']),y[2],atol=1e-10)
