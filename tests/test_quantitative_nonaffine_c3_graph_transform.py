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
C2 = _load("quantitative_c2_graph_transform", "quantitative_c2_graph_transform.py")
TC3 = _load("quantitative_c3_graph_transform", "quantitative_c3_graph_transform.py")
NC2 = _load("quantitative_nonaffine_c2_graph_transform", "quantitative_nonaffine_c2_graph_transform.py")
M = _load("ce_quantitative_nonaffine_c3", "quantitative_nonaffine_c3_graph_transform.py")


def _certificate(**overrides):
    bounds = M.sine_perturbed_base_c3_bounds(F(1, 10))
    values = dict(
        base_dimension=5,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=bounds.inverse_derivative_upper,
        base_inverse_hessian_upper=bounds.inverse_hessian_upper,
        base_inverse_third_derivative_upper=bounds.inverse_third_derivative_upper,
        fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 8),
        fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 16),
        fiber_derivative_fiber_variation=F(1, 16),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_third_derivative_upper=F(1, 16),
        normalized_map_third_derivative_fiber_lipschitz=F(1, 64),
        normalized_graph_hessian_upper=2,
        normalized_graph_third_derivative_upper=8,
    )
    values.update(overrides)
    return M.quantitative_nonaffine_c3_triangular_graph_transform(**values)


def test_strict_nonaffine_c3_certificate_has_exact_three_chain_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_NONAFFINE_C3_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.nonaffine_c2_certificate.validation_level is not None
    q, mu, nu, tau = F(1, 2), F(10, 9), F(100, 729), F(14000, 59049)
    r, k2, k3, lambda2, lambda3 = 2, F(1, 16), F(1, 16), 2, 8
    s = F(5, 8)
    a2 = q * lambda2 + k2 * r**2
    a3 = q * lambda3 + 3 * k2 * lambda2 * r + k3 * r**3
    assert result.output_graph_third_derivative_upper == mu**3 * a3 + 3 * mu * nu * a2 + s * tau
    assert result.graph_third_derivative_margin > 0
    assert result.third_derivative_bunching_factor_upper == F(500, 729)
    assert result.third_derivative_bunching_margin == F(229, 729)
    assert result.hessian_to_third_derivative_cross_coefficient_upper > 0
    assert result.derivative_to_third_derivative_cross_coefficient_upper > 0
    assert result.value_to_third_derivative_cross_coefficient_upper > 0
    assert result.c3_graph_real_dimension == 5
    assert result.robust_interior is True


def test_sine_inverse_c3_bounds_are_exact_and_affine_at_zero() -> None:
    zero = M.sine_perturbed_base_c3_bounds(0)
    tenth = M.sine_perturbed_base_c3_bounds(F(1, 10))
    assert (zero.inverse_derivative_upper, zero.inverse_hessian_upper, zero.inverse_third_derivative_upper) == (1, 0, 0)
    assert tenth.inverse_derivative_upper == F(10, 9)
    assert tenth.inverse_hessian_upper == F(100, 729)
    assert tenth.inverse_third_derivative_upper == F(14000, 59049)


@pytest.mark.parametrize("amplitude", [-1, 1, F(3, 2), 0.1, True, "01"])
def test_sine_inverse_c3_bounds_reject_invalid_amplitude(amplitude: object) -> None:
    with pytest.raises(ValueError):
        M.sine_perturbed_base_c3_bounds(amplitude)


def test_nonzero_inverse_third_chain_identity_at_sine_origin() -> None:
    # phi=x+a sin(x), psi=phi^-1. At zero: psi''=0 and psi'''=a/(1+a)^4.
    a = F(1, 10)
    p = 1 / (1 + a)
    h = F(0)
    t = a / (1 + a) ** 4
    # S(x)=x+x^2+x^3 at zero has derivatives 1,2,6.
    chain = 6 * p**3 + 3 * 2 * h * p + t
    assert chain == F(6000, 1331) + F(1000, 14641)


def test_exact_four_level_iteration_uses_previous_state() -> None:
    result = _certificate()
    one = M.nonaffine_c3_graph_iteration_bound(
        result, initial_value_distance=2, initial_derivative_distance=3,
        initial_hessian_distance=4, initial_third_derivative_distance=5,
        steps=1,
    )
    c2 = result.nonaffine_c2_certificate
    c1 = c2.c1_certificate
    assert one.value_distance_upper == 1
    assert one.derivative_distance_upper == 3 * c1.derivative_bunching_factor_upper + 2 * c1.derivative_cross_coefficient_upper
    assert one.hessian_distance_upper == 4 * c2.second_derivative_bunching_factor_upper + 3 * c2.derivative_to_hessian_cross_coefficient_upper + 2 * c2.value_to_hessian_cross_coefficient_upper
    assert one.third_derivative_distance_upper == 5 * result.third_derivative_bunching_factor_upper + 4 * result.hessian_to_third_derivative_cross_coefficient_upper + 3 * result.derivative_to_third_derivative_cross_coefficient_upper + 2 * result.value_to_third_derivative_cross_coefficient_upper


