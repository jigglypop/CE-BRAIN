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


for name in (
    "verified_rational_contour", "verified_interval_contour", "verified_interval_tightening",
    "verified_interval_residual", "verified_algebraic_riesz_projector",
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization",
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization",
    "verified_continuous_periodic_spline_knot_optimization",
):
    _load(name, f"{name}.py")
G = _load("ce_verified_defective_general_affine", "verified_defective_general_affine_moving_knot_spline_bridge.py")


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))
P = ((1, 0, 0), (0, 1, 0), (0, 0, 0))
R8 = ((0, 0, 0), (0, 0, 0), (0, 0, F(1, 8)))


def _run(**overrides):
    args = dict(
        nominal_transition=((0, 1, 0), (0, 0, 0), (0, 0, 8)),
        projector=P, exterior_centered_inverse=R8, center=0,
        axis_u=4, axis_v=(2, 2), spectral_reference_scale=1,
        knot_parameter_intervals=BOXES,
        patch_amplitudes=(F(1, 100), F(1, 200), F(1, 300), F(1, 400)),
        junction_order=1, normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384, sqrt_precision=48,
    )
    args.update(overrides)
    return G.verified_defective_general_affine_moving_knot_spline_bridge(**args)


def test_defective_jordan_block_is_certified_under_real_shear() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.general_shear_affine_verified
    assert result.defective_matrix_admitted
    assert result.exact_projector_rank == 2
    assert not result.diagonalization_witness_required


def test_affine_singular_value_sandwich_receipts_are_self_checked() -> None:
    result = _run()
    assert result.affine_orientation_determinant == 8
    assert result.affine_frobenius_norm_squared == 24
    assert result.affine_minimum_singular_value_squared_lower == F(8, 3)
    assert all(result.singular_value_sqrt_self_checks)
    assert result.affine_minimum_singular_value_lower ** 2 <= F(8, 3)
    assert result.affine_operator_norm_upper ** 2 >= 24


def test_uniform_gaps_and_algebraic_resolvent_are_positive() -> None:
    result = _run()
    assert result.uniform_euclidean_inner_radius_lower > 1
    assert result.inside_affine_gap_lower > 0
    assert result.exterior_affine_reciprocal_gap_lower > 0
    assert result.algebraic_uniform_resolvent_norm_upper > 0


def test_inside_equality_is_rejected_exactly() -> None:
    base = _run()
    value = base.uniform_euclidean_inner_radius_lower
    result = _run(nominal_transition=((0, value, 0), (0, 0, 0), (0, 0, 8)))
    assert result.validation_level is None
    assert "DEFECTIVE_GENERAL_AFFINE_INSIDE_GAP_NONPOSITIVE" in result.failure_codes


def test_outside_equality_is_rejected_exactly() -> None:
    base = _run()
    radius = base.uniform_euclidean_outer_radius_upper
    result = _run(
        nominal_transition=((0, 1, 0), (0, 0, 0), (0, 0, radius)),
        exterior_centered_inverse=((0, 0, 0), (0, 0, 0), (0, 0, 1 / radius)),
    )
    assert result.validation_level is None
    assert "DEFECTIVE_GENERAL_AFFINE_EXTERIOR_GAP_NONPOSITIVE" in result.failure_codes


def test_wrong_orientation_and_degenerate_axes_fail_closed() -> None:
    with pytest.raises(ValueError, match="positive orientation"):
        _run(axis_v=(2, -2))
    with pytest.raises(ValueError, match="positive orientation"):
        _run(axis_v=2)


def test_bad_algebraic_witness_is_not_promoted() -> None:
    result = _run(projector=((1, 0, 1), (0, 1, 0), (0, 0, 0)))
    assert result.validation_level is None
    assert "DEFECTIVE_GENERAL_AFFINE_ALGEBRAIC_PROJECTOR_FAILED" in result.failure_codes


def test_raw_scale_covariance_includes_affine_axes() -> None:
    base = _run()
    scaled = _run(
        nominal_transition=((0, 7, 0), (0, 0, 0), (0, 0, 56)),
        axis_u=28, axis_v=(14, 14), spectral_reference_scale=7,
    )
    assert scaled.normalized_axis_u == base.normalized_axis_u
    assert scaled.inside_affine_gap_lower == base.inside_affine_gap_lower


def test_empirical_and_dimension_claims_remain_false() -> None:
    assert not _run().empirical_matrix_provenance_verified
