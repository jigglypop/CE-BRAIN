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
_load("verified_rational_polygon_residual", "verified_rational_polygon_residual.py")
M = _load("ce_verified_polygon_quadrature", "verified_polygon_riesz_quadrature.py")


SQUARE = ((-1, -1), (1, -1), (1, 1), (-1, 1))


def _zero_radii(n: int):
    return tuple(tuple((0, 0) for _ in range(n)) for _ in range(n))


def _rank(matrix=((0,),), *, uncertainty=None, vertices=SQUARE, scale=1, **overrides):
    n = len(matrix)
    values = dict(
        nominal_transition=matrix,
        uncertainty_radii=_zero_radii(n) if uncertainty is None else uncertainty,
        vertices=vertices,
        spectral_reference_scale=scale,
        subdivisions=32,
        sqrt_precision=48,
        machin_terms=8,
    )
    values.update(overrides)
    return M.verified_polygon_midpoint_riesz_rank(**values)


def test_machin_series_gives_a_strict_rational_pi_enclosure() -> None:
    bracket = M.rational_machin_pi_bracket(terms=8)
    assert bracket.lower_positive
    assert bracket.ordered
    assert bracket.archimedean_sanity
    assert F(333, 106) < bracket.lower < bracket.upper < F(355, 113)


def test_scalar_inside_square_has_verified_rank_one() -> None:
    result = _rank()
    assert result.validation_level == "VERIFIED_RATIONAL_POLYGON_MIDPOINT_RIESZ_RANK"
    assert result.possible_ranks == (1,)
    assert result.certified_nominal_rank == 1
    assert result.nominal_rank_verified
    assert result.family_rank_verified
    assert result.midpoint_count == 128
    assert all(all(check) for check in result.midpoint_inverse_identity_checks)
    inverse_lower, inverse_upper = result.inverse_two_pi_bracket
    assert F(7, 44) < inverse_lower < inverse_upper < F(1, 6)
    projector_entry = result.scaled_projector_quadrature[0][0]
    assert abs(projector_entry.real - 1) <= result.scaled_projector_operator_error_upper
    assert abs(projector_entry.imag) <= result.scaled_projector_operator_error_upper


def test_scalar_outside_square_has_verified_rank_zero() -> None:
    result = _rank(matrix=((3,),), subdivisions=16)
    assert result.possible_ranks == (0,)
    assert result.certified_nominal_rank == 0
    assert result.nominal_rank_verified
    projector_entry = result.scaled_projector_quadrature[0][0]
    assert abs(projector_entry.real) <= result.scaled_projector_operator_error_upper
    assert abs(projector_entry.imag) <= result.scaled_projector_operator_error_upper


def test_two_by_two_polygon_rank_is_discovered_without_eigenvalue_input() -> None:
    result = _rank(matrix=((0, 0), (0, 3)), subdivisions=64)
    assert result.possible_ranks == (1,)
    assert result.certified_nominal_rank == 1
    assert result.nominal_rank_verified
    assert result.polygon_certificate.nominal_rank_value_supplied is False


def test_interval_family_inherits_the_verified_nominal_rank() -> None:
    result = _rank(uncertainty=(((F(1, 10), 0),),), subdivisions=64)
    assert result.certified_nominal_rank == 1
    assert result.polygon_certificate.rank_preserved_for_entire_family
    assert result.family_rank_verified


def test_coarse_quadrature_refuses_to_guess_between_possible_ranks() -> None:
    result = _rank(subdivisions=1)
    assert result.status == "RATIONAL_POLYGON_MIDPOINT_RIESZ_RANK_UNRESOLVED"
    assert result.validation_level is None
    assert len(result.possible_ranks) > 1
    assert result.certified_nominal_rank is None
    assert not result.nominal_rank_verified


def test_midpoint_error_decreases_quadratically_under_frozen_refinement() -> None:
    coarse = _rank(subdivisions=8)
    fine = _rank(subdivisions=16)
    assert coarse.unscaled_operator_quadrature_error_upper == (
        4 * fine.unscaled_operator_quadrature_error_upper
    )
    assert coarse.subdivisions_per_edge == (8, 8, 8, 8)
    assert fine.subdivisions_per_edge == (16, 16, 16, 16)


def test_per_edge_subdivision_vector_is_respected_exactly() -> None:
    result = _rank(subdivisions=(8, 16, 24, 32))
    assert result.subdivisions_per_edge == (8, 16, 24, 32)
    assert result.midpoint_count == 80
    assert len(result.edge_quadrature_error_uppers) == 4


def test_raw_spectral_rescaling_preserves_normalized_quadrature() -> None:
    base = _rank()
    scaled_vertices = tuple((7 * x, 7 * y) for x, y in SQUARE)
    scaled = _rank(
        matrix=((0,),),
        vertices=scaled_vertices,
        scale=7,
    )
    assert scaled.status == base.status
    assert scaled.normalized_midpoint_nodes == base.normalized_midpoint_nodes
    assert scaled.unscaled_projector_quadrature == base.unscaled_projector_quadrature
    assert scaled.unscaled_operator_quadrature_error_upper == base.unscaled_operator_quadrature_error_upper
    assert scaled.certified_nominal_rank == base.certified_nominal_rank


@pytest.mark.parametrize(
    "subdivisions",
    [0, True, (1, 1), (1, 1, 1, 0), (1, 1, 1, 1.0)],
)
def test_invalid_subdivision_contract_fails_closed(subdivisions: object) -> None:
    with pytest.raises(ValueError, match="subdivision"):
        _rank(subdivisions=subdivisions)


def test_invalid_machin_term_contract_fails_closed() -> None:
    with pytest.raises(ValueError, match="Machin terms"):
        M.rational_machin_pi_bracket(terms=0)
    with pytest.raises(ValueError, match="Machin terms"):
        _rank(machin_terms=True)


def test_provenance_and_adaptivity_flags_remain_false() -> None:
    result = _rank()
    assert not result.empirical_matrix_provenance_verified
    assert not result.adaptive_subdivision_used
