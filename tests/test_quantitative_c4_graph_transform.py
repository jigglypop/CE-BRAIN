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


_load("quantitative_graph_transform", "quantitative_graph_transform.py")
_load("quantitative_c1_graph_transform", "quantitative_c1_graph_transform.py")
_load("quantitative_c2_graph_transform", "quantitative_c2_graph_transform.py")
C3 = _load("quantitative_c3_graph_transform", "quantitative_c3_graph_transform.py")
M = _load("ce_quantitative_c4_graph", "quantitative_c4_graph_transform.py")


def _values() -> dict[str, object]:
    return dict(
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
        normalized_map_fourth_derivative_upper=F(1, 64),
        normalized_map_fourth_derivative_fiber_lipschitz=F(1, 256),
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=2,
        normalized_graph_fourth_derivative_upper=6,
    )


def _certificate(**overrides):
    values = _values()
    values.update(overrides)
    return M.quantitative_c4_triangular_graph_transform(**values)


def test_strict_c4_certificate_exposes_exact_fifth_layer() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_C4_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.c3_certificate.validation_level is not None
    assert result.output_graph_fourth_derivative_upper == F(95, 16)
    assert result.graph_fourth_derivative_margin == F(1, 16)
    assert result.fourth_derivative_bunching_factor_upper == F(1, 2)
    assert result.fourth_derivative_bunching_margin == F(1, 2)
    assert result.third_to_fourth_derivative_cross_coefficient_upper == F(1, 2)
    assert result.hessian_to_fourth_derivative_cross_coefficient_upper == F(15, 8)
    assert result.derivative_to_fourth_derivative_cross_coefficient_upper == F(5, 2)
    assert result.value_to_fourth_derivative_cross_coefficient_upper == 2
    assert result.c4_graph_real_dimension == 3
    assert result.robust_interior is True


def test_c4_passes_exact_k4_to_the_c3_predecessor_modulus() -> None:
    result = _certificate()
    expected = C3.quantitative_c3_triangular_graph_transform(
        **{
            key: value
            for key, value in _values().items()
            if key not in {
                "normalized_map_fourth_derivative_upper",
                "normalized_map_fourth_derivative_fiber_lipschitz",
                "normalized_graph_fourth_derivative_upper",
            }
        },
        normalized_map_third_derivative_fiber_lipschitz=F(1, 64),
    )
    assert result.c3_certificate == expected


def test_exact_five_level_iteration_recurrence() -> None:
    one = M.c4_graph_iteration_bound(
        _certificate(),
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        initial_third_derivative_distance=5,
        initial_fourth_derivative_distance=6,
        steps=1,
    )
    assert one.value_distance_upper == 1
    assert one.derivative_distance_upper == F(5, 2)
    assert one.hessian_distance_upper == F(27, 8)
    assert one.third_derivative_distance_upper == F(129, 16)
    assert one.fourth_derivative_distance_upper == F(49, 2)


def test_d5_modulus_enters_only_value_to_c4_coefficient() -> None:
    base = _certificate()
    zero = _certificate(normalized_map_fourth_derivative_fiber_lipschitz=0)
    assert zero.output_graph_fourth_derivative_upper == base.output_graph_fourth_derivative_upper
    assert zero.fourth_derivative_bunching_factor_upper == base.fourth_derivative_bunching_factor_upper
    assert zero.third_to_fourth_derivative_cross_coefficient_upper == base.third_to_fourth_derivative_cross_coefficient_upper
    assert zero.value_to_fourth_derivative_cross_coefficient_upper == F(31, 16)
    assert base.value_to_fourth_derivative_cross_coefficient_upper == 2


def test_c4_class_equality_passes_without_robust_interior() -> None:
    result = _certificate(normalized_graph_fourth_derivative_upper=F(47, 8))
    assert result.validation_level is not None
    assert result.output_graph_fourth_derivative_upper == F(47, 8)
    assert result.graph_fourth_derivative_margin == 0
    assert result.robust_interior is False


def test_c4_class_failure_is_named_after_c3_passes() -> None:
    result = _certificate(normalized_graph_fourth_derivative_upper=5)
    assert result.c3_certificate.validation_level is not None
    assert result.status == "C4_GRAPH_FOURTH_DERIVATIVE_CLASS_NOT_INVARIANT"


def test_c4_bunching_equality_fails_after_c3_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        fiber_linear_norm_upper=F(1, 16),
        fiber_nonlinear_lipschitz=0,
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
        base_derivative_fiber_variation=0,
        fiber_derivative_fiber_variation=0,
        normalized_map_hessian_upper=0,
        normalized_map_third_derivative_upper=0,
        normalized_map_fourth_derivative_upper=0,
        normalized_map_fourth_derivative_fiber_lipschitz=0,
        normalized_graph_hessian_upper=0,
        normalized_graph_third_derivative_upper=0,
        normalized_graph_fourth_derivative_upper=0,
    )
    assert result.c3_certificate.validation_level is not None
    assert result.c3_certificate.third_derivative_bunching_factor_upper == F(1, 2)
    assert result.fourth_derivative_bunching_factor_upper == 1
    assert result.status == "C4_FOURTH_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_equality_witness_is_c3_invariant_and_not_c4() -> None:
    def h(x: F) -> F:
        return x * abs(x) ** 3

    for x in (F(-3, 2), F(-1, 3), F(0), F(2, 5), F(7, 4)):
        assert h(x / 2) == h(x) / 16

    epsilon = F(1, 100)
    left_fourth = -24
    right_fourth = 24
    assert h(-epsilon) < 0 < h(epsilon)
    assert left_fourth != right_fourth


def test_predecessor_failure_stays_primary_and_iteration_rejects() -> None:
    result = _certificate(normalized_graph_third_derivative_upper=0)
    assert result.status == "C3_GRAPH_THIRD_DERIVATIVE_CLASS_NOT_INVARIANT"
    with pytest.raises(ValueError, match="verified"):
        M.c4_graph_iteration_bound(
            result,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            initial_third_derivative_distance=1,
            initial_fourth_derivative_distance=1,
            steps=1,
        )


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.c4_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_map_fourth_derivative_upper", -1),
        ("normalized_map_fourth_derivative_fiber_lipschitz", -1),
        ("normalized_graph_fourth_derivative_upper", -1),
        ("normalized_map_fourth_derivative_upper", 0.1),
        ("normalized_map_fourth_derivative_fiber_lipschitz", True),
        ("normalized_graph_fourth_derivative_upper", "06"),
    ],
)
def test_invalid_c4_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("initial_value_distance", -1),
        ("initial_fourth_derivative_distance", -1),
        ("initial_fourth_derivative_distance", 1.0),
    ],
)
def test_iteration_rejects_invalid_distances(field: str, value: object) -> None:
    values = dict(
        initial_value_distance=1,
        initial_derivative_distance=1,
        initial_hessian_distance=1,
        initial_third_derivative_distance=1,
        initial_fourth_derivative_distance=1,
        steps=1,
    )
    values[field] = value
    with pytest.raises(ValueError):
        M.c4_graph_iteration_bound(_certificate(), **values)


@pytest.mark.parametrize("steps", [-1, 1.0, True])
def test_iteration_rejects_invalid_steps(steps: object) -> None:
    with pytest.raises(ValueError):
        M.c4_graph_iteration_bound(
            _certificate(),
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            initial_third_derivative_distance=1,
            initial_fourth_derivative_distance=1,
            steps=steps,
        )
