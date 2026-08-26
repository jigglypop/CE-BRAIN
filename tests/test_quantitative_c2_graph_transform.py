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
C1 = _load("quantitative_c1_graph_transform", "quantitative_c1_graph_transform.py")
M = _load("ce_quantitative_c2_graph", "quantitative_c2_graph_transform.py")


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
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_hessian_fiber_lipschitz=F(1, 16),
        normalized_graph_hessian_upper=1,
    )
    values.update(overrides)
    return M.quantitative_c2_triangular_graph_transform(**values)


def test_strict_c2_certificate_exposes_exact_hessian_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_C2_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.c1_certificate.validation_level is not None
    assert result.output_graph_hessian_upper == F(3, 4)
    assert result.graph_hessian_margin == F(1, 4)
    assert result.second_derivative_bunching_factor_upper == F(1, 2)
    assert result.second_derivative_bunching_margin == F(1, 2)
    assert result.derivative_to_hessian_cross_coefficient_upper == F(1, 4)
    assert result.value_to_hessian_cross_coefficient_upper == F(5, 16)
    assert result.c2_graph_real_dimension == 3
    assert result.robust_interior is True


def test_exact_three_level_iteration_recurrence() -> None:
    result = _certificate()
    zero = M.c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=0,
    )
    assert (zero.value_distance_upper, zero.derivative_distance_upper) == (2, 3)
    assert zero.hessian_distance_upper == 4
    one = M.c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=1,
    )
    assert one.value_distance_upper == 1
    assert one.derivative_distance_upper == F(5, 2)
    assert one.hessian_distance_upper == F(27, 8)
    two = M.c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=2,
    )
    assert two.value_distance_upper == F(1, 2)
    assert two.derivative_distance_upper == F(7, 4)
    assert two.hessian_distance_upper == F(21, 8)


def test_zero_map_hessian_decouples_second_derivative_recurrence() -> None:
    result = _certificate(
        normalized_map_hessian_upper=0,
        normalized_map_hessian_fiber_lipschitz=0,
    )
    assert result.derivative_to_hessian_cross_coefficient_upper == 0
    assert result.value_to_hessian_cross_coefficient_upper == 0
    bound = M.c2_graph_iteration_bound(
        result,
        initial_value_distance=100,
        initial_derivative_distance=100,
        initial_hessian_distance=3,
        steps=4,
    )
    assert bound.hessian_distance_upper == F(3, 16)


def test_hessian_class_equality_passes_but_is_not_robust() -> None:
    result = _certificate(
        normalized_map_hessian_upper=F(1, 8),
        normalized_map_hessian_fiber_lipschitz=0,
    )
    assert result.validation_level is not None
    assert result.output_graph_hessian_upper == 1
    assert result.graph_hessian_margin == 0
    assert result.robust_interior is False


def test_hessian_class_failure_is_separate_from_c1_and_c2_bunching() -> None:
    result = _certificate(normalized_graph_hessian_upper=0)
    assert result.c1_certificate.validation_level is not None
    assert result.second_derivative_bunching_margin > 0
    assert result.status == "C2_GRAPH_HESSIAN_CLASS_NOT_INVARIANT"
    assert result.graph_hessian_margin < 0


def test_second_derivative_bunching_equality_fails_after_c1_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        fiber_linear_norm_upper=F(1, 8),
        fiber_nonlinear_lipschitz=F(1, 8),
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
        base_derivative_fiber_variation=0,
        fiber_derivative_fiber_variation=0,
        normalized_map_hessian_upper=0,
        normalized_map_hessian_fiber_lipschitz=0,
        normalized_graph_hessian_upper=0,
    )
    assert result.c1_certificate.validation_level is not None
    assert result.c1_certificate.derivative_bunching_factor_upper == F(1, 2)
    assert result.second_derivative_bunching_factor_upper == 1
    assert result.status == "C2_SECOND_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_local_equality_witness_is_c1_invariant_and_not_c2() -> None:
    q = F(1, 4)
    base_multiplier = F(1, 2)

    def h(x: F) -> F:
        return x * abs(x)

    for x in (F(-3, 2), F(-1, 3), F(0), F(2, 5), F(7, 4)):
        assert h(base_multiplier * x) == q * h(x)
    left_second = -2
    right_second = 2
    assert left_second != right_second


def test_predecessor_failure_is_preserved_as_primary_status() -> None:
    result = _certificate(forcing_at_zero_upper=1)
    assert result.c1_certificate.validation_level is None
    assert result.status == "GRAPH_TRANSFORM_TUBE_NOT_INVARIANT"


def test_iteration_rejects_failed_certificate_and_invalid_inputs() -> None:
    failed = _certificate(normalized_graph_hessian_upper=0)
    with pytest.raises(ValueError, match="verified"):
        M.c2_graph_iteration_bound(
            failed,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            steps=1,
        )
    valid = _certificate()
    for steps in (-1, True, 1.0):
        with pytest.raises(ValueError, match="steps"):
            M.c2_graph_iteration_bound(
                valid,
                initial_value_distance=1,
                initial_derivative_distance=1,
                initial_hessian_distance=1,
                steps=steps,
            )
    for field, value in (
        ("initial_value_distance", -1),
        ("initial_derivative_distance", -1),
        ("initial_hessian_distance", -1),
        ("initial_value_distance", 1.0),
        ("initial_hessian_distance", True),
    ):
        values = dict(
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            steps=1,
        )
        values[field] = value
        with pytest.raises(ValueError):
            M.c2_graph_iteration_bound(valid, **values)


def test_base_fiber_rescaling_preserves_normalized_c2_constants() -> None:
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
    assert scaled.status == base.status
    assert scaled.output_graph_hessian_upper == base.output_graph_hessian_upper
    assert scaled.second_derivative_bunching_factor_upper == base.second_derivative_bunching_factor_upper
    assert scaled.derivative_to_hessian_cross_coefficient_upper == base.derivative_to_hessian_cross_coefficient_upper
    assert scaled.value_to_hessian_cross_coefficient_upper == base.value_to_hessian_cross_coefficient_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_any_positive_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.c2_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_map_hessian_upper", -1),
        ("normalized_map_hessian_fiber_lipschitz", -1),
        ("normalized_graph_hessian_upper", -1),
        ("normalized_map_hessian_upper", 0.1),
        ("normalized_map_hessian_fiber_lipschitz", True),
        ("normalized_graph_hessian_upper", "01"),
    ],
)
def test_invalid_second_derivative_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_second_derivative_strings_are_exact() -> None:
    result = _certificate(
        normalized_map_hessian_upper="0.0625",
        normalized_map_hessian_fiber_lipschitz="1/16",
        normalized_graph_hessian_upper="1",
    )
    assert result.validation_level is not None
    assert result.value_to_hessian_cross_coefficient_upper == F(5, 16)
