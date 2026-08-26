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
AC2 = _load("quantitative_coupled_c2_graph_transform", "quantitative_coupled_c2_graph_transform.py")
G = _load("quantitative_graph_transform", "quantitative_graph_transform.py")
TC1 = _load("quantitative_c1_graph_transform", "quantitative_c1_graph_transform.py")
TNA = _load("quantitative_nonaffine_c2_graph_transform", "quantitative_nonaffine_c2_graph_transform.py")
NC1 = _load(
    "quantitative_nonaffine_coupled_c1_graph_transform",
    "quantitative_nonaffine_coupled_c1_graph_transform.py",
)
M = _load(
    "ce_quantitative_nonaffine_coupled_c2",
    "quantitative_nonaffine_coupled_c2_graph_transform.py",
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
        normalized_base_map_hessian_lipschitz=F(1, 1000),
        normalized_base_hessian_lipschitz=F(1, 1000),
        normalized_fiber_hessian_lipschitz=F(1, 1000),
        graph_hessian_lipschitz_upper=1,
    )
    values.update(overrides)
    return M.quantitative_nonaffine_coupled_c2_graph_transform(**values)


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
        normalized_base_hessian_lipschitz=F(1, 1000),
        normalized_fiber_hessian_lipschitz=F(1, 1000),
        graph_hessian_lipschitz_upper=1,
    )
    values.update(overrides)
    return AC2.quantitative_coupled_c2_graph_transform(**values)


def test_strict_nonaffine_coupled_c2_exposes_exact_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_NONAFFINE_COUPLED_C2_GRAPH_TRANSFORM"
    assert result.modified_hessian_upper == F(17347, 74000)
    assert result.first_derivative_transform_lipschitz_upper == F(17347, 68450)
    assert result.base_hessian_lipschitz_upper == F(159, 1600)
    assert result.fiber_hessian_lipschitz_upper == F(1987, 8000)
    assert result.modified_hessian_lipschitz_upper == F(77517343, 273800000)
    assert result.output_graph_hessian_lipschitz_upper == F(701739032, 1733598925)
    assert result.base_hessian_difference_derivative_coefficient_upper == F(3, 100)
    assert result.base_hessian_difference_value_coefficient_upper == F(163, 9250)
    assert result.modified_hessian_difference_derivative_coefficient_upper == F(8796, 171125)
    assert result.modified_hessian_difference_value_coefficient_upper == F(4895179, 158290625)
    assert result.second_derivative_bunching_factor_upper == F(12320, 50653)
    assert result.derivative_to_hessian_cross_coefficient_upper == F(840496, 9370805)
    assert result.value_to_hessian_cross_coefficient_upper == F(410712208, 8667994625)
    assert result.graph_hessian_lipschitz_required is True
    assert result.c2_graph_real_dimension == 3
    assert result.robust_interior is True


def test_sine_perturbed_c2_witness_is_exact() -> None:
    bounds = M.sine_perturbed_coupled_base_c2_bounds(
        linear_coefficient=F(1001, 1000),
        amplitude_upper=F(1, 1000),
    )
    assert bounds.inverse_lipschitz_upper == 1
    assert bounds.base_map_hessian_upper == F(1, 1000)
    assert bounds.base_map_hessian_lipschitz_upper == F(1, 1000)


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
        M.sine_perturbed_coupled_base_c2_bounds(**values)


def test_tphi_has_exact_one_graph_and_two_graph_increments() -> None:
    curved = _certificate(
        normalized_base_map_hessian_upper=0,
        normalized_base_map_hessian_lipschitz=F(1, 1000),
    )
    affine = _certificate(
        normalized_base_map_hessian_upper=0,
        normalized_base_map_hessian_lipschitz=0,
    )
    assert curved.base_hessian_lipschitz_upper - affine.base_hessian_lipschitz_upper == F(1, 1000)
    assert curved.base_hessian_difference_value_coefficient_upper - affine.base_hessian_difference_value_coefficient_upper == F(1, 18500)
    assert curved.modified_hessian_upper == affine.modified_hessian_upper
    assert curved.modified_hessian_lipschitz_upper > affine.modified_hessian_lipschitz_upper
    assert curved.value_to_hessian_cross_coefficient_upper > affine.value_to_hessian_cross_coefficient_upper


def test_zero_base_curvature_reduces_every_layer_to_affine_coupled_c2() -> None:
    nonaffine = _certificate(
        normalized_base_map_hessian_upper=0,
        normalized_base_map_hessian_lipschitz=0,
    )
    affine = _affine_certificate()
    assert nonaffine.base_hessian_lipschitz_upper == affine.base_hessian_lipschitz_upper
    assert nonaffine.fiber_hessian_lipschitz_upper == affine.fiber_hessian_lipschitz_upper
    assert nonaffine.first_derivative_transform_lipschitz_upper == affine.first_derivative_transform_lipschitz_upper
    assert nonaffine.modified_hessian_upper == affine.modified_hessian_upper
    assert nonaffine.modified_hessian_lipschitz_upper == affine.modified_hessian_lipschitz_upper
    assert nonaffine.output_graph_hessian_lipschitz_upper == affine.output_graph_hessian_lipschitz_upper
    assert nonaffine.base_hessian_difference_derivative_coefficient_upper == affine.base_hessian_difference_derivative_coefficient_upper
    assert nonaffine.base_hessian_difference_value_coefficient_upper == affine.base_hessian_difference_value_coefficient_upper
    assert nonaffine.modified_hessian_difference_derivative_coefficient_upper == affine.modified_hessian_difference_derivative_coefficient_upper
    assert nonaffine.modified_hessian_difference_value_coefficient_upper == affine.modified_hessian_difference_value_coefficient_upper
    assert nonaffine.second_derivative_bunching_factor_upper == affine.second_derivative_bunching_factor_upper
    assert nonaffine.derivative_to_hessian_cross_coefficient_upper == affine.derivative_to_hessian_cross_coefficient_upper
    assert nonaffine.value_to_hessian_cross_coefficient_upper == affine.value_to_hessian_cross_coefficient_upper


