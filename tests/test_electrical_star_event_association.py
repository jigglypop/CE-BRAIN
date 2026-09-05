"""Synthetic controls for temporal association and circuit sign limits."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'verify/Q-NPF-04/fixed_points_metric'))
from electrical_star_event_association import DT, RELATIVE, gain_fit, remove_quadratic, summary_score


def test_injected_fast_gain_survives_different_quadratic_backgrounds():
    t=RELATIVE*DT
    event=np.exp(-((t-.05)/.07)**2)*2000
    x=remove_quadratic(event+3+5*t+10*t*t)
    target=remove_quadratic(-.02*event-100+2*t-8*t*t)
    gain,error=gain_fit([x],[target],'free')
    assert abs(gain+.02)<1e-12 and error<1e-20
    constrained,_=gain_fit([x],[target],'positive')
    assert constrained==0


def test_training_gain_does_not_guarantee_event_specificity_against_controls():
    x=np.array([0.,1.,2.,1.,0.]); prediction=2*x
    fitted,_=gain_fit([x],[prediction],'free')
    assert fitted==2
    event=summary_score([prediction],[prediction])
    time_locked_control=summary_score([prediction],[prediction])
    assert event['mse_gain_over_zero_pA2']==time_locked_control['mse_gain_over_zero_pA2']


def test_reference_and_direct_gap_have_different_conditional_high_frequency_limits():
    D=np.diag([2.,3.,4.]); C=np.diag([.5,.8,.6])
    G=np.array([[1.,-.1,0.],[-.1,1.2,-.2],[0.,-.2,1.]])
    for reference in [0.,.4]:
        E=D+reference*np.ones((3,3)); inverse=np.linalg.inv(E)
        transfer=-inverse@np.linalg.inv(1e7*C+G+inverse)
        ratios=transfer[:,0]/transfer[0,0]
        np.testing.assert_allclose(ratios,inverse[:,0]/inverse[0,0],atol=1e-7)
        if reference:
            assert (ratios[1:]<0).all()
            q=-ratios[1:]; recovered=q/(1-q.sum())
            np.testing.assert_allclose(recovered,reference/np.diag(D)[1:],atol=1e-7)
        else:
            assert (ratios[1:]>0).all()
