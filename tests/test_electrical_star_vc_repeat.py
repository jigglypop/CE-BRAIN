"""Counterexamples to identifying junctions from repeatable clamp currents."""
import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric'
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('electrical_star_vc_repeat',HERE/'electrical_star_vc_repeat.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_different_intrinsic_circuits_have_the_same_measured_transfer():
    y=np.array([[2.,-.5],[-.5,1.]])
    measured=m.observed_transfer(y,[.2,.3])
    alternative=np.linalg.inv(np.linalg.inv(measured)-np.diag([.1,.1]))
    np.testing.assert_allclose(m.observed_transfer(alternative,[.1,.1]),measured)
    assert np.linalg.eigvalsh(alternative).min()>0
    assert not np.isclose(y[0,1],alternative[0,1])


def test_common_reference_without_junctions_can_pass_repeatability_gate():
    transfer=m.observed_transfer(np.eye(4),np.zeros(4),.5)
    assert transfer[0,1]<0
    time=m.TIME
    pulse=(time>=.0003)&(time<.002)
    waveform=transfer[:,:,None]*pulse
    records=[]
    for sweep in range(10):
        records.append(dict(sweep=sweep,aligned_current_pA=waveform.tolist(),sham_current_pA=(.01*waveform).tolist()))
    result=m.summarize(records)
    assert result['repeatability_necessary_gate']
    assert all(row['models']['repeat']['cross']['rmse_pA']<1e-14 for block in result['blocks'] for row in block['scores'][2:])


def test_local_baseline_is_invariant_to_offset_but_not_time_drift():
    values=np.zeros(2000);values[500:575]=20
    np.testing.assert_allclose(m.center_epoch(values+100),m.center_epoch(values))
    assert np.max(np.abs(m.center_epoch(np.arange(2000))))>1000
