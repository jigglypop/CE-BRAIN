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
_load("quantitative_coupled_arbitrary_order_implicit_jet", "quantitative_coupled_arbitrary_order_implicit_jet.py")
C0 = _load("quantitative_coupled_graph_transform", "quantitative_coupled_graph_transform.py")
CN = _load("quantitative_coupled_arbitrary_order_graph_transform", "quantitative_coupled_arbitrary_order_graph_transform.py")
LOCAL = _load("quantitative_local_coupled_arbitrary_order_graph_transform", "quantitative_local_coupled_arbitrary_order_graph_transform.py")
M = _load("ce_quantitative_full_coupled_arbitrary_order_graph_transform", "quantitative_full_coupled_arbitrary_order_graph_transform.py")


def _c0(dimension: int = 4, **overrides):
    values = dict(
        base_dimension=dimension,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 10),
        base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 200),
        base_self_lipschitz=F(1, 100),
        fiber_to_base_lipschitz=F(9, 100),
        base_to_fiber_lipschitz=0,
        fiber_self_lipschitz=F(1, 200),
        graph_slope_upper=1,
    )
    values.update(overrides)
    return C0.quantitative_coupled_graph_transform(**values)


def _cn(dimension: int = 4, order: int = 6, **overrides):
    tiny = F(1, 1_000_000)
    values = dict(
        base_dimension=dimension,
        base_invertibility_lower=F(9, 10),
        preimage_value_coupling_upper=F(1, 10),
        normalized_graph_derivative_bounds_with_point_modulus=(1, 1, 10, 100, 1000, 10000, 100000)[: order + 1],
        base_map_derivative_bounds=(F(1, 2),) + (tiny,) * (order - 1),
        base_map_derivative_point_lipschitz_bounds=(tiny,) * order,
        fiber_map_derivative_bounds=(F(1, 100),) + (tiny,) * (order - 1),
        fiber_map_derivative_point_lipschitz_bounds=(tiny,) * order,
    )
    values.update(overrides)
    return CN.quantitative_coupled_arbitrary_order_graph_transform(**values)


def _full(c0=None, cn=None):
    return M.quantitative_full_coupled_arbitrary_order_graph_transform(
        c0_certificate=_c0() if c0 is None else c0,
        derivative_certificate=_cn() if cn is None else cn,
    )


