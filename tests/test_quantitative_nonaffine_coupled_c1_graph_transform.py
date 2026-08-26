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
AC1 = _load("quantitative_coupled_c1_graph_transform", "quantitative_coupled_c1_graph_transform.py")
M = _load(
    "ce_quantitative_nonaffine_coupled_c1",
    "quantitative_nonaffine_coupled_c1_graph_transform.py",
)


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
        normalized_base_map_hessian_upper=F(1, 1000),
        normalized_base_jacobian_lipschitz=F(1, 100),
        normalized_fiber_jacobian_lipschitz=F(1, 100),
        graph_derivative_lipschitz_upper=1,
    )
    values.update(overrides)
    return M.quantitative_nonaffine_coupled_c1_graph_transform(**values)


def _affine_certificate(**overrides):
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
    return AC1.quantitative_coupled_c1_graph_transform(**values)


def test_strict_nonaffine_coupled_c1_exact_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_NONAFFINE_COUPLED_C1_GRAPH_TRANSFORM"
    assert result.coupled_lipschitz_certificate.base_invertibility_lower == F(37, 40)
    assert result.coupled_lipschitz_certificate.transform_contraction_factor_upper == F(77, 370)
    assert result.base_jacobian_lipschitz_upper == F(147, 2000)
    assert result.fiber_jacobian_lipschitz_upper == F(89, 400)
    assert result.output_graph_derivative_lipschitz_upper == F(69388, 253265)
    assert result.base_jacobian_difference_value_coefficient_upper == F(351, 18500)
    assert result.fiber_jacobian_difference_value_coefficient_upper == F(1, 37)
    assert result.derivative_bunching_factor_upper == F(308, 1369)
    assert result.derivative_cross_coefficient_upper == F(41212, 1266325)
    assert result.c1_graph_real_dimension == 3
    assert result.robust_interior is True


def test_sine_perturbed_base_witness_is_exact() -> None:
    bounds = M.sine_perturbed_coupled_base_c1_bounds(
        linear_coefficient=F(1001, 1000),
        amplitude_upper=F(1, 1000),
    )
    assert bounds.inverse_lipschitz_upper == 1
    assert bounds.base_map_hessian_upper == F(1, 1000)


def test_sine_witness_affine_limit() -> None:
    bounds = M.sine_perturbed_coupled_base_c1_bounds(
        linear_coefficient=2,
        amplitude_upper=0,
    )
    assert bounds.inverse_lipschitz_upper == F(1, 2)
    assert bounds.base_map_hessian_upper == 0


