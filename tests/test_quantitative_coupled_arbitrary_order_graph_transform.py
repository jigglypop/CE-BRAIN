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
_load(
    "quantitative_coupled_arbitrary_order_implicit_jet",
    "quantitative_coupled_arbitrary_order_implicit_jet.py",
)
M = _load(
    "ce_quantitative_coupled_arbitrary_order_graph_transform",
    "quantitative_coupled_arbitrary_order_graph_transform.py",
)


def _raw(**overrides):
    values = dict(
        normalized_graph_derivative_bounds_with_point_modulus=(1, 2, 3, 4, 5),
        map_derivative_bounds=(2, 3, 5, 7),
        map_derivative_point_lipschitz_bounds=(0, 0, 0, 0),
        preimage_value_coupling_upper=0,
    )
    values.update(overrides)
    return M.coupled_composite_raw_jet_envelopes(**values)


def _certificate(order: int = 6, **overrides):
    graph = (1,) + (0,) * order
    values = dict(
        base_dimension=5,
        base_invertibility_lower=1,
        preimage_value_coupling_upper=0,
        normalized_graph_derivative_bounds_with_point_modulus=graph,
        base_map_derivative_bounds=(F(1, 2),) + (0,) * (order - 1),
        base_map_derivative_point_lipschitz_bounds=(0,) * order,
        fiber_map_derivative_bounds=(F(1, 20),) + (0,) * (order - 1),
        fiber_map_derivative_point_lipschitz_bounds=(0,) * order,
    )
    values.update(overrides)
    return M.quantitative_coupled_arbitrary_order_graph_transform(**values)


def test_raw_c1_c2_c3_c4_bell_sizes_are_exact() -> None:
    raw = _raw()
    assert raw.graph_embedding_jet_bounds == (2, 2, 3, 4)
    assert raw.composite_jet_bounds == (4, 16, 82, 468)


def test_embedding_difference_includes_preimage_displacement_and_own_jet_slot() -> None:
    raw = _raw(preimage_value_coupling_upper=F(1, 3))
    assert raw.state_value_coupling_upper == F(5, 3)
    assert raw.graph_embedding_difference_coefficients_upper == (
        (F(2, 3), 1),
        (1, 0, 1),
        (F(4, 3), 0, 0, 1),
        (F(5, 3), 0, 0, 0, 1),
    )


def test_highest_map_point_modulus_changes_only_same_level_value_row() -> None:
    curved = _raw(map_derivative_point_lipschitz_bounds=(1, 1, 1, 1))
    lower = _raw(map_derivative_point_lipschitz_bounds=(1, 1, 1, 0))
    assert curved.composite_jet_bounds == lower.composite_jet_bounds
    assert curved.composite_difference_coefficients_upper[:3] == lower.composite_difference_coefficients_upper[:3]
    assert curved.composite_difference_coefficients_upper[3][1:] == lower.composite_difference_coefficients_upper[3][1:]
    assert curved.composite_difference_coefficients_upper[3][0] > lower.composite_difference_coefficients_upper[3][0]


def test_preimage_coupling_changes_only_value_coefficients() -> None:
    moved = _raw(
        preimage_value_coupling_upper=1,
        map_derivative_point_lipschitz_bounds=(1, 1, 1, 1),
    )
    fixed = _raw(
        preimage_value_coupling_upper=0,
        map_derivative_point_lipschitz_bounds=(1, 1, 1, 1),
    )
    assert moved.composite_jet_bounds == fixed.composite_jet_bounds
    for moved_row, fixed_row in zip(
        moved.composite_difference_coefficients_upper,
        fixed.composite_difference_coefficients_upper,
    ):
        assert moved_row[0] > fixed_row[0]
        assert moved_row[1:] == fixed_row[1:]


def test_raw_generator_feeds_verified_conditional_c6_derivative_hierarchy() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_CONDITIONAL_COUPLED_C6_DERIVATIVE_JET_GRAPH_TRANSFORM"
    assert result.validation_level is not None
    assert result.implicit_jet_certificate.validation_level is not None
    assert tuple(
        level.derivative_bunching_factor_upper
        for level in result.implicit_jet_certificate.levels
    ) == (F(1, 10),) * 6


def test_linear_map_fixture_has_only_first_jet_size_but_all_diagonal_rows() -> None:
    result = _certificate(4)
    assert result.base_raw_jet_envelope.composite_jet_bounds == (1, 0, 0, 0)
    assert result.fiber_raw_jet_envelope.composite_jet_bounds == (F(1, 10), 0, 0, 0)
    assert tuple(
        row[-1] for row in result.base_raw_jet_envelope.composite_difference_coefficients_upper
    ) == (F(1, 2),) * 4


def test_curved_c6_fixture_has_strict_class_and_bunching_margins() -> None:
    tiny = F(1, 1_000_000)
    result = _certificate(
        base_invertibility_lower=F(9, 10),
        preimage_value_coupling_upper=F(1, 10),
        normalized_graph_derivative_bounds_with_point_modulus=(1, 1, 10, 100, 1000, 10000, 100000),
        base_map_derivative_bounds=(F(1, 2), tiny, tiny, tiny, tiny, tiny),
        base_map_derivative_point_lipschitz_bounds=(tiny,) * 6,
        fiber_map_derivative_bounds=(F(1, 100), tiny, tiny, tiny, tiny, tiny),
        fiber_map_derivative_point_lipschitz_bounds=(tiny,) * 6,
    )
    assert result.validation_level is not None
    assert result.robust_interior is True
    assert all(level.graph_jet_margin > 0 for level in result.implicit_jet_certificate.levels)
    assert all(level.derivative_bunching_margin > 0 for level in result.implicit_jet_certificate.levels)


def test_bunching_equality_fails_closed() -> None:
    result = _certificate(
        2,
        fiber_map_derivative_bounds=(F(1, 2), 0),
    )
    assert result.validation_level is None
    assert result.status == "CONDITIONAL_IMPLICIT_C1_JET_BUNCHING_NOT_STRICT"
    assert result.implicit_jet_certificate.levels[0].derivative_bunching_factor_upper == 1


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    assert _certificate(base_dimension=dimension).cn_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "kwargs",
    [
        {"normalized_graph_derivative_bounds_with_point_modulus": (1, 2, 3, 4)},
        {"map_derivative_bounds": (2, 3, 5)},
        {"map_derivative_point_lipschitz_bounds": (0, 0, 0)},
        {"preimage_value_coupling_upper": -1},
        {"map_derivative_bounds": (2, 3, True, 7)},
    ],
)
def test_invalid_raw_inputs_fail_closed(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        _raw(**kwargs)


def test_graph_requires_one_extra_point_modulus() -> None:
    with pytest.raises(ValueError, match=r"D1..D\(n\+1\)"):
        _certificate(normalized_graph_derivative_bounds_with_point_modulus=(1,) + (0,) * 5)


def test_claim_scope_keeps_c0_and_empirical_claims_out() -> None:
    result = _certificate()
    assert "SEPARATE_C0_GATE" in result.claim_scope
    assert "SUPPLIED_GLOBAL_MAP_MODULI" in result.claim_scope
