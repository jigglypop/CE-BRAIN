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
_load("quantitative_c3_graph_transform", "quantitative_c3_graph_transform.py")
_load("quantitative_c4_graph_transform", "quantitative_c4_graph_transform.py")
_load("quantitative_arbitrary_order_graph_transform", "quantitative_arbitrary_order_graph_transform.py")
_load(
    "quantitative_coupled_arbitrary_order_implicit_jet",
    "quantitative_coupled_arbitrary_order_implicit_jet.py",
)
G = _load(
    "quantitative_coupled_arbitrary_order_graph_transform",
    "quantitative_coupled_arbitrary_order_graph_transform.py",
)
M = _load(
    "ce_quantitative_local_coupled_arbitrary_order_graph_transform",
    "quantitative_local_coupled_arbitrary_order_graph_transform.py",
)


def _global(dimension: int = 4):
    tiny = F(1, 1_000_000)
    return G.quantitative_coupled_arbitrary_order_graph_transform(
        base_dimension=dimension,
        base_invertibility_lower=F(9, 10),
        preimage_value_coupling_upper=F(1, 10),
        normalized_graph_derivative_bounds_with_point_modulus=(1, 1, 10, 100, 1000, 10000, 100000),
        base_map_derivative_bounds=(F(1, 2), tiny, tiny, tiny, tiny, tiny),
        base_map_derivative_point_lipschitz_bounds=(tiny,) * 6,
        fiber_map_derivative_bounds=(F(1, 100), tiny, tiny, tiny, tiny, tiny),
        fiber_map_derivative_point_lipschitz_bounds=(tiny,) * 6,
    )


def _local(**overrides):
    values = dict(
        global_certificate=_global(),
        base_reference_scale=1,
        collar_moduli_covered_through_order=7,
        input_base_domain_radius=1,
        output_base_domain_radius=1,
        uniform_inverse_base_image_radius_upper=F(3, 5),
        input_extension_collar_radius=F(1, 10),
        output_extension_collar_radius=F(1, 20),
        uniform_inverse_collar_image_radius_upper=F(21, 20),
    )
    values.update(overrides)
    return M.quantitative_local_coupled_arbitrary_order_graph_transform(**values)


def _matched(**overrides):
    local_overrides = overrides.pop("local_overrides", {})
    local_values = {"uniform_inverse_base_image_radius_upper": 1}
    local_values.update(local_overrides)
    local = _local(**local_values)
    values = dict(
        local_certificate=local,
        fiber_reference_scale=1,
        uniform_inverse_base_image_radius_exact=1,
        uniform_forward_base_image_radius_exact=1,
        graph_boundary_value_upper=0,
        fiber_boundary_forcing_upper=0,
    )
    values.update(overrides)
    return M.quantitative_matched_local_coupled_arbitrary_order_graph_transform(**values)


def test_local_c6_separates_core_and_extension_collar_coverage() -> None:
    result = _local()
    assert result.validation_level is not None
    assert result.inverse_domain_coverage_margin == F(2, 5)
    assert result.inverse_collar_coverage_margin == F(1, 20)
    assert result.extension_collar_certified is True
    assert result.forward_retention_certified is False
    assert result.robust_interior is True
    assert result.local_cn_graph_real_dimension == 4


@pytest.mark.parametrize("order", [2, 4, 6])
def test_wrapper_is_order_generic_and_requires_exactly_one_extra_modulus(order: int) -> None:
    global_certificate = G.quantitative_coupled_arbitrary_order_graph_transform(
        base_dimension=3, base_invertibility_lower=1,
        preimage_value_coupling_upper=0,
        normalized_graph_derivative_bounds_with_point_modulus=(1,) + (0,) * order,
        base_map_derivative_bounds=(F(1, 2),) + (0,) * (order - 1),
        base_map_derivative_point_lipschitz_bounds=(0,) * order,
        fiber_map_derivative_bounds=(F(1, 20),) + (0,) * (order - 1),
        fiber_map_derivative_point_lipschitz_bounds=(0,) * order,
    )
    result = _local(
        global_certificate=global_certificate,
        collar_moduli_covered_through_order=order + 1,
    )
    assert result.validation_level is not None
    assert f"C{order}_DERIVATIVE_JET" in result.status


def test_collar_moduli_must_cover_one_extra_point_order() -> None:
    result = _local(collar_moduli_covered_through_order=6)
    assert result.status == "LOCAL_COUPLED_CN_COLLAR_MODULI_ORDER_INSUFFICIENT"
    assert result.validation_level is None


@pytest.mark.parametrize(
    "field,code",
    [
        ("input_extension_collar_radius", "LOCAL_COUPLED_CN_INPUT_EXTENSION_COLLAR_NOT_OPEN"),
        ("output_extension_collar_radius", "LOCAL_COUPLED_CN_OUTPUT_EXTENSION_COLLAR_NOT_OPEN"),
    ],
)
def test_zero_collars_fail_closed(field: str, code: str) -> None:
    assert _local(**{field: 0}).status == code


def test_core_and_collar_overruns_are_independently_named() -> None:
    assert _local(uniform_inverse_base_image_radius_upper=F(11, 10)).status == "LOCAL_COUPLED_CN_INVERSE_BASE_DOMAIN_NOT_COVERED"
    assert _local(uniform_inverse_collar_image_radius_upper=F(1, 2)).status == "LOCAL_COUPLED_CN_COLLAR_INVERSE_BOUND_BELOW_CORE"
    assert _local(uniform_inverse_collar_image_radius_upper=F(6, 5)).status == "LOCAL_COUPLED_CN_INVERSE_EXTENSION_COLLAR_NOT_COVERED"


