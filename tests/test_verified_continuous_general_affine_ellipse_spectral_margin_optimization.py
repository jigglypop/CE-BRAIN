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
SE = _load(
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization",
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization.py",
)
M = _load(
    "ce_verified_general_affine_ellipse",
    "verified_continuous_general_affine_ellipse_spectral_margin_optimization.py",
)


def _run(**overrides):
    args = dict(
        nominal_transition=(((F(1, 2), F(1, 4)), 0), (0, (4, 4))),
        eigenvectors=((1, 0), (0, 1)),
        eigenvalues=((F(1, 2), F(1, 4)), (4, 4)),
        target_inside_labels=(True, False),
        center_real_interval=(0, 0),
        center_imag_interval=(0, 0),
        semiaxis_u_interval=(2, 2),
        semiaxis_v_interval=(1, 1),
        shear_interval=(-1, 1),
        orientation_parameter_interval=(0, 0),
        spectral_reference_scale=1,
        normalized_optimality_tolerance=F(1, 16),
        maximum_cells=16384,
    )
    args.update(overrides)
    return M.verified_continuous_general_affine_ellipse_spectral_margin_optimization(**args)


def test_continuous_shear_box_is_globally_certified() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.shear_optimized and result.orientation_optimized
    assert result.continuous_parameter_box_covered
    assert not result.finite_grid_only
    assert result.epsilon_global_optimality_verified
    assert result.certified_optimality_gap <= F(1, 16)
    assert result.selected_normalized_shear > F(1, 2)


def test_zero_shear_reduces_exactly_to_stereographic_ellipse_score() -> None:
    value = R.QComplex(F(3, 2), F(-2, 3))
    center = R.QComplex(F(1, 3), F(1, 4))
    for t in (F(-2), F(-1, 2), F(0), F(3, 5), F(2)):
        affine = M._point_score(value, True, center, F(2), F(1), F(0), t)
        orthogonal = SE._point_score(value, True, center, F(2), F(1), t)
        assert affine == orthogonal


def test_margin_equals_inverse_coordinate_ellipse_criterion() -> None:
    value = R.QComplex(F(3, 2), F(5, 4))
    center = R.QComplex(F(1, 4), F(-1, 3))
    a, b, shear, t = F(2), F(3, 2), F(2, 5), F(3, 7)
    unit_u, unit_v = SE._orientation_at(t)
    delta = value - center
    xi = unit_u.real * delta.real + unit_u.imag * delta.imag
    eta = unit_v.real * delta.real + unit_v.imag * delta.imag
    y = eta / b
    x = (xi - shear * y) / a
    expected = a * a * b * b * (1 - x * x - y * y)
    assert M._point_score(value, True, center, a, b, shear, t) == expected


def test_qr_axes_have_positive_determinant_independent_of_shear() -> None:
    for t in (F(-3), F(-1), F(0), F(2, 3), F(4)):
        for shear in (F(-5), F(0), F(7, 3)):
            axis_u, axis_v, determinant = M._point_geometry(F(2), F(3), shear, t)
            assert determinant == 6
            assert axis_u.real * axis_v.imag - axis_u.imag * axis_v.real == 6


def test_cell_upper_contains_dense_rational_shear_orientation_samples() -> None:
    result = _run(
        orientation_parameter_interval=(-1, 1),
        normalized_optimality_tolerance=1000,
        maximum_cells=1,
    )
    root = result.terminal_cells[0]
    for si in range(-8, 9):
        for ti in range(-8, 9):
            shear, t = F(si, 8), F(ti, 8)
            scores = (
                M._point_score(R.QComplex(F(1, 2), F(1, 4)), True, R.QComplex(0, 0), F(2), F(1), shear, t),
                M._point_score(R.QComplex(4, 4), False, R.QComplex(0, 0), F(2), F(1), shear, t),
            )
            assert min(scores) <= root.cell_global_upper


