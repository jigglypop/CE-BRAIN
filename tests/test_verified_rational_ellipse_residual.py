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


R = _load("verified_rational_contour", "verified_rational_contour.py")
_load("verified_interval_contour", "verified_interval_contour.py")
_load("verified_interval_tightening", "verified_interval_tightening.py")
_load("verified_interval_residual", "verified_interval_residual.py")
C = _load("verified_rational_mesh_residual", "verified_rational_mesh_residual.py")
M = _load("ce_verified_rational_ellipse", "verified_rational_ellipse_residual.py")


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


def _construct(
    matrix=((0,),),
    *,
    center=0,
    axis_u=1,
    axis_v=(0, 1),
    directions=CARDINAL,
    scale=1,
):
    result = M.exact_ellipse_nominal_inverse_witnesses(
        matrix,
        center=center,
        axis_u=axis_u,
        axis_v=axis_v,
        directions=directions,
        spectral_reference_scale=scale,
        sqrt_precision=48,
    )
    assert result.approximate_inverses is not None
    return result


def _verified(matrix=((0,),), uncertainty=(((0, 0),),), **overrides):
    args = dict(
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        directions=CARDINAL,
        scale=1,
    )
    args.update(overrides)
    construction = _construct(matrix, **args)
    return M.verified_componentwise_residual_rational_ellipse(
        matrix,
        uncertainty_radii=uncertainty,
        center=args["center"],
        axis_u=args["axis_u"],
        axis_v=args["axis_v"],
        directions=args["directions"],
        approximate_inverses=construction.approximate_inverses,
        spectral_reference_scale=args["scale"],
        sqrt_precision=48,
    )


def test_circle_axes_reduce_exactly_to_rational_circle_mesh() -> None:
    matrix = ((0, 0), (0, 10))
    uncertainty = (((0, 0), (0, 0)), ((0, 0), (1, 0)))
    construction = _construct(matrix)
    ellipse = _verified(matrix, uncertainty)
    circle = C.verified_componentwise_residual_rational_mesh_circle(
        matrix,
        uncertainty_radii=uncertainty,
        directions=CARDINAL,
        approximate_inverses=construction.approximate_inverses,
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert ellipse.nodes == circle.nodes
    assert ellipse.ellipse.axis_operator_norm_bracket == (1, 1)
    assert ellipse.ellipse.normalized_cover_chord_upper == circle.normalized_chord_upper
    assert ellipse.normalized_robust_delta_lower == circle.normalized_robust_delta_lower
    assert ellipse.projector_perturbation_upper == circle.projector_perturbation_upper


def test_non_circular_ellipse_is_a_verified_smooth_contour() -> None:
    result = _verified(axis_u=2, axis_v=(0, 1), directions=RATIONAL_EIGHT)
    assert result.validation_level == "VERIFIED_RATIONAL_ELLIPSE_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE"
    assert result.rank_preserved_for_entire_family
    assert result.smooth_nonpolygonal_contour_verified
    assert result.ellipse.orientation_determinant == 2
    assert result.ellipse.axis_operator_norm_bracket == (2, 2)
    assert result.ellipse.normalized_perimeter_over_two_pi_upper == 2


def test_mesh_refinement_closes_a_coarse_ellipse_cover_failure() -> None:
    coarse = _verified(axis_u=2, axis_v=(0, 1), directions=CARDINAL)
    fine = _verified(axis_u=2, axis_v=(0, 1), directions=RATIONAL_EIGHT)
    assert coarse.status == "VERIFIED_RATIONAL_ELLIPSE_RESIDUAL_COVER_NONPOSITIVE"
    assert fine.validation_level is not None
    assert fine.ellipse.normalized_cover_chord_upper < coarse.ellipse.normalized_cover_chord_upper


def test_rotated_ellipse_operator_norm_is_verified_exactly() -> None:
    result = _verified(
        axis_u=(1, 1),
        axis_v=(-1, 1),
        directions=RATIONAL_EIGHT,
    )
    lower, upper = result.ellipse.axis_operator_norm_bracket
    assert lower * lower <= 2 <= upper * upper
    assert all(result.ellipse.axis_norm_sqrt_self_checks)
    assert result.ellipse.gram_discriminant == 0


@pytest.mark.parametrize(
    ("axis_u", "axis_v"),
    [
        (1, 2),
        (1, (0, -1)),
        ((1, 1), (2, 2)),
    ],
)
def test_degenerate_or_reversed_axes_fail_closed(axis_u: object, axis_v: object) -> None:
    with pytest.raises(ValueError, match="orientation determinant"):
        _construct(axis_u=axis_u, axis_v=axis_v)


def test_singular_ellipse_node_is_reported_separately() -> None:
    result = M.exact_ellipse_nominal_inverse_witnesses(
        ((2,),),
        center=0,
        axis_u=2,
        axis_v=(0, 1),
        directions=RATIONAL_EIGHT,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert result.status == "EXACT_RATIONAL_ELLIPSE_NOMINAL_NODE_SINGULAR"
    assert result.failing_node_index == 0
    assert result.approximate_inverses is None


def test_witness_count_must_match_ellipse_mesh() -> None:
    construction = _construct(directions=RATIONAL_EIGHT)
    with pytest.raises(ValueError, match="one matrix per ellipse node"):
        M.verified_componentwise_residual_rational_ellipse(
            ((0,),),
            uncertainty_radii=(((0, 0),),),
            center=0,
            axis_u=1,
            axis_v=(0, 1),
            directions=RATIONAL_EIGHT,
            approximate_inverses=construction.approximate_inverses[:-1],
            spectral_reference_scale=1,
            sqrt_precision=48,
        )


def test_raw_spectral_rescaling_preserves_normalized_ellipse_result() -> None:
    base = _verified(axis_u=2, axis_v=(0, 1), directions=RATIONAL_EIGHT)
    scaled = _verified(
        matrix=((0,),),
        uncertainty=(((0, 0),),),
        center=0,
        axis_u=14,
        axis_v=(0, 7),
        directions=RATIONAL_EIGHT,
        scale=7,
    )
    assert scaled.status == base.status
    assert scaled.ellipse == base.ellipse
    assert scaled.nodes == base.nodes
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert scaled.raw_robust_delta_lower == 7 * base.raw_robust_delta_lower


def test_projector_prefactor_uses_verified_axis_operator_norm() -> None:
    uncertainty = (((F(1, 100), 0),),)
    result = _verified(
        uncertainty=uncertainty,
        axis_u=2,
        axis_v=(0, 1),
        directions=RATIONAL_EIGHT,
    )
    assert result.projector_perturbation_upper is not None
    expected = (
        2
        * result.normalized_selected_uncertainty_upper
        * result.normalized_robust_resolvent_upper
        * result.normalized_robust_resolvent_upper
    )
    assert result.projector_perturbation_upper == expected


def test_inexact_axis_input_and_provenance_claims_fail_closed() -> None:
    with pytest.raises(ValueError):
        _construct(axis_u=1.0)
    result = _verified(axis_u=2, axis_v=(0, 1), directions=RATIONAL_EIGHT)
    assert not result.empirical_matrix_provenance_verified
