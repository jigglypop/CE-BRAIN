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
E = _load("verified_rational_ellipse_residual", "verified_rational_ellipse_residual.py")
M = _load("ce_verified_radial_contour", "verified_rational_radial_contour_residual.py")


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


def _construct(matrix=((0,),), **overrides):
    values = dict(
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        radial_base=1,
        radial_cos=F(1, 4),
        radial_sin=0,
        directions=RATIONAL_EIGHT,
        scale=1,
    )
    values.update(overrides)
    result = M.exact_radial_nominal_inverse_witnesses(
        matrix,
        center=values["center"],
        axis_u=values["axis_u"],
        axis_v=values["axis_v"],
        radial_base=values["radial_base"],
        radial_cos=values["radial_cos"],
        radial_sin=values["radial_sin"],
        directions=values["directions"],
        spectral_reference_scale=values["scale"],
        sqrt_precision=48,
    )
    assert result.approximate_inverses is not None
    return result, values


def _verified(matrix=((0,),), uncertainty=(((0, 0),),), **overrides):
    construction, values = _construct(matrix, **overrides)
    return M.verified_componentwise_residual_rational_radial_contour(
        matrix,
        uncertainty_radii=uncertainty,
        center=values["center"],
        axis_u=values["axis_u"],
        axis_v=values["axis_v"],
        radial_base=values["radial_base"],
        radial_cos=values["radial_cos"],
        radial_sin=values["radial_sin"],
        directions=values["directions"],
        approximate_inverses=construction.approximate_inverses,
        spectral_reference_scale=values["scale"],
        sqrt_precision=48,
    )


def test_nonellipse_affine_radial_contour_is_smooth_and_certified() -> None:
    result = _verified()
    assert result.validation_level == "VERIFIED_RATIONAL_AFFINE_RADIAL_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE"
    assert result.rank_preserved_for_entire_family
    assert result.smooth_nonellipse_contour_verified
    assert result.contour.radial_minimum_lower == F(3, 4)
    assert result.contour.radial_maximum_upper == F(5, 4)
    assert result.contour.radial_lipschitz_before_affine_upper == F(3, 2)


def test_zero_radial_linear_term_reduces_exactly_to_an_ellipse() -> None:
    radial_construction, values = _construct(
        radial_base=2,
        radial_cos=0,
        radial_sin=0,
    )
    radial = M.verified_componentwise_residual_rational_radial_contour(
        ((0,),),
        uncertainty_radii=(((0, 0),),),
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        radial_base=2,
        radial_cos=0,
        radial_sin=0,
        directions=RATIONAL_EIGHT,
        approximate_inverses=radial_construction.approximate_inverses,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    ellipse_construction = E.exact_ellipse_nominal_inverse_witnesses(
        ((0,),),
        center=0,
        axis_u=2,
        axis_v=(0, 2),
        directions=RATIONAL_EIGHT,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert ellipse_construction.approximate_inverses is not None
    ellipse = E.verified_componentwise_residual_rational_ellipse(
        ((0,),),
        uncertainty_radii=(((0, 0),),),
        center=0,
        axis_u=2,
        axis_v=(0, 2),
        directions=RATIONAL_EIGHT,
        approximate_inverses=ellipse_construction.approximate_inverses,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert radial.contour.contour_nodes == ellipse.ellipse.contour_nodes
    assert radial.contour.normalized_cover_chord_upper == ellipse.ellipse.normalized_cover_chord_upper
    assert radial.nodes == ellipse.nodes
    assert radial.normalized_robust_delta_lower == ellipse.normalized_robust_delta_lower
    assert not radial.smooth_nonellipse_contour_verified


def test_eight_nodes_close_a_cardinal_cover_failure() -> None:
    coarse = _verified(directions=CARDINAL)
    fine = _verified(directions=RATIONAL_EIGHT)
    assert coarse.status == "VERIFIED_RATIONAL_RADIAL_RESIDUAL_COVER_NONPOSITIVE"
    assert fine.validation_level is not None
    assert fine.contour.normalized_cover_chord_upper < coarse.contour.normalized_cover_chord_upper


@pytest.mark.parametrize(
    ("base", "cos", "sin"),
    [
        (1, 1, 0),
        (1, 0, 1),
        (1, F(3, 5), F(4, 5)),
        (0, 0, 0),
    ],
)
def test_nonpositive_radial_margin_fails_closed(base: object, cos: object, sin: object) -> None:
    with pytest.raises(ValueError, match="strictly exceed"):
        _construct(radial_base=base, radial_cos=cos, radial_sin=sin)


def test_rotated_affine_axes_preserve_smooth_certificate() -> None:
    result = _verified(axis_u=(1, 1), axis_v=(-1, 1))
    assert result.validation_level is not None
    assert result.contour.affine_geometry.orientation_determinant == 2
    assert result.contour.full_lipschitz_upper > result.contour.radial_lipschitz_before_affine_upper


def test_singular_radial_node_is_reported_separately() -> None:
    result = M.exact_radial_nominal_inverse_witnesses(
        ((F(5, 4),),),
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        radial_base=1,
        radial_cos=F(1, 4),
        radial_sin=0,
        directions=RATIONAL_EIGHT,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert result.status == "EXACT_RATIONAL_RADIAL_NOMINAL_NODE_SINGULAR"
    assert result.failing_node_index == 0
    assert result.approximate_inverses is None


def test_witness_count_must_match_radial_mesh() -> None:
    construction, values = _construct()
    with pytest.raises(ValueError, match="one matrix per radial node"):
        M.verified_componentwise_residual_rational_radial_contour(
            ((0,),),
            uncertainty_radii=(((0, 0),),),
            center=values["center"],
            axis_u=values["axis_u"],
            axis_v=values["axis_v"],
            radial_base=values["radial_base"],
            radial_cos=values["radial_cos"],
            radial_sin=values["radial_sin"],
            directions=values["directions"],
            approximate_inverses=construction.approximate_inverses[:-1],
            spectral_reference_scale=1,
            sqrt_precision=48,
        )


def test_projector_prefactor_uses_full_radial_lipschitz_bound() -> None:
    result = _verified(uncertainty=(((F(1, 100), 0),),))
    assert result.projector_perturbation_upper is not None
    expected = (
        result.contour.full_lipschitz_upper
        * result.normalized_selected_uncertainty_upper
        * result.normalized_robust_resolvent_upper
        * result.normalized_robust_resolvent_upper
    )
    assert result.projector_perturbation_upper == expected


def test_raw_scale_covariance_preserves_normalized_radial_result() -> None:
    base = _verified()
    scaled = _verified(axis_u=7, axis_v=(0, 7), scale=7)
    assert scaled.status == base.status
    assert scaled.contour == base.contour
    assert scaled.nodes == base.nodes
    assert scaled.raw_robust_delta_lower == 7 * base.raw_robust_delta_lower


def test_inexact_radial_input_and_empirical_claim_fail_closed() -> None:
    with pytest.raises(ValueError):
        _construct(radial_cos=0.25)
    result = _verified()
    assert not result.empirical_matrix_provenance_verified
