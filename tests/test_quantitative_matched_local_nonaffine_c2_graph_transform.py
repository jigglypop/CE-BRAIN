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
L = _load(
    "quantitative_local_nonaffine_c2_graph_transform",
    "quantitative_local_nonaffine_c2_graph_transform.py",
)
M = _load(
    "ce_quantitative_matched_local_nonaffine_c2_graph",
    "quantitative_matched_local_nonaffine_c2_graph_transform.py",
)


def _certificate(**overrides):
    values = dict(
        base_dimension=1,
        base_reference_scale=1,
        fiber_reference_scale=1,
        base_domain_radius=1,
        output_base_domain_radius=1,
        inverse_base_image_radius_exact=1,
        forward_base_image_radius_exact=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=2,
        base_inverse_hessian_upper=12,
        fiber_linear_norm_upper=F(1, 16),
        base_to_fiber_lipschitz=0,
        fiber_nonlinear_lipschitz=F(1, 16),
        graph_slope_upper=F(1, 4),
        base_derivative_fiber_variation=0,
        fiber_derivative_fiber_variation=0,
        normalized_map_hessian_upper=0,
        normalized_map_hessian_fiber_lipschitz=0,
        normalized_graph_hessian_upper=1,
    )
    values.update(overrides)
    return M.quantitative_matched_local_nonaffine_c2_triangular_graph_transform(**values)


def test_matched_domain_certificate_has_exact_fixture_values() -> None:
    result = _certificate()
    predecessor = result.local_c2_certificate.nonaffine_c2_certificate
    assert result.status == "VERIFIED_QUANTITATIVE_MATCHED_LOCAL_NONAFFINE_C2_TRIANGULAR_GRAPH_TRANSFORM"
    assert predecessor.output_graph_hessian_upper == F(7, 8)
    assert predecessor.graph_hessian_margin == F(1, 8)
    assert predecessor.second_derivative_bunching_factor_upper == F(1, 2)
    assert predecessor.second_derivative_bunching_margin == F(1, 2)
    assert predecessor.derivative_to_hessian_cross_coefficient_upper == F(3, 2)
    assert predecessor.value_to_hessian_cross_coefficient_upper == 0
    assert result.inverse_boundary_contact_residual == 0
    assert result.forward_boundary_contact_residual == 0
    assert result.full_forward_retention_certified is True
    assert result.matched_domain_identity == M.MATCHED_LOCAL_INVARIANCE_KIND
    assert result.differential_robust_interior is True
    assert result.domain_contact_robust_interior is False
    assert result.robust_interior is False


def test_boundary_fixed_cubic_bounds_are_exact() -> None:
    bounds = M.boundary_fixed_cubic_unit_interval_c2_bounds(F(1, 4))
    assert bounds.inverse_derivative_upper == 2
    assert bounds.inverse_hessian_upper == 12
    assert bounds.forward_image_radius_exact == 1
    assert bounds.inverse_image_radius_exact == 1


def test_boundary_fixed_cubic_identity_limit() -> None:
    bounds = M.boundary_fixed_cubic_unit_interval_c2_bounds(0)
    assert bounds.inverse_derivative_upper == 1
    assert bounds.inverse_hessian_upper == 0
    result = _certificate(
        base_inverse_lipschitz=1,
        base_inverse_hessian_upper=0,
    )
    assert result.validation_level is not None
    assert result.local_c2_certificate.nonaffine_c2_certificate.output_graph_hessian_upper == F(1, 8)


@pytest.mark.parametrize("amplitude", [-1, F(1, 2), 1, 0.25, True, "01"])
def test_boundary_fixed_cubic_rejects_invalid_amplitude(amplitude: object) -> None:
    with pytest.raises(ValueError):
        M.boundary_fixed_cubic_unit_interval_c2_bounds(amplitude)


def test_cubic_is_monotone_and_boundary_fixed_on_exact_samples() -> None:
    a = F(1, 4)

    def phi(x: F) -> F:
        return x + a * x * (1 - x * x)

    points = [F(-1), F(-1, 2), F(0), F(1, 2), F(1)]
    images = [phi(x) for x in points]
    assert images[0] == -1
    assert images[-1] == 1
    assert images == sorted(images)
    assert min(1 + a - 3 * a * x * x for x in points) == F(1, 2)


def test_inverse_strict_interior_contact_is_rejected_as_not_exact() -> None:
    result = _certificate(inverse_base_image_radius_exact=F(1, 2))
    assert result.local_c2_certificate.validation_level is not None
    assert result.status == "MATCHED_LOCAL_C2_INVERSE_BOUNDARY_CONTACT_NOT_EXACT"
    assert result.inverse_boundary_contact_residual == F(1, 2)


