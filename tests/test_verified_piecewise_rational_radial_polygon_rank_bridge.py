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
_load("verified_polynomial_radial_contour_residual", "verified_polynomial_radial_contour_residual.py")
_load("verified_piecewise_polynomial_radial_contour_residual", "verified_piecewise_polynomial_radial_contour_residual.py")
_load("verified_piecewise_rational_radial_contour_residual", "verified_piecewise_rational_radial_contour_residual.py")
M = _load("ce_verified_piecewise_rational_rank_bridge", "verified_piecewise_rational_radial_polygon_rank_bridge.py")


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


def _bump_terms(u0, u1, scale):
    x0, y0 = map(F, u0)
    x1, y1 = map(F, u1)
    return (
        (1, 0, -scale * (x0 + x1)),
        (0, 1, -scale * (y0 + y1)),
        (2, 0, scale * x0 * x1),
        (1, 1, scale * (x0 * y1 + y0 * x1)),
        (0, 2, scale * y0 * y1),
    )


def _rational_patches(directions):
    patches = []
    for index, u0 in enumerate(directions):
        u1 = directions[(index + 1) % len(directions)]
        d = F(index + 1, 4000)
        e = F(index + 1, 8000)
        patches.append(
            (
                (1 + d + e, _bump_terms(u0, u1, d + e)),
                (1 + d, _bump_terms(u0, u1, d)),
            )
        )
    return tuple(patches)


def _bridge(**overrides):
    directions = overrides.pop("directions", RATIONAL_EIGHT)
    values = dict(
        nominal_transition=((0,),),
        uncertainty_radii=(((0, 0),),),
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        rational_patches=_rational_patches(directions),
        junction_order=1,
        directions=directions,
        spectral_reference_scale=1,
        initial_subdivisions=1,
        maximum_refinements=8,
        strategy="UNIFORM",
        subdivision_multiplier=2,
        sqrt_precision=48,
        machin_terms=8,
    )
    values.update(overrides)
    return M.verified_piecewise_rational_radial_rank_via_inscribed_polygon(**values)


def test_rational_c1_smooth_rank_one_is_verified_via_knot_polygon() -> None:
    result = _bridge()
    assert result.validation_level == "VERIFIED_PIECEWISE_RATIONAL_RADIAL_POLYGON_RIESZ_RANK"
    assert result.certified_nominal_rank == 1
    assert result.rational_family_rank_verified
    assert result.sector_homotopy_resolvent_verified
    assert result.smooth_contour_quadrature_rank_verified
    assert result.rational_construction.contour.denominator_pole_exclusion_verified


def test_polygon_vertices_and_cover_equal_rational_spline_receipts() -> None:
    result = _bridge()
    scale = result.rational_construction.spectral_reference_scale
    contour = result.rational_construction.contour
    assert result.raw_inscribed_polygon_vertices == tuple(
        node * scale for node in contour.contour_nodes
    )
    assert result.normalized_sector_homotopy_cover_upper == contour.normalized_cover_chord_upper


def test_homotopy_margin_is_rational_residual_margin() -> None:
    result = _bridge()
    assert result.rational_certificate is not None
    assert result.normalized_sector_homotopy_margin_lower == (
        result.rational_certificate.normalized_robust_delta_lower
    )


def test_projector_approximation_encloses_rational_smooth_projector() -> None:
    result = _bridge()
    assert result.rational_projector_quadrature is not None
    assert result.rational_projector_operator_error_upper is not None
    entry = result.rational_projector_quadrature[0][0]
    error = result.rational_projector_operator_error_upper
    assert abs(entry.real - 1) <= error
    assert abs(entry.imag) <= error


def test_outside_scalar_has_rational_smooth_rank_zero() -> None:
    result = _bridge(nominal_transition=((2,),))
    assert result.certified_nominal_rank == 0
    assert result.rational_projector_quadrature is not None
    entry = result.rational_projector_quadrature[0][0]
    error = result.rational_projector_operator_error_upper
    assert error is not None
    assert abs(entry.real) <= error
    assert abs(entry.imag) <= error


def test_interval_family_inherits_rational_smooth_rank() -> None:
    result = _bridge(uncertainty_radii=(((F(1, 20), 0),),))
    assert result.certified_nominal_rank == 1
    assert result.rational_certificate is not None
    assert result.rational_certificate.rank_preserved_for_entire_family
    assert result.rational_family_rank_verified


def test_zero_budget_keeps_high_multiplicity_rank_unresolved() -> None:
    zero5 = tuple(tuple(0 for _ in range(5)) for _ in range(5))
    uncertainty5 = tuple(tuple((0, 0) for _ in range(5)) for _ in range(5))
    result = _bridge(
        nominal_transition=zero5,
        uncertainty_radii=uncertainty5,
        maximum_refinements=0,
    )
    assert result.status == "PIECEWISE_RATIONAL_RADIAL_POLYGON_RANK_UNRESOLVED"
    assert result.certified_nominal_rank is None
    assert result.sector_homotopy_resolvent_verified
    assert result.rational_projector_quadrature is None


def test_failed_cover_stops_before_polygon_quadrature() -> None:
    result = _bridge(
        directions=CARDINAL,
        rational_patches=_rational_patches(CARDINAL),
        axis_u=F(4, 3),
    )
    assert result.validation_level is None
    assert result.rational_certificate is not None
    assert result.rational_certificate.status == "VERIFIED_PIECEWISE_RATIONAL_RADIAL_COVER_NONPOSITIVE"
    assert result.adaptive_polygon is None


def test_singular_knot_stops_before_residual_and_quadrature() -> None:
    result = _bridge(nominal_transition=((1,),))
    assert result.status == "EXACT_PIECEWISE_RATIONAL_RADIAL_NODE_SINGULAR"
    assert result.rational_certificate is None
    assert result.adaptive_polygon is None


def test_raw_scale_covariance_preserves_rank_and_refinement() -> None:
    base = _bridge()
    scaled = _bridge(axis_u=7, axis_v=(0, 7), spectral_reference_scale=7)
    assert scaled.certified_nominal_rank == base.certified_nominal_rank
    assert scaled.normalized_sector_homotopy_cover_upper == base.normalized_sector_homotopy_cover_upper
    assert scaled.adaptive_polygon is not None and base.adaptive_polygon is not None
    assert tuple(round_.subdivisions for round_ in scaled.adaptive_polygon.rounds) == tuple(
        round_.subdivisions for round_ in base.adaptive_polygon.rounds
    )


def test_pole_margin_failure_and_honesty_flags_remain_separate() -> None:
    patches = list(_rational_patches(RATIONAL_EIGHT))
    numerator, _ = patches[0]
    patches[0] = (numerator, (F(1, 4), ((2, 0, F(1, 4)),)))
    with pytest.raises(ValueError, match="denominator pole margin"):
        _bridge(rational_patches=tuple(patches))
    result = _bridge()
    assert not result.empirical_matrix_provenance_verified
    assert not result.contour_geometry_selected_from_data
