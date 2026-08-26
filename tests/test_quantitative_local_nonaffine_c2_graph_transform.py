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
NA = _load(
    "quantitative_nonaffine_c2_graph_transform",
    "quantitative_nonaffine_c2_graph_transform.py",
)
M = _load(
    "ce_quantitative_local_nonaffine_c2_graph",
    "quantitative_local_nonaffine_c2_graph_transform.py",
)


def _certificate(**overrides):
    values = dict(
        base_dimension=4,
        base_reference_scale=1,
        fiber_reference_scale=1,
        base_domain_radius=1,
        inverse_base_image_radius_upper=F(4, 7),
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=F(4, 7),
        base_inverse_hessian_upper=F(16, 343),
        fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 8),
        fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 16),
        fiber_derivative_fiber_variation=F(1, 16),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_hessian_fiber_lipschitz=F(1, 16),
        normalized_graph_hessian_upper=1,
    )
    values.update(overrides)
    return M.quantitative_local_nonaffine_c2_triangular_graph_transform(**values)


def test_strict_local_certificate_exposes_exact_contract_values() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_LOCAL_NONAFFINE_C2_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.inverse_domain_coverage_margin == F(3, 7)
    assert result.nonaffine_c2_certificate.output_graph_hessian_upper == F(94, 343)
    assert result.nonaffine_c2_certificate.second_derivative_bunching_factor_upper == F(8, 49)
    assert result.nonaffine_c2_certificate.derivative_to_hessian_cross_coefficient_upper == F(36, 343)
    assert result.nonaffine_c2_certificate.value_to_hessian_cross_coefficient_upper == F(37, 343)
    assert result.local_invariance_kind == "BACKWARD_COVERED_OVERFLOW_INVARIANT"
    assert result.forward_retention_certified is False
    assert result.local_c2_graph_real_dimension == 4
    assert result.robust_interior is True


def test_expanding_sine_witness_bounds_are_exact() -> None:
    bounds = M.expanding_sine_local_base_c2_bounds(
        linear_coefficient=2,
        amplitude_upper=F(1, 4),
        base_domain_radius=1,
    )
    assert bounds.inverse_derivative_upper == F(4, 7)
    assert bounds.inverse_hessian_upper == F(16, 343)
    assert bounds.inverse_image_radius_upper == F(4, 7)


def test_linear_expander_has_zero_inverse_curvature() -> None:
    bounds = M.expanding_sine_local_base_c2_bounds(
        linear_coefficient=2,
        amplitude_upper=0,
        base_domain_radius=3,
    )
    assert bounds.inverse_derivative_upper == F(1, 2)
    assert bounds.inverse_hessian_upper == 0
    assert bounds.inverse_image_radius_upper == F(3, 2)


@pytest.mark.parametrize(
    "values",
    [
        dict(linear_coefficient=0, amplitude_upper=0, base_domain_radius=1),
        dict(linear_coefficient=1, amplitude_upper=1, base_domain_radius=1),
        dict(linear_coefficient=1, amplitude_upper=2, base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=-1, base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=0, base_domain_radius=0),
        dict(linear_coefficient=2.0, amplitude_upper=0, base_domain_radius=1),
        dict(linear_coefficient=2, amplitude_upper=True, base_domain_radius=1),
    ],
)
def test_expanding_sine_witness_rejects_invalid_inputs(values: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        M.expanding_sine_local_base_c2_bounds(**values)


def test_coverage_equality_passes_but_is_not_robust() -> None:
    result = _certificate(inverse_base_image_radius_upper=1)
    assert result.validation_level is not None
    assert result.inverse_domain_coverage_margin == 0
    assert result.robust_interior is False


def test_inverse_domain_coverage_failure_is_named() -> None:
    result = _certificate(inverse_base_image_radius_upper=F(8, 7))
    assert result.nonaffine_c2_certificate.validation_level is not None
    assert result.status == "LOCAL_C2_INVERSE_BASE_DOMAIN_NOT_COVERED"
    assert result.validation_level is None
    assert result.inverse_domain_coverage_margin == F(-1, 7)


def test_predecessor_failure_remains_primary() -> None:
    result = _certificate(
        forcing_at_zero_upper=1,
        inverse_base_image_radius_upper=2,
    )
    assert result.status == "GRAPH_TRANSFORM_TUBE_NOT_INVARIANT"
    assert "LOCAL_C2_INVERSE_BASE_DOMAIN_NOT_COVERED" in result.failure_codes


def test_local_arithmetic_is_exactly_the_predecessor_arithmetic() -> None:
    result = _certificate()
    predecessor = NA.quantitative_nonaffine_c2_triangular_graph_transform(
        base_dimension=4,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=F(4, 7),
        base_inverse_hessian_upper=F(16, 343),
        fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 8),
        fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 16),
        fiber_derivative_fiber_variation=F(1, 16),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_hessian_fiber_lipschitz=F(1, 16),
        normalized_graph_hessian_upper=1,
    )
    assert result.nonaffine_c2_certificate == predecessor


