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
FEO = _load(
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization",
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py",
)
M = _load(
    "ce_verified_stereographic_ellipse",
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization.py",
)


def _run(**overrides):
    args = dict(
        nominal_transition=((0, 0), (0, (0, 4))),
        eigenvectors=((1, 0), (0, 1)),
        eigenvalues=(0, (0, 4)),
        target_inside_labels=(True, False),
        center_real_interval=(0, 0),
        center_imag_interval=(0, 0),
        semiaxis_u_interval=(2, 2),
        semiaxis_v_interval=(1, 1),
        orientation_parameter_interval=(-1, 1),
        spectral_reference_scale=1,
        normalized_optimality_tolerance=F(1, 16),
        maximum_cells=8192,
    )
    args.update(overrides)
    return M.verified_continuous_stereographic_ellipse_spectral_margin_optimization(**args)


def test_continuous_orientation_box_is_globally_certified() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.orientation_optimized
    assert result.continuous_parameter_box_covered
    assert not result.finite_grid_only
    assert result.epsilon_global_optimality_verified
    assert result.positive_target_margin_verified
    assert result.certified_optimality_gap <= F(1, 16)
    assert abs(result.selected_orientation_parameter) <= F(1, 32)


def test_true_geometric_margin_does_not_keep_stereographic_scale_factor() -> None:
    value = R.QComplex(0, 4)
    center = R.QComplex(0, 0)
    for t in (F(-2), F(-1), F(-1, 2), F(0), F(1, 2), F(1), F(2)):
        unit, _ = M._orientation_at(t)
        stereo = M._point_score(value, False, center, F(2), F(1), t)
        fixed = FEO._point_score(value, False, center, F(2), F(1), unit)
        assert stereo == fixed


def test_cell_upper_contains_dense_rational_orientation_samples() -> None:
    result = _run(normalized_optimality_tolerance=100, maximum_cells=1)
    root = result.terminal_cells[0]
    for numerator in range(-16, 17):
        t = F(numerator, 16)
        scores = (
            M._point_score(R.QComplex(0, 0), True, R.QComplex(0, 0), F(2), F(1), t),
            M._point_score(R.QComplex(0, 4), False, R.QComplex(0, 0), F(2), F(1), t),
        )
        assert min(scores) <= root.cell_global_upper


def test_singleton_orientation_is_exact() -> None:
    result = _run(
        orientation_parameter_interval=(1, 1),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.validation_level is not None
    assert result.selected_orientation_unit_u == R.QComplex(0, 1)
    assert result.selected_orientation_unit_v == R.QComplex(-1, 0)
    assert result.selected_orientation_unit_verified
    assert result.certified_optimality_gap == 0


def test_center_axes_and_orientation_can_all_vary_continuously() -> None:
    result = _run(
        center_real_interval=(F(-1, 8), F(1, 8)),
        center_imag_interval=(F(-1, 8), F(1, 8)),
        semiaxis_u_interval=(F(15, 8), F(17, 8)),
        semiaxis_v_interval=(F(7, 8), F(9, 8)),
        orientation_parameter_interval=(F(-1, 4), F(1, 4)),
        normalized_optimality_tolerance=F(1, 2),
        maximum_cells=8192,
    )
    assert result.validation_level is not None
    assert result.continuous_parameter_box_covered
    assert result.cells_evaluated > 1


def test_circle_axes_make_orientation_geometrically_irrelevant() -> None:
    value = R.QComplex(F(3, 2), F(-2, 3))
    radius = F(5, 2)
    center = R.QComplex(F(1, 3), F(1, 4))
    scores = {
        M._point_score(value, True, center, radius, radius, t)
        for t in (F(-3), F(-1), F(0), F(1, 2), F(2))
    }
    assert scores == {radius * radius * (radius * radius - (value - center).abs_squared())}


def test_exact_oblique_projector_is_preserved_during_orientation_search() -> None:
    result = _run(
        nominal_transition=((0, (0, 4)), (0, (0, 4))),
        eigenvectors=((1, 1), (0, 1)),
    )
    assert result.projector_identity_verified
    assert result.selected_projector == (
        (R.QComplex(1, 0), R.QComplex(-1, 0)),
        (R.QComplex(0, 0), R.QComplex(0, 0)),
    )
    assert result.selected_projector_rank == 1


def test_raw_spectral_scale_covariance() -> None:
    base = _run()
    scaled = _run(
        nominal_transition=((0, 0), (0, (0, 28))),
        eigenvalues=(0, (0, 28)),
        semiaxis_u_interval=(14, 14),
        semiaxis_v_interval=(7, 7),
        spectral_reference_scale=7,
    )
    assert scaled.normalized_transition == base.normalized_transition
    assert scaled.normalized_eigenvalues == base.normalized_eigenvalues
    assert scaled.selected_signed_ellipse_margin == base.selected_signed_ellipse_margin
    assert scaled.certified_optimality_gap == base.certified_optimality_gap


def test_boundary_contact_is_rejected() -> None:
    result = _run(
        nominal_transition=(((1, 0),),),
        eigenvectors=((1,),),
        eigenvalues=((1, 0),),
        target_inside_labels=(True,),
        semiaxis_u_interval=(1, 1),
        semiaxis_v_interval=(1, 1),
        orientation_parameter_interval=(0, 0),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.validation_level is None
    assert "STEREOGRAPHIC_ELLIPSE_NO_POSITIVE_TARGET_MARGIN" in result.failure_codes


def test_wrong_diagonalization_witness_fails_closed() -> None:
    result = _run(eigenvalues=(0, (0, 5)))
    assert result.validation_level is None
    assert "STEREOGRAPHIC_ELLIPSE_EXACT_DIAGONALIZATION_WITNESS_FAILED" in result.failure_codes


def test_zero_tolerance_small_budget_fails_closed() -> None:
    result = _run(normalized_optimality_tolerance=0, maximum_cells=1)
    assert result.validation_level is None
    assert "STEREOGRAPHIC_ELLIPSE_OPTIMIZATION_CELL_BUDGET_EXCEEDED" in result.failure_codes
    assert not result.continuous_parameter_box_covered


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("semiaxis_u_interval", (0, 1), "strictly positive"),
        ("semiaxis_v_interval", (-1, 1), "strictly positive"),
        ("spectral_reference_scale", 0, "positive"),
        ("normalized_optimality_tolerance", -1, "nonnegative"),
        ("maximum_cells", True, "positive built-in integer"),
        ("orientation_parameter_interval", (1, -1), "lower"),
        ("orientation_parameter_interval", (0.0, 1), "exact"),
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
