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
NC1 = _load(
    "quantitative_nonaffine_coupled_c1_graph_transform",
    "quantitative_nonaffine_coupled_c1_graph_transform.py",
)
NC2 = _load(
    "quantitative_nonaffine_coupled_c2_graph_transform",
    "quantitative_nonaffine_coupled_c2_graph_transform.py",
)
CC1 = _load("quantitative_coupled_c1_graph_transform", "quantitative_coupled_c1_graph_transform.py")
CC2 = _load("quantitative_coupled_c2_graph_transform", "quantitative_coupled_c2_graph_transform.py")
AC3 = _load("quantitative_coupled_c3_graph_transform", "quantitative_coupled_c3_graph_transform.py")
G = _load("quantitative_graph_transform", "quantitative_graph_transform.py")
C1 = _load("quantitative_c1_graph_transform", "quantitative_c1_graph_transform.py")
TNC2 = _load("quantitative_nonaffine_c2_graph_transform", "quantitative_nonaffine_c2_graph_transform.py")
TNC3 = _load("quantitative_nonaffine_c3_graph_transform", "quantitative_nonaffine_c3_graph_transform.py")
M = _load(
    "ce_quantitative_nonaffine_coupled_c3",
    "quantitative_nonaffine_coupled_c3_graph_transform.py",
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
        normalized_base_map_third_derivative_lipschitz=F(1, 1000),
        normalized_base_third_derivative_lipschitz=F(1, 10000),
        normalized_fiber_third_derivative_lipschitz=F(1, 10000),
        normalized_graph_third_derivative_upper=2,
        graph_third_derivative_lipschitz_upper=2,
    )
    values.update(overrides)
    return M.quantitative_nonaffine_coupled_c3_graph_transform(**values)


def test_strict_nonaffine_coupled_c3_certificate_exposes_all_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_NONAFFINE_COUPLED_C3_GRAPH_TRANSFORM"
    assert result.nonaffine_coupled_c2_certificate.validation_level is not None
    assert result.graph_third_derivative_lipschitz_required is True
    assert result.graph_third_derivative_margin > 0
    assert result.graph_third_derivative_lipschitz_margin > 0
    assert result.third_derivative_bunching_margin > 0
    assert result.base_third_derivative_upper > 0
    assert result.base_third_derivative_lipschitz_upper > 0
    assert result.modified_third_difference_value_coefficient_upper > 0
    assert result.c3_graph_real_dimension == 3
    assert result.robust_interior is True


def test_sine_perturbed_forward_c3_bounds_are_exact() -> None:
    result = M.sine_perturbed_coupled_base_c3_bounds(
        linear_coefficient=F(1001, 1000), amplitude_upper=F(1, 1000)
    )
    assert result.inverse_lipschitz_upper == 1
    assert result.base_map_hessian_upper == F(1, 1000)
    assert result.base_map_hessian_lipschitz_upper == F(1, 1000)
    assert result.base_map_third_derivative_lipschitz_upper == F(1, 1000)


@pytest.mark.parametrize(
    "linear,amplitude",
    [(1, 1), (1, -1), (0, 0), (F(1, 2), F(3, 4)), (0.1, 0)],
)
def test_sine_bounds_reject_invalid_exact_domains(linear: object, amplitude: object) -> None:
    with pytest.raises(ValueError):
        M.sine_perturbed_coupled_base_c3_bounds(
            linear_coefficient=linear, amplitude_upper=amplitude
        )


def test_nonzero_base_fourth_modulus_enters_only_increment_layers() -> None:
    zero = _certificate(normalized_base_map_third_derivative_lipschitz=0)
    curved = _certificate(normalized_base_map_third_derivative_lipschitz=F(1, 1000))
    assert curved.base_third_derivative_upper == zero.base_third_derivative_upper
    assert curved.base_third_derivative_lipschitz_upper == (
        zero.base_third_derivative_lipschitz_upper + F(1, 1000)
    )
    assert curved.modified_third_difference_hessian_coefficient_upper == (
        zero.modified_third_difference_hessian_coefficient_upper
    )
    assert curved.modified_third_difference_value_coefficient_upper > (
        zero.modified_third_difference_value_coefficient_upper
    )


