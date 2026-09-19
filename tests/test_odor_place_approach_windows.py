import importlib.util
from pathlib import Path
import numpy as np
import pytest
PATH=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/odor_place_approach_windows.py'
spec=importlib.util.spec_from_file_location('approach_windows',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_half_open_approach_can_touch_postcue_boundary_without_overlap():
    bounds,reasons=m.temporal_window(dict(choice_time_s=3.,stop_s=2.),(0.,5.),4.)
    assert bounds==(2.5,3.) and reasons==[]
    _,reasons=m.temporal_window(dict(choice_time_s=2.999,stop_s=2.),(0.,5.),4.)
    assert reasons==['overlaps_postcue_or_nosepoke']


def test_unknown_choice_and_outside_task_or_next_trial_remain_failures():
    assert m.temporal_window(dict(choice_time_s=None),(0.,5.),4.)==(None,['unresolved_choice'])
    _,reasons=m.temporal_window(dict(choice_time_s=5.,stop_s=2.),(0.,4.9),4.8)
    assert set(reasons)=={'outside_task_epoch','overlaps_next_nosepoke'}


def test_nonfinite_task_times_are_rejected():
    with pytest.raises(ValueError):m.temporal_window(dict(choice_time_s=3.,stop_s=2.),(0.,np.nan),4.)


def test_actual_position_and_half_open_spikes_exclude_contact_event():
    builder=m.window_builder()
    times=np.array([1.,1.05,1.10,1.15,1.20,1.25,1.30,1.35,1.40,1.45])
    values=np.c_[times,np.zeros(10),np.ones(10)]
    features,support=builder.position_window(times,values,1.,1.5)
    assert features is not None and support['reasons']==[]
    assert builder.count_window(np.array([.9,1.,1.499,1.5,1.6]),1.,1.5)==2
    features,support=builder.position_window(times[[0,9]],values[[0,9]],1.,1.5)
    assert features is None and 'position_gap_over_100ms' in support['reasons']


def test_payload_mutation_is_not_silently_loaded(tmp_path):
    path=tmp_path/'values.bin';np.arange(4,dtype='<f8').tofile(path)
    record=dict(path=str(path),bytes=32,sha256=m.sha(path),dtype_str='<f8',shape=[2,2])
    assert np.array_equal(m.load_values(dict(hdf={'k':record}),'k'),np.arange(4).reshape(2,2))
    np.zeros(4,dtype='<f8').tofile(path)
    with pytest.raises(ValueError):m.load_values(dict(hdf={'k':record}),'k')
