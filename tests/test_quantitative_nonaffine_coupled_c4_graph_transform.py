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
_load("quantitative_coupled_c1_graph_transform", "quantitative_coupled_c1_graph_transform.py")
_load("quantitative_coupled_c2_graph_transform", "quantitative_coupled_c2_graph_transform.py")
_load("quantitative_coupled_c3_graph_transform", "quantitative_coupled_c3_graph_transform.py")
AC4 = _load("quantitative_coupled_c4_graph_transform", "quantitative_coupled_c4_graph_transform.py")
_load("quantitative_nonaffine_coupled_c1_graph_transform", "quantitative_nonaffine_coupled_c1_graph_transform.py")
_load("quantitative_nonaffine_coupled_c2_graph_transform", "quantitative_nonaffine_coupled_c2_graph_transform.py")
_load("quantitative_nonaffine_coupled_c3_graph_transform", "quantitative_nonaffine_coupled_c3_graph_transform.py")
_load("quantitative_graph_transform", "quantitative_graph_transform.py")
_load("quantitative_c1_graph_transform", "quantitative_c1_graph_transform.py")
_load("quantitative_nonaffine_c2_graph_transform", "quantitative_nonaffine_c2_graph_transform.py")
_load("quantitative_nonaffine_c3_graph_transform", "quantitative_nonaffine_c3_graph_transform.py")
TNC4 = _load("quantitative_nonaffine_c4_graph_transform", "quantitative_nonaffine_c4_graph_transform.py")
M = _load("ce_quantitative_nonaffine_coupled_c4", "quantitative_nonaffine_coupled_c4_graph_transform.py")


def _values() -> dict[str, object]:
    return dict(
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
        normalized_base_map_fourth_derivative_lipschitz=F(1, 1000),
        normalized_base_fourth_derivative_lipschitz=F(1, 100000),
        normalized_fiber_fourth_derivative_lipschitz=F(1, 100000),
        normalized_graph_fourth_derivative_upper=20,
        graph_fourth_derivative_lipschitz_upper=100,
    )


def _certificate(**overrides):
    values = _values()
    values.update(overrides)
    return M.quantitative_nonaffine_coupled_c4_graph_transform(**values)


def test_strict_nonaffine_coupled_c4_certificate_exposes_all_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_NONAFFINE_COUPLED_C4_GRAPH_TRANSFORM"
    assert result.nonaffine_coupled_c3_certificate.validation_level is not None
    assert result.graph_fourth_derivative_lipschitz_required is True
    assert result.output_graph_fourth_derivative_upper == F(77166708988912, 11866484641625)
    assert result.graph_fourth_derivative_margin == F(160162983843588, 11866484641625)
    assert result.output_graph_fourth_derivative_lipschitz_upper == F(3149203994659911392, 81226087371923125)
    assert result.graph_fourth_derivative_lipschitz_margin == F(4973404742532401108, 81226087371923125)
    assert result.fourth_derivative_bunching_factor_upper == F(19712000, 69343957)
    assert result.fourth_derivative_bunching_margin > 0
    assert result.modified_fourth_difference_value_coefficient_upper > 0
    assert result.c4_graph_real_dimension == 3
    assert result.robust_interior is True


def test_forward_sine_c4_bounds_are_exact_and_fail_closed() -> None:
    result = M.sine_perturbed_coupled_base_c4_bounds(
        linear_coefficient=F(1001, 1000), amplitude_upper=F(1, 1000)
    )
    assert tuple(result.__dict__.values()) == (1, F(1, 1000), F(1, 1000), F(1, 1000), F(1, 1000))
    with pytest.raises(ValueError):
        M.sine_perturbed_coupled_base_c4_bounds(linear_coefficient=1, amplitude_upper=1)


