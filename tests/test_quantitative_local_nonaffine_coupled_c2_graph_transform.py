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


_load("quantitative_coupled_graph_transform", "quantitative_coupled_graph_transform.py")
_load("quantitative_nonaffine_coupled_c1_graph_transform", "quantitative_nonaffine_coupled_c1_graph_transform.py")
G = _load(
    "quantitative_nonaffine_coupled_c2_graph_transform",
    "quantitative_nonaffine_coupled_c2_graph_transform.py",
)
M = _load(
    "ce_quantitative_local_nonaffine_coupled_c2",
    "quantitative_local_nonaffine_coupled_c2_graph_transform.py",
)


def _certificate(**overrides):
    values = dict(
        base_dimension=4,
        base_reference_scale=1,
        fiber_reference_scale=1,
        input_base_domain_radius=1,
        output_base_domain_radius=1,
        uniform_inverse_base_image_radius_upper=F(3, 5),
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 5),
        base_inverse_lipschitz=F(4, 7),
        fiber_linear_norm_upper=F(1, 10),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=F(1, 20),
        base_to_fiber_lipschitz=F(1, 20),
        fiber_self_lipschitz=F(1, 10),
        graph_slope_upper=F(1, 2),
        normalized_base_map_hessian_upper=F(1, 4),
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=F(1, 100),
        graph_derivative_lipschitz_upper=1,
        normalized_base_map_hessian_lipschitz=F(1, 4),
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=F(1, 1000),
        graph_hessian_lipschitz_upper=4,
    )
    values.update(overrides)
    return M.quantitative_local_nonaffine_coupled_c2_graph_transform(**values)


def _global_certificate():
    return G.quantitative_nonaffine_coupled_c2_graph_transform(
        base_dimension=4,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 5),
        base_inverse_lipschitz=F(4, 7),
        fiber_linear_norm_upper=F(1, 10),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=F(1, 20),
        base_to_fiber_lipschitz=F(1, 20),
        fiber_self_lipschitz=F(1, 10),
        graph_slope_upper=F(1, 2),
        normalized_base_map_hessian_upper=F(1, 4),
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=F(1, 100),
        graph_derivative_lipschitz_upper=1,
        normalized_base_map_hessian_lipschitz=F(1, 4),
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=F(1, 1000),
        graph_hessian_lipschitz_upper=4,
    )


def test_strict_local_coupled_certificate_exposes_exact_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_LOCAL_NONAFFINE_COUPLED_C2_GRAPH_TRANSFORM"
    assert result.inverse_domain_coverage_margin == F(2, 5)
    predecessor = result.nonaffine_coupled_c2_certificate
    assert predecessor.output_graph_hessian_lipschitz_upper == F(34438424, 173781261)
    assert predecessor.second_derivative_bunching_factor_upper == F(7520, 109503)
    assert predecessor.derivative_to_hessian_cross_coefficient_upper == F(203008, 7555707)
    assert predecessor.value_to_hessian_cross_coefficient_upper == F(12948464, 868906305)
    assert result.local_invariance_kind == "GRAPH_DEPENDENT_BACKWARD_COVERED_OVERFLOW_INVARIANT"
    assert result.forward_retention_certified is False
    assert result.local_c2_graph_real_dimension == 4
    assert result.robust_interior is True


def test_expanding_sine_coupled_witness_is_exact() -> None:
    bounds = M.expanding_sine_coupled_local_base_c2_bounds(
        linear_coefficient=2,
        amplitude_upper=F(1, 4),
        fiber_coupling_upper=F(1, 20),
        graph_slope_upper=F(1, 2),
        fiber_radius=1,
        output_base_domain_radius=1,
    )
    assert bounds.base_inverse_lipschitz_upper == F(4, 7)
    assert bounds.coupled_inverse_lipschitz_upper == F(40, 69)
    assert bounds.base_map_hessian_upper == F(1, 4)
    assert bounds.base_map_hessian_lipschitz_upper == F(1, 4)
    assert bounds.uniform_inverse_image_radius_upper == F(3, 5)


def test_zero_coupling_reduces_witness_to_graph_independent_bound() -> None:
    bounds = M.expanding_sine_coupled_local_base_c2_bounds(
        linear_coefficient=2,
        amplitude_upper=F(1, 4),
        fiber_coupling_upper=0,
        graph_slope_upper=7,
        fiber_radius=7,
        output_base_domain_radius=1,
    )
    assert bounds.uniform_inverse_image_radius_upper == F(4, 7)