def test_contracting_base_exposes_missing_inverse_coverage() -> None:
    # U=[-1,1], phi(x)=x/2 and psi(x')=2x': x'=3/4 needs h(3/2).
    output_point = F(3, 4)
    preimage = 2 * output_point
    assert abs(preimage) > 1
    result = _certificate(
        base_inverse_lipschitz=2,
        base_inverse_hessian_upper=0,
        inverse_base_image_radius_upper=2,
        fiber_linear_norm_upper=F(1, 16),
        fiber_nonlinear_lipschitz=F(1, 16),
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
        base_derivative_fiber_variation=0,
        fiber_derivative_fiber_variation=0,
        normalized_map_hessian_upper=0,
        normalized_map_hessian_fiber_lipschitz=0,
        normalized_graph_hessian_upper=0,
    )
    assert result.status == "LOCAL_C2_INVERSE_BASE_DOMAIN_NOT_COVERED"


def test_expanding_base_proves_overflow_not_full_forward_retention() -> None:
    # U=[-1,1], phi(x)=2x has inverse coverage but x=3/4 exits forward.
    result = _certificate(
        base_inverse_lipschitz=F(1, 2),
        base_inverse_hessian_upper=0,
        inverse_base_image_radius_upper=F(1, 2),
    )
    assert result.validation_level is not None
    assert 2 * F(3, 4) > 1
    assert result.forward_retention_certified is False


def test_exact_local_iteration_uses_predecessor_recurrence() -> None:
    result = _certificate()
    one = M.local_nonaffine_c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=1,
    )
    assert one.value_distance_upper == 1
    assert one.derivative_distance_upper == 1
    assert one.hessian_distance_upper == F(406, 343)


def test_iteration_rejects_failed_local_coverage() -> None:
    result = _certificate(inverse_base_image_radius_upper=2)
    with pytest.raises(ValueError, match="verified local"):
        M.local_nonaffine_c2_graph_iteration_bound(
            result,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            steps=1,
        )


def test_base_scale_covariance_preserves_local_certificate() -> None:
    base = _certificate()
    scaled = _certificate(
        base_reference_scale=5,
        base_domain_radius=5,
        inverse_base_image_radius_upper=F(20, 7),
        base_to_fiber_lipschitz=F(1, 40),
        graph_slope_upper=F(1, 5),
        base_derivative_fiber_variation=F(1, 80),
    )
    assert scaled.normalized_base_domain_radius == base.normalized_base_domain_radius
    assert scaled.normalized_inverse_base_image_radius_upper == base.normalized_inverse_base_image_radius_upper
    assert scaled.inverse_domain_coverage_margin == base.inverse_domain_coverage_margin
    assert scaled.nonaffine_c2_certificate.output_graph_hessian_upper == base.nonaffine_c2_certificate.output_graph_hessian_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_supplied_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.local_c2_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_domain_radius", 0),
        ("base_domain_radius", -1),
        ("inverse_base_image_radius_upper", -1),
        ("base_domain_radius", 1.0),
        ("inverse_base_image_radius_upper", True),
        ("base_domain_radius", "01"),
    ],
)
def test_invalid_local_domain_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_domain_strings_are_exact() -> None:
    result = _certificate(
        base_domain_radius="1",
        inverse_base_image_radius_upper="4/7",
    )
    assert result.validation_level is not None
    assert result.inverse_domain_coverage_margin == F(3, 7)

