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
AC4 = _load("quantitative_c4_graph_transform", "quantitative_c4_graph_transform.py")
A = _load("quantitative_arbitrary_order_graph_transform", "quantitative_arbitrary_order_graph_transform.py")
_load("quantitative_nonaffine_c2_graph_transform", "quantitative_nonaffine_c2_graph_transform.py")
_load("quantitative_nonaffine_c3_graph_transform", "quantitative_nonaffine_c3_graph_transform.py")
NC4 = _load("quantitative_nonaffine_c4_graph_transform", "quantitative_nonaffine_c4_graph_transform.py")
M = _load("ce_quantitative_nonaffine_arbitrary_order", "quantitative_nonaffine_arbitrary_order_graph_transform.py")


FORWARD = (F(1, 100), F(1, 200), F(1, 400), F(1, 800), F(1, 1600))


def _c4(dimension: int = 3, *, mu: F = F(10, 9), forward=FORWARD, **overrides):
    inverse = M.inverse_derivative_bounds_from_forward_map(
        inverse_lipschitz_upper=mu,
        normalized_base_map_derivative_bounds=forward[:3],
    )
    values = dict(
        base_dimension=dimension, base_reference_scale=1, fiber_reference_scale=1,
        fiber_radius=1, forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=mu, base_inverse_hessian_upper=inverse[1],
        base_inverse_third_derivative_upper=inverse[2],
        base_inverse_fourth_derivative_upper=inverse[3],
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
    values.update(overrides)
    return NC4.quantitative_nonaffine_c4_triangular_graph_transform(**values)


def _hierarchy(**overrides):
    values = dict(
        nonaffine_c4_certificate=_c4(),
        normalized_base_map_derivative_bounds=FORWARD,
        normalized_graph_derivative_bounds=(1, 1, 8, 100, 3000, 200000),
        normalized_map_derivative_bounds=(F(1, 16), F(1, 16), F(1, 64), F(1, 256), F(1, 1024), F(1, 4096)),
    )
    values.update(overrides)
    return M.quantitative_nonaffine_triangular_arbitrary_order_graph_transform(**values)


def test_inverse_bell_recurrence_reproduces_d2_d3_d4_formulas() -> None:
    mu, h, t, u = F(10, 9), FORWARD[0], FORWARD[1], FORWARD[2]
    inverse = M.inverse_derivative_bounds_from_forward_map(
        inverse_lipschitz_upper=mu, normalized_base_map_derivative_bounds=FORWARD
    )
    assert inverse[1] == h * mu**3 == F(10, 729)
    assert inverse[2] == t * mu**4 + 3 * h**2 * mu**5 == F(160, 19683)
    assert inverse[3] == u * mu**5 + 10 * h * t * mu**6 + 15 * h**3 * mu**7 == F(8300, 1594323)
    assert inverse[4] == F(488600, 129140163)
    assert inverse[5] == F(3797600, 1162261467)


def test_nonaffine_c4_level_exactly_matches_predecessor() -> None:
    result = _hierarchy()
    level = result.levels[0]
    c4 = result.nonaffine_c4_certificate
    assert level.output_graph_derivative_upper == c4.output_graph_fourth_derivative_upper == F(45589325, 531441)
    assert level.coefficient_by_input_order_upper == (
        c4.value_to_fourth_derivative_cross_coefficient_upper,
        c4.derivative_to_fourth_derivative_cross_coefficient_upper,
        c4.hessian_to_fourth_derivative_cross_coefficient_upper,
        c4.third_to_fourth_derivative_cross_coefficient_upper,
        c4.fourth_derivative_bunching_factor_upper,
    )


def test_strict_nonaffine_c6_hierarchy_has_exact_layers() -> None:
    result = _hierarchy()
    assert result.status == "VERIFIED_QUANTITATIVE_NONAFFINE_TRIANGULAR_C6_GRAPH_TRANSFORM"
    c5, c6 = result.levels[1:]
    assert c5.inverse_derivative_upper == F(488600, 129140163)
    assert c5.output_graph_derivative_upper == F(116441578775, 43046721)
    assert c5.graph_derivative_margin == F(12698584225, 43046721)
    assert c6.inverse_derivative_upper == F(3797600, 1162261467)
    assert c6.output_graph_derivative_upper == F(75171452147900, 387420489)
    assert c6.graph_derivative_margin == F(2312645652100, 387420489)
    assert c5.derivative_bunching_factor_upper == F(50000, 59049)
    assert c6.derivative_bunching_factor_upper == F(500000, 531441)
    assert result.robust_interior is True


def test_high_forward_base_derivative_changes_inverse_and_output_at_same_level() -> None:
    base = _hierarchy()
    forward = list(FORWARD)
    forward[-1] = 0
    changed = _hierarchy(normalized_base_map_derivative_bounds=tuple(forward))
    assert base.levels[-1].inverse_derivative_upper > changed.levels[-1].inverse_derivative_upper
    assert base.levels[-1].output_graph_derivative_upper > changed.levels[-1].output_graph_derivative_upper
    assert base.levels[-2].output_graph_derivative_upper == changed.levels[-2].output_graph_derivative_upper


def test_k_n_plus_one_changes_only_value_coefficient() -> None:
    base = _hierarchy()
    maps = list(base.normalized_map_derivative_bounds)
    maps[-1] = 0
    changed = _hierarchy(normalized_map_derivative_bounds=tuple(maps))
    assert base.levels[-1].output_graph_derivative_upper == changed.levels[-1].output_graph_derivative_upper
    assert base.levels[-1].coefficient_by_input_order_upper[1:] == changed.levels[-1].coefficient_by_input_order_upper[1:]
    assert base.levels[-1].coefficient_by_input_order_upper[0] > changed.levels[-1].coefficient_by_input_order_upper[0]


def test_zero_forward_curvature_reduces_every_level_to_affine_hierarchy() -> None:
    zero_forward = (F(0),) * 5
    graph = (F(1), F(1), F(2), F(6), F(40), F(400))
    maps = (F(1, 16), F(1, 16), F(1, 64), F(1, 256), F(1, 1024), F(1, 4096))
    nonaffine_c4 = _c4(
        mu=F(1), forward=zero_forward,
        normalized_graph_third_derivative_upper=2,
        normalized_graph_fourth_derivative_upper=6,
    )
    nonaffine = M.quantitative_nonaffine_triangular_arbitrary_order_graph_transform(
        nonaffine_c4_certificate=nonaffine_c4,
        normalized_base_map_derivative_bounds=zero_forward,
        normalized_graph_derivative_bounds=graph,
        normalized_map_derivative_bounds=maps,
    )
    affine_c4 = AC4.quantitative_c4_triangular_graph_transform(
        base_dimension=3, base_reference_scale=1, fiber_reference_scale=1,
        fiber_radius=1, forcing_at_zero_upper=F(1, 4), base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 4), base_to_fiber_lipschitz=F(1, 4),
        fiber_nonlinear_lipschitz=F(1, 4), graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 16),
        fiber_derivative_fiber_variation=F(1, 16),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_third_derivative_upper=F(1, 16),
        normalized_map_fourth_derivative_upper=F(1, 64),
        normalized_map_fourth_derivative_fiber_lipschitz=F(1, 256),
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=2,
        normalized_graph_fourth_derivative_upper=6,
    )
    affine = A.quantitative_affine_triangular_arbitrary_order_graph_transform(
        c4_certificate=affine_c4,
        normalized_graph_derivative_bounds=graph,
        normalized_map_derivative_bounds=maps,
    )
    assert nonaffine.validation_level is not None and affine.validation_level is not None
    for nonaffine_level, affine_level in zip(nonaffine.levels, affine.levels):
        assert nonaffine_level.output_graph_derivative_upper == affine_level.output_graph_derivative_upper
        assert nonaffine_level.coefficient_by_input_order_upper == affine_level.coefficient_by_input_order_upper