def test_exact_four_level_iteration_uses_previous_state() -> None:
    result = _certificate()
    one = M.nonaffine_coupled_c3_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        initial_third_derivative_distance=5,
        steps=1,
    )
    c2 = result.nonaffine_coupled_c2_certificate
    c1 = c2.nonaffine_coupled_c1_certificate
    assert one.value_distance_upper == (
        2 * c1.coupled_lipschitz_certificate.transform_contraction_factor_upper
    )
    assert one.derivative_distance_upper == (
        3 * c1.derivative_bunching_factor_upper + 2 * c1.derivative_cross_coefficient_upper
    )
    assert one.hessian_distance_upper == (
        4 * c2.second_derivative_bunching_factor_upper
        + 3 * c2.derivative_to_hessian_cross_coefficient_upper
        + 2 * c2.value_to_hessian_cross_coefficient_upper
    )
    assert one.third_derivative_distance_upper == (
        5 * result.third_derivative_bunching_factor_upper
        + 4 * result.hessian_to_third_derivative_cross_coefficient_upper
        + 3 * result.derivative_to_third_derivative_cross_coefficient_upper
        + 2 * result.value_to_third_derivative_cross_coefficient_upper
    )


def test_zero_base_curvature_reduces_exactly_to_affine_coupled_c3() -> None:
    common = dict(
        forcing_at_zero_upper=F(1, 5), base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 10), base_self_lipschitz=F(1, 20),
        fiber_to_base_lipschitz=F(1, 20), base_to_fiber_lipschitz=F(1, 20),
        fiber_self_lipschitz=F(1, 10), graph_slope_upper=F(1, 2),
        normalized_base_jacobian_lipschitz=F(1, 100),
        normalized_fiber_jacobian_lipschitz=F(1, 100),
        graph_derivative_lipschitz_upper=1,
        normalized_base_hessian_lipschitz=F(1, 1000),
        normalized_fiber_hessian_lipschitz=F(1, 1000),
        normalized_base_third_derivative_lipschitz=F(1, 10000),
        normalized_fiber_third_derivative_lipschitz=F(1, 10000),
        normalized_graph_third_derivative_upper=2,
        graph_third_derivative_lipschitz_upper=2,
    )
    nonaffine = _certificate(
        normalized_base_map_hessian_upper=0,
        normalized_base_map_hessian_lipschitz=0,
        normalized_base_map_third_derivative_lipschitz=0,
    )
    affine = AC3.quantitative_coupled_c3_graph_transform(
        base_dimension=3, base_reference_scale=1, fiber_reference_scale=1,
        fiber_radius=1, **common,
    )
    assert nonaffine.validation_level is not None
    assert affine.validation_level is not None
    for field in (
        "base_third_derivative_upper",
        "fiber_third_derivative_upper",
        "modified_third_derivative_upper",
        "output_graph_third_derivative_upper",
        "base_third_derivative_lipschitz_upper",
        "modified_third_derivative_lipschitz_upper",
        "output_graph_third_derivative_lipschitz_upper",
        "third_derivative_bunching_factor_upper",
        "hessian_to_third_derivative_cross_coefficient_upper",
        "derivative_to_third_derivative_cross_coefficient_upper",
        "value_to_third_derivative_cross_coefficient_upper",
    ):
        assert getattr(nonaffine, field) == getattr(affine, field)


