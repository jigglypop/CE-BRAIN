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
_load(
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization",
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py",
)
_load(
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization",
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization.py",
)
M = _load(
    "ce_verified_continuous_spline_knots",
    "verified_continuous_periodic_spline_knot_optimization.py",
)


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))


def _run(**overrides):
    args = dict(
        knot_parameter_intervals=BOXES,
        patch_amplitudes=(F(1, 100), F(1, 200), F(1, 300), F(1, 400)),
        junction_order=1,
        normalized_optimality_tolerance=F(1, 32),
        maximum_cells=16384,
        sqrt_precision=48,
    )
    args.update(overrides)
    return M.verified_continuous_periodic_spline_knot_optimization(**args)


def test_continuous_periodic_knot_box_is_globally_certified() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.continuous_knot_box_covered
    assert result.epsilon_global_optimality_verified
    assert not result.finite_grid_only
    assert result.certified_optimality_gap <= F(1, 32)
    assert result.strict_order_and_minor_arc_domain_verified
    assert result.selected_knot_parameters is not None
    assert abs(result.selected_knot_parameters[0] + 1) <= F(1, 16)
    assert abs(result.selected_knot_parameters[1]) <= F(1, 16)
    assert abs(result.selected_knot_parameters[2] - 1) <= F(1, 16)


def test_uniform_singleton_four_arc_mesh_is_exact() -> None:
    result = _run(
        knot_parameter_intervals=((-1, -1), (0, 0), (1, 1)),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.selected_minimum_spacing_score == 2
    assert result.selected_maximum_endpoint_chord_squared == 2
    assert result.selected_maximum_endpoint_chord_bracket is not None
    lower, upper = result.selected_maximum_endpoint_chord_bracket
    assert lower * lower <= 2 <= upper * upper
    assert result.certified_optimality_gap == 0


def test_cell_upper_contains_dense_ordered_rational_samples() -> None:
    result = _run(normalized_optimality_tolerance=4, maximum_cells=1)
    root = result.terminal_cells[0]
    for t1 in (F(-3, 2), F(-5, 4), F(-1), F(-3, 4)):
        for t2 in (F(-1, 4), F(0), F(1, 4)):
            for t3 in (F(3, 4), F(1), F(5, 4), F(3, 2)):
                score = M._point_spacing_score((t1, t2, t3))
                assert score <= root.cell_global_upper


def test_automatic_patch_has_cq_endpoint_jets_for_any_knot_location() -> None:
    for order in (0, 1, 2, 3, 6, 10):
        result = _run(junction_order=order)
        assert result.automatic_periodic_cq_junction_verified
        assert result.automatic_vanishing_exponent == order + 1
        assert result.automatic_endpoint_vanishing_order == 2 * (order + 1)
        assert result.automatic_endpoint_vanishing_order > order


def test_nonnegative_bumps_give_explicit_radial_and_gradient_bounds() -> None:
    result = _run(junction_order=1)
    assert result.radial_minimum_lower == 1
    assert result.radial_maximum_upper == F(29, 25)
    assert result.radial_gradient_upper == F(8, 25)
    assert result.radial_lipschitz_upper == F(37, 25)
    assert result.selected_contour_cover_chord_upper is not None
    assert result.selected_contour_cover_chord_upper > 0


def test_zero_amplitudes_reduce_to_unit_circle_geometry() -> None:
    result = _run(patch_amplitudes=(0, 0, 0, 0), junction_order=8)
    assert result.radial_minimum_lower == 1
    assert result.radial_maximum_upper == 1
    assert result.radial_gradient_upper == 0
    assert result.radial_lipschitz_upper == 1


def test_selected_directions_are_exact_unit_vectors() -> None:
    result = _run()
    assert result.selected_knot_directions is not None
    assert all(direction.abs_squared() == 1 for direction in result.selected_knot_directions)
    assert result.cyclic_anchor_direction.abs_squared() == 1


def test_zero_tolerance_small_budget_fails_closed() -> None:
    result = _run(normalized_optimality_tolerance=0, maximum_cells=1)
    assert result.validation_level is None
    assert "CONTINUOUS_SPLINE_KNOT_OPTIMIZATION_CELL_BUDGET_EXCEEDED" in result.failure_codes
    assert not result.continuous_knot_box_covered


@pytest.mark.parametrize(
    "boxes",
    [
        ((-1, 0), (0, 1), (2, 3)),
        ((-3, -2), (-1, 0), (1, 2)),
        ((-2, -1), (F(3, 4), 1), (2, 3)),
        ((-1, -1), (0, 0)),
    ],
)
def test_invalid_order_or_nonminor_arc_domains_fail_closed(boxes: object) -> None:
    with pytest.raises(ValueError, match="strictly ordered"):
        _run(knot_parameter_intervals=boxes, patch_amplitudes=(0,) * (len(boxes) + 1))


def test_amplitude_count_and_sign_are_strict() -> None:
    with pytest.raises(ValueError, match="one value per cyclic arc"):
        _run(patch_amplitudes=(0, 0, 0))
    with pytest.raises(ValueError, match="nonnegative"):
        _run(patch_amplitudes=(0, 0, -1, 0))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("junction_order", True, "nonnegative built-in integer"),
        ("junction_order", -1, "nonnegative built-in integer"),
        ("normalized_optimality_tolerance", -1, "nonnegative"),
        ("maximum_cells", True, "positive built-in integer"),
        ("sqrt_precision", 0, "positive built-in integer"),
        ("knot_parameter_intervals", ((-1.0, -F(1, 2)), (0, F(1, 4)), (1, 2)), "exact"),
    ],
)
def test_invalid_scalar_inputs_fail_closed(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _run(**{field: value})


def test_geometry_only_result_does_not_claim_spectral_or_empirical_closure() -> None:
    result = _run()
    assert not result.spectral_split_verified
    assert not result.empirical_matrix_provenance_verified