def test_exact_seven_level_iteration_is_synchronous() -> None:
    result = _hierarchy()
    initial = tuple(F(index + 1) for index in range(7))
    one = M.nonaffine_arbitrary_order_graph_iteration_bound(
        result, initial_distance_by_derivative_order=initial, steps=1
    )
    for level in result.levels:
        assert one.distance_by_derivative_order_upper[level.order] == sum(
            coefficient * initial[index]
            for index, coefficient in enumerate(level.coefficient_by_input_order_upper)
        )


def test_forward_bounds_must_reproduce_predecessor_inverse_bounds() -> None:
    bad = list(FORWARD)
    bad[0] = F(1, 99)
    with pytest.raises(ValueError, match="reproduce"):
        _hierarchy(normalized_base_map_derivative_bounds=tuple(bad))


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _hierarchy(nonaffine_c4_certificate=_c4(dimension))
    assert result.cn_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "mu,forward",
    [
        (0, (1,)),
        (-1, (1,)),
        (1.0, (1,)),
        (1, (-1,)),
        (1, (True,)),
    ],
)
def test_invalid_inverse_recurrence_inputs_fail_closed(mu: object, forward: object) -> None:
    with pytest.raises(ValueError):
        M.inverse_derivative_bounds_from_forward_map(
            inverse_lipschitz_upper=mu,
            normalized_base_map_derivative_bounds=forward,
        )


def test_wrong_forward_length_is_rejected() -> None:
    with pytest.raises(ValueError, match="D2phi"):
        _hierarchy(normalized_base_map_derivative_bounds=FORWARD[:-1])
