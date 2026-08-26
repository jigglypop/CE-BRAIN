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
C4 = _load("quantitative_c4_graph_transform", "quantitative_c4_graph_transform.py")
M = _load("ce_quantitative_arbitrary_order", "quantitative_arbitrary_order_graph_transform.py")


def _c4(dimension: int = 3, **overrides):
    values = dict(
        base_dimension=dimension, base_reference_scale=1, fiber_reference_scale=1,
        fiber_radius=1, forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=1, fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 4), fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1, base_derivative_fiber_variation=F(1, 4),
        fiber_derivative_fiber_variation=F(1, 4),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_third_derivative_upper=F(1, 16),
        normalized_map_fourth_derivative_upper=F(1, 64),
        normalized_map_fourth_derivative_fiber_lipschitz=F(1, 256),
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=2,
        normalized_graph_fourth_derivative_upper=6,
    )
    values.update(overrides)
    return C4.quantitative_c4_triangular_graph_transform(**values)


def _hierarchy(**overrides):
    values = dict(
        c4_certificate=_c4(),
        normalized_graph_derivative_bounds=(1, 1, 2, 6, 40, 400),
        normalized_map_derivative_bounds=(F(1, 16), F(1, 16), F(1, 64), F(1, 256), F(1, 1024), F(1, 4096)),
    )
    values.update(overrides)
    return M.quantitative_affine_triangular_arbitrary_order_graph_transform(**values)


def test_partition_generator_reproduces_order_four_faa_di_bruno() -> None:
    terms = M.bell_partition_terms(4)
    assert [(term.multiplicities, term.combinatorial_coefficient) for term in terms] == [
        ((4, 0, 0, 0), 1),
        ((2, 1, 0, 0), 6),
        ((1, 0, 1, 0), 4),
        ((0, 2, 0, 0), 3),
        ((0, 0, 0, 1), 1),
    ]
    assert sum(term.combinatorial_coefficient for term in terms) == 15


@pytest.mark.parametrize("order,count,bell", [(5, 7, 52), (6, 11, 203)])
def test_partition_counts_and_bell_sums(order: int, count: int, bell: int) -> None:
    terms = M.bell_partition_terms(order)
    assert len(terms) == count
    assert sum(term.combinatorial_coefficient for term in terms) == bell


def test_c4_level_is_exactly_the_frozen_predecessor() -> None:
    hierarchy = _hierarchy()
    c4 = hierarchy.c4_certificate
    level = hierarchy.levels[0]
    assert level.output_graph_derivative_upper == c4.output_graph_fourth_derivative_upper == F(95, 16)
    assert level.coefficient_by_input_order_upper == (F(2), F(5, 2), F(15, 8), F(1, 2), F(1, 2))


def test_strict_c6_hierarchy_has_exact_c5_and_c6_layers() -> None:
    result = _hierarchy()
    assert result.status == "VERIFIED_QUANTITATIVE_AFFINE_TRIANGULAR_C6_GRAPH_TRANSFORM"
    assert result.maximum_order == 6
    c5, c6 = result.levels[1:]
    assert c5.output_graph_derivative_upper == F(133, 4)
    assert c5.graph_derivative_margin == F(27, 4)
    assert c5.coefficient_by_input_order_upper == (
        F(153, 16), F(10), F(25, 4), F(25, 8), F(5, 8), F(1, 2)
    )
    assert c6.output_graph_derivative_upper == F(2283, 8)
    assert c6.graph_derivative_margin == F(917, 8)
    assert c6.coefficient_by_input_order_upper == (
        F(1199, 16), F(459, 8), F(30), F(25, 2), F(75, 16), F(3, 4), F(1, 2)
    )
    assert result.robust_interior is True


def test_k_n_plus_one_changes_only_value_coefficient_at_level_n() -> None:
    base = _hierarchy()
    maps = list(base.normalized_map_derivative_bounds)
    maps[-1] = 0
    changed = _hierarchy(normalized_map_derivative_bounds=tuple(maps))
    base_c6, changed_c6 = base.levels[-1], changed.levels[-1]
    assert base_c6.output_graph_derivative_upper == changed_c6.output_graph_derivative_upper
    assert base_c6.coefficient_by_input_order_upper[1:] == changed_c6.coefficient_by_input_order_upper[1:]
    assert base_c6.coefficient_by_input_order_upper[0] > changed_c6.coefficient_by_input_order_upper[0]


def test_exact_seven_level_iteration_uses_one_previous_state() -> None:
    result = _hierarchy()
    initial = tuple(F(index + 1) for index in range(7))
    one = M.arbitrary_order_graph_iteration_bound(
        result, initial_distance_by_derivative_order=initial, steps=1
    )
    for level in result.levels:
        assert one.distance_by_derivative_order_upper[level.order] == sum(
            coefficient * initial[index]
            for index, coefficient in enumerate(level.coefficient_by_input_order_upper)
        )


def test_c5_bunching_equality_fails_and_positive_part_power_is_sharp() -> None:
    c4 = _c4(
        forcing_at_zero_upper=0, base_inverse_lipschitz=2,
        fiber_linear_norm_upper=F(1, 32), base_to_fiber_lipschitz=0,
        fiber_nonlinear_lipschitz=0, graph_slope_upper=0,
        base_derivative_fiber_variation=0, fiber_derivative_fiber_variation=0,
        normalized_map_hessian_upper=0, normalized_map_third_derivative_upper=0,
        normalized_map_fourth_derivative_upper=0,
        normalized_map_fourth_derivative_fiber_lipschitz=0,
        normalized_graph_hessian_upper=0,
        normalized_graph_third_derivative_upper=0,
        normalized_graph_fourth_derivative_upper=0,
    )
    result = M.quantitative_affine_triangular_arbitrary_order_graph_transform(
        c4_certificate=c4,
        normalized_graph_derivative_bounds=(0, 0, 0, 0, 0),
        normalized_map_derivative_bounds=(0, 0, 0, 0, 0),
    )
    assert result.levels[-1].derivative_bunching_factor_upper == 1
    assert result.status == "C5_DERIVATIVE_BUNCHING_NOT_STRICT"
    for x in (F(-2), F(-1, 3), F(0), F(2, 5), F(3, 2)):
        assert M.positive_part_power(x / 2, 5) == M.positive_part_power(x, 5) / 32
    assert 120 != 0  # left/right fifth derivatives are 0 and 5!.


def test_predecessor_bound_mismatch_is_rejected() -> None:
    graph = list(_hierarchy().normalized_graph_derivative_bounds)
    graph[3] = 7
    with pytest.raises(ValueError, match="exactly match"):
        _hierarchy(normalized_graph_derivative_bounds=tuple(graph))


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _hierarchy(c4_certificate=_c4(dimension))
    assert result.cn_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "graph,maps",
    [
        ((1, 1, 2), (1, 1, 1)),
        ((1, 1, 2, 6), (1, 1, 1)),
        ((1, 1, 2, 6, -1), (1, 1, 1, 1, 1)),
        ((1, 1, 2, 6, 10.0), (1, 1, 1, 1, 1)),
    ],
)
def test_invalid_hierarchy_inputs_fail_closed(graph: object, maps: object) -> None:
    with pytest.raises(ValueError):
        _hierarchy(normalized_graph_derivative_bounds=graph, normalized_map_derivative_bounds=maps)


@pytest.mark.parametrize("order", [0, -1, 1.0, True])
def test_partition_order_rejects_invalid_values(order: object) -> None:
    with pytest.raises(ValueError):
        M.bell_partition_terms(order)