def test_zero_inverse_curvature_reduces_exactly_to_affine_c3() -> None:
    nonaffine = _certificate(
        base_inverse_lipschitz=1,
        base_inverse_hessian_upper=0,
        base_inverse_third_derivative_upper=0,
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=2,
        base_to_fiber_lipschitz=F(1, 4),
    )
    affine = TC3.quantitative_c3_triangular_graph_transform(
        base_dimension=5, base_reference_scale=1, fiber_reference_scale=1,
        fiber_radius=1, forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=1, fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 4), fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1, base_derivative_fiber_variation=F(1, 16),
        fiber_derivative_fiber_variation=F(1, 16),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_third_derivative_upper=F(1, 16),
        normalized_map_third_derivative_fiber_lipschitz=F(1, 64),
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=2,
    )
    assert nonaffine.validation_level is not None
    assert affine.validation_level is not None
    assert nonaffine.output_graph_third_derivative_upper == affine.output_graph_third_derivative_upper
    assert nonaffine.third_derivative_bunching_factor_upper == affine.third_derivative_bunching_factor_upper
    assert nonaffine.hessian_to_third_derivative_cross_coefficient_upper == affine.hessian_to_third_derivative_cross_coefficient_upper
    assert nonaffine.derivative_to_third_derivative_cross_coefficient_upper == affine.derivative_to_third_derivative_cross_coefficient_upper
    assert nonaffine.value_to_third_derivative_cross_coefficient_upper == affine.value_to_third_derivative_cross_coefficient_upper


def test_inverse_hessian_and_third_terms_vanish_separately() -> None:
    curved = _certificate()
    no_tau = _certificate(base_inverse_third_derivative_upper=0)
    affine_inverse = _certificate(base_inverse_hessian_upper=0, base_inverse_third_derivative_upper=0)
    assert curved.output_graph_third_derivative_upper > no_tau.output_graph_third_derivative_upper
    assert no_tau.output_graph_third_derivative_upper > affine_inverse.output_graph_third_derivative_upper
    assert curved.derivative_to_third_derivative_cross_coefficient_upper > no_tau.derivative_to_third_derivative_cross_coefficient_upper
    assert no_tau.hessian_to_third_derivative_cross_coefficient_upper > affine_inverse.hessian_to_third_derivative_cross_coefficient_upper


def test_c3_class_equality_passes_nonrobust() -> None:
    common = dict(base_inverse_lipschitz=1, base_inverse_hessian_upper=0, base_inverse_third_derivative_upper=0, normalized_graph_hessian_upper=1)
    at_zero = _certificate(normalized_graph_third_derivative_upper=0, **common)
    at_two = _certificate(normalized_graph_third_derivative_upper=2, **common)
    a = at_zero.output_graph_third_derivative_upper
    b = (at_two.output_graph_third_derivative_upper - a) / 2
    fixed = a / (1 - b)
    result = _certificate(normalized_graph_third_derivative_upper=fixed, **common)
    assert result.validation_level is not None
    assert result.graph_third_derivative_margin == 0
    assert result.robust_interior is False


def test_c3_bunching_equality_fails_after_nonaffine_c2_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2, base_inverse_hessian_upper=0,
        base_inverse_third_derivative_upper=0, fiber_linear_norm_upper=F(1, 8),
        fiber_nonlinear_lipschitz=0, base_to_fiber_lipschitz=0,
        graph_slope_upper=0, base_derivative_fiber_variation=0,
        fiber_derivative_fiber_variation=0, normalized_map_hessian_upper=0,
        normalized_map_third_derivative_upper=0,
        normalized_map_third_derivative_fiber_lipschitz=0,
        normalized_graph_hessian_upper=0,
        normalized_graph_third_derivative_upper=0,
    )
    assert result.nonaffine_c2_certificate.validation_level is not None
    assert result.nonaffine_c2_certificate.second_derivative_bunching_factor_upper == F(1, 2)
    assert result.third_derivative_bunching_factor_upper == 1
    assert result.status == "NONAFFINE_C3_THIRD_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_predecessor_failure_is_primary_and_iteration_rejects() -> None:
    result = _certificate(forcing_at_zero_upper=1)
    assert result.status == "GRAPH_TRANSFORM_TUBE_NOT_INVARIANT"
    with pytest.raises(ValueError, match="verified"):
        M.nonaffine_c3_graph_iteration_bound(
            result, initial_value_distance=1, initial_derivative_distance=1,
            initial_hessian_distance=1, initial_third_derivative_distance=1,
            steps=1,
        )


def test_base_fiber_rescaling_preserves_normalized_nonaffine_c3_constants() -> None:
    base = _certificate()
    scaled = _certificate(
        base_reference_scale=5,
        fiber_reference_scale=7,
        fiber_radius=7,
        forcing_at_zero_upper=F(7, 4),
        base_to_fiber_lipschitz=F(7, 40),
        graph_slope_upper=F(7, 5),
        base_derivative_fiber_variation=F(1, 80),
        fiber_derivative_fiber_variation=F(1, 112),
    )
    assert scaled.status == base.status
    assert scaled.output_graph_third_derivative_upper == base.output_graph_third_derivative_upper
    assert scaled.third_derivative_bunching_factor_upper == base.third_derivative_bunching_factor_upper
    assert scaled.hessian_to_third_derivative_cross_coefficient_upper == base.hessian_to_third_derivative_cross_coefficient_upper
    assert scaled.derivative_to_third_derivative_cross_coefficient_upper == base.derivative_to_third_derivative_cross_coefficient_upper
    assert scaled.value_to_third_derivative_cross_coefficient_upper == base.value_to_third_derivative_cross_coefficient_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.c3_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_inverse_third_derivative_upper", -1),
        ("normalized_map_third_derivative_upper", -1),
        ("normalized_map_third_derivative_fiber_lipschitz", -1),
        ("normalized_graph_third_derivative_upper", -1),
        ("base_inverse_third_derivative_upper", 0.1),
        ("normalized_map_third_derivative_upper", True),
        ("normalized_graph_third_derivative_upper", "08"),
    ],
)
def test_invalid_nonaffine_c3_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})
