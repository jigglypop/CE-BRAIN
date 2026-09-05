"""Checks for the filtered RC measurement model, not biological validation."""
import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric'
sys.path.insert(0,str(HERE))
spec = importlib.util.spec_from_file_location('electrical_star_transient',HERE/'electrical_star_transient.py')
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_affine_quotient_removes_only_its_declared_nuisance():
    h = m.kernel((.02,.04))
    np.testing.assert_allclose(m.project(h+73+2*m.TIME),m.project(h),atol=1e-12)
    assert np.linalg.norm(m.project(m.TIME**2))>.1
    assert np.linalg.norm(m.project(h))>.1


def test_equal_and_unequal_poles_match_dense_integration():
    for taus in [(.02,),(.02,.04),(.04,.04)]:
        fine = m.EDGES[:-1,None]+(np.arange(1000)+.5)*.005/1000
        def step(time):
            x = np.maximum(time,0.)
            a = taus[0]
            if len(taus)==1: value = 1-np.exp(-x/a)
            elif a==taus[1]: value = 1-(1+x/a)*np.exp(-x/a)
            else:
                b = taus[1];value = 1-(a*np.exp(-x/a)-b*np.exp(-x/b))/(a-b)
            return value
        expected = (step(fine)-step(fine-1)).mean(axis=1)[m.KEEP]
        np.testing.assert_allclose(m.kernel(taus),expected,atol=2e-9)


def test_training_only_prediction_recovers_planted_response_with_new_drift():
    currents = np.array([[-20,-20],[24,14],[-45,-37]],float)
    v = np.zeros((3,2,2,len(m.TIME)))
    for sweep in range(3):
        for target in range(2):
            for source in range(2):
                h = 8*m.kernel()+100*m.kernel((.04,)) if target==source else 7*m.kernel((.04,.04))
                v[sweep,target,source] = currents[sweep,source]*h/1000+70+sweep+(.3+sweep)*m.TIME
    fitted = m.fit_model(v[:2],currents[:2])
    pred = m.predict(fitted,currents[2],'cascade')
    np.testing.assert_allclose(pred,m.project(v[2]),atol=1e-11)
    np.testing.assert_allclose(fitted['gains_MOhm']['cascade'],[[0,7],[7,0]],atol=1e-9)


def test_drift_only_has_no_inferred_command_gain():
    currents = np.array([[-20,-20],[24,14]],float)
    v = np.zeros((2,2,2,len(m.TIME)))
    v[:] = 65+4*m.TIME
    model = m.fit_model(v,currents)
    np.testing.assert_allclose(model['gains_MOhm']['cascade'],0,atol=1e-8)
