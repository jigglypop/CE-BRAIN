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
L = _load(
    "quantitative_local_nonaffine_coupled_c2_graph_transform",
    "quantitative_local_nonaffine_coupled_c2_graph_transform.py",
)
M = _load(
    "ce_quantitative_matched_local_nonaffine_coupled_c2",
    "quantitative_matched_local_nonaffine_coupled_c2_graph_transform.py",
)


def _certificate(**overrides):
    values = dict(
        base_dimension=4,
        base_reference_scale=1,
        fiber_reference_scale=1,
        input_base_domain_radius=1,
        output_base_domain_radius=1,
        uniform_inverse_base_image_radius_exact=1,
        uniform_forward_base_image_radius_exact=1,
        graph_boundary_value_upper=0,
        fiber_boundary_forcing_upper=0,
        fiber_radius=1,
        forcing_at_zero_upper=0,
        base_inverse_lipschitz=F(50, 49),
        fiber_linear_norm_upper=F(1, 10),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=F(1, 100),
        base_to_fiber_lipschitz=0,
        fiber_self_lipschitz=0,
        graph_slope_upper=F(1, 2),
        normalized_base_map_hessian_upper=F(3, 50),
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=1,
        normalized_base_map_hessian_lipschitz=F(3, 50),
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=0,
        graph_hessian_lipschitz_upper=1,
    )
    values.update(overrides)
    return M.quantitative_matched_local_nonaffine_coupled_c2_graph_transform(**values)


def _local_certificate():
    return L.quantitative_local_nonaffine_coupled_c2_graph_transform(
        base_dimension=4,
        base_reference_scale=1,
        fiber_reference_scale=1,
        input_base_domain_radius=1,
        output_base_domain_radius=1,
        uniform_inverse_base_image_radius_upper=1,
        fiber_radius=1,
        forcing_at_zero_upper=0,
        base_inverse_lipschitz=F(50, 49),
        fiber_linear_norm_upper=F(1, 10),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=F(1, 100),
        base_to_fiber_lipschitz=0,
        fiber_self_lipschitz=0,
        graph_slope_upper=F(1, 2),
        normalized_base_map_hessian_upper=F(3, 50),
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=1,
        normalized_base_map_hessian_lipschitz=F(3, 50),
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=0,
        graph_hessian_lipschitz_upper=1,
    )


def test_strict_matched_coupled_certificate_exposes_exact_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_MATCHED_LOCAL_NONAFFINE_COUPLED_C2_GRAPH_TRANSFORM"
    assert result.inverse_boundary_contact_residual == 0
    assert result.forward_boundary_contact_residual == 0
    assert result.normalized_graph_boundary_value_upper == 0
    assert result.normalized_fiber_boundary_forcing_upper == 0
    assert result.full_forward_retention_certified is True
    assert result.boundary_anchored_graph_class_certified is True
    assert result.domain_contact_robust_interior is False
    assert result.differential_robust_interior is True
    assert result.robust_interior is False
    assert result.matched_local_c2_graph_real_dimension == 4


def test_boundary_anchored_cubic_coupled_witness_is_exact() -> None:
    bounds = M.boundary_anchored_cubic_coupled_unit_interval_c2_bounds(
        amplitude_upper=F(1, 100),
        fiber_coupling_upper=F(1, 100),
        graph_slope_upper=F(1, 2),
    )
    assert bounds.base_inverse_lipschitz_upper == F(50, 49)
    assert bounds.coupled_inverse_lipschitz_upper == F(40, 39)
    assert bounds.base_map_hessian_upper == F(3, 50)
    assert bounds.base_map_hessian_lipschitz_upper == F(3, 50)
    assert bounds.forward_image_radius_exact == 1
    assert bounds.inverse_image_radius_exact == 1
    assert bounds.graph_boundary_value_exact == 0