def _derivative_local(cn=None, **overrides):
    values = dict(
        global_certificate=_cn() if cn is None else cn,
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
    return LOCAL.quantitative_local_coupled_arbitrary_order_graph_transform(**values)


def _full_local(full=None, local=None):
    full = _full() if full is None else full
    local = _derivative_local(cn=full.derivative_certificate) if local is None else local
    return M.quantitative_full_local_coupled_arbitrary_order_graph_transform(
        global_certificate=full, derivative_local_certificate=local
    )


def _derivative_matched(local=None, **overrides):
    local = _derivative_local(uniform_inverse_base_image_radius_upper=1) if local is None else local
    values = dict(
        local_certificate=local,
        fiber_reference_scale=1,
        uniform_inverse_base_image_radius_exact=1,
        uniform_forward_base_image_radius_exact=1,
        graph_boundary_value_upper=0,
        fiber_boundary_forcing_upper=0,
    )
    values.update(overrides)
    return LOCAL.quantitative_matched_local_coupled_arbitrary_order_graph_transform(**values)


def _full_matched():
    full = _full()
    derivative_local = _derivative_local(
        cn=full.derivative_certificate, uniform_inverse_base_image_radius_upper=1
    )
    full_local = _full_local(full=full, local=derivative_local)
    derivative_matched = _derivative_matched(local=derivative_local)
    return M.quantitative_full_matched_local_coupled_arbitrary_order_graph_transform(
        local_certificate=full_local,
        derivative_matched_certificate=derivative_matched,
    )


def test_full_c6_closes_c0_and_derivative_certificate_at_exact_contacts() -> None:
    result = _full()
    assert result.validation_level is not None
    assert result.expected_preimage_value_coupling_upper == F(1, 10)
    assert result.c0_fiber_first_jet_numerator_upper == F(1, 100)
    assert result.c0_certificate.transform_contraction_factor_upper == F(11, 1000)
    assert result.differential_robust_interior is True
    assert result.robust_interior is False
    assert result.constant_contact_robust_interior is False
    assert result.full_cn_graph_real_dimension == 4


@pytest.mark.parametrize("order", [2, 4, 6])
def test_full_adapter_is_order_generic(order: int) -> None:
    result = _full(cn=_cn(order=order))
    assert result.validation_level is not None
    assert f"C0_TO_C{order}" in result.status


@pytest.mark.parametrize(
    "c0,cn,code",
    [
        (_c0(), _cn(dimension=5), "FULL_COUPLED_CN_BASE_DIMENSION_MISMATCH"),
        (_c0(), _cn(base_invertibility_lower=F(91, 100)), "FULL_COUPLED_CN_BASE_INVERTIBILITY_LOWER_MISMATCH"),
        (_c0(), _cn(normalized_graph_derivative_bounds_with_point_modulus=(2, 1, 10, 100, 1000, 10000, 100000)), "FULL_COUPLED_CN_GRAPH_SLOPE_MISMATCH"),
        (_c0(), _cn(preimage_value_coupling_upper=F(11, 100)), "FULL_COUPLED_CN_PREIMAGE_COUPLING_MISMATCH"),
        (_c0(), _cn(fiber_map_derivative_bounds=(F(1, 1000),) + (F(1, 1_000_000),) * 5), "FULL_COUPLED_CN_FIBER_FIRST_JET_UNDER_C0_SLOPE_NUMERATOR"),
    ],
)
def test_each_same_version_contact_fails_closed(c0, cn, code: str) -> None:
    result = _full(c0=c0, cn=cn)
    assert result.validation_level is None
    assert code in result.failure_codes


def test_failed_c0_predecessor_is_primary() -> None:
    bad = _c0(forcing_at_zero_upper=2)
    result = _full(c0=bad)
    assert result.status == bad.status


def test_full_iteration_updates_d0_with_c0_factor_and_higher_rows_synchronously() -> None:
    certificate = _full(cn=_cn(order=2))
    initial = (F(2), F(3), F(5))
    result = M.full_coupled_arbitrary_order_iteration_bound(
        certificate, initial_distance_by_derivative_order=initial, steps=1
    )
    levels = certificate.derivative_certificate.implicit_jet_certificate.levels
    assert result.distance_by_derivative_order_upper[0] == F(11, 1000) * initial[0]
    assert result.distance_by_derivative_order_upper[1:] == tuple(
        sum(coefficient * initial[index] for index, coefficient in enumerate(level.coefficient_by_input_order_upper))
        for level in levels
    )


def test_zero_steps_is_identity_and_two_steps_reuse_new_d0() -> None:
    certificate = _full(cn=_cn(order=2))
    initial = (F(1), F(0), F(0))
    zero = M.full_coupled_arbitrary_order_iteration_bound(
        certificate, initial_distance_by_derivative_order=initial, steps=0
    )
    two = M.full_coupled_arbitrary_order_iteration_bound(
        certificate, initial_distance_by_derivative_order=initial, steps=2
    )
    assert zero.distance_by_derivative_order_upper == initial
    assert two.distance_by_derivative_order_upper[0] == F(121, 1_000_000)


def test_local_and_matched_layers_preserve_the_exact_certificate_chain() -> None:
    local = _full_local()
    matched = _full_matched()
    assert local.validation_level is not None
    assert local.differential_and_collar_robust_interior is True
    assert local.robust_interior is False
    assert matched.validation_level is not None
    assert matched.differential_and_collar_robust_interior is True
    assert matched.constant_and_domain_contact_robust_interior is False
    assert matched.robust_interior is False


def test_local_rejects_derivative_certificate_and_base_scale_mismatches() -> None:
    full = _full()
    other = _derivative_local(cn=_cn(dimension=5))
    mismatch = _full_local(full=full, local=other)
    assert "FULL_LOCAL_COUPLED_CN_DERIVATIVE_CERTIFICATE_MISMATCH" in mismatch.failure_codes
    scaled = _derivative_local(cn=full.derivative_certificate, base_reference_scale=2)
    scale_mismatch = _full_local(full=full, local=scaled)
    assert "FULL_LOCAL_COUPLED_CN_BASE_REFERENCE_SCALE_MISMATCH" in scale_mismatch.failure_codes


def test_matched_rejects_local_chain_and_fiber_scale_mismatches() -> None:
    full = _full()
    derivative_local = _derivative_local(cn=full.derivative_certificate, uniform_inverse_base_image_radius_upper=1)
    full_local = _full_local(full=full, local=derivative_local)
    other_matched = _derivative_matched(
        local=_derivative_local(cn=_cn(dimension=5), uniform_inverse_base_image_radius_upper=1)
    )
    mismatch = M.quantitative_full_matched_local_coupled_arbitrary_order_graph_transform(
        local_certificate=full_local, derivative_matched_certificate=other_matched
    )
    assert "FULL_MATCHED_LOCAL_COUPLED_CN_LOCAL_CERTIFICATE_MISMATCH" in mismatch.failure_codes
    scale_mismatch = M.quantitative_full_matched_local_coupled_arbitrary_order_graph_transform(
        local_certificate=full_local,
        derivative_matched_certificate=_derivative_matched(local=derivative_local, fiber_reference_scale=2),
    )
    assert "FULL_MATCHED_LOCAL_COUPLED_CN_FIBER_REFERENCE_SCALE_MISMATCH" in scale_mismatch.failure_codes


def test_iteration_is_identical_through_full_global_local_and_matched_layers() -> None:
    matched = _full_matched()
    local = matched.local_certificate
    global_certificate = local.global_certificate
    initial = tuple(F(index + 1) for index in range(7))
    global_bound = M.full_coupled_arbitrary_order_iteration_bound(
        global_certificate, initial_distance_by_derivative_order=initial, steps=2
    )
    local_bound = M.full_local_coupled_arbitrary_order_iteration_bound(
        local, initial_distance_by_derivative_order=initial, steps=2
    )
    matched_bound = M.full_matched_local_coupled_arbitrary_order_iteration_bound(
        matched, initial_distance_by_derivative_order=initial, steps=2
    )
    assert global_bound == local_bound == matched_bound


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_and_never_selected(dimension: int) -> None:
    result = _full(c0=_c0(dimension), cn=_cn(dimension=dimension))
    assert result.full_cn_graph_real_dimension == dimension


def test_scale_covariance_preserves_all_normalized_contacts() -> None:
    scaled_c0 = _c0(
        base_reference_scale=5, fiber_reference_scale=7,
        fiber_radius=7, forcing_at_zero_upper=F(7, 10),
        fiber_to_base_lipschitz=F(9, 140), graph_slope_upper=F(7, 5),
    )
    full = _full(c0=scaled_c0)
    assert full.validation_level is not None
    derivative_local = _derivative_local(
        cn=full.derivative_certificate,
        base_reference_scale=5,
        input_base_domain_radius=5,
        output_base_domain_radius=5,
        uniform_inverse_base_image_radius_upper=3,
        input_extension_collar_radius=F(1, 2),
        output_extension_collar_radius=F(1, 4),
        uniform_inverse_collar_image_radius_upper=F(21, 4),
    )
    full_local = _full_local(full=full, local=derivative_local)
    assert full_local.validation_level is not None


@pytest.mark.parametrize(
    "initial,steps",
    [((1.0, 0, 0), 1), ((-1, 0, 0), 1), ((1, 0), 1), ((1, 0, 0), True)],
)
def test_iteration_rejects_inexact_negative_wrong_size_and_boolean_steps(initial, steps) -> None:
    with pytest.raises(ValueError):
        M.full_coupled_arbitrary_order_iteration_bound(
            _full(cn=_cn(order=2)),
            initial_distance_by_derivative_order=initial,
            steps=steps,
        )


def test_failed_full_certificate_cannot_be_iterated() -> None:
    failed = _full(cn=_cn(preimage_value_coupling_upper=F(11, 100)))
    with pytest.raises(ValueError, match="verified"):
        M.full_coupled_arbitrary_order_iteration_bound(
            failed, initial_distance_by_derivative_order=(1,) * 7, steps=1
        )
