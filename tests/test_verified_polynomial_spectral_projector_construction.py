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
M = _load("ce_verified_projector_construction", "verified_polynomial_spectral_projector_construction.py")


def _construct(matrix=((0, 0), (0, 4)), **overrides):
    values = dict(
        inside_factor=(0, 1),
        outside_factor=(-4, 1),
        center=0,
        radius=2,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    values.update(overrides)
    return M.verified_projector_from_coprime_spectral_factors(matrix, **values)


def test_diagonal_rank_one_projector_and_exterior_inverse_are_constructed() -> None:
    result = _construct()
    assert result.validation_level == "VERIFIED_EXACT_PROJECTOR_CONSTRUCTED_FROM_COPRIME_SPECTRAL_FACTORS"
    assert result.projector_rank == 1
    assert result.constructed_projector is not None
    assert result.constructed_projector[0][0].real == 1
    assert result.constructed_projector[1][1].real == 0
    assert result.algebraic_certificate is not None
    assert result.algebraic_certificate.projector_verified
    assert result.projector_automatically_constructed
    assert result.exterior_inverse_automatically_constructed
    assert not result.diagonalization_witness_required


def test_defective_inside_jordan_block_is_constructed_without_eigenvectors() -> None:
    matrix = ((0, 1, 0), (0, 0, 0), (0, 0, 4))
    result = _construct(matrix, inside_factor=(0, 0, 1))
    assert result.validation_level is not None
    assert result.projector_rank == 2
    assert result.constructed_projector is not None
    assert result.constructed_projector[0][1].real == 0


def test_irrational_inside_spectrum_is_admitted_by_rational_factor() -> None:
    matrix = ((0, 2, 0), (1, 0, 0), (0, 0, 4))
    result = _construct(matrix, inside_factor=(-2, 0, 1), radius=3)
    assert result.validation_level is not None
    assert result.projector_rank == 2
    assert not result.characteristic_factorization_automatically_discovered


def test_full_rank_and_zero_rank_splits_are_constructed() -> None:
    full = _construct(((0,),), outside_factor=(-4, 1))
    assert full.validation_level is not None
    assert full.projector_rank == 1
    zero = _construct(
        ((4,),),
        inside_factor=(0, 1),
        outside_factor=(-4, 1),
    )
    assert zero.validation_level is not None
    assert zero.projector_rank == 0


def test_common_factor_scaling_is_normalized() -> None:
    base = _construct()
    scaled = _construct(inside_factor=(0, 7), outside_factor=(-12, 3))
    assert scaled.normalized_inside_factor == base.normalized_inside_factor
    assert scaled.normalized_outside_factor == base.normalized_outside_factor
    assert scaled.constructed_projector == base.constructed_projector


def test_raw_spectral_scale_covariance_preserves_projector() -> None:
    base = _construct()
    scaled = _construct(
        ((0, 0), (0, 28)),
        radius=14,
        spectral_reference_scale=7,
    )
    assert scaled.validation_level is not None
    assert scaled.constructed_projector == base.constructed_projector
    assert scaled.projector_rank == base.projector_rank


def test_noncoprime_factor_split_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be coprime"):
        _construct(inside_factor=(0, 1), outside_factor=(0, 0, 1))


def test_factor_product_must_annihilate_transition() -> None:
    result = _construct(((1, 0), (0, 4)))
    assert result.status == "SPECTRAL_FACTOR_PRODUCT_DOES_NOT_ANNIHILATE_TRANSITION"
    assert result.constructed_projector is None
    assert not result.projector_automatically_constructed


def test_swapped_factor_labels_fail_the_strict_inside_outside_gate() -> None:
    result = _construct(
        ((1, 0), (0, 4)),
        inside_factor=(-4, 1),
        outside_factor=(-1, 1),
    )
    assert result.validation_level is None
    assert result.algebraic_certificate is not None
    assert "ALGEBRAIC_INSIDE_NORM_NOT_STRICTLY_INSIDE" in result.failure_codes


def test_center_eigenvalue_in_complement_refuses_inverse_construction() -> None:
    result = _construct(
        ((0,),),
        inside_factor=(-1, 1),
        outside_factor=(0, 1),
    )
    assert result.status == "SPECTRAL_FACTOR_COMPLEMENT_CENTERED_OPERATOR_SINGULAR"
    assert result.constructed_projector is not None
    assert result.constructed_exterior_centered_inverse is None


@pytest.mark.parametrize(
    "factor",
    [(1,), (), (0, 0), (0, 1.0), (0, True)],
)
def test_malformed_or_constant_factors_are_rejected(factor) -> None:
    with pytest.raises(ValueError):
        _construct(inside_factor=factor)


def test_honesty_flags_separate_factor_supply_from_witness_construction() -> None:
    result = _construct()
    assert result.polynomial_factor_split_supplied
    assert result.projector_automatically_constructed
    assert result.exterior_inverse_automatically_constructed
    assert not result.characteristic_factorization_automatically_discovered
    assert not result.empirical_matrix_provenance_verified