@pytest.mark.parametrize(
    "values",
    [
        dict(linear_coefficient=0, amplitude_upper=0),
        dict(linear_coefficient=1, amplitude_upper=1),
        dict(linear_coefficient=1, amplitude_upper=2),
        dict(linear_coefficient=2, amplitude_upper=-1),
        dict(linear_coefficient=2.0, amplitude_upper=0),
        dict(linear_coefficient=2, amplitude_upper=True),
    ],
)
def test_sine_witness_rejects_invalid_inputs(values: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        M.sine_perturbed_coupled_base_c1_bounds(**values)


def test_nonaffine_increments_are_exactly_the_two_frozen_terms() -> None:
    curved = _certificate()
    affine = _certificate(normalized_base_map_hessian_upper=0)
    assert curved.base_jacobian_lipschitz_upper - affine.base_jacobian_lipschitz_upper == F(1, 1000)
    assert curved.output_graph_derivative_lipschitz_upper - affine.output_graph_derivative_lipschitz_upper == F(48, 253265)
    assert curved.base_jacobian_difference_value_coefficient_upper - affine.base_jacobian_difference_value_coefficient_upper == F(1, 18500)
    assert curved.derivative_cross_coefficient_upper - affine.derivative_cross_coefficient_upper == F(12, 1266325)


def test_zero_base_curvature_reduces_exactly_to_affine_coupled_c1() -> None:
    nonaffine = _certificate(normalized_base_map_hessian_upper=0)
    affine = _affine_certificate()
    assert nonaffine.coupled_lipschitz_certificate == affine.coupled_lipschitz_certificate
    assert nonaffine.base_jacobian_lipschitz_upper == affine.base_jacobian_lipschitz_upper
    assert nonaffine.fiber_jacobian_lipschitz_upper == affine.fiber_jacobian_lipschitz_upper
    assert nonaffine.output_graph_derivative_lipschitz_upper == affine.output_graph_derivative_lipschitz_upper
    assert nonaffine.preimage_value_coupling_upper == affine.preimage_value_coupling_upper
    assert nonaffine.state_value_coupling_upper == affine.state_value_coupling_upper
    assert nonaffine.derivative_bunching_factor_upper == affine.derivative_bunching_factor_upper
    assert nonaffine.derivative_cross_coefficient_upper == affine.derivative_cross_coefficient_upper


def test_base_curvature_does_not_change_diagonal_bunching_factor() -> None:
    curved = _certificate()
    affine = _certificate(normalized_base_map_hessian_upper=0)
    assert curved.derivative_bunching_factor_upper == affine.derivative_bunching_factor_upper
    assert curved.derivative_cross_coefficient_upper > affine.derivative_cross_coefficient_upper


def test_c11_class_failure_can_be_caused_only_by_base_curvature() -> None:
    affine = _certificate(
        normalized_base_map_hessian_upper=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=0,
    )
    curved = _certificate(
        normalized_base_map_hessian_upper=1,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=0,
    )
    assert affine.validation_level is not None
    assert curved.status == "NONAFFINE_COUPLED_C11_GRAPH_CLASS_NOT_INVARIANT"


def test_derivative_bunching_equality_still_fails() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        fiber_linear_norm_upper=F(1, 4),
        fiber_self_lipschitz=F(1, 4),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
        normalized_base_map_hessian_upper=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=0,
    )
    assert result.coupled_lipschitz_certificate.validation_level is not None
    assert result.derivative_bunching_factor_upper == 1
    assert result.status == "NONAFFINE_COUPLED_C1_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_predecessor_failure_remains_primary() -> None:
    result = _certificate(forcing_at_zero_upper=1)
    assert result.status == "COUPLED_GRAPH_TUBE_NOT_INVARIANT"


def test_exact_iteration_uses_nonaffine_cross_coefficient() -> None:
    result = _certificate()
    one = M.nonaffine_coupled_c1_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        steps=1,
    )
    assert one.value_distance_upper == F(77, 185)
    assert one.derivative_distance_upper == (
        3 * F(308, 1369) + 2 * F(41212, 1266325)
    )


def test_iteration_rejects_failed_certificate_and_invalid_steps() -> None:
    failed = _certificate(graph_derivative_lipschitz_upper=0)
    with pytest.raises(ValueError, match="verified"):
        M.nonaffine_coupled_c1_graph_iteration_bound(
            failed,
            initial_value_distance=1,
            initial_derivative_distance=1,
            steps=1,
        )
    valid = _certificate()
    for steps in (-1, True, 1.0):
        with pytest.raises(ValueError, match="steps"):
            M.nonaffine_coupled_c1_graph_iteration_bound(
                valid,
                initial_value_distance=1,
                initial_derivative_distance=1,
                steps=steps,
            )


def test_zero_base_coupling_removes_two_graph_curvature_increment() -> None:
    result = _certificate(
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=0,
    )
    assert result.preimage_value_coupling_upper == 0
    assert result.base_jacobian_difference_value_coefficient_upper == F(3, 200)
    assert result.derivative_cross_coefficient_upper == F(33, 2000)


def test_base_fiber_scale_covariance_preserves_normalized_result() -> None:
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
    assert scaled.base_jacobian_lipschitz_upper == base.base_jacobian_lipschitz_upper
    assert scaled.output_graph_derivative_lipschitz_upper == base.output_graph_derivative_lipschitz_upper
    assert scaled.derivative_cross_coefficient_upper == base.derivative_cross_coefficient_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_supplied_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.c1_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_base_map_hessian_upper", -1),
        ("normalized_base_map_hessian_upper", 0.1),
        ("normalized_base_map_hessian_upper", True),
        ("normalized_base_map_hessian_upper", "01"),
        ("normalized_base_jacobian_lipschitz", -1),
    ],
)
def test_invalid_nonaffine_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_curvature_string_is_exact() -> None:
    result = _certificate(normalized_base_map_hessian_upper="1/1000")
    assert result.validation_level is not None
    assert result.base_jacobian_lipschitz_upper == F(147, 2000)
