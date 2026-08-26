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


_load("verified_rational_contour", "verified_rational_contour.py")
_load("verified_interval_contour", "verified_interval_contour.py")
_load("verified_interval_tightening", "verified_interval_tightening.py")
_load("verified_interval_residual", "verified_interval_residual.py")
_load("verified_algebraic_riesz_projector", "verified_algebraic_riesz_projector.py")
_load("verified_polynomial_spectral_projector_construction", "verified_polynomial_spectral_projector_construction.py")
_load("verified_complete_q_polynomial_factorization", "verified_complete_q_polynomial_factorization.py")
M = _load("ce_verified_characteristic_split", "verified_characteristic_spectral_split_discovery.py")


def _discover(matrix=((0, 0), (0, 4)), **overrides):
    values = dict(
        center=0,
        radius=2,
        spectral_reference_scale=1,
        maximum_partitions=1024,
        maximum_factor_candidate_value_tuples=1_000_000,
        sqrt_precision=48,
    )
    values.update(overrides)
    return M.verified_characteristic_spectral_split_discovery(matrix, **values)


def test_diagonal_rational_spectrum_is_fully_discovered_and_classified() -> None:
    result = _discover()
    assert result.validation_level == "VERIFIED_CHARACTERISTIC_SPECTRAL_SPLIT_AND_PROJECTOR_DISCOVERED"
    assert result.characteristic_polynomial == (0, -4, 1)
    assert result.cayley_hamilton_verified
    assert tuple((item.root, item.multiplicity) for item in result.rational_root_factors) == (
        (F(0), 1),
        (F(4), 1),
    )
    assert result.complete_q_factorization_verified
    assert result.projector_rank == 1
    assert result.selected_construction is not None


def test_defective_repeated_rational_root_is_grouped_as_one_primary_atom() -> None:
    matrix = ((0, 1, 0), (0, 0, 0), (0, 0, 4))
    result = _discover(matrix)
    assert result.validation_level is not None
    zero = next(item for item in result.rational_root_factors if item.root == 0)
    assert zero.multiplicity == 2
    assert zero.factor == (0, 0, 1)
    assert result.projector_rank == 2


def test_irreducible_quadratic_sqrt_two_factor_is_automatically_proved() -> None:
    matrix = ((0, 2, 0), (1, 0, 0), (0, 0, 4))
    result = _discover(matrix, radius=3)
    assert result.validation_level is not None
    assert result.residual_factor == (-2, 0, 1)
    assert result.residual_degree == 2
    assert result.residual_irreducible_over_q_verified
    assert result.characteristic_factorization_automatically_discovered
    assert result.projector_rank == 2


def test_full_rank_and_zero_rank_partitions_use_coprime_dummy_factor() -> None:
    full = _discover(((0,),))
    assert full.validation_level is not None
    assert full.projector_rank == 1
    zero = _discover(((4,),))
    assert zero.validation_level is not None
    assert zero.projector_rank == 0


def test_raw_scale_covariance_preserves_normalized_characteristic_and_rank() -> None:
    base = _discover()
    scaled = _discover(
        ((0, 0), (0, 28)),
        radius=14,
        spectral_reference_scale=7,
    )
    assert scaled.characteristic_polynomial == base.characteristic_polynomial
    assert scaled.selected_inside_factor == base.selected_inside_factor
    assert scaled.projector_rank == base.projector_rank


def test_spectral_value_on_contour_has_no_strict_partition() -> None:
    result = _discover(((2,),))
    assert result.status == "CHARACTERISTIC_NO_CERTIFIED_INSIDE_OUTSIDE_PARTITION"
    assert result.selected_construction is None


def test_mixed_quartic_is_fully_factored_but_straddling_atom_fails_honestly() -> None:
    matrix = (
        (0, 1, 0, 0),
        (1, 1, 0, 0),
        (0, 0, 0, 1),
        (0, 0, 1, 3),
    )
    result = _discover(matrix, radius=2)
    assert result.residual_degree == 4
    assert result.complete_q_factorization_verified
    assert result.full_arbitrary_degree_q_factorization_verified
    assert len(result.atomic_factors) == 2
    assert result.status == "CHARACTERISTIC_NO_CERTIFIED_INSIDE_OUTSIDE_PARTITION"


def _companion(coefficients):
    degree = len(coefficients) - 1
    result = [[F(0) for _ in range(degree)] for _ in range(degree)]
    for row in range(1, degree):
        result[row][row - 1] = F(1)
    for row in range(degree):
        result[row][-1] = -F(coefficients[row])
    return tuple(tuple(row) for row in result)


