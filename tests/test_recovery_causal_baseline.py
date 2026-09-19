import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('causal_baseline',Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys/recovery_causal_baseline.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    t = np.arange(1100)*module.DT-.1
    spikes = np.r_[.0013+np.arange(8)*.02,.2678+np.arange(4)*.02]
    valid = t>=0
    for spike in spikes:
        valid &= ~((t<spike+.002)&(t+module.DT>spike-.0018))
    return t,spikes,valid


@pytest.mark.parametrize('kind',['local_level','local_trend'])
def test_filter_prefix_invariant_and_missing_values_not_assimilated(kind):
    y = np.sin(np.arange(100)*.1)
    update = np.ones(100,dtype=bool)
    update[50:60] = False
    before = module.filter_values(y,kind,.1,update)[0]
    changed = y.copy()
    changed[50:60] += 1e5
    after = module.filter_values(changed,kind,.1,update)[0]
    np.testing.assert_array_equal(before,after)
    changed[80:] += 1e3
    after = module.filter_values(changed,kind,.1,update)[0]
    np.testing.assert_array_equal(before[:,:80],after[:,:80])


@pytest.mark.parametrize('config',[{'kind':'last_bin'},{'kind':'mean2ms'},
    {'kind':'local_level','ratio':.1},{'kind':'local_trend','ratio':.01}])
def test_forecast_operator_has_no_current_response_leak_and_removes_constant(config):
    t,spikes,valid = fixture()
    m,b,update = module.forecast_operators(t,spikes,valid,config)
    np.testing.assert_allclose((m-b)@np.ones(len(t)),0.,atol=1e-9)
    y = np.sin(t*30)
    before = b@y
    current = m[3]>0
    changed = y.copy()
    changed[current] += 250
    assert (b@changed)[3] == before[3]
    assert ((m-b)@changed)[3]-((m-b)@y)[3] == pytest.approx(250)
    assert not update[current].any()


def test_operator_matches_direct_state_forecast_and_signal_subtraction():
    t,spikes,valid = fixture()
    config = dict(kind='local_trend',ratio=.02)
    m,b,update = module.forecast_operators(t,spikes,valid,config)
    y = 20*np.sin(t*20)
    states,_,_,_ = module.filter_values(y,config['kind'],config['ratio'],update)
    f,_ = module.state_matrices(config['kind'],config['ratio'])
    direct = np.zeros(12)
    for pulse in range(12):
        indices = np.flatnonzero(m[pulse])
        direct[pulse] = np.mean([(f@states[0,k-1])[0] for k in indices])
    np.testing.assert_allclose(b@y,direct,atol=1e-8)
    signal = module.base.kernel_basis(t,spikes,.001,.001,.016).sum(axis=1)
    a = 37.
    np.testing.assert_allclose(m@(y+a*signal)-b@y,b@(a*signal)+(m-b)@(y+a*signal),atol=1e-8)
    # Candidate contribution is transformed by the same M-B operator.
    np.testing.assert_allclose((m-b)@(y-a*signal),(m-b)@y-a*((m-b)@signal),atol=1e-8)


def test_forecast_mean_variance_matches_explicit_joint_covariance():
    kind,ratio = 'local_trend',.03
    f,q = module.state_matrices(kind,ratio)
    offsets = np.array([2,4,5])
    vector,extra = module.future_mean_geometry(kind,ratio,offsets)
    p = np.array([[2.,.1],[.1,.4]])
    covariance = np.zeros((3,3))
    for i,h in enumerate(offsets+1):
        for j,k in enumerate(offsets+1):
            fh,fk = np.linalg.matrix_power(f,int(h)),np.linalg.matrix_power(f,int(k))
            value = (fh@p@fk.T)[0,0]
            for n in range(1,min(h,k)+1):
                value += (np.linalg.matrix_power(f,int(h-n))@q@np.linalg.matrix_power(f,int(k-n)).T)[0,0]
            covariance[i,j] = value+(i==j)
    assert vector@p@vector+extra == pytest.approx(covariance.mean())


def test_efficacy_fit_ignores_recovery_and_later_target_outcomes(monkeypatch):
    monkeypatch.setattr(module.base,'KERNEL_GRID',((1.,1.,16.),))
    monkeypatch.setattr(module.base,'HISTORY_GRID',[('constant',0.,1.),('depression',.3,.1)])
    t,spikes,valid = fixture()
    m,b,_ = module.forecast_operators(t,spikes,valid,{'kind':'last_bin'})
    l=m-b
    signal=module.base.kernel_basis(t,spikes,.001,.001,.016).sum(axis=1)
    rows=[dict(sweep=sw,left_times=t,spikes=spikes,operator=l,innovation=27*(l@signal)) for sw in range(37,48)]
    result=module.fit_efficacy(rows)
    altered=copy.deepcopy(rows)
    for row in altered:
        row['innovation'][8:]+=1e6
        if row['sweep']>=47:
            row['innovation'][:]=-1e9
    assert module.fit_efficacy(altered)==result
    assert result['constant']['amplitude_uV']==pytest.approx(27)
