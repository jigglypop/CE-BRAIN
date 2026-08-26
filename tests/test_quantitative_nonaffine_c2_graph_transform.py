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
M = _load("ce_quantitative_nonaffine_c2_graph", "quantitative_nonaffine_c2_graph_transform.py")


def _certificate(**overrides):
    values = dict(
        base_dimension=5,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=F(4, 3),
        base_inverse_hessian_upper=F(16, 27),
        fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 8),
        fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 16),
        fiber_derivative_fiber_variation=F(1, 16),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_hessian_fiber_lipschitz=F(1, 16),
        normalized_graph_hessian_upper=8,
    )
    values.update(overrides)
    return M.quantitative_nonaffine_c2_triangular_graph_transform(**values)


def test_strict_nonaffine_c2_certificate_has_exact_contract_values() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_NONAFFINE_C2_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.output_graph_hessian_upper == F(214, 27)
    assert result.graph_hessian_margin == F(2, 27)
    assert result.second_derivative_bunching_factor_upper == F(8, 9)
    assert result.second_derivative_bunching_margin == F(1, 9)
    assert result.derivative_to_hessian_cross_coefficient_upper == F(20, 27)
    assert result.value_to_hessian_cross_coefficient_upper == F(38, 27)
    assert result.c2_graph_real_dimension == 5
    assert result.robust_interior is True


def test_sine_perturbed_base_bounds_are_exact_and_affine_at_zero() -> None:
    zero = M.sine_perturbed_base_c2_bounds(0)
    quarter = M.sine_perturbed_base_c2_bounds(F(1, 4))
    assert (zero.inverse_derivative_upper, zero.inverse_hessian_upper) == (1, 0)
    assert quarter.inverse_derivative_upper == F(4, 3)
    assert quarter.inverse_hessian_upper == F(16, 27)


@pytest.mark.parametrize("amplitude", [-1, 1, F(3, 2), 0.25, True, "01"])
def test_sine_perturbed_base_rejects_invalid_amplitude(amplitude: object) -> None:
    with pytest.raises(ValueError):
        M.sine_perturbed_base_c2_bounds(amplitude)


def test_nu_zero_reduces_exactly_to_affine_c2_coefficients() -> None:
    result = _certificate(base_inverse_lipschitz=1, base_inverse_hessian_upper=0)
    q, mu, kappa = F(1, 2), F(1), F(1)
    k2, k3, lambda2 = F(1, 16), F(1, 16), F(8)
    assert result.output_graph_hessian_upper == mu * mu * (q * lambda2 + k2 * (1 + kappa) ** 2)
    assert result.derivative_to_hessian_cross_coefficient_upper == 2 * mu * mu * k2 * (1 + kappa)
    assert result.value_to_hessian_cross_coefficient_upper == mu * mu * (k2 * lambda2 + k3 * (1 + kappa) ** 2)


def test_nonaffine_chain_rule_terms_vanish_separately_at_nu_zero() -> None:
    curved = _certificate()
    affine = _certificate(base_inverse_hessian_upper=0)
    assert curved.output_graph_hessian_upper - affine.output_graph_hessian_upper == F(10, 27)
    assert curved.derivative_to_hessian_cross_coefficient_upper - affine.derivative_to_hessian_cross_coefficient_upper == F(8, 27)
    assert curved.value_to_hessian_cross_coefficient_upper - affine.value_to_hessian_cross_coefficient_upper == F(2, 27)


def test_hessian_class_equality_passes_but_is_not_robust() -> None:
    result = _certificate(
        base_inverse_lipschitz=1,
        base_inverse_hessian_upper=0,
        normalized_graph_hessian_upper=F(1, 2),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_hessian_fiber_lipschitz=0,
    )
    assert result.validation_level is not None
    assert result.graph_hessian_margin == 0
    assert result.robust_interior is False


def test_nonaffine_hessian_class_failure_is_specific() -> None:
    result = _certificate(normalized_graph_hessian_upper=0)
    assert result.status == "NONAFFINE_C2_GRAPH_HESSIAN_CLASS_NOT_INVARIANT"


def test_second_derivative_bunching_equality_fails_after_c1_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        base_inverse_hessian_upper=0,
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
    assert result.status == "NONAFFINE_C2_SECOND_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_predecessor_failure_remains_primary() -> None:
    result = _certificate(forcing_at_zero_upper=1)
    assert result.status == "GRAPH_TRANSFORM_TUBE_NOT_INVARIANT"


def test_exact_nonaffine_three_level_iteration() -> None:
    result = _certificate()
    one = M.nonaffine_c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=1,
    )
    assert one.value_distance_upper == 1
    assert one.derivative_distance_upper == F(7, 3)
    assert one.hessian_distance_upper == F(232, 27)


def test_iteration_rejects_failed_certificate_and_bad_inputs() -> None:
    failed = _certificate(normalized_graph_hessian_upper=0)
    with pytest.raises(ValueError, match="verified"):
        M.nonaffine_c2_graph_iteration_bound(
            failed,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            steps=1,
        )
    valid = _certificate()
    for steps in (-1, True, 1.0):
        with pytest.raises(ValueError, match="steps"):
            M.nonaffine_c2_graph_iteration_bound(
                valid,
                initial_value_distance=1,
                initial_derivative_distance=1,
                initial_hessian_distance=1,
                steps=steps,
            )


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_supplied_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.c2_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_inverse_hessian_upper", -1),
        ("normalized_map_hessian_upper", -1),
        ("normalized_map_hessian_fiber_lipschitz", True),
        ("normalized_graph_hessian_upper", 0.1),
        ("base_inverse_hessian_upper", "01"),
    ],
)
def test_invalid_nonaffine_c2_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})