def test_forward_strict_interior_contact_is_rejected_as_not_exact() -> None:
    result = _certificate(forward_base_image_radius_exact=F(1, 2))
    assert result.status == "MATCHED_LOCAL_C2_FORWARD_BOUNDARY_CONTACT_NOT_EXACT"
    assert result.forward_boundary_contact_residual == F(1, 2)


def test_both_strict_contacts_fail_closed_instead_of_claiming_robustness() -> None:
    result = _certificate(
        inverse_base_image_radius_exact=F(1, 2),
        forward_base_image_radius_exact=F(1, 2),
    )
    assert result.status == "MATCHED_LOCAL_C2_INVERSE_BOUNDARY_CONTACT_NOT_EXACT"
    assert "MATCHED_LOCAL_C2_FORWARD_BOUNDARY_CONTACT_NOT_EXACT" in result.failure_codes
    assert result.robust_interior is False


def test_forward_domain_overrun_has_distinct_failure() -> None:
    result = _certificate(forward_base_image_radius_exact=2)
    assert result.status == "MATCHED_LOCAL_C2_FORWARD_BASE_DOMAIN_NOT_COVERED"
    assert result.forward_boundary_contact_residual == -1


def test_inverse_domain_overrun_preserves_local_failure() -> None:
    result = _certificate(inverse_base_image_radius_exact=2)
    assert result.status == "LOCAL_C2_INVERSE_BASE_DOMAIN_NOT_COVERED"


def test_overflow_expander_cannot_be_promoted_to_matched_domain() -> None:
    result = _certificate(
        inverse_base_image_radius_exact=F(1, 2),
        forward_base_image_radius_exact=2,
        base_inverse_lipschitz=F(1, 2),
        base_inverse_hessian_upper=0,
    )
    assert result.local_c2_certificate.validation_level is not None
    assert result.validation_level is None
    assert "MATCHED_LOCAL_C2_FORWARD_BASE_DOMAIN_NOT_COVERED" in result.failure_codes


def test_predecessor_failure_remains_primary() -> None:
    result = _certificate(
        forcing_at_zero_upper=1,
        forward_base_image_radius_exact=2,
    )
    assert result.status == "GRAPH_TRANSFORM_TUBE_NOT_INVARIANT"


def test_exact_matched_iteration_keeps_predecessor_recurrence() -> None:
    result = _certificate()
    one = M.matched_local_nonaffine_c2_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        steps=1,
    )
    assert one.value_distance_upper == F(1, 4)
    assert one.derivative_distance_upper == F(3, 4)
    assert one.hessian_distance_upper == F(13, 2)


def test_iteration_rejects_unmatched_domain() -> None:
    result = _certificate(forward_base_image_radius_exact=2)
    with pytest.raises(ValueError, match="verified"):
        M.matched_local_nonaffine_c2_graph_iteration_bound(
            result,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            steps=1,
        )


def test_base_scale_covariance_preserves_boundary_identity() -> None:
    base = _certificate()
    scaled = _certificate(
        base_reference_scale=5,
        base_domain_radius=5,
        output_base_domain_radius=5,
        inverse_base_image_radius_exact=5,
        forward_base_image_radius_exact=5,
        graph_slope_upper=F(1, 20),
    )
    assert scaled.normalized_output_base_domain_radius == base.normalized_output_base_domain_radius
    assert scaled.normalized_forward_base_image_radius_exact == base.normalized_forward_base_image_radius_exact
    assert scaled.inverse_boundary_contact_residual == 0
    assert scaled.forward_boundary_contact_residual == 0
    assert scaled.local_c2_certificate.nonaffine_c2_certificate.output_graph_hessian_upper == F(7, 8)


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_supplied_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.matched_local_c2_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("output_base_domain_radius", 0),
        ("output_base_domain_radius", -1),
        ("forward_base_image_radius_exact", -1),
        ("output_base_domain_radius", 1.0),
        ("forward_base_image_radius_exact", True),
        ("output_base_domain_radius", "01"),
    ],
)
def test_invalid_matched_domain_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_domain_strings_are_exact() -> None:
    result = _certificate(
        base_domain_radius="1",
        output_base_domain_radius="1",
        inverse_base_image_radius_exact="1",
        forward_base_image_radius_exact="1",
    )
    assert result.validation_level is not None
