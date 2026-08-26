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
_load("quantitative_nonaffine_coupled_c2_graph_transform", "quantitative_nonaffine_coupled_c2_graph_transform.py")
G = _load("quantitative_nonaffine_coupled_c3_graph_transform", "quantitative_nonaffine_coupled_c3_graph_transform.py")
L = _load("quantitative_local_nonaffine_coupled_c3_graph_transform", "quantitative_local_nonaffine_coupled_c3_graph_transform.py")
M = _load("ce_quantitative_matched_local_nonaffine_coupled_c3", "quantitative_matched_local_nonaffine_coupled_c3_graph_transform.py")


def _global_values() -> dict[str, object]:
    return dict(
        base_dimension=4,
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
        normalized_base_map_third_derivative_lipschitz=F(1, 1000),
        normalized_base_third_derivative_lipschitz=F(1, 10000),
        normalized_fiber_third_derivative_lipschitz=F(1, 10000),
        normalized_graph_third_derivative_upper=2,
        graph_third_derivative_lipschitz_upper=2,
    )


def _local(**overrides):
    values = dict(
        input_base_domain_radius=1,
        output_base_domain_radius=1,
        uniform_inverse_base_image_radius_upper=F(3, 5),
        input_c3_extension_collar_radius=F(1, 10),
        output_c3_extension_collar_radius=F(1, 20),
        uniform_inverse_c3_collar_image_radius_upper=F(21, 20),
        **_global_values(),
    )
    values.update(overrides)
    return L.quantitative_local_nonaffine_coupled_c3_graph_transform(**values)


def _matched(**overrides):
    values = dict(
        input_base_domain_radius=1,
        output_base_domain_radius=1,
        uniform_inverse_base_image_radius_exact=1,
        uniform_forward_base_image_radius_exact=1,
        input_c3_extension_collar_radius=F(1, 10),
        output_c3_extension_collar_radius=F(1, 20),
        uniform_inverse_c3_collar_image_radius_upper=F(21, 20),
        graph_boundary_value_upper=0,
        fiber_boundary_forcing_upper=0,
        **_global_values(),
    )
    values.update(overrides)
    return M.quantitative_matched_local_nonaffine_coupled_c3_graph_transform(**values)


def test_local_certificate_separates_core_and_collar_coverage() -> None:
    result = _local()
    assert result.validation_level is not None
    assert result.inverse_domain_coverage_margin == F(2, 5)
    assert result.inverse_c3_collar_coverage_margin == F(1, 20)
    assert result.c3_extension_collar_certified is True
    assert result.forward_retention_certified is False
    assert result.robust_interior is True
    assert result.local_c3_graph_real_dimension == 4


def test_local_wrapper_preserves_complete_global_c3_certificate() -> None:
    assert _local().nonaffine_coupled_c3_certificate == G.quantitative_nonaffine_coupled_c3_graph_transform(**_global_values())


@pytest.mark.parametrize(
    "field,code",
    [
        ("input_c3_extension_collar_radius", "LOCAL_NONAFFINE_COUPLED_C3_INPUT_EXTENSION_COLLAR_NOT_OPEN"),
        ("output_c3_extension_collar_radius", "LOCAL_NONAFFINE_COUPLED_C3_OUTPUT_EXTENSION_COLLAR_NOT_OPEN"),
    ],
)
def test_zero_collar_fails_closed(field: str, code: str) -> None:
    assert _local(**{field: 0}).status == code


def test_core_inverse_overrun_is_named() -> None:
    assert _local(uniform_inverse_base_image_radius_upper=F(11, 10)).status == "LOCAL_NONAFFINE_COUPLED_C3_INVERSE_BASE_DOMAIN_NOT_COVERED"


def test_collar_bound_cannot_be_smaller_than_core_bound() -> None:
    assert _local(uniform_inverse_c3_collar_image_radius_upper=F(1, 2)).status == "LOCAL_NONAFFINE_COUPLED_C3_COLLAR_INVERSE_BOUND_BELOW_CORE"


def test_collar_inverse_overrun_is_named() -> None:
    assert _local(uniform_inverse_c3_collar_image_radius_upper=F(6, 5)).status == "LOCAL_NONAFFINE_COUPLED_C3_INVERSE_EXTENSION_COLLAR_NOT_COVERED"


def test_collar_coverage_equality_passes_without_robust_interior() -> None:
    result = _local(uniform_inverse_c3_collar_image_radius_upper=F(11, 10))
    assert result.validation_level is not None
    assert result.inverse_c3_collar_coverage_margin == 0
    assert result.robust_interior is False