def test_cubic_coupled_witness_fixes_endpoints_and_is_strictly_increasing() -> None:
    amplitude = F(1, 100)
    coupling = F(1, 100)

    def h(x: F) -> F:
        return (1 - x * x) / 4

    def h_prime(x: F) -> F:
        return -x / 2

    def base_map(x: F) -> F:
        return x + amplitude * x * (1 - x * x) + coupling * h(x)

    assert base_map(F(-1)) == -1
    assert base_map(F(1)) == 1
    for x in [F(-1), F(-1, 2), F(0), F(1, 2), F(1)]:
        derivative = 1 + amplitude - 3 * amplitude * x * x + coupling * h_prime(x)
        assert derivative >= F(39, 40)


def test_zero_coupling_reduces_witness_to_graph_independent_cubic() -> None:
    bounds = M.boundary_anchored_cubic_coupled_unit_interval_c2_bounds(
        amplitude_upper=F(1, 100),
        fiber_coupling_upper=0,
        graph_slope_upper=100,
    )
    assert bounds.coupled_inverse_lipschitz_upper == bounds.base_inverse_lipschitz_upper


@pytest.mark.parametrize(
    "values",
    [
        dict(amplitude_upper=-1, fiber_coupling_upper=0, graph_slope_upper=0),
        dict(amplitude_upper=F(1, 2), fiber_coupling_upper=0, graph_slope_upper=0),
        dict(amplitude_upper=0, fiber_coupling_upper=-1, graph_slope_upper=0),
        dict(amplitude_upper=0, fiber_coupling_upper=0, graph_slope_upper=-1),
        dict(amplitude_upper=0, fiber_coupling_upper=1, graph_slope_upper=1),
        dict(amplitude_upper=0.0, fiber_coupling_upper=0, graph_slope_upper=0),
        dict(amplitude_upper=True, fiber_coupling_upper=0, graph_slope_upper=0),
    ],
)
def test_witness_rejects_invalid_inputs(values: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        M.boundary_anchored_cubic_coupled_unit_interval_c2_bounds(**values)


def test_matched_wrapper_preserves_the_complete_local_predecessor() -> None:
    assert _certificate().local_nonaffine_coupled_c2_certificate == _local_certificate()


def test_exact_differential_fixture_values_are_preserved() -> None:
    predecessor = _certificate().local_nonaffine_coupled_c2_certificate.nonaffine_coupled_c2_certificate
    assert predecessor.output_graph_hessian_lipschitz_upper == F(4085248, 30074733)
    assert predecessor.second_derivative_bunching_factor_upper == F(6272, 59319)
    assert predecessor.derivative_to_hessian_cross_coefficient_upper == F(37888, 3855735)
    assert predecessor.value_to_hessian_cross_coefficient_upper == F(1021312, 751868325)


def test_inverse_strict_contact_is_rejected_as_inconsistent() -> None:
    result = _certificate(uniform_inverse_base_image_radius_exact=F(9, 10))
    assert result.status == "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_INVERSE_BOUNDARY_CONTACT_NOT_EXACT"


def test_inverse_overrun_keeps_local_coverage_failure_primary() -> None:
    result = _certificate(uniform_inverse_base_image_radius_exact=F(11, 10))
    assert result.status == "LOCAL_NONAFFINE_COUPLED_C2_INVERSE_BASE_DOMAIN_NOT_COVERED"


def test_forward_strict_contact_is_rejected_as_inconsistent() -> None:
    result = _certificate(uniform_forward_base_image_radius_exact=F(9, 10))
    assert result.status == "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_FORWARD_BOUNDARY_CONTACT_NOT_EXACT"


def test_forward_overrun_fails_coverage() -> None:
    result = _certificate(uniform_forward_base_image_radius_exact=F(11, 10))
    assert result.status == "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_FORWARD_BASE_DOMAIN_NOT_COVERED"


def test_graph_boundary_failure_is_independent_and_named() -> None:
    result = _certificate(graph_boundary_value_upper=F(1, 100))
    assert result.status == "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_GRAPH_BOUNDARY_NOT_ANCHORED"
    assert "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_FIBER_BOUNDARY_NOT_PRESERVED" not in result.failure_codes


def test_fiber_boundary_failure_is_independent_and_named() -> None:
    result = _certificate(fiber_boundary_forcing_upper=F(1, 100))
    assert result.status == "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_FIBER_BOUNDARY_NOT_PRESERVED"


def test_all_matched_failures_have_stable_order() -> None:
    result = _certificate(
        uniform_inverse_base_image_radius_exact=F(9, 10),
        uniform_forward_base_image_radius_exact=F(9, 10),
        graph_boundary_value_upper=1,
        fiber_boundary_forcing_upper=1,
    )
    assert result.failure_codes == (
        "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_INVERSE_BOUNDARY_CONTACT_NOT_EXACT",
        "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_FORWARD_BOUNDARY_CONTACT_NOT_EXACT",
        "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_GRAPH_BOUNDARY_NOT_ANCHORED",
        "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_FIBER_BOUNDARY_NOT_PRESERVED",
    )


def test_predecessor_failure_remains_primary() -> None:
    result = _certificate(
        forcing_at_zero_upper=1,
        uniform_forward_base_image_radius_exact=F(9, 10),
    )
    assert result.status == "COUPLED_GRAPH_TUBE_NOT_INVARIANT"
    assert "MATCHED_LOCAL_NONAFFINE_COUPLED_C2_FORWARD_BOUNDARY_CONTACT_NOT_EXACT" in result.failure_codes


def test_unanchored_graph_shifts_a_fixed_base_boundary() -> None:
    epsilon = F(1, 100)
    assert 1 + epsilon > 1


def test_nonzero_fiber_boundary_forcing_exits_the_anchored_class() -> None:
    boundary_graph_value = F(0)
    boundary_forcing = F(1, 100)
    assert F(1, 10) * boundary_graph_value + boundary_forcing != 0


def test_exact_iteration_uses_the_local_predecessor_recurrence() -> None:
    one = M.matched_local_nonaffine_coupled_c2_graph_iteration_bound(
        _certificate(),
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=1,
    )
    assert one.value_distance_upper == F(196, 975)
    assert one.derivative_distance_upper == F(461872, 1482975)
    assert one.hessian_distance_upper == F(342197504, 751868325)


def test_iteration_rejects_failed_matched_certificate() -> None:
    result = _certificate(graph_boundary_value_upper=1)
    with pytest.raises(ValueError, match="verified certificate"):
        M.matched_local_nonaffine_coupled_c2_graph_iteration_bound(
            result,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            steps=1,
        )


def test_base_and_fiber_scale_covariance_preserves_certificate() -> None:
    base = _certificate()
    scaled = _certificate(
        base_reference_scale=5,
        fiber_reference_scale=7,
        input_base_domain_radius=5,
        output_base_domain_radius=5,
        uniform_inverse_base_image_radius_exact=5,
        uniform_forward_base_image_radius_exact=5,
        fiber_radius=7,
        fiber_to_base_lipschitz=F(1, 140),
        graph_slope_upper=F(7, 10),
    )
    assert scaled.inverse_boundary_contact_residual == base.inverse_boundary_contact_residual
    assert scaled.forward_boundary_contact_residual == base.forward_boundary_contact_residual
    assert scaled.local_nonaffine_coupled_c2_certificate.nonaffine_coupled_c2_certificate.output_graph_hessian_lipschitz_upper == base.local_nonaffine_coupled_c2_certificate.nonaffine_coupled_c2_certificate.output_graph_hessian_lipschitz_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_supplied_dimension_is_preserved_not_selected(dimension: int) -> None:
    assert _certificate(base_dimension=dimension).matched_local_c2_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("uniform_forward_base_image_radius_exact", -1),
        ("graph_boundary_value_upper", -1),
        ("fiber_boundary_forcing_upper", -1),
        ("uniform_forward_base_image_radius_exact", 1.0),
        ("graph_boundary_value_upper", True),
        ("fiber_boundary_forcing_upper", "01"),
    ],
)
def test_invalid_matched_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_strings_are_exact() -> None:
    result = _certificate(
        uniform_inverse_base_image_radius_exact="1",
        uniform_forward_base_image_radius_exact="1",
        graph_boundary_value_upper="0",
        fiber_boundary_forcing_upper="0",
    )
    assert result.validation_level is not None
