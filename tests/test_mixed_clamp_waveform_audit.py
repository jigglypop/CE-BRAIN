import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys'
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('mixed_clamp_waveform_audit',HERE/'mixed_clamp_waveform_audit.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_window_keeps_half_open_support_and_refuses_padding():
    assert m.window(np.arange(10),1000,.001,.003)[:2]==(1,3)
    assert m.window(np.arange(10),1000,-.001,.003) is None
    assert m.window(np.arange(10),1000,.008,.011) is None


def test_missing_detector_time_does_not_erase_raw_voltage_excursion():
    source=np.full(100,-.07);source[11:14]=[.02,.01,-.02]
    target=np.zeros(100);target[12:18]=-5e-12
    r=m.measure(source,target,1000,.010,.020,None)
    assert r['raw_reaches_zero_mV'] and r['upward_zero_crossings']==1
    assert r['stored_time_finite'] is False
    assert r['target_post_minus_pre_A']==pytest.approx(-5e-12,abs=1e-24)


def test_next_pulse_caps_source_window_and_tracks_existing_crossing():
    source=np.full(100,-.07);source[10:14]=.02;source[16]=.05
    r=m.measure(source,np.zeros(100),1000,.010,.015,.011)
    assert r['raw_peak_V']==.02 and r['starts_above_zero']
    assert r['upward_zero_crossings']==0 and r['window_stop_s']==.015


def test_command_overlap_uses_half_open_boundaries():
    rows=[dict(start_s=0.,stop_s=1.),dict(start_s=1.,stop_s=2.),dict(start_s=2.,stop_s=3.)]
    assert m.overlaps(1.,2.,rows)==[rows[1]]


@pytest.mark.parametrize('change',['time','amplitude','count'])
def test_command_mismatch_retained_without_fabricated_binding(change):
    pulses=[dict(id=1,pulse_number=0,onset_time=.01,duration=.002,amplitude=1e-9)]
    command=dict(command_intervals=[dict(start_s=.01,duration_s=.002,delta_min=1e-9,delta_max=1e-9)])
    assert m.match_commands(pulses,command,50000)['matches']
    if change=='time':command['command_intervals'][0]['start_s']+=.001
    elif change=='amplitude':command['command_intervals'][0]['delta_min']=5e-10
    else:command['command_intervals']=[]
    assert not m.match_commands(pulses,command,50000)['matches']