def test_base_d5_modulus_enters_only_point_and_value_increment_layers() -> None:
    curved = _certificate()
    zero = _certificate(normalized_base_map_fourth_derivative_lipschitz=0)
    assert curved.output_graph_fourth_derivative_upper == zero.output_graph_fourth_derivative_upper
    assert curved.fourth_derivative_bunching_factor_upper == zero.fourth_derivative_bunching_factor_upper
    assert curved.third_to_fourth_derivative_cross_coefficient_upper == zero.third_to_fourth_derivative_cross_coefficient_upper
    assert curved.hessian_to_fourth_derivative_cross_coefficient_upper == zero.hessian_to_fourth_derivative_cross_coefficient_upper
    assert curved.derivative_to_fourth_derivative_cross_coefficient_upper == zero.derivative_to_fourth_derivative_cross_coefficient_upper
    assert curved.base_fourth_derivative_lipschitz_upper > zero.base_fourth_derivative_lipschitz_upper
    assert curved.output_graph_fourth_derivative_lipschitz_upper > zero.output_graph_fourth_derivative_lipschitz_upper
    assert curved.value_to_fourth_derivative_cross_coefficient_upper > zero.value_to_fourth_derivative_cross_coefficient_upper


def test_zero_forward_base_curvature_reduces_exactly_to_affine_coupled_c4() -> None:
    overrides = dict(
        normalized_base_map_hessian_upper=0,
        normalized_base_map_hessian_lipschitz=0,
        normalized_base_map_third_derivative_lipschitz=0,
        normalized_base_map_fourth_derivative_lipschitz=0,
    )
    nonaffine = _certificate(**overrides)
    values = _values()
    for field in (
        "normalized_base_map_hessian_upper",
        "normalized_base_map_hessian_lipschitz",
        "normalized_base_map_third_derivative_lipschitz",
        "normalized_base_map_fourth_derivative_lipschitz",
    ):
        values.pop(field)
    affine = AC4.quantitative_coupled_c4_graph_transform(**values)
    assert nonaffine.validation_level is not None and affine.validation_level is not None
    names = (
        "base_fourth_derivative_upper", "fiber_fourth_derivative_upper",
        "modified_fourth_derivative_upper", "output_graph_fourth_derivative_upper",
        "base_fourth_derivative_lipschitz_upper",
        "modified_fourth_derivative_lipschitz_upper",
        "output_graph_fourth_derivative_lipschitz_upper",
        "fourth_derivative_bunching_factor_upper",
        "third_to_fourth_derivative_cross_coefficient_upper",
        "hessian_to_fourth_derivative_cross_coefficient_upper",
        "derivative_to_fourth_derivative_cross_coefficient_upper",
        "value_to_fourth_derivative_cross_coefficient_upper",
    )
    assert tuple(getattr(nonaffine, name) for name in names) == tuple(getattr(affine, name) for name in names)


