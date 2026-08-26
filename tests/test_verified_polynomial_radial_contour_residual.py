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
_load("verified_rational_ellipse_residual", "verified_rational_ellipse_residual.py")
R = _load("verified_rational_radial_contour_residual", "verified_rational_radial_contour_residual.py")
M = _load("ce_verified_polynomial_radial", "verified_polynomial_radial_contour_residual.py")


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
HIGHER_TERMS = (
    (2, 0, F(1, 16)),
    (0, 2, F(-1, 32)),
    (1, 1, F(1, 32)),
)


def _construct(matrix=((0,),), **overrides):
    values = dict(
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        radial_base=1,
        radial_terms=HIGHER_TERMS,
        directions=RATIONAL_EIGHT,
        scale=1,
    )
    values.update(overrides)
    result = M.exact_polynomial_radial_nominal_inverse_witnesses(
        matrix,
        center=values["center"],
        axis_u=values["axis_u"],
        axis_v=values["axis_v"],
        radial_base=values["radial_base"],
        radial_terms=values["radial_terms"],
        directions=values["directions"],
        spectral_reference_scale=values["scale"],
        sqrt_precision=48,
    )
    return result, values


def _verified(matrix=((0,),), uncertainty=(((0, 0),),), **overrides):
    construction, values = _construct(matrix, **overrides)
    assert construction.approximate_inverses is not None
    return M.verified_componentwise_residual_polynomial_radial_contour(
        matrix,
        uncertainty_radii=uncertainty,
        center=values["center"],
        axis_u=values["axis_u"],
        axis_v=values["axis_v"],
        radial_base=values["radial_base"],
        radial_terms=values["radial_terms"],
        directions=values["directions"],
        approximate_inverses=construction.approximate_inverses,
        spectral_reference_scale=values["scale"],
        sqrt_precision=48,
    )


def test_genuine_quadratic_radial_contour_is_smooth_and_certified() -> None:
    result = _verified()
    contour = result.contour
    assert result.validation_level == "VERIFIED_RATIONAL_POLYNOMIAL_RADIAL_RESIDUAL_CONTOUR_BRIDGE"
    assert result.rank_preserved_for_entire_family
    assert result.higher_order_polynomial_contour_verified
    assert contour.radial_degree == 2
    assert contour.higher_amplitude_upper == F(1, 8)
    assert contour.higher_gradient_upper == F(1, 4)
    assert contour.radial_minimum_lower == F(7, 8)
    assert contour.radial_lipschitz_before_affine_upper == F(11, 8)


def test_degree_one_terms_reduce_exactly_to_affine_linear_radial_route() -> None:
    terms = ((1, 0, F(1, 4)), (0, 1, F(1, 8)))
    polynomial = _verified(radial_terms=terms)
    radial_construction = R.exact_radial_nominal_inverse_witnesses(
        ((0,),),
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        radial_base=1,
        radial_cos=F(1, 4),
        radial_sin=F(1, 8),
        directions=RATIONAL_EIGHT,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert radial_construction.approximate_inverses is not None
    radial = R.verified_componentwise_residual_rational_radial_contour(
        ((0,),),
        uncertainty_radii=(((0, 0),),),
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        radial_base=1,
        radial_cos=F(1, 4),
        radial_sin=F(1, 8),
        directions=RATIONAL_EIGHT,
        approximate_inverses=radial_construction.approximate_inverses,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert polynomial.contour.contour_nodes == radial.contour.contour_nodes
    assert polynomial.contour.normalized_cover_chord_upper == radial.contour.normalized_cover_chord_upper
    assert polynomial.normalized_robust_delta_lower == radial.normalized_robust_delta_lower
    assert not polynomial.higher_order_polynomial_contour_verified


def test_duplicate_terms_are_combined_and_zero_terms_removed() -> None:
    result, _ = _construct(
        radial_terms=((2, 0, F(1, 16)), (2, 0, F(1, 16)), (1, 1, 0))
    )
    assert result.contour.radial_terms == ((2, 0, F(1, 8)),)


def test_eight_nodes_close_a_cardinal_cover_failure() -> None:
    coarse = _verified(directions=CARDINAL)
    fine = _verified(directions=RATIONAL_EIGHT)
    assert coarse.status == "VERIFIED_POLYNOMIAL_RADIAL_RESIDUAL_COVER_NONPOSITIVE"
    assert fine.validation_level is not None
    assert fine.contour.normalized_cover_chord_upper < coarse.contour.normalized_cover_chord_upper


@pytest.mark.parametrize(
    ("base", "terms"),
    [
        (F(1, 4), ((2, 0, F(1, 4)),)),
        (F(1, 8), ((2, 0, F(1, 4)),)),
        (0, ()),
    ],
)
def test_nonpositive_polynomial_amplitude_margin_fails_closed(base, terms) -> None:
    with pytest.raises(ValueError, match="strictly exceed"):
        _construct(radial_base=base, radial_terms=terms)


@pytest.mark.parametrize(
    "terms",
    [((0, 0, 1),), ((-1, 0, 1),), ((True, 1, 1),), ((1, 2),)],
)
def test_malformed_polynomial_terms_are_rejected(terms) -> None:
    with pytest.raises(ValueError):
        _construct(radial_terms=terms)


def test_singular_polynomial_node_is_reported_separately() -> None:
    result, _ = _construct(matrix=((F(17, 16),),))
    assert result.status == "EXACT_POLYNOMIAL_RADIAL_NOMINAL_NODE_SINGULAR"
    assert result.failing_node_index == 0
    assert result.approximate_inverses is None


def test_interval_family_projector_bound_and_scale_covariance() -> None:
    base = _verified(uncertainty=(((F(1, 100), 0),),))
    scaled = _verified(
        matrix=((0,),),
        uncertainty=(((F(7, 100), 0),),),
        axis_u=7,
        axis_v=(0, 7),
        scale=7,
    )
    assert base.projector_perturbation_upper is not None
    assert scaled.projector_perturbation_upper == base.projector_perturbation_upper
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert not scaled.empirical_matrix_provenance_verified
