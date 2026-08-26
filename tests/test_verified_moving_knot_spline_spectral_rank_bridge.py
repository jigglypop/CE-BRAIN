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
_load(
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization",
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py",
)
_load(
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization",
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization.py",
)
_load(
    "verified_continuous_periodic_spline_knot_optimization",
    "verified_continuous_periodic_spline_knot_optimization.py",
)
M = _load(
    "ce_verified_moving_knot_spectral_bridge",
    "verified_moving_knot_spline_spectral_rank_bridge.py",
)


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))


def _run(**overrides):
    args = dict(
        nominal_transition=((0, 0), (0, 3)),
        eigenvectors=((1, 0), (0, 1)),
        eigenvalues=(0, 3),
        target_inside_labels=(True, False),
        center=0,
        axis_u=1,
        axis_v=(0, 1),
        spectral_reference_scale=1,
        knot_parameter_intervals=BOXES,
        patch_amplitudes=(F(1, 100), F(1, 200), F(1, 300), F(1, 400)),
        junction_order=1,
        normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384,
        sqrt_precision=48,
    )
    args.update(overrides)
    return M.verified_moving_knot_spline_spectral_rank_bridge(**args)


def test_entire_continuous_knot_box_has_one_exact_spectral_rank() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.entire_moving_knot_box_resolvent_verified
    assert result.moving_knot_family_spectral_split_verified
    assert result.moving_knot_family_rank_preserved
    assert result.simple_periodic_cq_jordan_family_verified
    assert result.selected_projector_rank == 1
    assert result.knot_optimization.continuous_knot_box_covered


def test_uniform_radial_envelope_margin_is_exact() -> None:
    result = _run()
    assert result.uniform_radial_minimum_lower == 1
    assert result.uniform_radial_maximum_upper == F(29, 25)
    assert result.affine_inverse_coordinate_squared == (0, 9)
    assert result.per_eigenvalue_uniform_signed_squared_margins == (
        1,
        F(4784, 625),
    )
    assert result.uniform_family_margin == 1
    assert result.positive_uniform_family_margin_verified


def test_quantitative_resolvent_bound_includes_affine_and_eigenvector_conditioning() -> None:
    result = _run()
    assert result.affine_frobenius_norm_squared == 2
    assert result.affine_minimum_singular_value_squared_lower == F(1, 2)
    assert result.eigenvector_frobenius_condition_squared_upper == 4
    assert result.per_eigenvalue_normalized_contour_distance_squared_lower[0] == F(1, 2)
    assert result.uniform_normalized_contour_distance_squared_lower == F(1, 2)
    assert result.uniform_affine_contour_distance_squared_lower == F(1, 4)
    assert result.quantitative_resolvent_norm_squared_upper == 16
    assert result.quantitative_resolvent_norm_bound == 4


def test_oblique_witness_increases_the_conditioned_bound() -> None:
    normal = _run()
    oblique = _run(
        nominal_transition=((0, 3), (0, 3)),
        eigenvectors=((1, 1), (0, 1)),
    )
    assert oblique.eigenvector_frobenius_condition_squared_upper == 9
    assert oblique.quantitative_resolvent_norm_squared_upper == 36
    assert oblique.quantitative_resolvent_norm_bound == 6
    assert oblique.quantitative_resolvent_norm_bound > normal.quantitative_resolvent_norm_bound


def test_general_affine_inverse_coordinates_are_used() -> None:
    result = _run(
        nominal_transition=((0, 0), (0, 6)),
        eigenvalues=(0, 6),
        axis_u=2,
        axis_v=(1, 1),
    )
    assert result.validation_level is not None
    assert result.affine_orientation_determinant == 2
    assert result.affine_inverse_coordinate_squared == (0, 9)


def test_exact_oblique_projector_is_verified() -> None:
    result = _run(
        nominal_transition=((0, 3), (0, 3)),
        eigenvectors=((1, 1), (0, 1)),
    )
    assert result.projector_identity_verified
    assert result.selected_projector == (
        (R.QComplex(1, 0), R.QComplex(-1, 0)),
        (R.QComplex(0, 0), R.QComplex(0, 0)),
    )


