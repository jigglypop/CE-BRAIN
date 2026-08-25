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


G = _load("quantitative_graph_transform", "quantitative_graph_transform.py")
M = _load("ce_quantitative_c1_graph", "quantitative_c1_graph_transform.py")


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
        base_derivative_fiber_variation=F(1, 4),
        fiber_derivative_fiber_variation=F(1, 4),
    )
    values.update(overrides)
    return M.quantitative_c1_triangular_graph_transform(**values)


def test_strict_c1_certificate_exposes_exact_bunching_and_cross_term() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_C1_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.lipschitz_certificate.validation_level is not None
    assert result.derivative_bunching_factor_upper == F(1, 2)
    assert result.derivative_bunching_margin == F(1, 2)
    assert result.derivative_cross_coefficient_upper == F(1, 2)
    assert result.c1_graph_real_dimension == 3


def test_exact_derivative_recurrence_including_zero_steps() -> None:
    result = _certificate()
    zero = M.c1_graph_iteration_bound(
        result, initial_value_distance=2, initial_derivative_distance=3, steps=0
    )
    assert zero.value_distance_upper == 2
    assert zero.derivative_distance_upper == 3
    one = M.c1_graph_iteration_bound(
        result, initial_value_distance=2, initial_derivative_distance=3, steps=1
    )
    assert one.value_distance_upper == 1
    assert one.derivative_distance_upper == F(5, 2)
    two = M.c1_graph_iteration_bound(
        result, initial_value_distance=2, initial_derivative_distance=3, steps=2
    )
    assert two.value_distance_upper == F(1, 2)
    assert two.derivative_distance_upper == F(7, 4)


def test_zero_derivative_variation_decouples_derivative_recurrence() -> None:
    result = _certificate(
        base_derivative_fiber_variation=0,
        fiber_derivative_fiber_variation=0,
    )
    assert result.derivative_cross_coefficient_upper == 0
    bound = M.c1_graph_iteration_bound(
        result, initial_value_distance=100, initial_derivative_distance=3, steps=4
    )
    assert bound.derivative_distance_upper == F(3, 16)


def test_zero_q_has_one_cross_forcing_step_then_zero() -> None:
    result = _certificate(
        fiber_linear_norm_upper=0,
        fiber_nonlinear_lipschitz=0,
        base_to_fiber_lipschitz=0,
    )
    assert result.derivative_bunching_factor_upper == 0
    first = M.c1_graph_iteration_bound(
        result, initial_value_distance=2, initial_derivative_distance=3, steps=1
    )
    second = M.c1_graph_iteration_bound(
        result, initial_value_distance=2, initial_derivative_distance=3, steps=2
    )
    assert first.derivative_distance_upper == 1
    assert second.derivative_distance_upper == 0


def test_bunching_equality_fails_after_lipschitz_gate_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        base_to_fiber_lipschitz=0,
    )
    assert result.lipschitz_certificate.validation_level is not None
    assert result.derivative_bunching_factor_upper == 1
    assert result.status == "C1_DERIVATIVE_BUNCHING_NOT_STRICT"
    assert result.validation_level is None


def test_bunching_above_one_can_fail_even_at_zero_slope() -> None:
    result = _certificate(
        base_inverse_lipschitz=3,
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
    )
    assert result.lipschitz_certificate.validation_level is not None
    assert result.derivative_bunching_factor_upper == F(3, 2)
    assert result.status == "C1_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_predecessor_failure_is_preserved_as_primary_status() -> None:
    result = _certificate(forcing_at_zero_upper=1)
    assert result.lipschitz_certificate.validation_level is None
    assert result.status == "GRAPH_TRANSFORM_TUBE_NOT_INVARIANT"
    assert "GRAPH_TRANSFORM_TUBE_NOT_INVARIANT" in result.failure_codes


def test_c1_iteration_rejects_failed_certificate_and_invalid_inputs() -> None:
    failed = _certificate(base_inverse_lipschitz=2, base_to_fiber_lipschitz=0)
    with pytest.raises(ValueError, match="verified"):
        M.c1_graph_iteration_bound(
            failed, initial_value_distance=1, initial_derivative_distance=1, steps=1
        )
    valid = _certificate()
    for steps in (-1, True, 1.0):
        with pytest.raises(ValueError, match="steps"):
            M.c1_graph_iteration_bound(
                valid, initial_value_distance=1, initial_derivative_distance=1, steps=steps
            )
    for field, value in (
        ("initial_value_distance", -1),
        ("initial_derivative_distance", -1),
        ("initial_value_distance", 1.0),
        ("initial_derivative_distance", True),
    ):
        values = dict(initial_value_distance=1, initial_derivative_distance=1, steps=1)
        values[field] = value
        with pytest.raises(ValueError):
            M.c1_graph_iteration_bound(valid, **values)


def test_derivative_variation_normalization_is_unit_invariant() -> None:
    base = _certificate()
    scaled = _certificate(
        base_reference_scale=5,
        fiber_reference_scale=7,
        fiber_radius=7,
        forcing_at_zero_upper=F(7, 4),
        base_to_fiber_lipschitz=F(7, 20),
        graph_slope_upper=F(7, 5),
        base_derivative_fiber_variation=F(1, 20),
        fiber_derivative_fiber_variation=F(1, 28),
    )
    assert scaled.normalized_base_derivative_fiber_variation == base.normalized_base_derivative_fiber_variation
    assert scaled.normalized_fiber_derivative_fiber_variation == base.normalized_fiber_derivative_fiber_variation
    assert scaled.derivative_bunching_factor_upper == base.derivative_bunching_factor_upper
    assert scaled.derivative_cross_coefficient_upper == base.derivative_cross_coefficient_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_c1_theorem_preserves_any_supplied_positive_dimension(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.c1_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_derivative_fiber_variation", -1),
        ("fiber_derivative_fiber_variation", -1),
        ("base_derivative_fiber_variation", 0.1),
        ("fiber_derivative_fiber_variation", True),
        ("base_derivative_fiber_variation", "01"),
    ],
)
def test_invalid_derivative_variation_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_derivative_variation_strings_are_exact() -> None:
    result = _certificate(
        base_derivative_fiber_variation="0.25",
        fiber_derivative_fiber_variation="1/4",
    )
    assert result.validation_level is not None
    assert result.derivative_cross_coefficient_upper == F(1, 2)

