"""Ensure the star predictor is useful without pretending to identify anatomy."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric/electrical_star_structure.py'
spec = importlib.util.spec_from_file_location('electrical_star',PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_cross_only_fit_ignores_held_pairs_and_diagonal_electrode_terms():
    _,z = m.passive_star([1.,1.5,2.,.7],[.3,.7,.4])
    training = z+np.diag([4.,3.,2.,1.])
    for i,j in [(1,3),(3,1),(2,3),(3,2)]:
        training[i,j] = np.nan
    fit = m.predict_unseen_leaf_pairs(training)
    np.testing.assert_allclose(fit['predicted_leaf_ac'],z[1,3],rtol=1e-12)
    np.testing.assert_allclose(fit['predicted_leaf_bc'],z[2,3],rtol=1e-12)
    np.testing.assert_allclose(fit['effective_star_center_parameter'],z[0,0],rtol=1e-12)
    assert not np.isclose(z[1,0]/z[0,0],z[0,1]/z[1,1])  # Ratios can be asymmetric in a reciprocal circuit.


def test_hidden_hub_passes_products_without_identifying_observed_center():
    y = np.eye(5)
    for leaf in range(4):
        edge = np.eye(5)[:,4]-np.eye(5)[:,leaf]
        y += np.outer(edge,edge)
    z = np.linalg.inv(y)[:4,:4]
    np.testing.assert_allclose(z,.5*np.eye(4)+np.ones((4,4))/12,rtol=1e-12)
    fit = m.predict_unseen_leaf_pairs(z)
    np.testing.assert_allclose(fit['effective_star_center_parameter'],1/12,rtol=1e-12)
    assert not np.isclose(fit['effective_star_center_parameter'],z[0,0])
    np.testing.assert_allclose(m.tetrad_products(z),np.full(3,1/144),rtol=1e-12)


def test_additional_leaf_path_changes_star_predictions():
    y,_ = m.passive_star([1.,1.5,2.,.7],[.3,.7,.4])
    edge = np.array([0.,1.,0.,-1.])
    z = np.linalg.inv(y+.4*np.outer(edge,edge))
    fit = m.predict_unseen_leaf_pairs(z)
    assert abs(fit['predicted_leaf_ac']-z[1,3]) > .01
    assert np.ptp(m.tetrad_products(z)) > .001


def test_zero_transfer_does_not_identify_positive_star():
    np.testing.assert_array_equal(m.tetrad_products(np.eye(4)),np.zeros(3))
    with pytest.raises(ValueError,match='Positive finite'):
        m.predict_unseen_leaf_pairs(np.eye(4))
