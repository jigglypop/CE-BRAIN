from __future__ import annotations

import importlib.util
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
M = _load("ce_verified_algebraic_riesz_projector", "verified_algebraic_riesz_projector.py")


P2 = ((1, 0, 0), (0, 1, 0), (0, 0, 0))
R4 = ((0, 0, 0), (0, 0, 0), (0, 0, "1/4"))


def _verified(**overrides):
    values = dict(
        nominal_transition=((0, 1, 0), (0, 0, 0), (0, 0, 4)),
        projector=P2,
        exterior_centered_inverse=R4,
        center=0,
        radius=2,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    values.update(overrides)
    return M.verified_algebraic_riesz_projector(**values)


def test_defective_inside_jordan_block_is_certified_without_diagonalization() -> None:
    result = _verified()
    assert result.status == "VERIFIED_EXACT_ALGEBRAIC_RIESZ_PROJECTOR"
    assert result.validation_level == result.status
    assert result.projector_verified
    assert result.projector_rank == 2
    assert result.idempotence_check
    assert all(result.commutation_checks)
    assert all(result.exterior_support_checks)
    assert all(result.exterior_inverse_identity_checks)
    assert result.normalized_inside_margin > 0
    assert result.exterior_reciprocal_margin > 0
    assert not result.diagonalization_witness_required


def test_irrational_eigenvalue_pair_is_certified_without_listing_roots() -> None:
    result = _verified(
        nominal_transition=((0, 2, 0), (1, 0, 0), (0, 0, 4)),
        radius=3,
    )
    assert result.validation_level is not None
    assert result.projector_rank == 2
    assert result.inside_operator_norm.selected_two_norm_upper < 3
    assert 3 * result.exterior_inverse_norm.selected_two_norm_upper < 1


def test_zero_and_full_rank_projectors_are_valid_boundary_ranks() -> None:
    zero = ((0, 0), (0, 0))
    identity = ((1, 0), (0, 1))
    zero_rank = M.verified_algebraic_riesz_projector(
        ((4, 0), (0, 4)),
        projector=zero,
        exterior_centered_inverse=(("1/4", 0), (0, "1/4")),
        center=0,
        radius=2,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    full_rank = M.verified_algebraic_riesz_projector(
        ((0, 1), (0, 0)),
        projector=identity,
        exterior_centered_inverse=zero,
        center=0,
        radius=2,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    assert zero_rank.validation_level is not None and zero_rank.projector_rank == 0
    assert full_rank.validation_level is not None and full_rank.projector_rank == 2


def test_nonidempotent_and_noninteger_trace_fail_closed() -> None:
    result = _verified(projector=(("1/2", 0, 0), (0, 1, 0), (0, 0, 0)))
    assert result.validation_level is None
    assert "ALGEBRAIC_PROJECTOR_NOT_IDEMPOTENT" in result.failure_codes
    assert "ALGEBRAIC_PROJECTOR_TRACE_NOT_AN_INTEGER_RANK" in result.failure_codes


def test_noncommuting_projector_fails_closed() -> None:
    result = _verified(projector=((1, 0, 1), (0, 1, 0), (0, 0, 0)))
    assert result.validation_level is None
    assert "ALGEBRAIC_PROJECTOR_NOT_COMMUTING" in result.failure_codes


def test_exterior_inverse_must_be_complement_supported_and_two_sided() -> None:
    unsupported = _verified(
        exterior_centered_inverse=((1, 0, 0), (0, 0, 0), (0, 0, "1/4"))
    )
    wrong = _verified(
        exterior_centered_inverse=((0, 0, 0), (0, 0, 0), (0, 0, "1/5"))
    )
    assert "ALGEBRAIC_EXTERIOR_INVERSE_NOT_COMPLEMENT_SUPPORTED" in unsupported.failure_codes
    assert "ALGEBRAIC_EXTERIOR_INVERSE_IDENTITY_FAILED" in wrong.failure_codes


def test_inside_and_outside_strict_equality_boundaries_fail() -> None:
    inside_equal = _verified(radius=1)
    outside_equal = _verified(
        nominal_transition=((0, 0, 0), (0, 0, 0), (0, 0, 2)),
        exterior_centered_inverse=((0, 0, 0), (0, 0, 0), (0, 0, "1/2")),
        radius=2,
    )
    assert "ALGEBRAIC_INSIDE_NORM_NOT_STRICTLY_INSIDE" in inside_equal.failure_codes
    assert "ALGEBRAIC_EXTERIOR_INVERSE_NORM_NOT_STRICTLY_OUTSIDE" in outside_equal.failure_codes


def test_raw_spectral_rescaling_preserves_normalized_algebraic_receipt() -> None:
    base = _verified()
    scaled = _verified(
        nominal_transition=((0, 7, 0), (0, 0, 0), (0, 0, 28)),
        radius=14,
        spectral_reference_scale=7,
    )
    assert scaled.status == base.status
    assert scaled.normalized_transition == base.normalized_transition
    assert scaled.normalized_radius == base.normalized_radius
    assert scaled.normalized_inside_margin == base.normalized_inside_margin
    assert scaled.raw_inside_margin == 7 * base.raw_inside_margin
    assert scaled.exterior_reciprocal_margin == base.exterior_reciprocal_margin


@pytest.mark.parametrize(
    "field,value",
    [
        ("projector", ((1.0, 0, 0), (0, 1, 0), (0, 0, 0))),
        ("exterior_centered_inverse", ((0, 0, 0), (0, 0, 0), (0, 0, True))),
        ("nominal_transition", ((0, 1, 0), (0, 0, 0), (0, 0, "04"))),
    ],
)
def test_inexact_or_noncanonical_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _verified(**{field: value})


def test_empirical_provenance_remains_false() -> None:
    assert not _verified().empirical_matrix_provenance_verified
