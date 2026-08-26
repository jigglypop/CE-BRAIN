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
_load("verified_rational_mesh_residual", "verified_rational_mesh_residual.py")
_load("verified_rational_polygon_residual", "verified_rational_polygon_residual.py")
_load("verified_polygon_riesz_quadrature", "verified_polygon_riesz_quadrature.py")
_load("verified_adaptive_polygon_riesz", "verified_adaptive_polygon_riesz.py")
_load("verified_rational_ellipse_residual", "verified_rational_ellipse_residual.py")
M = _load("ce_verified_ellipse_rank_bridge", "verified_ellipse_polygon_rank_bridge.py")


CARDINAL = ((1, 0), (0, 1), (-1, 0), (0, -1))
RATIONAL_EIGHT = (
    (1, 0),
    (F(3, 5), F(4, 5)),
    (0, 1),
    (F(-3, 5), F(4, 5)),
    (-1, 0),
    (F(-3, 5), F(-4, 5)),
    (0, -1),
    (F(3, 5), F(-4, 5)),
)


def _bridge(**overrides):
    values = dict(
        nominal_transition=((0,),),
        uncertainty_radii=(((0, 0),),),
        center=0,
        axis_u=2,
        axis_v=(0, 1),
        directions=RATIONAL_EIGHT,
        spectral_reference_scale=1,
        initial_subdivisions=1,
        maximum_refinements=8,
        strategy="UNIFORM",
        subdivision_multiplier=2,
        sqrt_precision=48,
        machin_terms=8,
    )
    values.update(overrides)
    return M.verified_ellipse_rank_via_inscribed_polygon(**values)


def test_smooth_ellipse_rank_one_is_verified_via_polygon_homotopy() -> None:
    result = _bridge()
    assert result.validation_level == "VERIFIED_RATIONAL_ELLIPSE_POLYGON_HOMOTOPY_RIESZ_RANK"
    assert result.certified_nominal_rank == 1
    assert result.ellipse_family_rank_verified
    assert result.sector_homotopy_resolvent_verified
    assert result.smooth_contour_quadrature_rank_verified
    assert result.adaptive_polygon is not None
    assert result.adaptive_polygon.certified_nominal_rank == 1


def test_polygon_vertices_are_exactly_the_mapped_ellipse_nodes() -> None:
    result = _bridge()
    scale = result.ellipse_construction.spectral_reference_scale
    expected = tuple(
        node * scale for node in result.ellipse_construction.ellipse.contour_nodes
    )
    assert result.raw_inscribed_polygon_vertices == expected
    assert result.normalized_sector_homotopy_cover_upper == (
        result.ellipse_construction.ellipse.normalized_cover_chord_upper
    )


def test_sector_homotopy_margin_is_the_ellipse_residual_margin() -> None:
    result = _bridge()
    assert result.ellipse_certificate is not None
    assert result.normalized_sector_homotopy_margin_lower == (
        result.ellipse_certificate.normalized_robust_delta_lower
    )
    assert result.normalized_sector_homotopy_margin_lower > 0


def test_polygon_projector_approximation_encloses_the_ellipse_projector() -> None:
    result = _bridge()
    assert result.ellipse_projector_quadrature is not None
    assert result.ellipse_projector_operator_error_upper is not None
    entry = result.ellipse_projector_quadrature[0][0]
    error = result.ellipse_projector_operator_error_upper
    assert abs(entry.real - 1) <= error
    assert abs(entry.imag) <= error


def test_outside_scalar_has_smooth_ellipse_rank_zero() -> None:
    result = _bridge(nominal_transition=((3,),))
    assert result.certified_nominal_rank == 0
    assert result.ellipse_projector_quadrature is not None
    entry = result.ellipse_projector_quadrature[0][0]
    error = result.ellipse_projector_operator_error_upper
    assert error is not None
    assert abs(entry.real) <= error
    assert abs(entry.imag) <= error


def test_interval_family_inherits_the_smooth_ellipse_rank() -> None:
    result = _bridge(uncertainty_radii=(((F(1, 20), 0),),))
    assert result.certified_nominal_rank == 1
    assert result.ellipse_certificate is not None
    assert result.ellipse_certificate.rank_preserved_for_entire_family
    assert result.ellipse_family_rank_verified


def test_zero_budget_keeps_smooth_rank_unresolved_without_guessing() -> None:
    result = _bridge(maximum_refinements=0)
    assert result.status == "RATIONAL_ELLIPSE_POLYGON_HOMOTOPY_RANK_UNRESOLVED"
    assert result.validation_level is None
    assert result.certified_nominal_rank is None
    assert result.sector_homotopy_resolvent_verified
    assert result.ellipse_projector_quadrature is None


def test_failed_ellipse_cover_stops_before_polygon_quadrature() -> None:
    result = _bridge(directions=CARDINAL)
    assert result.validation_level is None
    assert result.ellipse_certificate is not None
    assert result.ellipse_certificate.status == "VERIFIED_RATIONAL_ELLIPSE_RESIDUAL_COVER_NONPOSITIVE"
    assert result.adaptive_polygon is None
    assert not result.sector_homotopy_resolvent_verified


def test_singular_ellipse_node_stops_before_residual_and_quadrature() -> None:
    result = _bridge(nominal_transition=((2,),))
    assert result.status == "EXACT_RATIONAL_ELLIPSE_NOMINAL_NODE_SINGULAR"
    assert result.ellipse_certificate is None
    assert result.adaptive_polygon is None


def test_raw_scale_covariance_preserves_rank_and_refinement() -> None:
    base = _bridge()
    scaled = _bridge(
        axis_u=14,
        axis_v=(0, 7),
        spectral_reference_scale=7,
    )
    assert scaled.certified_nominal_rank == base.certified_nominal_rank
    assert scaled.normalized_sector_homotopy_cover_upper == base.normalized_sector_homotopy_cover_upper
    assert scaled.adaptive_polygon is not None and base.adaptive_polygon is not None
    assert tuple(round_.subdivisions for round_ in scaled.adaptive_polygon.rounds) == tuple(
        round_.subdivisions for round_ in base.adaptive_polygon.rounds
    )


def test_invalid_axes_and_honesty_flags_remain_separate() -> None:
    with pytest.raises(ValueError, match="orientation determinant"):
        _bridge(axis_v=(0, -1))
    result = _bridge()
    assert not result.empirical_matrix_provenance_verified
    assert not result.contour_geometry_selected_from_data