def test_singleton_general_affine_geometry_is_exact() -> None:
    result = _run(
        shear_interval=(F(1, 2), F(1, 2)),
        orientation_parameter_interval=(1, 1),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.validation_level is not None
    assert result.selected_axis_u == R.QComplex(0, 2)
    assert result.selected_axis_v == R.QComplex(-1, F(1, 2))
    assert result.selected_orientation_determinant == 2
    assert result.selected_general_affine_geometry_verified
    assert result.certified_optimality_gap == 0


def test_all_six_parameters_can_vary_continuously() -> None:
    result = _run(
        center_real_interval=(F(-1, 16), F(1, 16)),
        center_imag_interval=(F(-1, 16), F(1, 16)),
        semiaxis_u_interval=(F(31, 16), F(33, 16)),
        semiaxis_v_interval=(F(15, 16), F(17, 16)),
        shear_interval=(F(-1, 8), F(1, 8)),
        orientation_parameter_interval=(F(-1, 8), F(1, 8)),
        normalized_optimality_tolerance=F(1, 16),
        maximum_cells=16384,
    )
    assert result.validation_level is not None
    assert result.cells_evaluated > 1
    assert result.continuous_parameter_box_covered


def test_raw_scale_covariance_includes_shear() -> None:
    base = _run()
    scaled = _run(
        nominal_transition=(((F(7, 2), F(7, 4)), 0), (0, (28, 28))),
        eigenvalues=((F(7, 2), F(7, 4)), (28, 28)),
        semiaxis_u_interval=(14, 14),
        semiaxis_v_interval=(7, 7),
        shear_interval=(-7, 7),
        spectral_reference_scale=7,
    )
    assert scaled.normalized_transition == base.normalized_transition
    assert scaled.normalized_eigenvalues == base.normalized_eigenvalues
    assert scaled.normalized_shear_interval == base.normalized_shear_interval
    assert scaled.selected_signed_affine_margin == base.selected_signed_affine_margin


def test_exact_oblique_projector_is_preserved() -> None:
    result = _run(
        nominal_transition=(
            ((F(1, 2), F(1, 4)), (F(7, 2), F(15, 4))),
            (0, (4, 4)),
        ),
        eigenvectors=((1, 1), (0, 1)),
    )
    assert result.projector_identity_verified
    assert result.selected_projector == (
        (R.QComplex(1, 0), R.QComplex(-1, 0)),
        (R.QComplex(0, 0), R.QComplex(0, 0)),
    )


def test_boundary_contact_is_rejected() -> None:
    result = _run(
        nominal_transition=(((1, 0),),),
        eigenvectors=((1,),),
        eigenvalues=((1, 0),),
        target_inside_labels=(True,),
        semiaxis_u_interval=(1, 1),
        semiaxis_v_interval=(1, 1),
        shear_interval=(0, 0),
        orientation_parameter_interval=(0, 0),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.validation_level is None
    assert "GENERAL_AFFINE_ELLIPSE_NO_POSITIVE_TARGET_MARGIN" in result.failure_codes


def test_wrong_diagonalization_witness_fails_closed() -> None:
    result = _run(eigenvalues=(0, (5, 5)))
    assert result.validation_level is None
    assert "GENERAL_AFFINE_ELLIPSE_EXACT_DIAGONALIZATION_WITNESS_FAILED" in result.failure_codes


def test_small_budget_fails_closed() -> None:
    result = _run(normalized_optimality_tolerance=0, maximum_cells=1)
    assert result.validation_level is None
    assert "GENERAL_AFFINE_ELLIPSE_OPTIMIZATION_CELL_BUDGET_EXCEEDED" in result.failure_codes
    assert not result.continuous_parameter_box_covered


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("semiaxis_u_interval", (0, 1), "strictly positive"),
        ("semiaxis_v_interval", (-1, 1), "strictly positive"),
        ("spectral_reference_scale", 0, "positive"),
        ("normalized_optimality_tolerance", -1, "nonnegative"),
        ("maximum_cells", True, "positive built-in integer"),
        ("shear_interval", (1, -1), "lower"),
        ("shear_interval", (0.0, 1), "exact"),
    ],
)
def test_invalid_domains_fail_closed(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _run(**{field: value})


def test_labels_must_be_exact_booleans() -> None:
    with pytest.raises(ValueError, match="built-in booleans"):
        _run(target_inside_labels=(1, 0))


def test_empirical_claim_remains_false() -> None:
    result = _run()
    assert not result.empirical_matrix_provenance_verified