def test_zero_graph_coupling_reduces_exactly_to_nonaffine_triangular_c3() -> None:
    mu, hphi, tphi = F(4, 3), F(1, 4), F(1, 4)
    nu = hphi * mu**3
    tau = tphi * mu**4 + 3 * hphi**2 * mu**5
    coupled = _certificate(
        forcing_at_zero_upper=F(1, 8), base_inverse_lipschitz=mu,
        fiber_linear_norm_upper=F(1, 8), base_self_lipschitz=0,
        fiber_to_base_lipschitz=0, base_to_fiber_lipschitz=F(1, 8),
        fiber_self_lipschitz=F(1, 8), graph_slope_upper=1,
        normalized_base_map_hessian_upper=hphi,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=F(1, 16),
        graph_derivative_lipschitz_upper=8,
        normalized_base_map_hessian_lipschitz=tphi,
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=F(1, 16),
        normalized_base_map_third_derivative_lipschitz=F(1, 4),
        normalized_base_third_derivative_lipschitz=0,
        normalized_fiber_third_derivative_lipschitz=F(1, 16),
        normalized_graph_third_derivative_upper=100,
        graph_third_derivative_lipschitz_upper=0,
    )
    triangular = TNC3.quantitative_nonaffine_c3_triangular_graph_transform(
        base_dimension=3, base_reference_scale=1, fiber_reference_scale=1,
        fiber_radius=1, forcing_at_zero_upper=F(1, 8),
        base_inverse_lipschitz=mu, base_inverse_hessian_upper=nu,
        base_inverse_third_derivative_upper=tau,
        fiber_linear_norm_upper=F(1, 8), base_to_fiber_lipschitz=F(1, 8),
        fiber_nonlinear_lipschitz=F(1, 8), graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 16),
        fiber_derivative_fiber_variation=F(1, 16),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_third_derivative_upper=F(1, 16),
        normalized_map_third_derivative_fiber_lipschitz=F(1, 16),
        normalized_graph_hessian_upper=8,
        normalized_graph_third_derivative_upper=100,
    )
    assert coupled.validation_level is not None
    assert triangular.validation_level is not None
    assert coupled.graph_third_derivative_lipschitz_required is False
    assert coupled.output_graph_third_derivative_upper == triangular.output_graph_third_derivative_upper
    assert coupled.third_derivative_bunching_factor_upper == triangular.third_derivative_bunching_factor_upper
    assert coupled.hessian_to_third_derivative_cross_coefficient_upper == triangular.hessian_to_third_derivative_cross_coefficient_upper
    assert coupled.derivative_to_third_derivative_cross_coefficient_upper == triangular.derivative_to_third_derivative_cross_coefficient_upper
    assert coupled.value_to_third_derivative_cross_coefficient_upper == triangular.value_to_third_derivative_cross_coefficient_upper


def test_graph_c31_modulus_failure_is_separate() -> None:
    result = _certificate(graph_third_derivative_lipschitz_upper=0)
    assert result.nonaffine_coupled_c2_certificate.validation_level is not None
    assert result.graph_third_derivative_margin > 0
    assert result.third_derivative_bunching_margin > 0
    assert result.status == "NONAFFINE_COUPLED_C31_GRAPH_CLASS_NOT_INVARIANT"


def test_exact_graph_c31_class_equality_passes_nonrobust() -> None:
    at_zero = _certificate(graph_third_derivative_lipschitz_upper=0)
    at_two = _certificate(graph_third_derivative_lipschitz_upper=2)
    a = at_zero.output_graph_third_derivative_lipschitz_upper
    b = (at_two.output_graph_third_derivative_lipschitz_upper - a) / 2
    assert a is not None and b is not None and b < 1
    fixed = a / (1 - b)
    result = _certificate(graph_third_derivative_lipschitz_upper=fixed)
    assert result.validation_level is not None
    assert result.graph_third_derivative_lipschitz_margin == 0
    assert result.robust_interior is False


def test_exact_c3_class_equality_passes_nonrobust() -> None:
    common = dict(
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_base_hessian_lipschitz=0,
        normalized_base_third_derivative_lipschitz=0,
        graph_third_derivative_lipschitz_upper=0,
    )
    at_zero = _certificate(normalized_graph_third_derivative_upper=0, **common)
    at_two = _certificate(normalized_graph_third_derivative_upper=2, **common)
    a = at_zero.output_graph_third_derivative_upper
    b = (at_two.output_graph_third_derivative_upper - a) / 2
    assert a is not None and b is not None and b < 1
    fixed = a / (1 - b)
    result = _certificate(normalized_graph_third_derivative_upper=fixed, **common)
    assert result.validation_level is not None
    assert result.graph_third_derivative_margin == 0
    assert result.robust_interior is False


def test_graph_independent_preimage_bypasses_c31_gate() -> None:
    result = _certificate(
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_base_hessian_lipschitz=0,
        normalized_base_third_derivative_lipschitz=0,
        graph_third_derivative_lipschitz_upper=0,
    )
    assert result.graph_third_derivative_lipschitz_required is False
    assert result.output_graph_third_derivative_lipschitz_upper > 0
    assert result.graph_third_derivative_lipschitz_margin < 0
    assert result.validation_level is not None


