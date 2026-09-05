"""Controls against unbalanced chemistry and unsupported geometry inference."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verify/Q-NPF-04/fixed_points_metric"))
from hippocampal_hormone_chemistry import REACTIONS, balance, cost_metric, occupancy, two_receptor_effect


def test_curated_reactions_balance_but_missing_proton_is_detected():
    assert all(balance(r["stoichiometry"])["balanced"] for r in REACTIONS.values())
    broken = dict(REACTIONS["glutamate_decarboxylase"]["stoichiometry"])
    del broken["proton"]
    assert balance(broken) == {"atom_residual": {"H": 1}, "charge_residual": 1, "balanced": False}


def test_equal_equilibrium_does_not_identify_kinetic_response():
    a, b = occupancy(1000., 10., .01, .1), occupancy(1000., 10., .1, 1.)
    assert a == b == .5
    assert occupancy(1., 10., .1, 1.) > 4 * occupancy(1., 10., .01, .1)
    assert occupancy(0., 0., .1, 1., initial=.7) == pytest.approx(.7)
    assert occupancy(10., 0., .1, 1., initial=.7) < .001


def test_distinct_receptor_pools_allow_nonmonotonic_net_effect():
    assert two_receptor_effect(10.) > two_receptor_effect(1.)
    assert two_receptor_effect(10.) > two_receptor_effect(100.)
    assert two_receptor_effect(0.) == 0.


def test_metric_cost_coordinate_change_and_loss_of_spanning():
    edges = np.array([[1., 0., 0.], [1., 1., 0.], [0., 1., 2.], [1., 0., 1.]])
    c = np.array([1., 2., 3., 4.])
    K, g = cost_metric(edges, c)
    gradient = np.array([.2, -.1, .3])
    current_moment = K @ gradient
    assert current_moment @ g @ current_moment == pytest.approx(np.sum(c * (edges @ gradient)**2))
    transform = np.array([[2., .2, 0.], [0., 1., .3], [.1, 0., 3.]])
    _, changed_g = cost_metric(edges @ transform.T, c)
    inverse = np.linalg.inv(transform)
    np.testing.assert_allclose(changed_g, inverse.T @ g @ inverse, atol=1e-14)
    with pytest.raises(ValueError):
        cost_metric(np.eye(3), [1., 1., 0.])
    with pytest.raises(ValueError):
        cost_metric(np.eye(3), [1., 1., -1.])
    _, scaled_g = cost_metric(edges, 3*c)
    np.testing.assert_allclose(scaled_g, g/3)
