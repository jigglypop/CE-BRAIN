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
TC4 = _load("quantitative_c4_graph_transform", "quantitative_c4_graph_transform.py")
_load("quantitative_nonaffine_c2_graph_transform", "quantitative_nonaffine_c2_graph_transform.py")
_load("quantitative_nonaffine_c3_graph_transform", "quantitative_nonaffine_c3_graph_transform.py")
M = _load("ce_quantitative_nonaffine_c4", "quantitative_nonaffine_c4_graph_transform.py")


def _values() -> dict[str, object]:
    bounds = M.sine_perturbed_base_c4_bounds(F(1, 10))
    return dict(
        base_dimension=5,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=bounds.inverse_derivative_upper,
        base_inverse_hessian_upper=bounds.inverse_hessian_upper,
        base_inverse_third_derivative_upper=bounds.inverse_third_derivative_upper,
        base_inverse_fourth_derivative_upper=bounds.inverse_fourth_derivative_upper,
        fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 8),
        fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 16),
        fiber_derivative_fiber_variation=F(1, 16),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_third_derivative_upper=F(1, 16),
        normalized_map_fourth_derivative_upper=F(1, 64),
        normalized_map_fourth_derivative_fiber_lipschitz=F(1, 256),
        normalized_graph_hessian_upper=2,
        normalized_graph_third_derivative_upper=8,
        normalized_graph_fourth_derivative_upper=100,
    )


def _certificate(**overrides):
    values = _values()
    values.update(overrides)
    return M.quantitative_nonaffine_c4_triangular_graph_transform(**values)


def test_strict_certificate_exposes_all_nonaffine_fourth_chain_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_NONAFFINE_C4_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.nonaffine_c3_certificate.validation_level is not None
    assert result.output_graph_fourth_derivative_upper == F(152045000, 1594323)
    assert result.graph_fourth_derivative_margin == F(7387300, 1594323)
    assert result.fourth_derivative_bunching_factor_upper == F(5000, 6561)
    assert result.fourth_derivative_bunching_margin == F(1561, 6561)
    assert result.third_to_fourth_derivative_cross_coefficient_upper == F(25000, 19683)
    assert result.hessian_to_fourth_derivative_cross_coefficient_upper == F(2320000, 531441)
    assert result.derivative_to_fourth_derivative_cross_coefficient_upper == F(15940000, 1594323)
    assert result.value_to_fourth_derivative_cross_coefficient_upper == F(31673125, 1594323)
    assert result.c4_graph_real_dimension == 5
    assert result.robust_interior is True


def test_fourth_composition_formula_is_reconstructed_term_by_term() -> None:
    result = _certificate()
    c3 = result.nonaffine_c3_certificate
    c2 = c3.nonaffine_c2_certificate
    lip = c2.c1_certificate.lipschitz_certificate
    q, mu = lip.contraction_factor_upper, lip.base_inverse_lipschitz
    nu, tau = c2.base_inverse_hessian_upper, c3.base_inverse_third_derivative_upper
    upsilon = result.base_inverse_fourth_derivative_upper
    r = 1 + lip.normalized_graph_slope_upper
    k2, k3 = c2.normalized_map_hessian_upper, c3.normalized_map_third_derivative_upper
    k4 = result.normalized_map_fourth_derivative_upper
    l2, l3, l4 = c2.normalized_graph_hessian_upper, c3.normalized_graph_third_derivative_upper, result.normalized_graph_fourth_derivative_upper
    a2 = q * l2 + k2 * r**2
    a3 = q * l3 + 3 * k2 * l2 * r + k3 * r**3
    a4 = q * l4 + 4 * k2 * l3 * r + 3 * k2 * l2**2 + 6 * k3 * l2 * r**2 + k4 * r**4
    s = q * lip.normalized_graph_slope_upper + lip.normalized_base_to_fiber_lipschitz
    assert result.output_graph_fourth_derivative_upper == mu**4 * a4 + 6 * mu**2 * nu * a3 + (3 * nu**2 + 4 * mu * tau) * a2 + upsilon * s


def test_sine_inverse_c4_bound_matches_scalar_inverse_formula() -> None:
    zero = M.sine_perturbed_base_c4_bounds(0)
    tenth = M.sine_perturbed_base_c4_bounds(F(1, 10))
    assert tuple(zero.__dict__.values()) == (1, 0, 0, 0)
    assert tenth.inverse_fourth_derivative_upper == F(620000, 1594323)
    a, gap = F(1, 10), F(9, 10)
    assert tenth.inverse_fourth_derivative_upper == a / gap**5 + 10 * a**2 / gap**6 + 15 * a**3 / gap**7


