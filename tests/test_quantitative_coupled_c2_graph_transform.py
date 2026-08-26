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


CG = _load("quantitative_coupled_graph_transform", "quantitative_coupled_graph_transform.py")
CC1 = _load("quantitative_coupled_c1_graph_transform", "quantitative_coupled_c1_graph_transform.py")
G = _load("quantitative_graph_transform", "quantitative_graph_transform.py")
C1 = _load("quantitative_c1_graph_transform", "quantitative_c1_graph_transform.py")
TC2 = _load("quantitative_c2_graph_transform", "quantitative_c2_graph_transform.py")
M = _load("ce_quantitative_coupled_c2", "quantitative_coupled_c2_graph_transform.py")


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
        normalized_base_hessian_lipschitz=F(1, 1000),
        normalized_fiber_hessian_lipschitz=F(1, 1000),
        graph_hessian_lipschitz_upper=1,
    )
    values.update(overrides)
    return M.quantitative_coupled_c2_graph_transform(**values)


def test_strict_coupled_c2_certificate_exposes_every_exact_layer() -> None:
    result = _certificate()
    c1 = result.coupled_c1_certificate
    base = c1.coupled_lipschitz_certificate
    assert result.status == "VERIFIED_QUANTITATIVE_COUPLED_C2_GRAPH_TRANSFORM"
    assert c1.validation_level is not None
    assert result.graph_hessian_lipschitz_required is True
    assert result.graph_hessian_lipschitz_margin > 0
    assert result.second_derivative_bunching_factor_upper == (
        base.transform_contraction_factor_upper / base.base_invertibility_lower**2
    )
    assert result.second_derivative_bunching_factor_upper == F(12320, 50653)
    assert result.modified_hessian_upper / base.base_invertibility_lower**2 == (
        c1.output_graph_derivative_lipschitz_upper
    )
    assert result.base_hessian_lipschitz_upper > 0
    assert result.fiber_hessian_lipschitz_upper > 0
    assert result.modified_hessian_lipschitz_upper > 0
    assert result.derivative_to_hessian_cross_coefficient_upper > 0
    assert result.value_to_hessian_cross_coefficient_upper > 0
    assert result.c2_graph_real_dimension == 3
    assert result.robust_interior is True


def test_exact_coupled_three_level_iteration_uses_previous_state() -> None:
    result = _certificate()
    zero = M.coupled_c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=0,
    )
    assert (zero.value_distance_upper, zero.derivative_distance_upper) == (2, 3)
    assert zero.hessian_distance_upper == 4
    one = M.coupled_c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=1,
    )
    c1 = result.coupled_c1_certificate
    assert one.value_distance_upper == 2 * c1.coupled_lipschitz_certificate.transform_contraction_factor_upper
    assert one.derivative_distance_upper == (
        3 * c1.derivative_bunching_factor_upper
        + 2 * c1.derivative_cross_coefficient_upper
    )
    assert one.hessian_distance_upper == (
        4 * result.second_derivative_bunching_factor_upper
        + 3 * result.derivative_to_hessian_cross_coefficient_upper
        + 2 * result.value_to_hessian_cross_coefficient_upper
    )


def test_graph_hessian_modulus_failure_is_separate_from_predecessor_and_bunching() -> None:
    result = _certificate(graph_hessian_lipschitz_upper=0)
    assert result.coupled_c1_certificate.validation_level is not None
    assert result.second_derivative_bunching_margin > 0
    assert result.status == "COUPLED_C21_GRAPH_CLASS_NOT_INVARIANT"
    assert result.graph_hessian_lipschitz_margin < 0


def test_exact_graph_hessian_class_equality_passes_nonrobust() -> None:
    at_zero = _certificate(graph_hessian_lipschitz_upper=0)
    at_one = _certificate(graph_hessian_lipschitz_upper=1)
    a = at_zero.output_graph_hessian_lipschitz_upper
    b = at_one.output_graph_hessian_lipschitz_upper - a
    assert a is not None and b is not None and b < 1
    fixed_xi = a / (1 - b)
    result = _certificate(graph_hessian_lipschitz_upper=fixed_xi)
    assert result.validation_level is not None
    assert result.graph_hessian_lipschitz_margin == 0
    assert result.robust_interior is False


