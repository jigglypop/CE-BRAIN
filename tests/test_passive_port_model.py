"""Independent physical ODE and frequency reciprocity checks for passive ports."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.integrate import quad

SOURCE = Path(__file__).resolve().parents[1] / 'verify/Q-NPF-04/fixed_points_metric/passive_port_model.py'
spec = importlib.util.spec_from_file_location('passive_port_model', SOURCE)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def test_two_branch_ic_against_capacitor_state_ode():
    g0, g, tau = .12, np.array([.4, .9]), np.array([.0003, .012])
    amp, on, off, bridge = -50., .01, .02, 12.
    t = np.arange(0, .08, .0001)
    x = np.zeros((len(t), 2))
    total = g0 + g.sum()
    def dynamics(current):
        return lambda _, state: ((current + g @ state) / total - state) / tau
    during = (t >= on) & (t < off)
    after = t >= off
    charge = solve_ivp(dynamics(amp), (on, off), [0., 0.], dense_output=True,
                       rtol=2e-10, atol=1e-11)
    x[during] = charge.sol(t[during]).T
    discharge = solve_ivp(dynamics(0.), (off, t[-1]), charge.y[:, -1], dense_output=True,
                          rtol=2e-10, atol=1e-11)
    x[after] = discharge.sol(t[after]).T
    u = amp * during
    measured = (u + x @ g) / total - bridge * 1e-3 * u
    prediction = model.ic_prediction(t, on, off, amp, g0, g, tau, bridge)
    np.testing.assert_allclose(prediction, measured, atol=2e-8, rtol=1e-9)
    assert np.all(prediction[t < on] == 0)


def test_frequency_inverse_and_dc_resistance_with_zero_branch():
    for conductance in ([.4, .9], [.4, 0.]):
        g0, tau = .12, np.array([.0003, .012])
        modes = model.impedance_modes(g0, conductance, tau)
        s = 2j * np.pi * np.r_[0., np.logspace(-3, 6, 100)]
        y = g0 + np.sum(np.asarray(conductance) * s[:, None] * tau
                        / (1 + s[:, None] * tau), axis=1)
        z = modes['direct_mV_per_pA'] + np.sum(
            modes['resistance_mV_per_pA'] / (1 + s[:, None] * modes['tau_s']), axis=1)
        np.testing.assert_allclose(z * y, 1., atol=2e-13)
        assert np.all(modes['resistance_mV_per_pA'] >= 0)
        assert np.all(modes['tau_s'] > 0)


def test_one_branch_reduces_to_original_series_membrane_rc():
    g0, g1, tau = .7, 2.1, .004
    modes = model.impedance_modes(g0, [g1], [tau])
    np.testing.assert_allclose(modes['direct_mV_per_pA'], 1 / (g0+g1))
    np.testing.assert_allclose(modes['resistance_mV_per_pA'], 1/g0 - 1/(g0+g1))
    np.testing.assert_allclose(modes['tau_s'], tau * (g0+g1) / g0)


def test_nonpassive_and_invalid_parameters_rejected():
    for arguments in [(0., [1.], [.01]), (1., [-1.], [.01]),
                      (1., [1.], [0.]), (1., [np.nan], [.01]), (1., [1., 2.], [.01])]:
        with pytest.raises(ValueError):
            model.impedance_modes(*arguments)


def test_finite_horizon_one_input_reaches_two_distinct_states_at_stated_cost():
    tau = np.array([.004, .017])
    d, horizon, weight = 1 / tau, .03, 2.7
    gramian = model.voltage_control_gramian(tau, horizon, weight)
    numerical = np.array([[quad(lambda s: d[i]*d[j]*np.exp(-(d[i]+d[j])*s)/weight,
                                0, horizon, epsabs=1e-11)[0] for j in range(2)] for i in range(2)])
    np.testing.assert_allclose(gramian, numerical, rtol=2e-13)
    assert np.linalg.eigvalsh(gramian)[0] > 0
    initial, target = np.array([.5, -.2]), np.array([-.3, .8])
    delta = target - np.exp(-d*horizon)*initial
    multiplier = np.linalg.solve(gramian, delta)
    def voltage(t):
        return (d*np.exp(-d*(horizon-t))) @ multiplier / weight
    reached = solve_ivp(lambda t, x: -d*x+d*voltage(t), (0, horizon), initial,
                        rtol=1e-10, atol=1e-11).y[:, -1]
    cost = quad(lambda t: weight*voltage(t)**2, 0, horizon, epsabs=1e-12)[0]
    np.testing.assert_allclose(reached, target, atol=2e-10)
    np.testing.assert_allclose(cost, delta @ multiplier, rtol=1e-12)
    same = model.voltage_control_gramian([.004, .004], horizon, weight)
    assert np.linalg.matrix_rank(same) == 1
