import sys
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric'))
from electrical_star_fastrheo_response import channel_quality, predict_if_eligible


def test_early_main_pulse_is_included_and_high_voltage_is_excluded():
    v=np.full(6400,-70.)
    v[1250:1400]=-62.
    quality,response=channel_quality(v)
    assert quality['local_waveform_pass']
    assert np.all(response[:30]==8.)
    v[1300]=0.
    quality,_=channel_quality(v)
    assert not quality['high_voltage_exclusion_pass']
    assert not quality['local_waveform_pass']


def records_for(inputs,split,transfer):
    return [dict(sweep=100+i,split=split,all_seven_quality_pass=True,currents_pA=row.tolist(),
                 response_delta_mV_0p1ms=np.repeat((transfer@row/1000)[:,None],750,axis=1).tolist(),
                 channels=[dict(baseline_rms_mV=.001) for _ in range(7)]) for i,row in enumerate(inputs)]


def test_positive_independent_commands_predict_cross_response():
    transfer=np.eye(7)*100+(np.ones((7,7))-np.eye(7))*5
    train=records_for(np.eye(7)*100,'train',transfer)
    held=records_for(np.eye(7)*150,'held',transfer)
    result=predict_if_eligible(train+held)
    assert result['executed'] and result['waveform_development_gate']
    assert result['scores']['full_rmse_mV']<1e-12
    assert result['scores']['zero_own_zero_rmse_mV']>.7
    assert result['full_seven_input_validation_possible']


def test_held_directions_never_repair_rank_deficient_training():
    transfer=np.eye(7)*100
    train=records_for(np.ones((10,7))*100,'train',transfer)
    held=records_for(np.eye(7)*100,'held',transfer)
    result=predict_if_eligible(train+held)
    assert result['training_design']['rank']==1
    assert result['held_design']['rank']==7
    assert not result['executed']