def test_exact_five_level_iteration_uses_previous_state() -> None:
    result = _certificate()
    one = M.nonaffine_c4_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        initial_third_derivative_distance=5,
        initial_fourth_derivative_distance=6,
        steps=1,
    )
    assert one.value_distance_upper == 1
    assert one.fourth_derivative_distance_upper == (
        6 * result.fourth_derivative_bunching_factor_upper
        + 5 * result.third_to_fourth_derivative_cross_coefficient_upper
        + 4 * result.hessian_to_fourth_derivative_cross_coefficient_upper
        + 3 * result.derivative_to_fourth_derivative_cross_coefficient_upper
        + 2 * result.value_to_fourth_derivative_cross_coefficient_upper
    )


def test_zero_inverse_curvature_reduces_exactly_to_affine_c4() -> None:
    nonaffine = _certificate(
        base_inverse_lipschitz=1,
        base_inverse_hessian_upper=0,
        base_inverse_third_derivative_upper=0,
        base_inverse_fourth_derivative_upper=0,
        base_to_fiber_lipschitz=F(1, 4),
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=2,
        normalized_graph_fourth_derivative_upper=6,
    )
    affine_values = _values()
    for field in (
        "base_inverse_hessian_upper",
        "base_inverse_third_derivative_upper",
        "base_inverse_fourth_derivative_upper",
    ):
        affine_values.pop(field)
    affine_values.update(
        base_inverse_lipschitz=1,
        base_to_fiber_lipschitz=F(1, 4),
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=2,
        normalized_graph_fourth_derivative_upper=6,
    )
    affine = TC4.quantitative_c4_triangular_graph_transform(**affine_values)
    assert nonaffine.validation_level is not None and affine.validation_level is not None
    names = (
        "output_graph_fourth_derivative_upper",
        "fourth_derivative_bunching_factor_upper",
        "third_to_fourth_derivative_cross_coefficient_upper",
        "hessian_to_fourth_derivative_cross_coefficient_upper",
        "derivative_to_fourth_derivative_cross_coefficient_upper",
        "value_to_fourth_derivative_cross_coefficient_upper",
    )
    assert tuple(getattr(nonaffine, name) for name in names) == tuple(getattr(affine, name) for name in names)


def test_each_inverse_curvature_order_has_a_visible_effect() -> None:
    curved = _certificate()
    no_u = _certificate(base_inverse_fourth_derivative_upper=0)
    no_tu = _certificate(base_inverse_third_derivative_upper=0, base_inverse_fourth_derivative_upper=0)
    affine_inverse = _certificate(base_inverse_hessian_upper=0, base_inverse_third_derivative_upper=0, base_inverse_fourth_derivative_upper=0)
    assert curved.output_graph_fourth_derivative_upper > no_u.output_graph_fourth_derivative_upper
    assert no_u.output_graph_fourth_derivative_upper > no_tu.output_graph_fourth_derivative_upper
    assert no_tu.output_graph_fourth_derivative_upper > affine_inverse.output_graph_fourth_derivative_upper


def test_bunching_equality_is_a_named_failure_after_c3_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        base_inverse_hessian_upper=0,
        base_inverse_third_derivative_upper=0,
        base_inverse_fourth_derivative_upper=0,
        fiber_linear_norm_upper=F(1, 16),
        fiber_nonlinear_lipschitz=0,
        base_to_fiber_lipschitz=0,
        graph_slope_upper=0,
        base_derivative_fiber_variation=0,
        fiber_derivative_fiber_variation=0,
        normalized_map_hessian_upper=0,
        normalized_map_third_derivative_upper=0,
        normalized_map_fourth_derivative_upper=0,
        normalized_map_fourth_derivative_fiber_lipschitz=0,
        normalized_graph_hessian_upper=0,
        normalized_graph_third_derivative_upper=0,
        normalized_graph_fourth_derivative_upper=0,
    )
    assert result.nonaffine_c3_certificate.validation_level is not None
    assert result.fourth_derivative_bunching_factor_upper == 1
    assert result.status == "NONAFFINE_C4_FOURTH_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_equality_witness_is_c3_and_not_c4() -> None:
    def h(x: F) -> F:
        return x * abs(x) ** 3
    for x in (F(-3, 2), F(-1, 3), F(0), F(2, 5)):
        assert h(x / 2) == h(x) / 16
    assert -24 != 24


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.c4_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_inverse_fourth_derivative_upper", -1),
        ("normalized_map_fourth_derivative_upper", -1),
        ("normalized_map_fourth_derivative_fiber_lipschitz", True),
        ("normalized_graph_fourth_derivative_upper", 0.1),
    ],
)
def test_invalid_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_predecessor_failure_remains_primary_and_iteration_rejects() -> None:
    result = _certificate(normalized_graph_third_derivative_upper=0)
    assert result.status == "NONAFFINE_C3_GRAPH_THIRD_DERIVATIVE_CLASS_NOT_INVARIANT"
    with pytest.raises(ValueError, match="verified"):
        M.nonaffine_c4_graph_iteration_bound(
            result,
            initial_value_distance=1,
            initial_derivative_distance=1,
            initial_hessian_distance=1,
            initial_third_derivative_distance=1,
            initial_fourth_derivative_distance=1,
            steps=1,
        )
