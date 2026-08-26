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
C2 = _load("quantitative_c2_graph_transform", "quantitative_c2_graph_transform.py")
M = _load("ce_quantitative_c3_graph", "quantitative_c3_graph_transform.py")


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
        normalized_map_third_derivative_upper=F(1, 16),
        normalized_map_third_derivative_fiber_lipschitz=F(1, 64),
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=2,
    )
    values.update(overrides)
    return M.quantitative_c3_triangular_graph_transform(**values)


def test_strict_c3_certificate_exposes_exact_fourth_layer() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_C3_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.c2_certificate.validation_level is not None
    assert result.output_graph_third_derivative_upper == F(15, 8)
    assert result.graph_third_derivative_margin == F(1, 8)
    assert result.third_derivative_bunching_factor_upper == F(1, 2)
    assert result.third_derivative_bunching_margin == F(1, 2)
    assert result.hessian_to_third_derivative_cross_coefficient_upper == F(3, 8)
    assert result.derivative_to_third_derivative_cross_coefficient_upper == F(15, 16)
    assert result.value_to_third_derivative_cross_coefficient_upper == F(5, 8)
    assert result.c3_graph_real_dimension == 3
    assert result.robust_interior is True


def test_exact_four_level_iteration_recurrence() -> None:
    result = _certificate()
    one = M.c3_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        initial_third_derivative_distance=5,
        steps=1,
    )
    assert one.value_distance_upper == 1
    assert one.derivative_distance_upper == F(5, 2)
    assert one.hessian_distance_upper == F(27, 8)
    assert one.third_derivative_distance_upper == F(129, 16)


def test_d4_level_modulus_only_enters_value_to_c3_coupling() -> None:
    base = _certificate()
    zero = _certificate(normalized_map_third_derivative_fiber_lipschitz=0)
    assert zero.output_graph_third_derivative_upper == base.output_graph_third_derivative_upper
    assert zero.third_derivative_bunching_factor_upper == base.third_derivative_bunching_factor_upper
    assert zero.value_to_third_derivative_cross_coefficient_upper == F(1, 2)
    assert base.value_to_third_derivative_cross_coefficient_upper == F(5, 8)


def test_c3_class_equality_passes_but_is_not_robust() -> None:
    result = _certificate(normalized_graph_third_derivative_upper=F(7, 4))
    assert result.validation_level is not None
    assert result.output_graph_third_derivative_upper == F(7, 4)
    assert result.graph_third_derivative_margin == 0
    assert result.robust_interior is False


def test_c2_class_equality_is_retained_as_nonrobust_predecessor() -> None:
    result = _certificate(
        normalized_map_hessian_upper=F(1, 8),
        normalized_graph_third_derivative_upper=3,
    )
    assert result.validation_level is not None
    assert result.c2_certificate.graph_hessian_margin == 0
    assert result.graph_third_derivative_margin > 0
    assert result.robust_interior is False


def test_c3_bunching_equality_fails_after_c2_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        fiber_linear_norm_upper=F(1, 8),
        fiber_nonlinear_lipschitz=0,
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
        base_derivative_fiber_variation=0,
        fiber_derivative_fiber_variation=0,
        normalized_map_hessian_upper=0,
        normalized_map_third_derivative_upper=0,
        normalized_map_third_derivative_fiber_lipschitz=0,
        normalized_graph_hessian_upper=0,
        normalized_graph_third_derivative_upper=0,
    )
    assert result.c2_certificate.validation_level is not None
    assert result.c2_certificate.second_derivative_bunching_factor_upper == F(1, 2)
    assert result.third_derivative_bunching_factor_upper == 1
    assert result.status == "C3_THIRD_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_local_equality_witness_is_c2_invariant_and_not_c3() -> None:
    q = F(1, 8)
    base_multiplier = F(1, 2)

    def h(x: F) -> F:
        return abs(x) ** 3

    for x in (F(-3, 2), F(-1, 3), F(0), F(2, 5), F(7, 4)):
        assert h(base_multiplier * x) == q * h(x)
    def second_derivative(x: F) -> F:
        return 6 * abs(x)

    epsilon = F(1, 100)
    left_third = (second_derivative(-epsilon) - second_derivative(0)) / (-epsilon)
    right_third = (second_derivative(epsilon) - second_derivative(0)) / epsilon
    assert (left_third, right_third) == (-6, 6)


def test_predecessor_failure_is_primary_and_failed_iteration_rejects() -> None:
    result = _certificate(normalized_graph_hessian_upper=0)
    assert result.status == "C2_GRAPH_HESSIAN_CLASS_NOT_INVARIANT"
    with pytest.raises(ValueError, match="verified"):
        M.c3_graph_iteration_bound(
            result,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            initial_third_derivative_distance=1,
            steps=1,
        )


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.c3_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_map_third_derivative_upper", -1),
        ("normalized_map_third_derivative_fiber_lipschitz", -1),
        ("normalized_graph_third_derivative_upper", -1),
        ("normalized_map_third_derivative_upper", 0.1),
        ("normalized_map_third_derivative_fiber_lipschitz", True),
        ("normalized_graph_third_derivative_upper", "02"),
    ],
)
def test_invalid_c3_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})
