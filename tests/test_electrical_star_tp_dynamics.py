"""Prediction, pulse superposition and derivative-mode counterexamples."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'verify/Q-NPF-04/fixed_points_metric'))
from electrical_star_tp_dynamics import fit_onset, predict, pulse_basis, step_basis
from electrical_star_tp_broadband import broad_step


def test_onset_fit_predicts_unseen_offset_in_a_known_filtered_system():
    time = np.arange(0, 10, .02)
    coefficients = np.array([[40., 60.], [180., 90.], [100., -30.]])
    onset = step_basis(time, [.4, 3.2], .015, .01) @ coefficients
    model = fit_onset(time, onset, np.ones(2), 2)
    future = np.arange(10, 17.5, .02)
    expected = pulse_basis(future, [.4, 3.2], .015, .01) @ coefficients
    assert np.max(np.abs(predict(model, future) - expected)) < 1e-4


def test_pulse_is_difference_of_steps_but_offset_is_not_simple_reversal():
    duration = 2.
    relative = np.array([.1, .4, 1.])
    coefficients = np.array([20., 80.])
    step_now = step_basis(relative, [12.], .02, 0) @ coefficients
    step_later = step_basis(duration + relative, [12.], .02, 0) @ coefficients
    actual = pulse_basis(duration + relative, [12.], .02, 0, duration) @ coefficients
    np.testing.assert_allclose(actual, step_later - step_now)
    step_at_end = (step_basis(np.array([duration]), [12.], .02, 0) @ coefficients)[0]
    assert np.max(np.abs(actual - (step_at_end - step_now))) > 1


def test_raw_rank_two_can_have_only_one_dynamic_mode():
    time = np.linspace(0, 3, 100)
    # E=I,C=diag(1,2),G=diag(1,3), common unit step.
    trace = np.array([.5, .75]) + np.exp(-2 * time[:, None]) * np.array([.5, .25])
    assert np.linalg.matrix_rank(trace) == 2
    assert np.linalg.matrix_rank(np.diff(trace, axis=0), tol=1e-12) == 1


def test_filter_and_transient_coincident_poles_have_finite_analytic_limit():
    time = np.linspace(0, .5, 100)
    tau = .02
    expected = .5 * (time / tau) ** 2 * np.exp(-time / tau)
    np.testing.assert_allclose(broad_step(time, [tau], tau, 0)[:, 1], expected, atol=1e-13)
    for ratio in (1 - 1e-9, 1 + 1e-9):
        np.testing.assert_allclose(broad_step(time, [tau * ratio], tau, 0)[:, 1], expected, atol=1e-8)


def test_broad_filter_agrees_with_original_formula_away_from_coincident_poles():
    time = np.arange(-.1, 10, .02)
    np.testing.assert_allclose(broad_step(time, [.3, 3.], .015, .01),
                               step_basis(time, [.3, 3.], .015, .01), atol=1e-12)
