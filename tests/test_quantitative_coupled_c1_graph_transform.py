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


C = _load("quantitative_coupled_graph_transform", "quantitative_coupled_graph_transform.py")
M = _load("ce_quantitative_coupled_c1", "quantitative_coupled_c1_graph_transform.py")


def _certificate(**overrides):
    values = dict(
        base_dimension=3,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 5),
        base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 10),
        base_self_lipschitz=F(1, 20),
        fiber_to_base_lipschitz=F(1, 20),
        base_to_fiber_lipschitz=F(1, 20),
        fiber_self_lipschitz=F(1, 10),
        graph_slope_upper=F(1, 2),
        normalized_base_jacobian_lipschitz=F(1, 100),
        normalized_fiber_jacobian_lipschitz=F(1, 100),
        graph_derivative_lipschitz_upper=1,
    )
    values.update(overrides)
    return M.quantitative_coupled_c1_graph_transform(**values)


def test_strict_coupled_c1_certificate_exposes_all_exact_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_COUPLED_C1_GRAPH_TRANSFORM"
    assert result.coupled_lipschitz_certificate.validation_level is not None
    assert result.derivative_bunching_factor_upper == (
        result.coupled_lipschitz_certificate.transform_contraction_factor_upper
        / result.coupled_lipschitz_certificate.base_invertibility_lower
    )
    assert result.derivative_bunching_factor_upper == F(308, 1369)
    assert result.derivative_bunching_margin > 0
    assert result.graph_derivative_lipschitz_margin > 0
    assert result.derivative_cross_coefficient_upper > 0
    assert result.c1_graph_real_dimension == 3
    assert result.robust_interior is True


def test_exact_coupled_derivative_iteration_recurrence() -> None:
    result = _certificate()
    zero = M.coupled_c1_graph_iteration_bound(
        result, initial_value_distance=2, initial_derivative_distance=3, steps=0
    )
    assert zero.value_distance_upper == 2
    assert zero.derivative_distance_upper == 3
    one = M.coupled_c1_graph_iteration_bound(
        result, initial_value_distance=2, initial_derivative_distance=3, steps=1
    )
    assert one.value_distance_upper == 2 * result.coupled_lipschitz_certificate.transform_contraction_factor_upper
    assert one.derivative_distance_upper == (
        3 * result.derivative_bunching_factor_upper
        + 2 * result.derivative_cross_coefficient_upper
    )


def test_zero_second_derivatives_and_zero_graph_modulus_give_boundary_class() -> None:
    result = _certificate(
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=0,
    )
    assert result.validation_level is not None
    assert result.output_graph_derivative_lipschitz_upper == 0
    assert result.graph_derivative_lipschitz_margin == 0
    assert result.derivative_cross_coefficient_upper == 0
    assert result.robust_interior is False


def test_c11_class_failure_is_separate_from_lipschitz_and_bunching() -> None:
    result = _certificate(graph_derivative_lipschitz_upper=0)
    assert result.coupled_lipschitz_certificate.validation_level is not None
    assert result.derivative_bunching_margin > 0
    assert result.status == "COUPLED_C11_GRAPH_CLASS_NOT_INVARIANT"
    assert result.graph_derivative_lipschitz_margin < 0


def test_derivative_bunching_equality_recovers_triangular_boundary() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        fiber_linear_norm_upper=F(1, 4),
        fiber_self_lipschitz=F(1, 4),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=0,
    )
    assert result.coupled_lipschitz_certificate.validation_level is not None
    assert result.derivative_bunching_factor_upper == 1
    assert result.status == "COUPLED_C1_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_predecessor_failure_is_preserved_as_primary_status() -> None:
    result = _certificate(forcing_at_zero_upper=1)
    assert result.coupled_lipschitz_certificate.validation_level is None
    assert result.status == "COUPLED_GRAPH_TUBE_NOT_INVARIANT"


def test_zero_base_coupling_reduces_derivative_factor_to_q_mu() -> None:
    result = _certificate(
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        normalized_base_jacobian_lipschitz=0,
    )
    base = result.coupled_lipschitz_certificate
    assert base.base_invertibility_lower == 1
    assert base.transform_contraction_factor_upper == base.fiber_factor_upper
    assert result.derivative_bunching_factor_upper == (
        base.base_inverse_lipschitz * base.fiber_factor_upper
    )


def test_iteration_rejects_failed_certificate_and_invalid_inputs() -> None:
    failed = _certificate(graph_derivative_lipschitz_upper=0)
    with pytest.raises(ValueError, match="verified"):
        M.coupled_c1_graph_iteration_bound(
            failed, initial_value_distance=1, initial_derivative_distance=1, steps=1
        )
    valid = _certificate()
    for steps in (-1, True, 1.0):
        with pytest.raises(ValueError, match="steps"):
            M.coupled_c1_graph_iteration_bound(
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
            M.coupled_c1_graph_iteration_bound(valid, **values)


def test_base_fiber_rescaling_preserves_normalized_coupled_c1_constants() -> None:
    base = _certificate()
    scaled = _certificate(
        base_reference_scale=5,
        fiber_reference_scale=7,
        fiber_radius=7,
        forcing_at_zero_upper=F(7, 5),
        fiber_to_base_lipschitz=F(1, 28),
        base_to_fiber_lipschitz=F(7, 100),
        graph_slope_upper=F(7, 10),
    )
    assert scaled.status == base.status
    assert scaled.coupled_lipschitz_certificate.normalized_fiber_to_base_lipschitz == F(1, 20)
    assert scaled.coupled_lipschitz_certificate.normalized_base_to_fiber_lipschitz == F(1, 20)
    assert scaled.derivative_bunching_factor_upper == base.derivative_bunching_factor_upper
    assert scaled.derivative_cross_coefficient_upper == base.derivative_cross_coefficient_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_any_positive_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.c1_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_base_jacobian_lipschitz", -1),
        ("normalized_fiber_jacobian_lipschitz", -1),
        ("graph_derivative_lipschitz_upper", -1),
        ("normalized_base_jacobian_lipschitz", 0.1),
        ("normalized_fiber_jacobian_lipschitz", True),
        ("graph_derivative_lipschitz_upper", "01"),
    ],
)
def test_invalid_derivative_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_derivative_inputs_are_exact() -> None:
    result = _certificate(
        normalized_base_jacobian_lipschitz="0.01",
        normalized_fiber_jacobian_lipschitz="1/100",
        graph_derivative_lipschitz_upper="1",
    )
    assert result.validation_level is not None