def test_third_bunching_equality_fails_after_c2_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2, fiber_linear_norm_upper=F(1, 8),
        base_self_lipschitz=0, fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=0, fiber_self_lipschitz=0,
        graph_slope_upper=0, normalized_base_map_hessian_upper=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=0,
        normalized_base_map_hessian_lipschitz=0,
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=0,
        normalized_base_map_third_derivative_lipschitz=0,
        normalized_base_third_derivative_lipschitz=0,
        normalized_fiber_third_derivative_lipschitz=0,
        normalized_graph_third_derivative_upper=0,
        graph_third_derivative_lipschitz_upper=0,
    )
    assert result.nonaffine_coupled_c2_certificate.validation_level is not None
    assert result.nonaffine_coupled_c2_certificate.second_derivative_bunching_factor_upper == F(1, 2)
    assert result.third_derivative_bunching_factor_upper == 1
    assert result.status == "NONAFFINE_COUPLED_C3_THIRD_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_equality_witness_is_c2_invariant_and_not_c3() -> None:
    h = lambda x: abs(x) ** 3
    for x in (F(-3, 2), F(-1, 3), F(0), F(2, 5), F(7, 4)):
        assert h(x / 2) == h(x) / 8
    epsilon = F(1, 100)
    d2 = lambda x: 6 * abs(x)
    assert ((d2(-epsilon) - d2(0)) / -epsilon, (d2(epsilon) - d2(0)) / epsilon) == (-6, 6)


def test_predecessor_failure_is_primary_and_iteration_rejects() -> None:
    result = _certificate(forcing_at_zero_upper=1)
    assert result.status == "COUPLED_GRAPH_TUBE_NOT_INVARIANT"
    with pytest.raises(ValueError, match="verified"):
        M.nonaffine_coupled_c3_graph_iteration_bound(
            result, initial_value_distance=1, initial_derivative_distance=1,
            initial_hessian_distance=1, initial_third_derivative_distance=1, steps=1
        )


def test_iteration_rejects_invalid_steps_and_distances() -> None:
    result = _certificate()
    for steps in (-1, True, 1.0):
        with pytest.raises(ValueError, match="steps"):
            M.nonaffine_coupled_c3_graph_iteration_bound(
                result, initial_value_distance=1, initial_derivative_distance=1,
                initial_hessian_distance=1, initial_third_derivative_distance=1,
                steps=steps,
            )
    with pytest.raises(ValueError, match="nonnegative"):
        M.nonaffine_coupled_c3_graph_iteration_bound(
            result, initial_value_distance=-1, initial_derivative_distance=1,
            initial_hessian_distance=1, initial_third_derivative_distance=1, steps=1
        )


def test_base_fiber_rescaling_preserves_normalized_constants() -> None:
    base = _certificate()
    scaled = _certificate(
        base_reference_scale=5, fiber_reference_scale=7, fiber_radius=7,
        forcing_at_zero_upper=F(7, 5), fiber_to_base_lipschitz=F(1, 28),
        base_to_fiber_lipschitz=F(7, 100), graph_slope_upper=F(7, 10),
    )
    for field in (
        "output_graph_third_derivative_upper",
        "output_graph_third_derivative_lipschitz_upper",
        "third_derivative_bunching_factor_upper",
        "hessian_to_third_derivative_cross_coefficient_upper",
        "derivative_to_third_derivative_cross_coefficient_upper",
        "value_to_third_derivative_cross_coefficient_upper",
    ):
        assert getattr(scaled, field) == getattr(base, field)


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.c3_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_base_map_third_derivative_lipschitz", -1),
        ("normalized_base_third_derivative_lipschitz", -1),
        ("normalized_fiber_third_derivative_lipschitz", -1),
        ("normalized_graph_third_derivative_upper", -1),
        ("graph_third_derivative_lipschitz_upper", -1),
        ("normalized_base_map_third_derivative_lipschitz", 0.1),
        ("normalized_base_third_derivative_lipschitz", True),
        ("normalized_graph_third_derivative_upper", "02"),
    ],
)
def test_invalid_c3_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})
