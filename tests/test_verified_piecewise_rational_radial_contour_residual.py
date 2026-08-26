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
P = _load("verified_piecewise_polynomial_radial_contour_residual", "verified_piecewise_polynomial_radial_contour_residual.py")
M = _load("ce_verified_piecewise_rational_radial", "verified_piecewise_rational_radial_contour_residual.py")


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
        denominator = (1 + d, _bump_terms(u0, u1, d))
        numerator = (1 + d + e, _bump_terms(u0, u1, d + e))
        patches.append((numerator, denominator))
    return tuple(patches)


def _construct(matrix=((0,),), **overrides):
    directions = overrides.pop("directions", RATIONAL_EIGHT)
    values = dict(
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        rational_patches=_rational_patches(directions),
        junction_order=1,
        directions=directions,
        scale=1,
    )
    values.update(overrides)
    result = M.exact_piecewise_rational_radial_nominal_inverse_witnesses(
        matrix,
        center=values["center"],
        axis_u=values["axis_u"],
        axis_v=values["axis_v"],
        rational_patches=values["rational_patches"],
        junction_order=values["junction_order"],
        directions=values["directions"],
        spectral_reference_scale=values["scale"],
        sqrt_precision=48,
    )
    return result, values


def _verified(matrix=((0,),), uncertainty=(((0, 0),),), **overrides):
    construction, values = _construct(matrix, **overrides)
    assert construction.approximate_inverses is not None
    return M.verified_componentwise_residual_piecewise_rational_radial_contour(
        matrix,
        uncertainty_radii=uncertainty,
        center=values["center"],
        axis_u=values["axis_u"],
        axis_v=values["axis_v"],
        rational_patches=values["rational_patches"],
        junction_order=values["junction_order"],
        directions=values["directions"],
        approximate_inverses=construction.approximate_inverses,
        spectral_reference_scale=values["scale"],
        sqrt_precision=48,
    )


def test_genuine_piecewise_rational_c1_contour_excludes_poles_and_passes() -> None:
    result = _verified()
    contour = result.contour
    assert result.validation_level == "VERIFIED_PIECEWISE_RATIONAL_RADIAL_CQ_RESIDUAL_CONTOUR"
    assert result.rank_preserved_for_entire_family
    assert contour.denominator_pole_exclusion_verified
    assert contour.periodic_rational_cq_contour_verified
    assert all(values == (1, 0) for values in contour.junction_quotient_jets)
    assert contour.minimum_denominator_lower > 0


def test_constant_denominator_reduces_to_piecewise_polynomial_receipts() -> None:
    polynomial_patches = tuple(
        (numerator[0], numerator[1]) for numerator, _ in _rational_patches(RATIONAL_EIGHT)
    )
    rational_patches = tuple((patch, (1, ())) for patch in polynomial_patches)
    rational = _verified(rational_patches=rational_patches)
    construction = P.exact_piecewise_polynomial_radial_nominal_inverse_witnesses(
        ((0,),),
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        radial_patches=polynomial_patches,
        junction_order=1,
        directions=RATIONAL_EIGHT,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert construction.contour.contour_nodes == rational.contour.contour_nodes
    assert construction.contour.normalized_cover_chord_upper == rational.contour.normalized_cover_chord_upper


def test_c1_rational_bumps_refuse_false_c2_promotion() -> None:
    with pytest.raises(ValueError, match="derivative order 2"):
        _construct(junction_order=2)


def test_quotient_value_mismatch_is_rejected() -> None:
    patches = list(_rational_patches(RATIONAL_EIGHT))
    numerator, denominator = patches[0]
    patches[0] = ((numerator[0] + F(1, 100), numerator[1]), denominator)
    with pytest.raises(ValueError, match="junction mismatch"):
        _construct(rational_patches=tuple(patches))


def test_denominator_pole_margin_and_numerator_positivity_fail_closed() -> None:
    patches = list(_rational_patches(RATIONAL_EIGHT))
    numerator, _ = patches[0]
    patches[0] = (numerator, (F(1, 4), ((2, 0, F(1, 4)),)))
    with pytest.raises(ValueError, match="denominator pole margin"):
        _construct(rational_patches=tuple(patches))
    patches = list(_rational_patches(RATIONAL_EIGHT))
    _, denominator = patches[0]
    patches[0] = ((F(1, 4), ((2, 0, F(1, 4)),)), denominator)
    with pytest.raises(ValueError, match="numerator positivity"):
        _construct(rational_patches=tuple(patches))


def test_patch_count_and_junction_order_are_strict() -> None:
    with pytest.raises(ValueError, match="one .* per mesh arc"):
        _construct(rational_patches=_rational_patches(RATIONAL_EIGHT)[:-1])
    with pytest.raises(ValueError, match="at least one"):
        _construct(junction_order=0)


def test_anisotropic_cardinal_cover_fails_and_eight_knots_pass() -> None:
    coarse = _verified(
        directions=CARDINAL,
        rational_patches=_rational_patches(CARDINAL),
        axis_u=F(4, 3),
    )
    fine = _verified(axis_u=F(4, 3))
    assert coarse.status == "VERIFIED_PIECEWISE_RATIONAL_RADIAL_COVER_NONPOSITIVE"
    assert fine.validation_level is not None


def test_singular_knot_is_reported_separately() -> None:
    result, _ = _construct(matrix=((1,),))
    assert result.status == "EXACT_PIECEWISE_RATIONAL_RADIAL_NODE_SINGULAR"
    assert result.approximate_inverses is None


def test_interval_projector_bound_and_scale_covariance() -> None:
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
