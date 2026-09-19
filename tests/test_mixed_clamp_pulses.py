from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys'))
import mixed_clamp_pulses as m


def inputs():
    pre=dict(id=1,sync_rec_id=9,clamp_mode='ic',qc_pass=1)
    post=dict(id=2,sync_rec_id=9,clamp_mode='vc',qc_pass=1)
    pulses=[dict(id=n,recording_id=1,cell_id=8,n_spikes=1,first_spike_time=.1*n,qc_pass=1) for n in (10,11,12)]
    responses=[dict(id=n,recording_id=2,pair_id=7,stim_pulse_id=n,ex_qc_pass=1,in_qc_pass=0) for n in (10,11)]
    return pre,post,pulses,responses,dict(id=7,pre_cell_id=8,has_synapse=0)


def test_no_response_and_no_reported_synapse_are_retained():
    result=m.summarize(*inputs())
    assert result['source_pulses']==3 and result['response_rows']==2
    assert result['pulses_without_response']==[12]
    assert result['single_spike_ex_qc_responses']==2
    assert result['response_in_qc_passed']==0


def test_detected_ap_and_recording_pulse_response_qc_are_distinct():
    args=inputs()
    args[2][0]['first_spike_time']=None
    args[2][1]['n_spikes']=2
    result=m.summarize(*args)
    assert result['detected_single_spike_pulses']==1
    assert result['single_spike_ex_qc_responses']==0
    args=inputs();args[0]['qc_pass']=0
    assert m.summarize(*args)['single_spike_ex_qc_responses']==0
    args=inputs();args[2][0]['qc_pass']=0;args[3][1]['ex_qc_pass']=0
    assert m.summarize(*args)['single_spike_ex_qc_responses']==0
    assert not m.detected_single(dict(n_spikes=1,first_spike_time=float('nan')))


def test_null_pulse_cell_and_qc_remain_unknown_with_recording_identity():
    args=inputs()
    for p in args[2]:
        p['cell_id']=None;p['qc_pass']=None
    result=m.summarize(*args)
    assert result['pulse_cell_id_missing']==result['pulse_qc_missing']==3
    assert result['recording_response_qc_single_spikes']==2
    assert result['single_spike_ex_qc_responses']==0
    assert result['single_spike_source_qc_pulses']==0


@pytest.mark.parametrize('problem',['sweep','cell','recording','pair','pulse','duplicate'])
def test_identity_errors_are_not_silently_filtered(problem):
    args=inputs()
    if problem=='sweep':args[1]['sync_rec_id']=10
    elif problem=='cell':args[2][0]['cell_id']=88
    elif problem=='recording':args[3][0]['recording_id']=22
    elif problem=='pair':args[3][0]['pair_id']=77
    elif problem=='pulse':args[3][0]['stim_pulse_id']=999
    else:args[3].append(dict(args[3][0],id=999))
    with pytest.raises(ValueError):m.summarize(*args)