def test_raw_scale_covariance_includes_center_and_axes() -> None:
    base = _run()
    scaled = _run(
        nominal_transition=((0, 0), (0, 21)),
        eigenvalues=(0, 21),
        center=0,
        axis_u=7,
        axis_v=(0, 7),
        spectral_reference_scale=7,
    )
    assert scaled.normalized_transition == base.normalized_transition
    assert scaled.normalized_eigenvalues == base.normalized_eigenvalues
    assert scaled.normalized_axis_u == base.normalized_axis_u
    assert scaled.uniform_family_margin == base.uniform_family_margin


@pytest.mark.parametrize(
    ("value", "inside", "expected_code"),
    [
        (1, True, "MOVING_KNOT_SPLINE_UNIFORM_SPECTRAL_MARGIN_NONPOSITIVE"),
        (1, False, "MOVING_KNOT_SPLINE_UNIFORM_SPECTRAL_MARGIN_NONPOSITIVE"),
    ],
)
def test_inside_or_outside_envelope_equality_fails_closed(
    value: object, inside: bool, expected_code: str
) -> None:
    result = _run(
        nominal_transition=((value,),),
        eigenvectors=((1,),),
        eigenvalues=(value,),
        target_inside_labels=(inside,),
        patch_amplitudes=(0, 0, 0, 0),
    )
    assert result.validation_level is None
    assert expected_code in result.failure_codes


def test_incorrect_label_assignment_fails_closed() -> None:
    result = _run(target_inside_labels=(True, True))
    assert result.validation_level is None
    assert "MOVING_KNOT_SPLINE_UNIFORM_SPECTRAL_MARGIN_NONPOSITIVE" in result.failure_codes


def test_wrong_diagonalization_witness_fails_closed() -> None:
    result = _run(eigenvalues=(0, 4))
    assert result.validation_level is None
    assert "MOVING_KNOT_SPLINE_EXACT_DIAGONALIZATION_WITNESS_FAILED" in result.failure_codes


def test_knot_optimization_failure_is_not_promoted() -> None:
    result = _run(normalized_knot_optimality_tolerance=0, maximum_knot_cells=1)
    assert result.validation_level is None
    assert "MOVING_KNOT_SPLINE_GEOMETRY_OPTIMIZATION_FAILED" in result.failure_codes
    assert not result.moving_knot_family_rank_preserved


@pytest.mark.parametrize(
    ("matrix", "values", "labels", "rank"),
    [
        (((3,),), (3,), (False,), 0),
        (((0,),), (0,), (True,), 1),
    ],
)
def test_rank_zero_and_full_are_not_special_cases(
    matrix: object, values: object, labels: object, rank: int
) -> None:
    result = _run(
        nominal_transition=matrix,
        eigenvectors=((1,),),
        eigenvalues=values,
        target_inside_labels=labels,
    )
    assert result.validation_level is not None
    assert result.selected_projector_rank == rank


def test_reversed_or_degenerate_affine_axes_fail_closed() -> None:
    with pytest.raises(ValueError, match="positive orientation determinant"):
        _run(axis_v=(0, -1))
    with pytest.raises(ValueError, match="positive orientation determinant"):
        _run(axis_v=2)


def test_labels_must_be_exact_booleans() -> None:
    with pytest.raises(ValueError, match="built-in booleans"):
        _run(target_inside_labels=(1, 0))


def test_inexact_spectral_scale_fails_closed() -> None:
    with pytest.raises(ValueError, match="exact"):
        _run(spectral_reference_scale=1.0)


def test_interval_and_empirical_claims_remain_false() -> None:
    result = _run()
    assert result.quantitative_resolvent_norm_bound is not None
    assert not result.interval_matrix_family_verified
    assert not result.empirical_matrix_provenance_verified