def test_zero_coupling_reduces_to_common_inverse_nonaffine_triangular_c4() -> None:
    mu = F(10, 9)
    hphi, tphi, uphi = F(1, 100), F(1, 200), F(1, 400)
    nu = hphi * mu**3
    tau = tphi * mu**4 + 3 * hphi**2 * mu**5
    upsilon = uphi * mu**5 + 10 * hphi * tphi * mu**6 + 15 * hphi**3 * mu**7
    coupled = _certificate(
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=mu,
        fiber_linear_norm_upper=F(1, 4),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=F(1, 4),
        fiber_self_lipschitz=F(1, 4),
        graph_slope_upper=1,
        normalized_base_map_hessian_upper=hphi,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=F(1, 16),
        graph_derivative_lipschitz_upper=1,
        normalized_base_map_hessian_lipschitz=tphi,
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=F(1, 16),
        normalized_base_map_third_derivative_lipschitz=uphi,
        normalized_base_third_derivative_lipschitz=0,
        normalized_fiber_third_derivative_lipschitz=F(1, 64),
        normalized_graph_third_derivative_upper=8,
        graph_third_derivative_lipschitz_upper=0,
        normalized_base_map_fourth_derivative_lipschitz=F(1, 800),
        normalized_base_fourth_derivative_lipschitz=0,
        normalized_fiber_fourth_derivative_lipschitz=F(1, 256),
        normalized_graph_fourth_derivative_upper=100,
        graph_fourth_derivative_lipschitz_upper=0,
    )
    triangular = TNC4.quantitative_nonaffine_c4_triangular_graph_transform(
        base_dimension=3, base_reference_scale=1, fiber_reference_scale=1,
        fiber_radius=1, forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=mu, base_inverse_hessian_upper=nu,
        base_inverse_third_derivative_upper=tau,
        base_inverse_fourth_derivative_upper=upsilon,
        fiber_linear_norm_upper=F(1, 4), base_to_fiber_lipschitz=F(1, 4),
        fiber_nonlinear_lipschitz=F(1, 4), graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 16),
        fiber_derivative_fiber_variation=F(1, 16),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_third_derivative_upper=F(1, 16),
        normalized_map_fourth_derivative_upper=F(1, 64),
        normalized_map_fourth_derivative_fiber_lipschitz=F(1, 256),
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=8,
        normalized_graph_fourth_derivative_upper=100,
    )
    assert coupled.validation_level is not None and triangular.validation_level is not None
    names = (
        "output_graph_fourth_derivative_upper",
        "fourth_derivative_bunching_factor_upper",
        "third_to_fourth_derivative_cross_coefficient_upper",
        "hessian_to_fourth_derivative_cross_coefficient_upper",
        "derivative_to_fourth_derivative_cross_coefficient_upper",
        "value_to_fourth_derivative_cross_coefficient_upper",
    )
    assert tuple(getattr(coupled, name) for name in names) == tuple(getattr(triangular, name) for name in names)


def test_exact_five_level_iteration_uses_previous_state() -> None:
    result = _certificate()
    one = M.nonaffine_coupled_c4_graph_iteration_bound(
        result, initial_value_distance=2, initial_derivative_distance=3,
        initial_hessian_distance=4, initial_third_derivative_distance=5,
        initial_fourth_derivative_distance=6, steps=1,
    )
    assert one.fourth_derivative_distance_upper == (
        6 * result.fourth_derivative_bunching_factor_upper
        + 5 * result.third_to_fourth_derivative_cross_coefficient_upper
        + 4 * result.hessian_to_fourth_derivative_cross_coefficient_upper
        + 3 * result.derivative_to_fourth_derivative_cross_coefficient_upper
        + 2 * result.value_to_fourth_derivative_cross_coefficient_upper
    )


def test_bunching_equality_is_a_named_failure_after_c3_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2, fiber_linear_norm_upper=F(1, 16),
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
        normalized_base_map_fourth_derivative_lipschitz=0,
        normalized_base_fourth_derivative_lipschitz=0,
        normalized_fiber_fourth_derivative_lipschitz=0,
        normalized_graph_fourth_derivative_upper=0,
        graph_fourth_derivative_lipschitz_upper=0,
    )
    assert result.nonaffine_coupled_c3_certificate.validation_level is not None
    assert result.fourth_derivative_bunching_factor_upper == 1
    assert result.status == "NONAFFINE_COUPLED_C4_FOURTH_DERIVATIVE_BUNCHING_NOT_STRICT"


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
        ("normalized_base_map_fourth_derivative_lipschitz", -1),
        ("normalized_base_fourth_derivative_lipschitz", -1),
        ("normalized_fiber_fourth_derivative_lipschitz", True),
        ("normalized_graph_fourth_derivative_upper", 0.1),
        ("graph_fourth_derivative_lipschitz_upper", "0100"),
    ],
)
def test_invalid_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_predecessor_failure_remains_primary_and_iteration_rejects() -> None:
    result = _certificate(normalized_graph_third_derivative_upper=0)
    assert result.status == "NONAFFINE_COUPLED_C21_GRAPH_CLASS_NOT_INVARIANT"
    with pytest.raises(ValueError, match="verified"):
        M.nonaffine_coupled_c4_graph_iteration_bound(
            result, initial_value_distance=1, initial_derivative_distance=1,
            initial_hessian_distance=1, initial_third_derivative_distance=1,
            initial_fourth_derivative_distance=1, steps=1,
        )
