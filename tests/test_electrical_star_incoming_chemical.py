"""Prevent pulse pooling, timing and current-polarity mistakes in repeat scores."""
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric"))
from electrical_star_incoming_chemical import center_epoch, model_templates, score, PRIMARY, SOURCES, TIME_MS
from electrical_star_incoming_variation import expected_mse_ratio


def test_offset_alignment_preserves_onset_baseline_for_both_durations():
    for duration in [75,76]:
        raw=np.ones(2000)*17
        raw[625:1350]+=4
        current,baseline=center_epoch(raw,duration)
        assert baseline==17
        np.testing.assert_allclose(current[PRIMARY],4)
        assert np.sum(current[PRIMARY])*.1==pytest.approx(4*14.5)
        assert TIME_MS[PRIMARY][0]==pytest.approx(.54)


def test_pulse_identity_and_negative_source_remain_separate():
    signal=np.zeros((2,6,12,400))
    for source in range(6):
        for pulse in range(12):
            signal[:,source,pulse,PRIMARY]=(source+1)*(pulse+1)
    models=model_templates(signal,np.zeros_like(signal))
    assert score(signal[0],models["pulse_specific"])["rmse_pA"]==0
    assert score(signal[0],models["pulse_pooled"])["rmse_pA"]>0
    for source in range(6):
        np.testing.assert_array_equal(models["negative_source"][source],signal[0,SOURCES.index(4)])


def test_opposite_current_directions_do_not_cancel_pooled_error():
    observed=np.array([[1.,2.,1.],[-1.,-2.,-1.]])
    assert np.mean(observed)==0
    out=score(observed,np.zeros_like(observed))
    assert out["zero_rmse_pA"]==pytest.approx(np.sqrt(2))
    assert out["rmse_over_zero"]==1
    assert score(observed,observed)["rmse_over_zero"]==0


def test_noise_only_repeat_difference_can_prevent_deterministic_gate():
    from itertools import product
    errors=[];zero_errors=[];cross_moments=[];variations=[]
    for e1,e2,e3 in product([-3.,3.],repeat=3):
        first,second,evaluate=2+e1,2+e2,2+e3
        errors.append((evaluate-(first+second)/2)**2)
        zero_errors.append(evaluate**2)
        cross_moments.append(first*second)
        variations.append((first-second)**2/2)
    assert np.mean(errors)/np.mean(zero_errors)==pytest.approx(expected_mse_ratio(4,9,2))
    assert np.mean(cross_moments)==pytest.approx(4)
    assert np.mean(variations)==pytest.approx(9)
    assert expected_mse_ratio(4,9,2)>.8**2
