import importlib.util
from pathlib import Path
import sys
import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys'
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('mixed_clamp_measurement_state',HERE/'mixed_clamp_measurement_state.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(mode='vc'):
    unit='V' if mode=='vc' else 'A'
    r=dict(id=10,electrode_id=7,stim_meta=dict(type='Offset',args=dict(amplitude=-.055,units=unit),items=[
        dict(type='SquarePulse',args=dict(description='test pulse',amplitude=-.01,start_time=.01,duration=.005))]))
    p=dict(clamp_mode=mode,baseline_potential=-.055,access_adj_baseline_potential=-.045)
    t=dict(id=1,recording_id=10,electrode_id=7,start_index=0,stop_index=20,
        access_resistance_lowpass=1e7,baseline_current=-1e-9)
    c=dict(rate=1000,samples=100,command_intervals=[dict(start_index=10,stop_index=15,start_s=.01,duration_s=.005,delta_min=-.01,delta_max=-.01)])
    return r,p,t,c


def test_vc_baseline_uses_test_pulse_current_and_lowpass_access():
    out=m.diagnose(*fixture())
    assert out['baseline_ir_drop_estimate_V']==pytest.approx(-.045)
    assert out['baseline_ir_drop_formula_residual_V']==pytest.approx(0.)
    assert out['embedded_tp_confirmed']


def test_nearest_tp_from_other_recording_is_not_embedded():
    r,p,t,c=fixture();t['recording_id']=11
    assert not m.diagnose(r,p,t,c)['embedded_tp_confirmed']


def test_ic_has_no_vc_baseline_ir_estimate_and_missing_tp_stays_missing():
    r,p,t,c=fixture('ic');t.update(id=None,access_resistance_lowpass=None)
    out=m.diagnose(r,p,t,c)
    assert out['baseline_ir_drop_estimate_V'] is None and not out['embedded_tp_confirmed']


def test_history_gap_uses_only_completed_past_commands():
    intervals=[dict(stop_s=1.),dict(stop_s=2.)]
    assert m.prior_excursion_gap(.5,intervals) is None
    assert m.prior_excursion_gap(1.5,intervals)==.5


def notebook():
    values=np.full((4,3,9),np.nan)
    values[:,0,0]=64
    values[:,1,0]=[0,np.nan,1,0]
    values[:,2,1]=[0,1,1,0]
    return ['SweepNum','EntrySourceType','RsComp Enable'],values


def test_unclassified_entries_are_retained_without_overriding_acquisition():
    keys,values=notebook()
    settings,selection=m.classified_settings(keys,values,64,1,requested=('RsComp Enable',))
    assert settings['RsComp Enable']==dict(value=0.,raw_row_indices=[0,3])
    assert selection['unclassified_row_indices']==[1]
    assert selection['acquisition_row_indices']==[0,3]


def test_conflicting_classified_acquisition_settings_are_still_rejected():
    keys,values=notebook();values[3,2,1]=1
    with pytest.raises(ValueError,match='Conflicting'):m.classified_settings(keys,values,64,1,requested=('RsComp Enable',))


def test_unknown_entries_cannot_substitute_for_missing_acquisition():
    keys,values=notebook();values[[0,3],1,0]=np.nan
    with pytest.raises(ValueError,match='No explicit acquisition'):m.classified_settings(keys,values,64,1,requested=('RsComp Enable',))
