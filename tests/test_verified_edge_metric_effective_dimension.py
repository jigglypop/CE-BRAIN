from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "verified_edge_metric_effective_dimension.py"
SPEC = importlib.util.spec_from_file_location("verified_edge_metric_effective_dimension", MODULE)
assert SPEC and SPEC.loader
E = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = E
SPEC.loader.exec_module(E)


def _identity(size: int):
    return tuple(tuple(int(i == j) for j in range(size)) for i in range(size))


def _run(**overrides):
    args = dict(
        baseline_metric=_identity(6),
        edge_metric_terms=(_identity(6),),
        lower_edge_weights=(0,),
        upper_edge_weights=(1,),
        measurement_operator=_identity(6),
        ridge_parameter=F(1, 10),
        candidate_band=(4, 6),
    )
    args.update(overrides)
    return E.verified_edge_metric_effective_dimension(**args)


def test_uniform_edge_strengthening_certifies_robust_four_to_six_ridge_band() -> None:
    result = _run()
    assert result.ridge_dimension_at_lower_weights == F(60, 11)
    assert result.ridge_dimension_at_upper_weights == 5
    assert result.ridge_dimension_drop == F(5, 11)
    assert result.robust_candidate_band_verified
    assert result.ridge_dimension_monotonicity_verified


def test_hard_observable_rank_is_preserved_by_positive_metric_reweighting() -> None:
    result = _run()
    assert result.measurement_rank == 6
    assert result.hard_rank_at_lower_weights == result.hard_rank_at_upper_weights == 6
    assert result.hard_rank_invariance_verified
    assert not result.selected_signal_rank_claim_admitted


def test_scalar_edge_derivative_matches_closed_form() -> None:
    result = _run(
        baseline_metric=((1,),),
        edge_metric_terms=(((2,),),),
        lower_edge_weights=(0,),
        upper_edge_weights=(1,),
        measurement_operator=((3,),),
        ridge_parameter=F(1, 2),
        candidate_band=(0, 1),
    )
    assert result.edge_derivatives_at_lower_weights == (F(-36, 361),)
    assert result.edge_derivatives_at_lower_weights[0] < 0


def test_zero_edge_term_gives_exact_equality_case() -> None:
    zero = tuple(tuple(0 for _ in range(3)) for _ in range(3))
    result = _run(
        baseline_metric=_identity(3), edge_metric_terms=(zero,),
        lower_edge_weights=(0,), upper_edge_weights=(1,),
        measurement_operator=_identity(3), candidate_band=(0, 3),
    )
    assert result.ridge_dimension_drop == 0
    assert result.edge_derivatives_at_lower_weights == (0,)
    assert result.metric_at_lower_weights == result.metric_at_upper_weights


def test_rectangular_measurement_preserves_its_rank_not_ambient_rank() -> None:
    result = _run(
        baseline_metric=_identity(3),
        edge_metric_terms=(((1, 0, 0), (0, 0, 0), (0, 0, 0)),),
        lower_edge_weights=(0,), upper_edge_weights=(1,),
        measurement_operator=((1, 0, 0), (0, 1, 0)),
        candidate_band=(0, 2),
    )
    assert result.measurement_rank == 2
    assert result.hard_rank_at_lower_weights == result.hard_rank_at_upper_weights == 2


def test_participation_ratio_can_increase_under_edge_strengthening() -> None:
    result = _run(
        baseline_metric=((F(1, 10), 0), (0, 1)),
        edge_metric_terms=(((F(9, 10), 0), (0, 0)),),
        lower_edge_weights=(0,), upper_edge_weights=(1,),
        measurement_operator=_identity(2), candidate_band=(0, 2),
    )
    assert result.participation_ratio_at_lower_weights == F(121, 101)
    assert result.participation_ratio_at_upper_weights == 2
    assert not result.participation_ratio_monotonicity_claim_admitted


def test_participation_ratio_can_decrease_under_edge_strengthening() -> None:
    result = _run(
        baseline_metric=_identity(2),
        edge_metric_terms=(((9, 0), (0, 0)),),
        lower_edge_weights=(0,), upper_edge_weights=(1,),
        measurement_operator=_identity(2), candidate_band=(0, 2),
    )
    assert result.participation_ratio_at_lower_weights == 2
    assert result.participation_ratio_at_upper_weights == F(121, 101)


def test_common_metric_scale_with_inverse_ridge_scale_is_covariant() -> None:
    original = _run()
    scaled = _run(
        baseline_metric=tuple(tuple(7 * item for item in row) for row in _identity(6)),
        edge_metric_terms=(tuple(tuple(7 * item for item in row) for row in _identity(6)),),
        ridge_parameter=F(1, 70),
    )
    assert scaled.ridge_dimension_at_lower_weights == original.ridge_dimension_at_lower_weights
    assert scaled.ridge_dimension_at_upper_weights == original.ridge_dimension_at_upper_weights


def test_invalid_metric_edge_and_weight_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="positive definite"):
        _run(baseline_metric=((1, 0), (0, 0)), edge_metric_terms=(), lower_edge_weights=(), upper_edge_weights=(), measurement_operator=_identity(2))
    with pytest.raises(ValueError, match="positive semidefinite"):
        _run(baseline_metric=_identity(2), edge_metric_terms=(((1, 0), (0, -1)),), lower_edge_weights=(0,), upper_edge_weights=(1,), measurement_operator=_identity(2))
    with pytest.raises(ValueError, match="strengthen"):
        _run(lower_edge_weights=(1,), upper_edge_weights=(0,))


def test_inexact_or_invalid_ridge_and_band_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="exact"):
        _run(ridge_parameter=0.1)
    with pytest.raises(ValueError, match="strictly positive"):
        _run(ridge_parameter=0)
    with pytest.raises(ValueError, match="candidate_band"):
        _run(candidate_band=(6, 4))


def test_four_to_six_band_failure_does_not_become_consciousness_claim() -> None:
    result = _run(
        baseline_metric=_identity(2), edge_metric_terms=(),
        lower_edge_weights=(), upper_edge_weights=(),
        measurement_operator=_identity(2), candidate_band=(4, 6),
    )
    assert not result.robust_candidate_band_verified
    assert not result.consciousness_dimension_claim_admitted