def _block_diagonal(left, right):
    m, n = len(left), len(right)
    return tuple(
        tuple(
            left[i][j] if i < m and j < m
            else right[i - m][j - m] if i >= m and j >= m
            else F(0)
            for j in range(m + n)
        )
        for i in range(m + n)
    )


def _scaled_quartic_cycle(scale):
    scale = F(scale)
    return (
        (0, 0, 0, -scale),
        (scale, 0, 0, 0),
        (0, scale, 0, 0),
        (0, 0, scale, 0),
    )


def test_two_irreducible_quartic_atoms_are_split_and_projected_without_roots() -> None:
    inside = _scaled_quartic_cycle(1)
    outside = _scaled_quartic_cycle(3)
    result = _discover(_block_diagonal(inside, outside), radius=2)
    assert result.validation_level is not None
    assert tuple(len(factor) - 1 for factor in result.atomic_factors) == (4, 4)
    assert result.projector_rank == 4
    assert result.full_arbitrary_degree_q_factorization_verified


def test_q_factorization_budget_is_explicit_and_fails_before_partitions() -> None:
    result = _discover(
        _companion((1, 0, 0, 0, 1)),
        maximum_factor_candidate_value_tuples=1,
    )
    assert result.status == "CHARACTERISTIC_Q_FACTORIZATION_BUDGET_EXCEEDED"
    assert result.partitions_evaluated == 0
    assert not result.complete_q_factorization_verified


def test_partition_budget_is_explicit_and_fail_closed() -> None:
    matrix = tuple(
        tuple(F(i) if i == j else F(0) for j in range(5))
        for i in range(5)
    )
    result = _discover(matrix, radius=F(5, 2), maximum_partitions=8)
    assert result.status == "CHARACTERISTIC_FACTOR_PARTITION_BUDGET_EXCEEDED"
    assert result.partitions_evaluated == 0
    assert len(result.atomic_factors) == 5


def test_complex_rational_nonreal_center_is_shifted_to_zero_exactly() -> None:
    result = _discover(
        (((0, 1), 0), (0, (0, 3))),
        center=(0, 1),
        radius=1,
    )
    assert result.validation_level is not None
    assert result.characteristic_polynomial == (0, 0, 4, 0, 1)
    assert result.projector_rank == 1
    assert result.center_shift_to_zero_verified
    assert result.characteristic_variable_center == M.ZERO
    with pytest.raises(ValueError, match="at least two"):
        _discover(maximum_partitions=1)


def test_gaussian_rational_diagonal_matrix_uses_real_envelope_and_complex_rank() -> None:
    matrix = (((0, 1), 0), (0, (0, 3)))
    result = _discover(matrix, radius=2)
    assert result.validation_level is not None
    assert result.characteristic_polynomial == (9, 0, 10, 0, 1)
    assert result.atomic_factors == ((1, 0, 1), (9, 0, 1))
    assert result.projector_rank == 1
    assert result.complex_rational_input_processed
    assert result.realification_characteristic_envelope_used
    assert result.projector_rank_convention == "COMPLEX_RANK_OF_ORIGINAL_MATRIX"


def test_gaussian_rational_defective_primary_atom_preserves_complex_multiplicity() -> None:
    matrix = (
        ((0, 1), 1, 0),
        (0, (0, 1), 0),
        (0, 0, (0, 3)),
    )
    result = _discover(matrix, radius=2)
    assert result.validation_level is not None
    assert result.atomic_factors == ((1, 0, 2, 0, 1), (9, 0, 1))
    assert result.projector_rank == 2


def test_gaussian_rational_raw_scale_covariance() -> None:
    base = _discover((((0, 1), 0), (0, (0, 3))), radius=2)
    scaled = _discover(
        (((0, 5), 0), (0, (0, 15))),
        radius=10,
        spectral_reference_scale=5,
    )
    assert scaled.characteristic_polynomial == base.characteristic_polynomial
    assert scaled.projector_rank == base.projector_rank


def test_real_matrix_with_nonreal_center_uses_same_shifted_envelope_route() -> None:
    result = _discover(((0, 0), (0, 4)), center=(0, 1), radius=2)
    assert result.validation_level is not None
    assert result.projector_rank == 1
    assert not result.complex_rational_input_processed
    assert result.realification_characteristic_envelope_used
    assert result.center_shift_to_zero_verified


def test_honesty_flags_distinguish_supported_from_arbitrary_factorization() -> None:
    result = _discover()
    assert result.characteristic_polynomial_automatically_constructed
    assert result.rational_linear_factors_automatically_discovered
    assert result.characteristic_factorization_automatically_discovered
    assert result.full_arbitrary_degree_q_factorization_verified
    assert not result.diagonalization_witness_required
    assert not result.empirical_matrix_provenance_verified