@pytest.mark.parametrize(
    "values",
    [
        dict(linear_coefficient=0, amplitude_upper=0, fiber_coupling_upper=0, graph_slope_upper=0, fiber_radius=1, output_base_domain_radius=1),
        dict(linear_coefficient=1, amplitude_upper=1, fiber_coupling_upper=0, graph_slope_upper=0, fiber_radius=1, output_base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=-1, fiber_coupling_upper=0, graph_slope_upper=0, fiber_radius=1, output_base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=0, fiber_coupling_upper=-1, graph_slope_upper=0, fiber_radius=1, output_base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=0, fiber_coupling_upper=0, graph_slope_upper=-1, fiber_radius=1, output_base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=0, fiber_coupling_upper=2, graph_slope_upper=1, fiber_radius=1, output_base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=0, fiber_coupling_upper=0, graph_slope_upper=0, fiber_radius=0, output_base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=0, fiber_coupling_upper=0, graph_slope_upper=0, fiber_radius=1, output_base_domain_radius=0),
        dict(linear_coefficient=2.0, amplitude_upper=0, fiber_coupling_upper=0, graph_slope_upper=0, fiber_radius=1, output_base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=True, fiber_coupling_upper=0, graph_slope_upper=0, fiber_radius=1, output_base_domain_radius=1),
    ],
)
def test_witness_rejects_invalid_inputs(values: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        M.expanding_sine_coupled_local_base_c2_bounds(**values)


def test_local_wrapper_preserves_every_global_differential_layer() -> None:
    assert _certificate().nonaffine_coupled_c2_certificate == _global_certificate()


def test_coverage_equality_passes_but_is_not_robust() -> None:
    result = _certificate(uniform_inverse_base_image_radius_upper=1)
    assert result.validation_level is not None
    assert result.inverse_domain_coverage_margin == 0
    assert result.robust_interior is False


def test_uniform_inverse_coverage_failure_is_named() -> None:
    result = _certificate(uniform_inverse_base_image_radius_upper=F(6, 5))
    assert result.nonaffine_coupled_c2_certificate.validation_level is not None
    assert result.status == "LOCAL_NONAFFINE_COUPLED_C2_INVERSE_BASE_DOMAIN_NOT_COVERED"
    assert result.inverse_domain_coverage_margin == F(-1, 5)


def test_predecessor_failure_remains_primary() -> None:
    result = _certificate(
        forcing_at_zero_upper=1,
        uniform_inverse_base_image_radius_upper=2,
    )
    assert result.status == "COUPLED_GRAPH_TUBE_NOT_INVARIANT"
    assert "LOCAL_NONAFFINE_COUPLED_C2_INVERSE_BASE_DOMAIN_NOT_COVERED" in result.failure_codes


def test_phi_inverse_coverage_does_not_cover_the_coupled_inverse() -> None:
    # phi(x)=2x covers [-1,1], but F_h=2x-2 for h=-2 has F_h^-1(1)=3/2.
    phi_preimage = F(1, 2)
    coupled_preimage = F(3, 2)
    assert phi_preimage <= 1
    assert coupled_preimage > 1


def test_inverse_coverage_does_not_imply_forward_retention() -> None:
    result = _certificate(
        fiber_to_base_lipschitz=0,
        uniform_inverse_base_image_radius_upper=F(1, 2),
    )
    assert result.validation_level is not None
    assert 2 * F(3, 4) > 1
    assert result.forward_retention_certified is False


def test_exact_iteration_uses_the_global_recurrence() -> None:
    result = _certificate()
    one = M.local_nonaffine_coupled_c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=1,
    )
    assert one.value_distance_upper == F(47, 115)
    assert one.derivative_distance_upper == F(208676, 547515)
    assert one.hessian_distance_upper == F(334619488, 868906305)


def test_iteration_rejects_failed_domain_coverage() -> None:
    result = _certificate(uniform_inverse_base_image_radius_upper=2)
    with pytest.raises(ValueError, match="verified certificate"):
        M.local_nonaffine_coupled_c2_graph_iteration_bound(
            result,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            steps=1,
        )


def test_base_and_fiber_scale_covariance_preserves_local_certificate() -> None:
    base = _certificate()
    scaled = _certificate(
        base_reference_scale=5,
        fiber_reference_scale=7,
        input_base_domain_radius=5,
        output_base_domain_radius=5,
        uniform_inverse_base_image_radius_upper=3,
        fiber_radius=7,
        forcing_at_zero_upper=F(7, 5),
        fiber_to_base_lipschitz=F(1, 28),
        base_to_fiber_lipschitz=F(7, 100),
        graph_slope_upper=F(7, 10),
    )
    assert scaled.inverse_domain_coverage_margin == base.inverse_domain_coverage_margin
    assert scaled.normalized_output_base_domain_radius == base.normalized_output_base_domain_radius
    assert scaled.nonaffine_coupled_c2_certificate.output_graph_hessian_lipschitz_upper == base.nonaffine_coupled_c2_certificate.output_graph_hessian_lipschitz_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_supplied_dimension_is_preserved_not_selected(dimension: int) -> None:
    assert _certificate(base_dimension=dimension).local_c2_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("input_base_domain_radius", 0),
        ("input_base_domain_radius", -1),
        ("output_base_domain_radius", 0),
        ("uniform_inverse_base_image_radius_upper", -1),
        ("input_base_domain_radius", 1.0),
        ("uniform_inverse_base_image_radius_upper", True),
        ("output_base_domain_radius", "01"),
    ],
)
def test_invalid_local_domain_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_domain_strings_are_exact() -> None:
    result = _certificate(
        input_base_domain_radius="1",
        output_base_domain_radius="1",
        uniform_inverse_base_image_radius_upper="3/5",
    )
    assert result.validation_level is not None
    assert result.inverse_domain_coverage_margin == F(2, 5)
