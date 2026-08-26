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
_load("verified_algebraic_riesz_projector", "verified_algebraic_riesz_projector.py")
_load("verified_continuous_axis_aligned_ellipse_spectral_margin_optimization", "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py")
_load("verified_continuous_stereographic_ellipse_spectral_margin_optimization", "verified_continuous_stereographic_ellipse_spectral_margin_optimization.py")
_load("verified_continuous_periodic_spline_knot_optimization", "verified_continuous_periodic_spline_knot_optimization.py")
D = _load("ce_verified_defective_conformal_knot", "verified_defective_conformal_moving_knot_spline_bridge.py")


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))
P = ((1, 0, 0), (0, 1, 0), (0, 0, 0))
R = ((0, 0, 0), (0, 0, 0), (0, 0, F(1, 4)))


def _run(**overrides):
    args = dict(
        nominal_transition=((0, 1, 0), (0, 0, 0), (0, 0, 4)),
        projector=P, exterior_centered_inverse=R, center=0,
        conformal_scale=2, conformal_unit=1, spectral_reference_scale=1,
        knot_parameter_intervals=BOXES,
        patch_amplitudes=(F(1, 100), F(1, 200), F(1, 300), F(1, 400)),
        junction_order=1, normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384, sqrt_precision=48,
    )
    args.update(overrides)
    return D.verified_defective_conformal_moving_knot_spline_bridge(**args)


def test_defective_jordan_block_preserves_rank_over_whole_knot_box() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.defective_matrix_admitted
    assert result.entire_moving_knot_box_rank_preserved
    assert result.exact_projector_rank == 2
    assert not result.diagonalization_witness_required


def test_uniform_algebraic_gaps_and_resolvent_are_positive() -> None:
    result = _run()
    assert result.uniform_inner_radius_lower == 2
    assert result.uniform_outer_radius_upper == F(58, 25)
    assert result.inside_block_norm_upper == 1
    assert result.exterior_inverse_norm_upper == F(1, 4)
    assert result.inside_algebraic_gap_lower == 1
    assert result.exterior_reciprocal_gap_lower == F(21, 50)
    assert result.algebraic_uniform_resolvent_norm_upper > 0


def test_exact_rotation_unit_is_admitted() -> None:
    result = _run(conformal_unit=(0, 1))
    assert result.validation_level is not None
    assert result.conformal_unit_squared_norm == 1


def test_inside_equality_fails_closed() -> None:
    result = _run(conformal_scale=1)
    assert result.validation_level is None
    assert "DEFECTIVE_CONFORMAL_INSIDE_GAP_NONPOSITIVE" in result.failure_codes


def test_outer_envelope_equality_fails_closed() -> None:
    result = _run(
        nominal_transition=((0, 1, 0), (0, 0, 0), (0, 0, F(58, 25))),
        exterior_centered_inverse=((0, 0, 0), (0, 0, 0), (0, 0, F(25, 58))),
    )
    assert result.validation_level is None
    assert "DEFECTIVE_CONFORMAL_EXTERIOR_GAP_NONPOSITIVE" in result.failure_codes


def test_bad_projector_or_inverse_is_not_promoted() -> None:
    result = _run(projector=((1, 0, 1), (0, 1, 0), (0, 0, 0)))
    assert result.validation_level is None
    assert "DEFECTIVE_CONFORMAL_ALGEBRAIC_PROJECTOR_FAILED" in result.failure_codes


def test_raw_scale_covariance() -> None:
    base = _run()
    scaled = _run(
        nominal_transition=((0, 7, 0), (0, 0, 0), (0, 0, 28)),
        exterior_centered_inverse=((0, 0, 0), (0, 0, 0), (0, 0, F(1, 4))),
        conformal_scale=14, spectral_reference_scale=7,
    )
    assert scaled.normalized_conformal_scale == base.normalized_conformal_scale
    assert scaled.inside_algebraic_gap_lower == base.inside_algebraic_gap_lower


def test_nonunit_or_inexact_conformal_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="squared norm one"):
        _run(conformal_unit=(1, 1))
    with pytest.raises(ValueError, match="exact"):
        _run(conformal_scale=2.0)


def test_general_shear_empirical_and_dimension_claims_remain_false() -> None:
    result = _run()
    assert not result.general_shear_affine_verified
    assert not result.empirical_matrix_provenance_verified
