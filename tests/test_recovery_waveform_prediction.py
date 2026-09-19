import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location('waveform',Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys/recovery_waveform_prediction.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_sampled_kernel_matches_explicit_sum_across_causal_boundary():
    left = np.array([-.002,-.000253,-.00001,0.,.00013,.003,.010,.100])
    spikes = np.array([0.,.0023])
    got = module.kernel_basis(left,spikes,.0002,.001,.020)
    delta = left[:,None,None]+np.arange(50)[None,None,:]/100000-spikes[None,:,None]-.0002
    causal = np.maximum(delta,0.)
    brute = ((np.exp(-causal/.020)-np.exp(-causal/.001))*(delta>=0)).mean(axis=2)/module.kernel_norm(.001,.020)
    np.testing.assert_allclose(got,brute,rtol=1e-11,atol=1e-13)


def test_kernel_overlap_retains_history_and_no_future_input():
    times = np.array([0.,.020,.040,.060])
    basis = module.kernel_basis(times,np.array([.010,.030]),.001,.001,.050)
    assert basis[0].sum() == 0 and basis[1,1] == 0
    assert basis[2,0] > 0 and basis[2,1] > 0
    assert basis[2].sum() > basis[2,1]


def test_resource_recovers_and_facilitation_relaxes_with_gap():
    t = np.array([0.,.02,.04,4.])
    q = module.efficacy(t,'depression',.5,.1)
    assert q[2] < q[1] < q[0] and q[-1] == pytest.approx(1.)
    f = module.efficacy(t,'facilitation',.5,.1)
    assert f[2] > f[1] > f[0] and f[-1] == pytest.approx(1.)


def test_affine_fit_recovers_scale_and_does_not_depend_on_zero_weight_outcomes():
    x = np.arange(10.)
    y = 12+3*x
    w = np.r_[np.ones(7),np.zeros(3)]
    a,b,mse = module.fit_affine_basis(x,y,w)
    assert a[0] == pytest.approx(3) and b[0] == pytest.approx(12) and mse[0] < 1e-20
    y[7:] += 1e9
    a2,b2,mse2 = module.fit_affine_basis(x,y,w)
    np.testing.assert_array_equal(a,a2)
    np.testing.assert_array_equal(b,b2)
    np.testing.assert_array_equal(mse,mse2)
    a,b,_ = module.fit_affine_basis(x,-x,np.ones(10))
    assert a[0] == 0 and b[0] == pytest.approx(-4.5)


def test_frequency_phase_matches_complex_transfer_and_group_delay():
    lag,rise,decay,f = .002,.001,.032,50.
    omega = 2*np.pi*f
    h = np.exp(-1j*omega*lag)*(decay/(1+1j*omega*decay)-rise/(1+1j*omega*rise))
    got = module.frequency_response(lag,rise,decay,f)
    assert got['amplitude_over_DC'] == pytest.approx(abs(h)/(decay-rise))
    assert np.exp(1j*np.deg2rad(got['phase_degrees'])) == pytest.approx(h/abs(h))
    step = .001
    derivative = (module.frequency_response(lag,rise,decay,f+step)['phase_degrees']-
                  module.frequency_response(lag,rise,decay,f-step)['phase_degrees'])/360/(2*step)
    assert -derivative*1000 == pytest.approx(got['group_delay_ms'],rel=1e-8)


def test_model_selection_cannot_see_recovery_or_later_sweep_outcomes(monkeypatch):
    import copy
    monkeypatch.setattr(module,'KERNEL_GRID',((1.,1.,16.),(2.,2.,32.)))
    monkeypatch.setattr(module,'HISTORY_GRID',[('constant',0.,1.),('depression',.3,.1)])
    times = np.arange(700)*.0005
    spikes = np.r_[.001+np.arange(8)*.020,.268+np.arange(4)*.020]
    y = 4+20*module.kernel_basis(times,spikes,.001,.001,.016).sum(axis=1)
    records = [dict(sweep=sw,left_times=times,spikes=spikes,y=y.copy(),initial=times<.160)
               for sw in range(37,48)]
    original = module.fit_models(records)
    changed = copy.deepcopy(records)
    for row in changed:
        row['y'][~row['initial']] += 1e9
        if row['sweep'] >= 47:
            row['y'][:] = -1e12
    assert module.fit_models(changed) == original


@pytest.mark.parametrize('rise,decay',[(0.,.01),(.01,.01),(.02,.01)])
def test_invalid_kernel_scales_fail(rise,decay):
    with pytest.raises(ValueError):
        module.kernel_basis(np.arange(3.),np.array([0.]),0.,rise,decay)
