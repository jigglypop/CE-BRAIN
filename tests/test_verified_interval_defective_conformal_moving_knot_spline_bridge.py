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
    "verified_rational_contour", "verified_interval_contour",
    "verified_interval_tightening", "verified_interval_residual",
    "verified_algebraic_riesz_projector",
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization",
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization",
    "verified_continuous_periodic_spline_knot_optimization",
    "verified_defective_conformal_moving_knot_spline_bridge",
):
    _load(name, f"{name}.py")
I = _load("ce_verified_interval_defective_conformal", "verified_interval_defective_conformal_moving_knot_spline_bridge.py")


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
        matrix_uncertainty_frobenius_upper=F(1, 4),
    )
    args.update(overrides)
    return I.verified_interval_defective_conformal_moving_knot_spline_bridge(**args)


def test_defective_interval_ball_preserves_rank_without_diagonalization() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.defective_interval_matrix_family_resolvent_verified
    assert result.defective_interval_matrix_family_rank_preserved
    assert result.nominal_defective_bridge.exact_projector_rank == 2
    assert not result.diagonalization_witness_required


def test_exact_neumann_receipts_use_algebraic_resolvent() -> None:
    result = _run()
    assert result.nominal_algebraic_resolvent_norm_upper == F(67, 42)
    assert result.neumann_product_upper == F(67, 168)
    assert result.neumann_margin_lower == F(101, 168)
    assert result.perturbed_algebraic_resolvent_norm_upper == F(268, 101)


def test_projector_bound_retains_contour_length_and_two_resolvents() -> None:
    result = _run()
    assert result.normalized_contour_length_over_two_pi_upper > 0
    expected = (
        result.normalized_contour_length_over_two_pi_upper
        * F(1, 4) * F(67, 42) ** 2 / F(101, 168)
    )
    assert result.interval_projector_perturbation_norm_upper == expected


@pytest.mark.parametrize("uncertainty", [F(42, 67), F(1, 1)])
def test_neumann_equality_and_failure_are_rejected(uncertainty: F) -> None:
    result = _run(matrix_uncertainty_frobenius_upper=uncertainty)
    assert result.validation_level is None
    assert "INTERVAL_DEFECTIVE_CONFORMAL_NEUMANN_MARGIN_NONPOSITIVE" in result.failure_codes


def test_nominal_algebraic_failure_is_not_promoted() -> None:
    result = _run(conformal_scale=1)
    assert result.validation_level is None
    assert "INTERVAL_DEFECTIVE_CONFORMAL_NOMINAL_BRIDGE_FAILED" in result.failure_codes


def test_raw_scale_covariance_includes_uncertainty() -> None:
    base = _run()
    scaled = _run(
        nominal_transition=((0, 7, 0), (0, 0, 0), (0, 0, 28)),
        conformal_scale=14, spectral_reference_scale=7,
        matrix_uncertainty_frobenius_upper=F(7, 4),
    )
    assert scaled.normalized_matrix_uncertainty_frobenius_upper == base.normalized_matrix_uncertainty_frobenius_upper
    assert scaled.neumann_margin_lower == base.neumann_margin_lower


def test_zero_uncertainty_reduces_to_nominal_defective_bridge() -> None:
    result = _run(matrix_uncertainty_frobenius_upper=0)
    assert result.validation_level is not None
    assert result.neumann_margin_lower == 1
    assert result.interval_projector_perturbation_norm_upper == 0


def test_invalid_uncertainty_and_honesty_boundaries() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        _run(matrix_uncertainty_frobenius_upper=F(-1, 4))
    with pytest.raises(ValueError, match="exact"):
        _run(matrix_uncertainty_frobenius_upper=0.25)
    result = _run()
    assert not result.general_shear_affine_verified
    assert not result.empirical_matrix_provenance_verified