def test_graph_independent_base_does_not_require_xi_gate() -> None:
    result = _certificate(
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_base_hessian_lipschitz=0,
        graph_hessian_lipschitz_upper=0,
    )
    assert result.graph_hessian_lipschitz_required is False
    assert result.output_graph_hessian_lipschitz_upper > 0
    assert result.graph_hessian_lipschitz_margin < 0
    assert result.validation_level is not None


def test_full_zero_coupling_reduces_exactly_to_triangular_c2_coefficients() -> None:
    coupled = _certificate(
        forcing_at_zero_upper=F(1, 4),
        fiber_linear_norm_upper=F(1, 4),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=F(1, 4),
        fiber_self_lipschitz=F(1, 4),
        graph_slope_upper=1,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=F(1, 16),
        graph_derivative_lipschitz_upper=1,
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=F(1, 16),
        graph_hessian_lipschitz_upper=0,
    )
    triangular = TC2.quantitative_c2_triangular_graph_transform(
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
    assert coupled.validation_level is not None
    assert triangular.validation_level is not None
    assert coupled.second_derivative_bunching_factor_upper == triangular.second_derivative_bunching_factor_upper
    assert coupled.derivative_to_hessian_cross_coefficient_upper == triangular.derivative_to_hessian_cross_coefficient_upper
    assert coupled.value_to_hessian_cross_coefficient_upper == triangular.value_to_hessian_cross_coefficient_upper


def test_second_derivative_bunching_equality_fails_after_coupled_c1_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        fiber_linear_norm_upper=F(1, 8),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=0,
        fiber_self_lipschitz=F(1, 8),
        graph_slope_upper=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=0,
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=0,
        graph_hessian_lipschitz_upper=0,
    )
    assert result.coupled_c1_certificate.validation_level is not None
    assert result.coupled_c1_certificate.derivative_bunching_factor_upper == F(1, 2)
    assert result.second_derivative_bunching_factor_upper == 1
    assert result.status == "COUPLED_C2_SECOND_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_predecessor_failure_is_preserved_as_primary_status() -> None:
    result = _certificate(forcing_at_zero_upper=1)
    assert result.coupled_c1_certificate.validation_level is None
    assert result.status == "COUPLED_GRAPH_TUBE_NOT_INVARIANT"


def test_iteration_rejects_failed_certificate_and_invalid_inputs() -> None:
    failed = _certificate(graph_hessian_lipschitz_upper=0)
    with pytest.raises(ValueError, match="verified"):
        M.coupled_c2_graph_iteration_bound(
            failed,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            steps=1,
        )
    valid = _certificate()
    for steps in (-1, True, 1.0):
        with pytest.raises(ValueError, match="steps"):
            M.coupled_c2_graph_iteration_bound(
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
            M.coupled_c2_graph_iteration_bound(valid, **values)


def test_base_fiber_rescaling_preserves_normalized_coupled_c2_constants() -> None:
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
    assert scaled.second_derivative_bunching_factor_upper == base.second_derivative_bunching_factor_upper
    assert scaled.output_graph_hessian_lipschitz_upper == base.output_graph_hessian_lipschitz_upper
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
        ("normalized_base_hessian_lipschitz", -1),
        ("normalized_fiber_hessian_lipschitz", -1),
        ("graph_hessian_lipschitz_upper", -1),
        ("normalized_base_hessian_lipschitz", 0.1),
        ("normalized_fiber_hessian_lipschitz", True),
        ("graph_hessian_lipschitz_upper", "01"),
    ],
)
def test_invalid_hessian_modulus_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_hessian_modulus_strings_are_exact() -> None:
    result = _certificate(
        normalized_base_hessian_lipschitz="0.001",
        normalized_fiber_hessian_lipschitz="1/1000",
        graph_hessian_lipschitz_upper="1",
    )
    assert result.validation_level is not None
