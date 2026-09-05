"""Distinguish physical boundary control, metric covariance, and identification."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric'
spec = importlib.util.spec_from_file_location('open_boundary', HERE/'open_boundary_metric.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_no_direct_edges_still_give_positive_anisotropic_metric():
    example = m.no_direct_edge_example()
    np.testing.assert_allclose(example['Y_eff'], np.eye(4)-np.ones((4, 4))/4)
    np.testing.assert_allclose(example['g'], np.eye(3)+np.ones((3, 3)))
    np.testing.assert_allclose(np.linalg.eigvalsh(example['g']), [1, 1, 4])


def test_nonreciprocal_compensation_power_and_coordinate_law():
    rng = np.random.default_rng(91)
    p = rng.normal(size=(6, 3))
    b, s = rng.normal(size=(6, 6)), rng.normal(size=(6, 6))
    ys = b.T@b+np.eye(6)
    y = ys+3*(s-s.T)
    a, u = np.array([.7, -.3, 1.1]), np.ones(6)
    z = m.compensated_metric(p, y)
    v, i = z['R']@p@a, y@z['R']@p@a
    j = p.T@i
    np.testing.assert_allclose(i.sum(), 0, atol=1e-12)
    np.testing.assert_allclose(z['Y_eff']@u, 0, atol=1e-12)
    np.testing.assert_allclose(u@z['Y_eff'], 0, atol=1e-12)
    np.testing.assert_allclose(z['Y_eff'], z['R'].T@y@z['R'], atol=1e-12)
    np.testing.assert_allclose(v@i, j@z['g']@j, rtol=1e-12)
    np.testing.assert_allclose(z['K'], z['K_minimum_at_fixed_gradient']+
                               z['compensation_excess_at_fixed_gradient'], atol=1e-12)
    assert a@z['compensation_excess_at_fixed_gradient']@a > .01
    vmin = p@a-u*(u@ys@p@a)/(u@ys@u)
    assert abs(u@y@vmin) > .1  # Minimum power does not impose zero total current.
    translated = m.compensated_metric(p+np.array([2., -4., 3.]), y)
    np.testing.assert_allclose(translated['g'], z['g'], rtol=1e-12, atol=1e-12)
    coordinate = np.array([[2., .3, 0.], [.1, 1., .2], [0., -.2, .6]])
    transformed = m.compensated_metric(p@coordinate.T, y)
    inverse = np.linalg.inv(coordinate)
    np.testing.assert_allclose(transformed['g'], inverse.T@z['g']@inverse, atol=1e-12)


def test_same_common_observation_different_metrics_and_individual_responses():
    p = np.vstack((np.zeros(3), np.eye(3), np.array([.2, .3, .4])))
    dv, di = np.full(5, -1.), -np.arange(1., 6.)
    previous = None
    for eta in [0., .1, 1.]:
        y = m.common_mode_family(dv, di, eta)
        np.testing.assert_allclose(y@dv, di, atol=1e-12)
        assert np.linalg.eigvalsh(y)[0] > 0
        z = m.compensated_metric(p, y)
        eigen = np.linalg.eigvalsh((z['Y_eff']+z['Y_eff'].T)/2)
        assert abs(eigen[0]) < 1e-12 and eigen[1] > 0
        assert np.linalg.eigvalsh(z['K'])[0] > 0
        np.testing.assert_allclose(z['g'], np.linalg.inv(z['K']), atol=1e-12)
        if previous is not None:
            assert np.linalg.eigvalsh(previous['g']-z['g'])[0] > 0
            assert np.linalg.norm(y[:, 0]-previous['y'][:, 0]) > .1
        previous = dict(g=z['g'], y=y)
    origin_shift = np.array([2., 0., 0.])
    np.testing.assert_allclose((p+origin_shift).T@di-p.T@di, origin_shift*di.sum())
    assert dv@di > 0  # Common voltage has zero spatial gradient, nonzero boundary cost.


def test_two_state_currents_do_not_determine_conductance_or_reversal():
    voltage, current = np.array([-.070, -.055]), np.array([-1.46e-12, -2.44e-12])
    first = m.conductance_witness(voltage, current, 0.)
    second = m.conductance_witness(voltage, current, .020)
    assert (first > 0).all() and (second > 0).all()
    assert not np.allclose(first, second, rtol=.01, atol=0)
    np.testing.assert_allclose(first*voltage, current, rtol=1e-12, atol=0)
    np.testing.assert_allclose(second*(voltage-.020), current, rtol=1e-12, atol=0)


def test_ineligible_inputs_are_not_regularized_into_brain_metrics():
    p = np.vstack((np.zeros(3), np.eye(3)))
    with pytest.raises(ValueError, match='positive definite'):
        m.compensated_metric(p, -np.eye(4))
    p[:, 2] = 0
    with pytest.raises(ValueError, match='rank'):
        m.compensated_metric(p, np.eye(4))
    with pytest.raises(ValueError, match='common voltage'):
        m.common_mode_family([-1., -2.], [-1., -2.], 0.)