def test_matched_certificate_has_exact_contacts_and_strict_collar() -> None:
    result = _matched()
    assert result.validation_level is not None
    assert result.inverse_boundary_contact_residual == 0
    assert result.forward_boundary_contact_residual == 0
    assert result.differential_and_collar_robust_interior is True
    assert result.domain_contact_robust_interior is False
    assert result.robust_interior is False
    assert result.full_forward_retention_certified is True
    assert result.boundary_anchored_graph_class_certified is True


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("uniform_inverse_base_image_radius_exact", F(9, 10), "MATCHED_LOCAL_NONAFFINE_COUPLED_C3_INVERSE_BOUNDARY_CONTACT_NOT_EXACT"),
        ("uniform_forward_base_image_radius_exact", F(9, 10), "MATCHED_LOCAL_NONAFFINE_COUPLED_C3_FORWARD_BOUNDARY_CONTACT_NOT_EXACT"),
        ("uniform_forward_base_image_radius_exact", F(11, 10), "MATCHED_LOCAL_NONAFFINE_COUPLED_C3_FORWARD_BASE_DOMAIN_NOT_COVERED"),
        ("graph_boundary_value_upper", F(1, 100), "MATCHED_LOCAL_NONAFFINE_COUPLED_C3_GRAPH_BOUNDARY_NOT_ANCHORED"),
        ("fiber_boundary_forcing_upper", F(1, 100), "MATCHED_LOCAL_NONAFFINE_COUPLED_C3_FIBER_BOUNDARY_NOT_PRESERVED"),
    ],
)
def test_matched_failures_are_independent(field: str, value: object, code: str) -> None:
    assert _matched(**{field: value}).status == code


def test_exact_cubic_collar_witness() -> None:
    result = M.boundary_anchored_cubic_coupled_unit_interval_c3_bounds(
        amplitude_upper=F(1, 100),
        fiber_coupling_upper=F(1, 100),
        graph_slope_upper=F(1, 2),
        input_c3_extension_collar_radius=F(1, 10),
    )
    assert result.base_inverse_lipschitz_upper == F(50, 49)
    assert result.coupled_inverse_lipschitz_upper == F(40, 39)
    assert result.coupled_collar_inverse_lipschitz_upper == F(10000, 9687)
    assert result.base_map_hessian_upper == F(33, 500)
    assert result.base_map_hessian_lipschitz_upper == F(3, 50)
    assert result.base_map_third_derivative_lipschitz_upper == 0
    assert result.output_c3_extension_collar_radius == F(9687, 200000)
    assert result.inverse_c3_collar_image_radius_upper == F(21, 20)


def test_iteration_is_identical_through_local_and_matched_wrappers() -> None:
    kwargs = dict(
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        initial_third_derivative_distance=5,
        steps=2,
    )
    global_bound = G.nonaffine_coupled_c3_graph_iteration_bound(
        _local().nonaffine_coupled_c3_certificate, **kwargs
    )
    assert L.local_nonaffine_coupled_c3_graph_iteration_bound(_local(), **kwargs) == global_bound
    assert M.matched_local_nonaffine_coupled_c3_graph_iteration_bound(_matched(), **kwargs) == global_bound


def test_scale_covariance_preserves_normalized_domain_and_collar_gates() -> None:
    base = _matched()
    scaled = _matched(
        base_reference_scale=5,
        fiber_reference_scale=7,
        input_base_domain_radius=5,
        output_base_domain_radius=5,
        uniform_inverse_base_image_radius_exact=5,
        uniform_forward_base_image_radius_exact=5,
        input_c3_extension_collar_radius=F(1, 2),
        output_c3_extension_collar_radius=F(1, 4),
        uniform_inverse_c3_collar_image_radius_upper=F(21, 4),
        fiber_radius=7,
        forcing_at_zero_upper=F(7, 5),
        fiber_to_base_lipschitz=F(1, 140),
        base_to_fiber_lipschitz=F(7, 100),
        graph_slope_upper=F(7, 10),
    )
    assert scaled.inverse_boundary_contact_residual == base.inverse_boundary_contact_residual
    assert scaled.forward_boundary_contact_residual == base.forward_boundary_contact_residual
    assert scaled.local_nonaffine_coupled_c3_certificate.inverse_c3_collar_coverage_margin == base.local_nonaffine_coupled_c3_certificate.inverse_c3_collar_coverage_margin


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    assert _matched(base_dimension=dimension).matched_local_c3_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("input_base_domain_radius", 0),
        ("output_base_domain_radius", 0),
        ("uniform_inverse_base_image_radius_upper", -1),
        ("input_c3_extension_collar_radius", -1),
        ("output_c3_extension_collar_radius", 1.0),
        ("uniform_inverse_c3_collar_image_radius_upper", True),
    ],
)
def test_invalid_local_inputs_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _local(**{field: value})
