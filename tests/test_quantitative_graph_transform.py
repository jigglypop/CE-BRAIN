from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "quantitative_graph_transform.py"


def _load():
    spec = importlib.util.spec_from_file_location("ce_quantitative_graph_transform", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


M = _load()


def _certificate(**overrides):
    values = dict(
        base_dimension=3,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 4),
        fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1,
    )
    values.update(overrides)
    return M.quantitative_triangular_graph_transform(**values)


def test_strict_interior_certificate_exposes_exact_margins() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.validation_level == result.status
    assert result.robust_interior is True
    assert result.contraction_factor_upper == F(1, 2)
    assert result.contraction_margin == F(1, 2)
    assert result.tube_margin == F(1, 4)
    assert result.slope_margin == F(1, 4)
    assert result.graph_real_dimension == 3


def test_exact_tube_and_slope_boundaries_pass_but_are_not_robust() -> None:
    result = _certificate(
        forcing_at_zero_upper=F(1, 2),
        base_to_fiber_lipschitz=F(1, 2),
    )
    assert result.validation_level == "VERIFIED_QUANTITATIVE_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.tube_margin == 0
    assert result.slope_margin == 0
    assert result.robust_interior is False


@pytest.mark.parametrize("b,ly", [(F(3, 4), F(1, 4)), (1, F(1, 4))])
def test_contraction_equality_and_above_fail_strictly(b: F, ly: F) -> None:
    result = _certificate(fiber_linear_norm_upper=b, fiber_nonlinear_lipschitz=ly)
    assert result.validation_level is None
    assert "GRAPH_TRANSFORM_CONTRACTION_NOT_STRICT" in result.failure_codes
    assert result.status == "GRAPH_TRANSFORM_CONTRACTION_NOT_STRICT"


def test_tube_and_slope_failures_are_reported_separately_and_together() -> None:
    tube = _certificate(forcing_at_zero_upper=F(3, 4))
    assert tube.failure_codes == ("GRAPH_TRANSFORM_TUBE_NOT_INVARIANT",)
    slope = _certificate(base_to_fiber_lipschitz=1)
    assert slope.failure_codes == ("GRAPH_TRANSFORM_SLOPE_NOT_INVARIANT",)
    both = _certificate(forcing_at_zero_upper=F(3, 4), base_to_fiber_lipschitz=1)
    assert both.failure_codes == (
        "GRAPH_TRANSFORM_TUBE_NOT_INVARIANT",
        "GRAPH_TRANSFORM_SLOPE_NOT_INVARIANT",
    )


def test_exact_tracking_bound_handles_steps_and_zero_contraction() -> None:
    result = _certificate()
    assert M.graph_tracking_bound(result, initial_fiber_distance=3, steps=0) == 3
    assert M.graph_tracking_bound(result, initial_fiber_distance=3, steps=4) == F(3, 16)
    zero_q = _certificate(fiber_linear_norm_upper=0, fiber_nonlinear_lipschitz=0)
    assert M.graph_tracking_bound(zero_q, initial_fiber_distance=3, steps=1) == 0


def test_tracking_rejects_failed_certificate_steps_and_distance() -> None:
    failed = _certificate(fiber_linear_norm_upper=1)
    with pytest.raises(ValueError, match="verified"):
        M.graph_tracking_bound(failed, initial_fiber_distance=1, steps=1)
    valid = _certificate()
    for steps in (True, -1, 1.0):
        with pytest.raises(ValueError, match="steps"):
            M.graph_tracking_bound(valid, initial_fiber_distance=1, steps=steps)
    for distance in (-1, 1.0, True, "01"):
        with pytest.raises(ValueError):
            M.graph_tracking_bound(valid, initial_fiber_distance=distance, steps=1)


def test_zero_cross_lipschitz_slope_and_forcing_boundary_is_valid() -> None:
    result = _certificate(
        forcing_at_zero_upper=0,
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
    )
    assert result.validation_level is not None
    assert result.slope_margin == 0
    assert result.robust_interior is False


def test_independent_base_and_fiber_unit_rescaling_is_exactly_invariant() -> None:
    base = _certificate(
        base_reference_scale=2,
        fiber_reference_scale=3,
        fiber_radius=3,
        forcing_at_zero_upper=F(3, 4),
        base_to_fiber_lipschitz=F(3, 8),
        graph_slope_upper=F(3, 2),
    )
    scaled = _certificate(
        base_reference_scale=10,
        fiber_reference_scale=21,
        fiber_radius=21,
        forcing_at_zero_upper=F(21, 4),
        base_to_fiber_lipschitz=F(21, 40),
        graph_slope_upper=F(21, 10),
    )
    assert scaled.status == base.status
    assert scaled.normalized_fiber_radius == base.normalized_fiber_radius
    assert scaled.normalized_forcing_at_zero_upper == base.normalized_forcing_at_zero_upper
    assert scaled.normalized_base_to_fiber_lipschitz == base.normalized_base_to_fiber_lipschitz
    assert scaled.normalized_graph_slope_upper == base.normalized_graph_slope_upper
    assert scaled.contraction_margin == base.contraction_margin
    assert scaled.tube_margin == base.tube_margin
    assert scaled.slope_margin == base.slope_margin


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_any_positive_declared_dimension_is_accepted_without_selection(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_dimension", 0),
        ("base_dimension", True),
        ("base_reference_scale", 0),
        ("fiber_reference_scale", -1),
        ("fiber_radius", 0),
        ("base_inverse_lipschitz", 0),
        ("forcing_at_zero_upper", -1),
        ("fiber_linear_norm_upper", -1),
        ("base_to_fiber_lipschitz", 0.1),
        ("fiber_nonlinear_lipschitz", True),
        ("graph_slope_upper", "01"),
    ],
)
def test_invalid_dimensions_scales_types_and_bounds_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_strings_are_exact() -> None:
    result = _certificate(
        forcing_at_zero_upper="1/4",
        fiber_linear_norm_upper="0.25",
        base_to_fiber_lipschitz="1/4",
        fiber_nonlinear_lipschitz="1/4",
    )
    assert result.validation_level is not None
    assert result.contraction_factor_upper == F(1, 2)
