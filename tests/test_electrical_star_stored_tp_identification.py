"""Protect numeric channel association and conditional common-input claims."""
import sys
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'verify/Q-NPF-04/fixed_points_metric'))
from electrical_star_stored_tp_consistency import baseline_mapping
from electrical_star_common_step_identifiability import exact_example, step_observables


def test_channel_association_recovers_permutation_and_rejects_ambiguity():
    wave = np.tile([20., 30., 10.], (1250, 1))
    assert baseline_mapping(wave, [0, 2, 7], [10., 20., 30.]) == [2, 7, 0]
    with pytest.raises(ValueError, match='unique permutation'):
        baseline_mapping(wave, [0, 2, 7], [10., 20., 20.])


def test_heterogeneous_common_step_has_unique_physical_reciprocal_solution():
    case = exact_example()
    alpha = case['alpha']
    expected = 3 * (4 * alpha - 3) * (6682 * alpha + 5911) / (80 * alpha * (69 + 28 * alpha) * (23 - 14 * alpha))
    assert sp.simplify(case['skew'] - expected) == 0
    assert case['krylov'].det() != 0
    assert case['admissible_roots'] == [sp.Rational(3, 4)]
    for name in ('E', 'C', 'G'):
        assert case['candidate_' + name].subs(alpha, sp.Rational(3, 4)) == case[name]
    assert case['G'].is_positive_definite


def test_recording_all_channels_does_not_guarantee_all_modes_excited():
    # Adding a gap between identical cells is invisible to their common mode.
    traces = []
    t = sp.Symbol('t', nonnegative=True)
    for gap in (0, 7):
        G = sp.Matrix([[1 + gap, -gap], [-gap, 1 + gap]])
        A, i0, steady, d0 = step_observables(sp.eye(2), sp.eye(2), G)
        assert sp.Matrix.hstack(d0, A * d0).rank() == 1
        traces.append(sp.simplify(steady + (-A * t).exp() * (i0 - steady)))
    assert sp.simplify(traces[0] - traces[1]) == sp.zeros(2, 1)
