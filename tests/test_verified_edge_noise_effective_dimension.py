from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("verified_edge_metric_effective_dimension", "verified_edge_metric_effective_dimension.py")
N = _load("verified_edge_noise_effective_dimension", "verified_edge_noise_effective_dimension.py")


def _identity(size: int):
    return tuple(tuple(int(i == j) for j in range(size)) for i in range(size))


def _run(**overrides):
    args = dict(
        baseline_metric=_identity(6),
        edge_metric_terms=(_identity(6),),
        lower_edge_weights=(0,),
        upper_edge_weights=(1,),
        forcing_covariance=_identity(6),
        measurement_operator=_identity(6),
        ridge_parameter=F(1, 10),
        candidate_band=(4, 6),
    )
    args.update(overrides)
    return N.verified_edge_noise_effective_dimension(**args)


def test_commuting_fixed_noise_gives_exact_monotone_four_to_six_band() -> None:
    result = _run()
    assert result.pairwise_commutation_verified
    assert result.ridge_dimension_at_lower_weights == F(60, 11)
    assert result.ridge_dimension_at_upper_weights == F(30, 7)
    assert result.commuting_noise_monotonicity_theorem_admitted
    assert result.robust_candidate_band_verified


def test_commuting_derivative_matches_closed_form_at_both_endpoints() -> None:
    result = _run()
    assert result.edge_derivatives_at_lower_weights == (F(-120, 121),)
    assert result.edge_derivatives_at_upper_weights == (F(-60, 49),)


def test_commuting_singular_noise_preserves_observed_hard_rank() -> None:
    forcing = ((1, 0, 0), (0, 0, 0), (0, 0, 2))
    result = _run(
        baseline_metric=_identity(3), edge_metric_terms=(_identity(3),),
        forcing_covariance=forcing, measurement_operator=_identity(3),
        candidate_band=(0, 3),
    )
    assert result.hard_observed_rank_at_lower_weights == 2
    assert result.hard_observed_rank_at_upper_weights == 2
    assert result.hard_rank_invariance_under_commuting_family_verified


def test_zero_forcing_is_exact_equality_case() -> None:
    zero = tuple(tuple(0 for _ in range(2)) for _ in range(2))
    result = _run(
        baseline_metric=_identity(2), edge_metric_terms=(_identity(2),),
        forcing_covariance=zero, measurement_operator=_identity(2),
        candidate_band=(0, 0),
    )
    assert result.ridge_dimension_at_lower_weights == result.ridge_dimension_at_upper_weights == 0
    assert result.edge_derivatives_at_lower_weights == (0,)
    assert result.robust_candidate_band_verified


def test_noncommuting_noise_can_increase_ridge_dimension_when_edge_strengthens() -> None:
    result = _run(
        baseline_metric=((2, 0), (0, 1)),
        edge_metric_terms=(((1, 0), (0, 0)),),
        lower_edge_weights=(0,), upper_edge_weights=(1,),
        forcing_covariance=((1, F(-9, 10)), (F(-9, 10), 1)),
        measurement_operator=((1, 1),), ridge_parameter=1,
        candidate_band=(0, 1),
    )
    assert result.ridge_dimension_at_lower_weights == F(7, 27)
    assert result.ridge_dimension_at_upper_weights == F(23, 68)
    assert result.ridge_dimension_change_upper_minus_lower == F(145, 1836) > 0
    assert result.edge_derivatives_at_lower_weights == (F(80, 729),)
    assert not result.pairwise_commutation_verified
    assert not result.noncommuting_monotonicity_claim_admitted


def test_noncommuting_counterexample_fails_loewner_decrease() -> None:
    result = _run(
        baseline_metric=((2, 0), (0, 1)),
        edge_metric_terms=(((1, 0), (0, 0)),),
        forcing_covariance=((1, F(-9, 10)), (F(-9, 10), 1)),
        lower_edge_weights=(0,), upper_edge_weights=(1,),
        measurement_operator=_identity(2), ridge_parameter=1,
        candidate_band=(0, 2),
    )
    assert not result.response_covariance_loewner_decrease_verified
    assert not result.commuting_noise_monotonicity_theorem_admitted


def test_pairwise_edge_commutation_is_required_not_only_noise_commutation() -> None:
    result = _run(
        baseline_metric=_identity(2),
        edge_metric_terms=(((1, 0), (0, 0)), ((1, 1), (1, 1))),
        lower_edge_weights=(0, 0), upper_edge_weights=(1, 1),
        forcing_covariance=_identity(2), measurement_operator=_identity(2),
        candidate_band=(0, 2),
    )
    assert not result.pairwise_commutation_verified
    assert not result.commuting_noise_monotonicity_theorem_admitted


def test_metric_and_edge_scaling_with_quadratic_noise_scaling_is_covariant() -> None:
    original = _run()
    scaled = _run(
        baseline_metric=tuple(tuple(3 * x for x in row) for row in _identity(6)),
        edge_metric_terms=(tuple(tuple(3 * x for x in row) for row in _identity(6)),),
        forcing_covariance=tuple(tuple(9 * x for x in row) for row in _identity(6)),
    )
    assert scaled.observed_gram_at_lower_weights == original.observed_gram_at_lower_weights
    assert scaled.observed_gram_at_upper_weights == original.observed_gram_at_upper_weights
    assert scaled.ridge_dimension_at_upper_weights == original.ridge_dimension_at_upper_weights


def test_invalid_forcing_covariance_and_inexact_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="positive semidefinite"):
        _run(forcing_covariance=((1, 0), (0, -1)), baseline_metric=_identity(2), edge_metric_terms=(), lower_edge_weights=(), upper_edge_weights=(), measurement_operator=_identity(2))
    with pytest.raises(ValueError, match="exact"):
        _run(ridge_parameter=0.1)
    with pytest.raises(ValueError, match="strengthen"):
        _run(lower_edge_weights=(1,), upper_edge_weights=(0,))


def test_noise_bridge_never_promotes_candidate_band_to_consciousness() -> None:
    result = _run()
    assert result.robust_candidate_band_verified
    assert not result.selected_signal_rank_claim_admitted
    assert not result.consciousness_dimension_claim_admitted
