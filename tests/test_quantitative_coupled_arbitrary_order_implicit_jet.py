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
M = _load(
    "ce_quantitative_coupled_arbitrary_order_implicit_jet",
    "quantitative_coupled_arbitrary_order_implicit_jet.py",
)


def _zero_rows(order: int):
    return tuple(tuple(F(0) for _ in range(level + 1)) for level in range(1, order + 1))


def _certificate(order: int = 6, **overrides):
    values = dict(
        base_dimension=5,
        base_invertibility_lower=1,
        normalized_graph_derivative_bounds=tuple(10 ** (3 * level) for level in range(1, order + 1)),
        forward_jet_bounds=(2, 1, 1, 1, 1, 1)[:order],
        observed_output_jet_bounds=(1, 1, 1, 1, 1, 1)[:order],
        forward_difference_coefficients_upper=_zero_rows(order),
        observed_output_difference_coefficients_upper=_zero_rows(order),
    )
    values.update(overrides)
    return M.quantitative_coupled_arbitrary_order_implicit_jet_recurrence(**values)


def test_all_singletons_are_isolated_not_the_single_n_block() -> None:
    result = _certificate(4)
    assert tuple(level.isolated_all_singletons for level in result.levels) == (
        (1,), (2, 0), (3, 0, 0), (4, 0, 0, 0)
    )
    assert (0, 0, 0, 1) != result.levels[3].isolated_all_singletons


def test_c2_c3_c4_implicit_faa_di_bruno_numerators_are_exact() -> None:
    result = _certificate(4)
    x1, x2, x3, x4 = (level.transform_jet_upper for level in result.levels)
    f1, f2, f3, f4 = result.forward_jet_bounds
    y1, y2, y3, y4 = result.observed_output_jet_bounds
    assert x1 == y1
    assert x2 == y2 + x1 * f2
    assert x3 == y3 + 3 * x2 * f1 * f2 + x1 * f3
    assert x4 == y4 + 6 * x3 * f1**2 * f2 + 3 * x2 * f2**2 + 4 * x2 * f1 * f3 + x1 * f4
    assert x4 == 360


def test_linear_base_reduces_to_alpha_power_transport_at_every_level() -> None:
    order = 6
    targets = tuple(F(index + 1) for index in range(order))
    result = _certificate(
        order,
        base_invertibility_lower=2,
        normalized_graph_derivative_bounds=tuple(value + 1 for value in targets),
        forward_jet_bounds=(2,) + (0,) * (order - 1),
        observed_output_jet_bounds=tuple(targets[index] * 2 ** (index + 1) for index in range(order)),
    )
    assert result.validation_level is not None
    assert tuple(level.transform_jet_upper for level in result.levels) == targets


def test_product_telescoping_and_inverse_slot_are_kept_separate() -> None:
    order = 2
    forward_delta = (((1, 0)), ((0, 0, 0)))
    result = _certificate(order, forward_difference_coefficients_upper=forward_delta)
    first = result.levels[0]
    assert first.numerator_difference_coefficients_upper == (0, 0)
    assert first.inverse_slot_correction_coefficients_upper == (1, 0)
    assert first.coefficient_by_input_order_upper == (1, 0)
    second = result.levels[1]
    assert second.numerator_difference_coefficients_upper[0] > 0
    assert second.inverse_slot_correction_coefficients_upper[0] == 4
    assert second.coefficient_by_input_order_upper[0] > 4


def test_diagonal_equality_fails_closed_with_named_boundary() -> None:
    rows = list(_zero_rows(2))
    rows[0] = (0, 1)
    rows[1] = (0, 0, 1)
    result = _certificate(
        2,
        forward_jet_bounds=(1, 0),
        observed_output_jet_bounds=(1, 1),
        observed_output_difference_coefficients_upper=tuple(rows),
    )
    assert result.validation_level is None
    assert result.status == "CONDITIONAL_IMPLICIT_C1_JET_BUNCHING_NOT_STRICT"
    assert result.levels[0].derivative_bunching_factor_upper == 1


def test_exact_iteration_is_synchronous_and_preserves_external_d0() -> None:
    result = _certificate(4)
    initial = (F(7), F(1), F(2), F(3), F(4))
    one = M.coupled_implicit_jet_iteration_bound(
        result, initial_distance_by_derivative_order=initial, steps=1
    )
    assert one.distance_by_derivative_order_upper[0] == 7
    for level in result.levels:
        assert one.distance_by_derivative_order_upper[level.order] == sum(
            coefficient * initial[index]
            for index, coefficient in enumerate(level.coefficient_by_input_order_upper)
        )


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.cn_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_dimension", 0),
        ("base_dimension", True),
        ("base_invertibility_lower", 0),
        ("base_invertibility_lower", 1.0),
        ("forward_jet_bounds", (F(1, 2), 1, 1, 1, 1, 1)),
        ("observed_output_jet_bounds", (1, -1, 1, 1, 1, 1)),
    ],
)
def test_invalid_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_coefficient_rows_must_be_exactly_triangular() -> None:
    rows = list(_zero_rows(6))
    rows[3] = (0, 0, 0, 0)
    with pytest.raises(ValueError, match="D0..D4"):
        _certificate(forward_difference_coefficients_upper=tuple(rows))


def test_claim_scope_does_not_overclaim_a_map_specific_graph_theorem() -> None:
    result = _certificate()
    assert result.validation_level is not None
    assert "CONDITIONAL_ALGEBRAIC_JET_SOLVER" in result.claim_scope
    assert "RAW_F_AND_Y_JET_ENVELOPES_REQUIRE_A_SEPARATE_MAP_SPECIFIC_PROOF" in result.claim_scope
