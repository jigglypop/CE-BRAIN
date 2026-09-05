"""Time/row safety and structural nonidentifiability of common test pulses."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric'
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('electrical_star_tp_calibration',HERE/'electrical_star_tp_calibration.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_common_tp_cannot_separate_series_from_reference_or_gap():
    n=7;time=np.linspace(0,25,501);g=.01*np.eye(n);cap=np.full(n,.1);u=np.full(n,-10.)
    expected=m.step_current(time,g,cap,np.full(n,14.),0,u)
    np.testing.assert_allclose(expected[0],u/14,atol=1e-13)
    np.testing.assert_allclose(m.step_current(time,g,cap,np.full(n,7.),1,u),expected,atol=1e-13)
    edge=np.eye(n)[0]-np.eye(n)[1]
    np.testing.assert_allclose(m.step_current(time,g+.1*np.outer(edge,edge),cap,np.full(n,14.),0,u),expected,atol=1e-13)


def test_tp_pairing_does_not_skip_or_merge_distant_measurements():
    def rows(start):
        first={'EntrySourceType':[1]*9,'TimeStamp':[start-25200]*9,'TimeStampSinceIgorEpochUTC':[start]*9,'TP Peak Resistance':[20]*9}
        second={'EntrySourceType':[1]*9,'TimeStampSinceIgorEpochUTC':[start+.001]*9,'TP Pulse Duration':[None]*8+[10]}
        return first,second
    a,b=rows(100000);c,d=rows(100010)
    records=[dict(row=i,fields=f) for i,f in enumerate([a,b,c,d])]
    assert [p['measurement_row'] for p in m.tp_pairs(records)]==[0,2]
    records[1]['fields']['TimeStampSinceIgorEpochUTC']=[100001]*9
    with pytest.raises(ValueError,match='timestamps'):m.tp_pairs(records)


def test_inserted_estimator_preserves_signed_response_and_units():
    v=np.full(1250,30.);v[375:876]-=100
    r=m.measure_inserted(v,.0075,.01752,-10.)
    np.testing.assert_allclose(r['defined_peak_resistance_MOhm'],100.)
    np.testing.assert_allclose(r['defined_late_resistance_MOhm'],100.)
    assert r['relative_late_change']==0
