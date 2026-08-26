from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = (
    ROOT
    / "reality_stone"
    / "python"
    / "reality_stone"
    / "clarus"
    / "verified_complete_q_polynomial_factorization.py"
)
SPEC = importlib.util.spec_from_file_location("ce_complete_q_factorization", MODULE)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def _factor(polynomial, **overrides):
    return M.verified_complete_q_polynomial_factorization(
        polynomial,
        maximum_candidate_value_tuples=overrides.get("maximum", 1_000_000),
    )


def test_mixed_quartic_is_split_into_two_irreducible_quadratics() -> None:
    result = _factor((1, 4, 1, -4, 1))
    assert result.validation_level == "VERIFIED_COMPLETE_Q_POLYNOMIAL_FACTORIZATION"
    assert tuple(item.monic_factor for item in result.factors) == (
        (-1, -3, 1),
        (-1, -1, 1),
    )
    assert result.product_reconstruction_verified
    assert result.full_arbitrary_degree_q_factorization_verified


def test_irreducible_quartic_is_proved_by_exhausting_all_factor_degrees() -> None:
    result = _factor((1, 0, 0, 0, 1))
    assert result.validation_level is not None
    assert len(result.factors) == 1
    assert result.factors[0].monic_factor == (1, 0, 0, 0, 1)
    assert [record.trial_factor_degree for record in result.search_records] == [1, 2]
    assert all(record.search_space_exhausted for record in result.search_records)


def test_repeated_irreducible_factor_is_grouped_as_one_primary_factor() -> None:
    result = _factor((1, 0, 3, 0, 3, 0, 1))
    assert result.validation_level is not None
    assert len(result.factors) == 1
    factor = result.factors[0]
    assert factor.monic_factor == (1, 0, 1)
    assert factor.multiplicity == 3
    assert factor.primary_factor == (1, 0, 3, 0, 3, 0, 1)


def test_rational_coefficients_are_primitive_lifted_and_reconstructed() -> None:
    result = _factor((F(-3, 2), F(1, 2), -3, 1))
    assert result.primitive_integer_input == (-3, 1, -6, 2)
    assert tuple(item.monic_factor for item in result.factors) == (
        (-3, 1),
        (F(1, 2), 0, 1),
    )
    assert result.product_reconstruction_verified


def test_degree_eight_irreducible_polynomial_is_supported() -> None:
    result = _factor((1, 0, 0, 0, 0, 0, 0, 0, 1))
    assert result.validation_level is not None
    assert result.factors[0].monic_factor == (1, 0, 0, 0, 0, 0, 0, 0, 1)
    assert result.candidate_value_tuples_examined > 0


def test_linear_polynomial_needs_no_candidate_search() -> None:
    result = _factor((-7, 3))
    assert result.validation_level is not None
    assert result.factors[0].monic_factor == (F(-7, 3), 1)
    assert result.candidate_value_tuples_examined == 0


def test_candidate_budget_fails_closed_before_unexhausted_search() -> None:
    result = _factor((1, 0, 0, 0, 1), maximum=1)
    assert result.status == "Q_FACTORIZATION_CANDIDATE_BUDGET_EXCEEDED"
    assert result.validation_level is None
    assert not result.full_arbitrary_degree_q_factorization_verified
    assert not result.product_reconstruction_verified
    assert result.search_records[-1].search_space_exhausted is False


def test_search_records_carry_points_counts_and_exact_found_factor() -> None:
    result = _factor((1, 4, 1, -4, 1))
    found = [record for record in result.search_records if record.proper_factor_found]
    assert found
    assert all(len(record.interpolation_points) == record.trial_factor_degree + 1 for record in result.search_records)
    assert all(record.candidates_examined <= record.candidate_value_tuples for record in result.search_records)


def test_no_numerical_root_finding_and_gauss_lemma_flags_are_explicit() -> None:
    result = _factor((1, 0, 0, 0, 1))
    assert result.gauss_lemma_applicable
    assert result.kronecker_completeness_verified
    assert not result.numerical_root_finding_used


@pytest.mark.parametrize("bad", [(1,), (0, 0), (1.0, 0, 1), (True, 0, 1)])
def test_input_contract_rejects_constants_zero_and_inexact_coefficients(bad) -> None:
    with pytest.raises(ValueError):
        _factor(bad)


@pytest.mark.parametrize("budget", [0, True, F(3, 2)])
def test_budget_contract_is_strict(budget) -> None:
    with pytest.raises(ValueError, match="positive built-in integer"):
        _factor((1, 0, 1), maximum=budget)
