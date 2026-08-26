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
_load("verified_polynomial_radial_contour_residual", "verified_polynomial_radial_contour_residual.py")
M = _load("ce_verified_piecewise_polynomial_radial", "verified_piecewise_polynomial_radial_contour_residual.py")


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


def _patches(directions, *, denominator=400):
    patches = []
    for index, (x0, y0) in enumerate(directions):
        x1, y1 = directions[(index + 1) % len(directions)]
        x0, y0, x1, y1 = map(F, (x0, y0, x1, y1))
        epsilon = F(index + 1, denominator)
        # 1 + eps*(1-u.u0)*(1-u.u1); value and first angular derivative
        # agree with the constant radius at both endpoints.
        terms = (
            (1, 0, -epsilon * (x0 + x1)),
            (0, 1, -epsilon * (y0 + y1)),
            (2, 0, epsilon * x0 * x1),
            (1, 1, epsilon * (x0 * y1 + y0 * x1)),
            (0, 2, epsilon * y0 * y1),
        )
        patches.append((1 + epsilon, terms))
    return tuple(patches)


def _construct(matrix=((0,),), **overrides):
    directions = overrides.pop("directions", RATIONAL_EIGHT)
    values = dict(
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        radial_patches=_patches(directions),
        junction_order=1,
        directions=directions,
        scale=1,
    )
    values.update(overrides)
    result = M.exact_piecewise_polynomial_radial_nominal_inverse_witnesses(
        matrix,
        center=values["center"],
        axis_u=values["axis_u"],
        axis_v=values["axis_v"],
        radial_patches=values["radial_patches"],
        junction_order=values["junction_order"],
        directions=values["directions"],
        spectral_reference_scale=values["scale"],
        sqrt_precision=48,
    )
    return result, values


def _verified(matrix=((0,),), uncertainty=(((0, 0),),), **overrides):
    construction, values = _construct(matrix, **overrides)
    assert construction.approximate_inverses is not None
    return M.verified_componentwise_residual_piecewise_polynomial_radial_contour(
        matrix,
        uncertainty_radii=uncertainty,
        center=values["center"],
        axis_u=values["axis_u"],
        axis_v=values["axis_v"],
        radial_patches=values["radial_patches"],
        junction_order=values["junction_order"],
        directions=values["directions"],
        approximate_inverses=construction.approximate_inverses,
        spectral_reference_scale=values["scale"],
        sqrt_precision=48,
    )


def test_genuinely_piecewise_quadratic_c1_radial_contour_is_verified() -> None:
    result = _verified()
    contour = result.contour
    assert result.validation_level == "VERIFIED_PIECEWISE_POLYNOMIAL_RADIAL_CQ_RESIDUAL_CONTOUR"
    assert result.rank_preserved_for_entire_family
    assert result.piecewise_polynomial_cq_contour_verified
    assert contour.junction_order == 1
    assert all(all(row) for row in contour.junction_self_checks)
    assert all(values == (1, 0) for values in contour.junction_derivative_values)
    assert len(set(contour.patches)) == len(RATIONAL_EIGHT)


def test_identical_patches_admit_arbitrary_supplied_finite_junction_order() -> None:
    patch = (1, ((2, 0, F(1, 32)), (0, 2, F(1, 32))))
    result = _verified(radial_patches=(patch,) * 8, junction_order=6)
    assert result.contour.junction_order == 6
    assert all(all(row) for row in result.contour.junction_self_checks)


def test_c1_bumps_refuse_false_c2_promotion() -> None:
    with pytest.raises(ValueError, match="derivative order 2"):
        _construct(junction_order=2)


def test_value_mismatch_at_periodic_knot_is_rejected() -> None:
    patches = list(_patches(RATIONAL_EIGHT))
    base, terms = patches[0]
    patches[0] = (base + F(1, 100), terms)
    with pytest.raises(ValueError, match="junction mismatch"):
        _construct(radial_patches=tuple(patches))


def test_first_derivative_mismatch_is_rejected_separately() -> None:
    patches = list(_patches(RATIONAL_EIGHT))
    base, terms = patches[0]
    patches[0] = (base, tuple(terms) + ((1, 0, F(1, 100)),))
    with pytest.raises(ValueError, match="junction mismatch"):
        _construct(radial_patches=tuple(patches))


def test_patch_count_and_junction_order_are_strict() -> None:
    with pytest.raises(ValueError, match="one .* patch per mesh arc"):
        _construct(radial_patches=_patches(RATIONAL_EIGHT)[:-1])
    with pytest.raises(ValueError, match="at least one"):
        _construct(junction_order=0)


def test_patch_positivity_equality_fails_closed() -> None:
    patches = list(_patches(RATIONAL_EIGHT))
    patches[0] = (F(1, 4), ((2, 0, F(1, 4)),))
    with pytest.raises(ValueError, match="strict polynomial amplitude positivity"):
        _construct(radial_patches=tuple(patches))


def test_eight_knots_close_an_anisotropic_cardinal_cover_failure() -> None:
    coarse = _verified(
        directions=CARDINAL,
        radial_patches=_patches(CARDINAL),
        axis_u=F(5, 4),
    )
    fine = _verified(axis_u=F(5, 4))
    assert coarse.status == "VERIFIED_PIECEWISE_POLYNOMIAL_RADIAL_COVER_NONPOSITIVE"
    assert fine.validation_level is not None


def test_singular_knot_is_reported_before_residual() -> None:
    result, _ = _construct(matrix=((1,),))
    assert result.status == "EXACT_PIECEWISE_POLYNOMIAL_RADIAL_NODE_SINGULAR"
    assert result.failing_node_index == 0
    assert result.approximate_inverses is None


def test_interval_projector_bound_and_raw_scale_covariance() -> None:
    base = _verified(uncertainty=(((F(1, 100), 0),),))
    scaled = _verified(
        uncertainty=(((F(7, 100), 0),),),
        axis_u=7,
        axis_v=(0, 7),
        scale=7,
    )
    assert base.projector_perturbation_upper is not None
    assert scaled.projector_perturbation_upper == base.projector_perturbation_upper
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert not scaled.empirical_matrix_provenance_verified