def test_graph_independent_reduction_matches_nonaffine_triangular_c2() -> None:
    coupled = _certificate(
        base_inverse_lipschitz=F(4, 3),
        fiber_linear_norm_upper=F(1, 4),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=F(1, 8),
        fiber_self_lipschitz=F(1, 4),
        graph_slope_upper=1,
        normalized_base_map_hessian_upper=F(1, 4),
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=F(1, 16),
        graph_derivative_lipschitz_upper=8,
        normalized_base_map_hessian_lipschitz=F(1, 4),
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=F(1, 16),
        graph_hessian_lipschitz_upper=0,
        forcing_at_zero_upper=F(1, 4),
    )
    triangular = TNA.quantitative_nonaffine_c2_triangular_graph_transform(
        base_dimension=3,
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
    assert coupled.validation_level is not None
    assert coupled.graph_hessian_lipschitz_required is False
    assert coupled.nonaffine_coupled_c1_certificate.output_graph_derivative_lipschitz_upper == triangular.output_graph_hessian_upper
    assert coupled.second_derivative_bunching_factor_upper == triangular.second_derivative_bunching_factor_upper
    assert coupled.derivative_to_hessian_cross_coefficient_upper == triangular.derivative_to_hessian_cross_coefficient_upper
    assert coupled.value_to_hessian_cross_coefficient_upper == triangular.value_to_hessian_cross_coefficient_upper


def test_graph_hessian_modulus_failure_is_specific() -> None:
    result = _certificate(graph_hessian_lipschitz_upper=0)
    assert result.nonaffine_coupled_c1_certificate.validation_level is not None
    assert result.status == "NONAFFINE_COUPLED_C21_GRAPH_CLASS_NOT_INVARIANT"


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


def test_second_bunching_equality_fails_after_c1_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        fiber_linear_norm_upper=F(1, 8),
        fiber_self_lipschitz=F(1, 8),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
        normalized_base_map_hessian_upper=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=0,
        normalized_base_map_hessian_lipschitz=0,
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=0,
        graph_hessian_lipschitz_upper=0,
    )
    assert result.nonaffine_coupled_c1_certificate.validation_level is not None
    assert result.nonaffine_coupled_c1_certificate.derivative_bunching_factor_upper == F(1, 2)
    assert result.second_derivative_bunching_factor_upper == 1
    assert result.status == "NONAFFINE_COUPLED_C2_SECOND_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_predecessor_failure_remains_primary() -> None:
    result = _certificate(forcing_at_zero_upper=1)
    assert result.status == "COUPLED_GRAPH_TUBE_NOT_INVARIANT"


def test_exact_three_level_iteration() -> None:
    result = _certificate()
    one = M.nonaffine_coupled_c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=1,
    )
    c1 = result.nonaffine_coupled_c1_certificate
    assert one.value_distance_upper == 2 * F(77, 370)
    assert one.derivative_distance_upper == (
        3 * F(308, 1369) + 2 * F(41212, 1266325)
    )
    assert one.hessian_distance_upper == (
        4 * F(12320, 50653)
        + 3 * F(840496, 9370805)
        + 2 * F(410712208, 8667994625)
    )
    assert c1.validation_level is not None


def test_iteration_rejects_failed_certificate_and_invalid_steps() -> None:
    failed = _certificate(graph_hessian_lipschitz_upper=0)
    with pytest.raises(ValueError, match="verified"):
        M.nonaffine_coupled_c2_graph_iteration_bound(
            failed,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            steps=1,
        )
    valid = _certificate()
    for steps in (-1, True, 1.0):
        with pytest.raises(ValueError, match="steps"):
            M.nonaffine_coupled_c2_graph_iteration_bound(
                valid,
                initial_value_distance=1,
                initial_derivative_distance=1,
                initial_hessian_distance=1,
                steps=steps,
            )


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
    assert scaled.modified_hessian_upper == base.modified_hessian_upper
    assert scaled.output_graph_hessian_lipschitz_upper == base.output_graph_hessian_lipschitz_upper
    assert scaled.derivative_to_hessian_cross_coefficient_upper == base.derivative_to_hessian_cross_coefficient_upper
    assert scaled.value_to_hessian_cross_coefficient_upper == base.value_to_hessian_cross_coefficient_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_supplied_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.c2_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_base_map_hessian_lipschitz", -1),
        ("normalized_base_map_hessian_lipschitz", 0.1),
        ("normalized_base_map_hessian_lipschitz", True),
        ("normalized_base_map_hessian_lipschitz", "01"),
        ("normalized_base_hessian_lipschitz", -1),
    ],
)
def test_invalid_nonaffine_c2_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_modulus_string_is_exact() -> None:
    result = _certificate(normalized_base_map_hessian_lipschitz="1/1000")
    assert result.validation_level is not None
    assert result.base_hessian_lipschitz_upper == F(159, 1600)

