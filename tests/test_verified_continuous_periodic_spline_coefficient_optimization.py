from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


for name in (
    "verified_rational_contour",
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization",
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization",
    "verified_continuous_periodic_spline_knot_optimization",
):
    _load(name)
C = _load("verified_continuous_periodic_spline_coefficient_optimization")


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))
COEFFICIENTS = tuple((((0, F(1, 100)), (0, F(1, 100)))) for _ in range(4))
WEIGHTS = tuple(((1, 8) for _ in range(4)))


def _run(**overrides):
    args = dict(
        knot_parameter_intervals=BOXES,
        coefficient_intervals=COEFFICIENTS,
        objective_weights=WEIGHTS,
        basis_powers=(2, 3), junction_order=1,
        normalized_radial_maximum_cap=F(43, 25),
        normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384, sqrt_precision=48,
    )
    args.update(overrides)
    return C.verified_continuous_periodic_spline_coefficient_optimization(**args)


def test_exact_fractional_knapsack_optimum_on_every_patch() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.selected_coefficients == tuple(((F(1, 200), F(1, 100)) for _ in range(4)))
    assert result.selected_weighted_objective == result.certified_global_weighted_objective_upper == F(17, 50)
    assert result.exact_continuous_box_linear_optimum_verified


def test_basis_and_selected_radial_receipts_are_exact() -> None:
    result = _run()
    assert result.basis_radial_weights == (16, 64)
    assert result.basis_gradient_weights == (32, 192)
    assert result.per_patch_selected_radial_excess == (F(18, 25),) * 4
    assert result.selected_box_radial_maximum_upper == F(43, 25)


def test_whole_selected_coefficient_box_is_covered() -> None:
    result = _run()
    assert result.selected_admissible_coefficient_box[0] == ((0, F(1, 200)), (0, F(1, 100)))
    assert result.selected_box_radial_minimum_lower == 1
    assert result.continuous_coefficient_box_covered


def test_general_modes_keep_automatic_cq_junction() -> None:
    result = _run(
        basis_powers=(4, 7), junction_order=3,
        normalized_radial_maximum_cap=3,
    )
    assert result.validation_level is not None
    assert result.automatic_endpoint_vanishing_order == 4
    assert result.selected_box_automatic_periodic_cq_junction_verified


def test_positive_lower_corner_above_cap_fails_closed() -> None:
    rows = list(COEFFICIENTS)
    rows[0] = ((F(1, 100), F(1, 100)), (F(1, 100), F(1, 100)))
    result = _run(coefficient_intervals=tuple(rows), normalized_radial_maximum_cap=F(3, 2))
    assert result.validation_level is None
    assert "CONTINUOUS_SPLINE_COEFFICIENT_CAP_INFEASIBLE" in result.failure_codes


def test_zero_cap_selects_zero_coefficients() -> None:
    result = _run(normalized_radial_maximum_cap=1)
    assert result.validation_level is not None
    assert result.selected_coefficients == tuple(((0, 0) for _ in range(4)))


def test_large_cap_selects_the_full_upper_corner() -> None:
    result = _run(normalized_radial_maximum_cap=2)
    assert result.selected_coefficients == tuple(((F(1, 100), F(1, 100)) for _ in range(4)))
    assert result.original_box_radial_maximum_upper == F(9, 5)


def test_knot_budget_failure_is_not_promoted() -> None:
    result = _run(normalized_knot_optimality_tolerance=0, maximum_knot_cells=1)
    assert result.validation_level is None
    assert "CONTINUOUS_SPLINE_COEFFICIENT_KNOT_OPTIMIZATION_FAILED" in result.failure_codes


def test_invalid_power_shape_and_weights_are_rejected() -> None:
    with pytest.raises(ValueError, match="at least"):
        _run(basis_powers=(1, 3))
    with pytest.raises(ValueError, match="shape-match"):
        _run(objective_weights=WEIGHTS[:-1])
    bad = list(WEIGHTS); bad[0] = (-1, 8)
    with pytest.raises(ValueError, match="nonnegative"):
        _run(objective_weights=tuple(bad))


def test_spectral_empirical_and_grid_claims_remain_false() -> None:
    result = _run()
    assert not result.finite_grid_only
    assert not result.spectral_split_verified
    assert not result.empirical_matrix_provenance_verified
