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
_load("verified_continuous_axis_aligned_ellipse_spectral_margin_optimization", "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py")
_load("verified_continuous_stereographic_ellipse_spectral_margin_optimization", "verified_continuous_stereographic_ellipse_spectral_margin_optimization.py")
_load("verified_continuous_periodic_spline_knot_optimization", "verified_continuous_periodic_spline_knot_optimization.py")
_load("verified_moving_knot_spline_spectral_rank_bridge", "verified_moving_knot_spline_spectral_rank_bridge.py")
I = _load("ce_verified_interval_moving_knot", "verified_interval_moving_knot_spline_spectral_rank_bridge.py")


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))


def _run(**overrides):
    args = dict(
        nominal_transition=((0, 0), (0, 3)), eigenvectors=((1, 0), (0, 1)),
        eigenvalues=(0, 3), target_inside_labels=(True, False), center=0,
        axis_u=1, axis_v=(0, 1), spectral_reference_scale=1,
        knot_parameter_intervals=BOXES,
        patch_amplitudes=(F(1, 100), F(1, 200), F(1, 300), F(1, 400)),
        junction_order=1, normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384, sqrt_precision=48,
        matrix_uncertainty_frobenius_upper=F(1, 8),
    )
    args.update(overrides)
    return I.verified_interval_moving_knot_spline_spectral_rank_bridge(**args)


def test_whole_matrix_ball_and_knot_box_preserve_rank() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.interval_matrix_family_resolvent_verified
    assert result.interval_matrix_family_rank_preserved
    assert result.interval_matrix_family_verified
    assert result.nominal_bridge.selected_projector_rank == 1


def test_neumann_and_perturbed_resolvent_receipts_are_exact() -> None:
    result = _run()
    assert result.nominal_uniform_resolvent_norm_upper == 4
    assert result.neumann_product_upper == F(1, 2)
    assert result.neumann_margin_lower == F(1, 2)
    assert result.perturbed_uniform_resolvent_norm_upper == 8


def test_projector_perturbation_bound_contains_length_and_conditioning() -> None:
    result = _run()
    assert result.affine_frobenius_norm_upper ** 2 >= 2
    assert result.normalized_contour_length_over_two_pi_upper > 0
    expected = result.normalized_contour_length_over_two_pi_upper * 4
    assert result.interval_projector_perturbation_norm_upper == expected


@pytest.mark.parametrize("uncertainty", [F(1, 4), F(1, 3)])
def test_neumann_equality_and_failure_are_rejected(uncertainty: F) -> None:
    result = _run(matrix_uncertainty_frobenius_upper=uncertainty)
    assert result.validation_level is None
    assert "INTERVAL_MOVING_KNOT_NEUMANN_MARGIN_NONPOSITIVE" in result.failure_codes
    assert not result.interval_matrix_family_rank_preserved


def test_oblique_conditioning_tightens_admissible_uncertainty() -> None:
    result = _run(
        nominal_transition=((0, 3), (0, 3)),
        eigenvectors=((1, 1), (0, 1)),
        matrix_uncertainty_frobenius_upper=F(1, 8),
    )
    assert result.nominal_uniform_resolvent_norm_upper == 6
    assert result.neumann_product_upper == F(3, 4)
    assert result.perturbed_uniform_resolvent_norm_upper == 24


def test_raw_scale_covariance_includes_uncertainty() -> None:
    base = _run()
    scaled = _run(
        nominal_transition=((0, 0), (0, 21)), eigenvalues=(0, 21),
        axis_u=7, axis_v=(0, 7), spectral_reference_scale=7,
        matrix_uncertainty_frobenius_upper=F(7, 8),
    )
    assert scaled.normalized_matrix_uncertainty_frobenius_upper == base.normalized_matrix_uncertainty_frobenius_upper
    assert scaled.neumann_product_upper == base.neumann_product_upper


def test_zero_uncertainty_is_a_valid_nominal_reduction() -> None:
    result = _run(matrix_uncertainty_frobenius_upper=0)
    assert result.validation_level is not None
    assert result.neumann_margin_lower == 1
    assert result.interval_projector_perturbation_norm_upper == 0


def test_invalid_uncertainty_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        _run(matrix_uncertainty_frobenius_upper=F(-1, 8))
    with pytest.raises(ValueError, match="exact"):
        _run(matrix_uncertainty_frobenius_upper=0.1)


def test_defective_empirical_and_dimension_claims_remain_false() -> None:
    result = _run()
    assert not result.defective_or_no_witness_family_verified
    assert not result.empirical_matrix_provenance_verified
