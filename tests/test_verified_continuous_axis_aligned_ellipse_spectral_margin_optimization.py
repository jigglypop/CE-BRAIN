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
M = _load(
    "ce_verified_continuous_ellipse",
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py",
)


def _run(**overrides):
    args = dict(
        nominal_transition=((0, 0), (0, 4)),
        eigenvectors=((1, 0), (0, 1)),
        eigenvalues=(0, 4),
        target_inside_labels=(True, False),
        orientation_unit_u=1,
        center_real_interval=(0, 0),
        center_imag_interval=(0, 0),
        semiaxis_u_interval=(1, 3),
        semiaxis_v_interval=(F(1, 2), 1),
        spectral_reference_scale=1,
        normalized_quartic_optimality_tolerance=F(1, 16),
        maximum_cells=4096,
    )
    args.update(overrides)
    return M.verified_continuous_axis_aligned_ellipse_spectral_margin_optimization(**args)


def test_continuous_non_circle_shape_box_is_globally_certified() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.epsilon_global_optimality_verified
    assert result.positive_target_margin_verified
    assert result.continuous_parameter_box_covered
    assert not result.finite_grid_only
    assert result.selected_normalized_semiaxis_u != result.selected_normalized_semiaxis_v
    assert result.certified_optimality_gap <= F(1, 16)


def test_exact_interval_upper_contains_many_point_scores() -> None:
    result = _run(normalized_quartic_optimality_tolerance=1, maximum_cells=1)
    root = result.terminal_cells[0]
    for a in (F(1), F(3, 2), F(2), F(5, 2), F(3)):
        for b in (F(1, 2), F(3, 4), F(1)):
            scores = (
                M._point_score(R.QComplex(0, 0), True, R.QComplex(0, 0), a, b, R.QComplex(1, 0)),
                M._point_score(R.QComplex(4, 0), False, R.QComplex(0, 0), a, b, R.QComplex(1, 0)),
            )
            assert min(scores) <= root.cell_global_upper


def test_singleton_score_and_global_upper_are_exact() -> None:
    result = _run(
        semiaxis_u_interval=(2, 2),
        semiaxis_v_interval=(1, 1),
        normalized_quartic_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.selected_signed_quartic_margin == 4
    assert result.certified_global_score_upper == 4
    assert result.certified_optimality_gap == 0


def test_circle_subfamily_has_same_sign_as_circle_squared_margin() -> None:
    center = R.QComplex(F(1, 2), F(-1, 3))
    value = R.QComplex(2, 1)
    radius = F(5, 2)
    ellipse = M._point_score(value, True, center, radius, radius, R.QComplex(1, 0))
    circle = radius * radius - (value - center).abs_squared()
    assert ellipse == radius * radius * circle


def test_fixed_rational_rotation_is_supported() -> None:
    unit = (F(3, 5), F(4, 5))
    inside = (F(3, 5), F(4, 5))
    outside = (F(18, 5), F(24, 5))
    result = _run(
        nominal_transition=((inside, 0), (0, outside)),
        eigenvalues=(inside, outside),
        orientation_unit_u=unit,
        semiaxis_u_interval=(2, 3),
        semiaxis_v_interval=(F(1, 2), 1),
    )
    assert result.validation_level is not None
    assert result.orientation_unit_v == R.QComplex(F(-4, 5), F(3, 5))
    assert result.selected_axes_positive_orientation_verified


def test_exact_oblique_projector_is_returned_and_verified() -> None:
    vectors = ((1, 1), (0, 1))
    matrix = ((0, 4), (0, 4))
    result = _run(nominal_transition=matrix, eigenvectors=vectors)
    assert result.projector_identity_verified
    assert result.selected_projector == (
        (R.QComplex(1, 0), R.QComplex(-1, 0)),
        (R.QComplex(0, 0), R.QComplex(0, 0)),
    )
    assert result.selected_projector_rank == 1


def test_raw_scale_covariance_preserves_normalized_receipt() -> None:
    base = _run()
    scaled = _run(
        nominal_transition=((0, 0), (0, 28)),
        eigenvalues=(0, 28),
        center_real_interval=(0, 0),
        center_imag_interval=(0, 0),
        semiaxis_u_interval=(7, 21),
        semiaxis_v_interval=(F(7, 2), 7),
        spectral_reference_scale=7,
    )
    assert scaled.normalized_transition == base.normalized_transition
    assert scaled.normalized_eigenvalues == base.normalized_eigenvalues
    assert scaled.selected_signed_quartic_margin == base.selected_signed_quartic_margin
    assert scaled.certified_optimality_gap == base.certified_optimality_gap


def test_boundary_contact_is_rejected() -> None:
    result = _run(
        nominal_transition=((0,),),
        eigenvectors=((1,),),
        eigenvalues=(1,),
        target_inside_labels=(True,),
        semiaxis_u_interval=(1, 1),
        semiaxis_v_interval=(1, 1),
        normalized_quartic_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.validation_level is None
    assert "CONTINUOUS_ELLIPSE_NO_POSITIVE_TARGET_MARGIN" in result.failure_codes


def test_wrong_diagonalization_witness_fails_closed() -> None:
    result = _run(eigenvalues=(0, 5))
    assert result.validation_level is None
    assert "CONTINUOUS_ELLIPSE_EXACT_DIAGONALIZATION_WITNESS_FAILED" in result.failure_codes


def test_small_cell_budget_fails_closed() -> None:
    result = _run(normalized_quartic_optimality_tolerance=0, maximum_cells=1)
    assert result.validation_level is None
    assert "CONTINUOUS_ELLIPSE_OPTIMIZATION_CELL_BUDGET_EXCEEDED" in result.failure_codes
    assert not result.continuous_parameter_box_covered


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("orientation_unit_u", (1, 1), "unit direction"),
        ("semiaxis_u_interval", (0, 1), "strictly positive"),
        ("semiaxis_v_interval", (-1, 1), "strictly positive"),
        ("spectral_reference_scale", 0, "positive"),
        ("normalized_quartic_optimality_tolerance", -1, "nonnegative"),
        ("maximum_cells", True, "positive built-in integer"),
    ],
)
def test_invalid_domains_fail_closed(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _run(**{field: value})


def test_labels_must_be_exact_booleans() -> None:
    with pytest.raises(ValueError, match="built-in booleans"):
        _run(target_inside_labels=(1, 0))


def test_empirical_and_orientation_optimization_claims_remain_false() -> None:
    result = _run()
    assert not result.empirical_matrix_provenance_verified
    assert not result.orientation_optimized