def test_collar_equality_passes_without_robust_interior() -> None:
    result = _local(uniform_inverse_collar_image_radius_upper=F(11, 10))
    assert result.validation_level is not None
    assert result.inverse_collar_coverage_margin == 0
    assert result.robust_interior is False


def test_exact_matched_contacts_are_separate_from_strict_differential_collar() -> None:
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
        ("uniform_inverse_base_image_radius_exact", F(9, 10), "MATCHED_LOCAL_COUPLED_CN_INVERSE_EXACT_BOUND_MISMATCH"),
        ("uniform_forward_base_image_radius_exact", F(9, 10), "MATCHED_LOCAL_COUPLED_CN_FORWARD_BOUNDARY_CONTACT_NOT_EXACT"),
        ("uniform_forward_base_image_radius_exact", F(11, 10), "MATCHED_LOCAL_COUPLED_CN_FORWARD_BASE_DOMAIN_NOT_COVERED"),
        ("graph_boundary_value_upper", F(1, 100), "MATCHED_LOCAL_COUPLED_CN_GRAPH_BOUNDARY_NOT_ANCHORED"),
        ("fiber_boundary_forcing_upper", F(1, 100), "MATCHED_LOCAL_COUPLED_CN_FIBER_BOUNDARY_NOT_PRESERVED"),
    ],
)
def test_matched_failures_are_independently_named(field: str, value: object, code: str) -> None:
    assert _matched(**{field: value}).status == code


def test_iteration_is_identical_through_global_local_and_matched_layers() -> None:
    initial = tuple(F(index + 1) for index in range(7))
    global_bound = sys.modules[
        "quantitative_coupled_arbitrary_order_implicit_jet"
    ].coupled_implicit_jet_iteration_bound(
        _global().implicit_jet_certificate,
        initial_distance_by_derivative_order=initial,
        steps=2,
    )
    local_bound = M.local_coupled_arbitrary_order_iteration_bound(
        _local(), initial_distance_by_derivative_order=initial, steps=2
    )
    matched_bound = M.matched_local_coupled_arbitrary_order_iteration_bound(
        _matched(), initial_distance_by_derivative_order=initial, steps=2
    )
    assert local_bound.steps == matched_bound.steps == global_bound.steps
    assert local_bound.distance_by_derivative_order_upper == global_bound.distance_by_derivative_order_upper
    assert matched_bound.distance_by_derivative_order_upper == global_bound.distance_by_derivative_order_upper


def test_scale_covariance_preserves_normalized_contacts_and_collars() -> None:
    base = _matched()
    scaled = _matched(
        fiber_reference_scale=7,
        uniform_inverse_base_image_radius_exact=5,
        uniform_forward_base_image_radius_exact=5,
        local_overrides=dict(
            base_reference_scale=5,
            input_base_domain_radius=5,
            output_base_domain_radius=5,
            input_extension_collar_radius=F(1, 2),
            output_extension_collar_radius=F(1, 4),
            uniform_inverse_collar_image_radius_upper=F(21, 4),
            uniform_inverse_base_image_radius_upper=5,
        ),
    )
    assert scaled.inverse_boundary_contact_residual == base.inverse_boundary_contact_residual
    assert scaled.forward_boundary_contact_residual == base.forward_boundary_contact_residual
    assert scaled.local_certificate.inverse_collar_coverage_margin == base.local_certificate.inverse_collar_coverage_margin


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _matched(local_overrides={"global_certificate": _global(dimension)})
    assert result.matched_local_cn_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_reference_scale", 0),
        ("input_base_domain_radius", 0),
        ("output_base_domain_radius", 0),
        ("uniform_inverse_base_image_radius_upper", -1),
        ("input_extension_collar_radius", -1),
        ("output_extension_collar_radius", 1.0),
        ("uniform_inverse_collar_image_radius_upper", True),
        ("collar_moduli_covered_through_order", True),
    ],
)
def test_invalid_local_inputs_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _local(**{field: value})


def test_failed_global_certificate_is_primary_and_iteration_rejects() -> None:
    bad_global = _global()
    # Rebuild with an undersized highest graph class while retaining exact input types.
    tiny = F(1, 1_000_000)
    bad_global = G.quantitative_coupled_arbitrary_order_graph_transform(
        base_dimension=4, base_invertibility_lower=F(9, 10),
        preimage_value_coupling_upper=F(1, 10),
        normalized_graph_derivative_bounds_with_point_modulus=(1, 1, 10, 100, 1000, 1, 100000),
        base_map_derivative_bounds=(F(1, 2), tiny, tiny, tiny, tiny, tiny),
        base_map_derivative_point_lipschitz_bounds=(tiny,) * 6,
        fiber_map_derivative_bounds=(F(1, 100), tiny, tiny, tiny, tiny, tiny),
        fiber_map_derivative_point_lipschitz_bounds=(tiny,) * 6,
    )
    result = _local(global_certificate=bad_global)
    assert result.status == bad_global.status
    with pytest.raises(ValueError, match="verified"):
        M.local_coupled_arbitrary_order_iteration_bound(
            result, initial_distance_by_derivative_order=(1,) * 7, steps=1
        )


def test_claim_scopes_keep_declared_collar_coverage_and_exact_contact_semantics() -> None:
    assert "DECLARED_HYPOTHESIS" in _local().claim_scope
    assert "NOT_ROBUST_INTERIOR_MARGINS" in _matched().claim_scope
