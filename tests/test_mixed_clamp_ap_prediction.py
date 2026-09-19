import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys'
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('mixed_clamp_ap_prediction',HERE/'mixed_clamp_ap_prediction.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_observed_history_excludes_current_and_future_events():
    assert m.history_at(1.,[0.,1.,2.],.5)==pytest.approx(np.exp(-2))
    assert m.history_at(0.,[0.,1.],.5)==0
    with pytest.raises(ValueError):m.history_at(1.,[np.nan],.5)


def test_causal_kernel_and_peak_normalization():
    t=np.arange(-.01,.1,.00001);k=m.kernel(t,.001,.005)
    assert np.all(k[t<=.001]==0) and np.all(k>=0)
    assert k.max()==pytest.approx(1,abs=1e-5)
    with pytest.raises(ValueError):m.kernel(t,.001,.0001)


def test_split_does_not_train_recovery_or_later_sweeps():
    assert m.cohort(70,7)=='train_initial'
    assert m.cohort(70,8)=='within_sweep_recovery'
    assert m.cohort(74,0)=='later_50Hz'
    assert m.cohort(77,0)=='transport_20Hz'
    assert m.cohort(82,0)=='transport_100Hz'
    assert m.cohort(64,0)=='outside_fitting_cohorts'


def sample_data():
    rng=np.random.default_rng(84);n=12;t=30
    q=rng.normal(size=(n,5));times=np.broadcast_to(np.linspace(.0011,.0069,t),(n,t)).copy()
    return dict(q=q,schedule=np.column_stack((np.tile([0,1],6),np.tile([0.,.6],6))),ta=times,tc=times+.001,
        h={tau:np.tile([0.,np.exp(-.02/tau)],6) for tau in m.TAUS},
        y=2*q[:,0,None]+np.sin(times*90),sweep=np.repeat([69,70,71,72,73,74],2),pulse=np.tile([0,1],6))


def test_training_normalization_has_no_evaluation_statistics():
    x=np.array([[1.],[3.],[1000.]])
    z,norm=m.normalize(x,np.array([True,True,False]))
    assert norm==dict(center=[2.],scale=[1.]) and z[-1,0]==998


def test_held_out_targets_do_not_change_fits_or_selection():
    data=sample_data();candidates=m.configurations('fixed')[:2]
    _,first=m.fit_model(data,candidates,lambdas=(.01,.1))
    data['y'][data['sweep']==74]+=10000
    _,second=m.fit_model(data,candidates,lambdas=(.01,.1))
    assert first==second


def test_missing_training_sweep_is_rejected():
    data=sample_data();data['sweep'][data['sweep']==70]=74
    with pytest.raises(ValueError,match='Training sweep missing'):
        m.fit_model(data,m.configurations('state'))


def test_command_and_ap_kernel_use_same_state_and_samples():
    data=sample_data();train=data['sweep']!=74
    ap=dict(family='fixed',alignment='ap',delay_s=.001,decay_s=.005,shift_s=0.)
    cmd=dict(ap,alignment='command')
    xa,_=m.design(data,train,ap);xc,_=m.design(data,train,cmd)
    assert np.array_equal(xa[:,:,:-1],xc[:,:,:-1])
    assert not np.array_equal(xa[:,:,-1],xc[:,:,-1])


def test_response_support_does_not_pad_or_extrapolate():
    a=np.arange(100.)
    assert len(m.supported_slice(a,0.,.0018))==90
    with pytest.raises(ValueError,match='outside'):m.supported_slice(a,-.001,.001)
