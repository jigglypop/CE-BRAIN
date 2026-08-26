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
_load("quantitative_coupled_arbitrary_order_implicit_jet", "quantitative_coupled_arbitrary_order_implicit_jet.py")
C0 = _load("quantitative_coupled_graph_transform", "quantitative_coupled_graph_transform.py")
CN = _load("quantitative_coupled_arbitrary_order_graph_transform", "quantitative_coupled_arbitrary_order_graph_transform.py")
_load("quantitative_local_coupled_arbitrary_order_graph_transform", "quantitative_local_coupled_arbitrary_order_graph_transform.py")
FULL = _load("quantitative_full_coupled_arbitrary_order_graph_transform", "quantitative_full_coupled_arbitrary_order_graph_transform.py")
M = _load("ce_quantitative_smooth_projective_graph_transform", "quantitative_smooth_projective_graph_transform.py")


def _c0(dimension: int = 4):
    return C0.quantitative_coupled_graph_transform(
        base_dimension=dimension, base_reference_scale=1, fiber_reference_scale=1,
        fiber_radius=1, forcing_at_zero_upper=F(1, 10), base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 200), base_self_lipschitz=F(1, 100),
        fiber_to_base_lipschitz=F(9, 100), base_to_fiber_lipschitz=0,
        fiber_self_lipschitz=F(1, 200), graph_slope_upper=1,
    )


def _full(order: int, dimension: int = 4, **cn_overrides):
    tiny = F(1, 1_000_000)
    values = dict(
        base_dimension=dimension, base_invertibility_lower=F(9, 10),
        preimage_value_coupling_upper=F(1, 10),
        normalized_graph_derivative_bounds_with_point_modulus=(1, 1, 10, 100, 1000, 10000, 100000)[: order + 1],
        base_map_derivative_bounds=(F(1, 2),) + (tiny,) * (order - 1),
        base_map_derivative_point_lipschitz_bounds=(tiny,) * order,
        fiber_map_derivative_bounds=(F(1, 100),) + (tiny,) * (order - 1),
        fiber_map_derivative_point_lipschitz_bounds=(tiny,) * order,
    )
    values.update(cn_overrides)
    derivative = CN.quantitative_coupled_arbitrary_order_graph_transform(**values)
    return FULL.quantitative_full_coupled_arbitrary_order_graph_transform(
        c0_certificate=_c0(dimension), derivative_certificate=derivative
    )


def _prefix(maximum: int = 6, dimension: int = 4):
    return M.quantitative_smooth_projective_prefix_graph_transform(
        certificates_by_maximum_order=tuple(_full(order, dimension) for order in range(2, maximum + 1))
    )


def test_compatible_c2_to_c6_prefix_is_verified_but_never_promoted_to_cinfinity() -> None:
    result = _prefix()
    assert result.validation_level is not None
    assert result.covered_orders == (2, 3, 4, 5, 6)
    assert result.maximum_verified_order == 6
    assert result.triangular_convergence_margin > 0
    assert result.every_finite_order_hypothesis_verified is False
    assert result.projective_limit_completeness_hypothesis_verified is False
    assert result.common_orbit_hypothesis_verified is False
    assert result.cinfinity_claim_admitted is False
    assert result.robust_interior is False


@pytest.mark.parametrize("maximum", [2, 3, 4, 6])
def test_every_finite_prefix_length_is_supported(maximum: int) -> None:
    result = _prefix(maximum)
    assert result.validation_level is not None
    assert result.maximum_verified_order == maximum


def test_transition_matrix_is_lower_triangular_with_strict_diagonal() -> None:
    result = _prefix(4)
    matrix = result.transition_matrix_upper
    for row_index, row in enumerate(matrix):
        assert all(value == 0 for value in row[row_index + 1 :])
        assert row[row_index] < 1
    assert matrix[0][0] == F(11, 1000)
    assert result.maximum_diagonal_factor_upper == max(
        matrix[index][index] for index in range(len(matrix))
    )


def test_prefix_iteration_is_exactly_the_highest_full_iteration() -> None:
    prefix = _prefix(4)
    initial = (1, 2, 3, 4, 5)
    projective = M.smooth_projective_prefix_iteration_bound(
        prefix, initial_distance_by_derivative_order=initial, steps=2
    )
    direct = FULL.full_coupled_arbitrary_order_iteration_bound(
        prefix.certificates_by_maximum_order[-1],
        initial_distance_by_derivative_order=initial, steps=2,
    )
    assert projective == direct


def test_nonconsecutive_or_reordered_orders_fail_closed() -> None:
    skipped = M.quantitative_smooth_projective_prefix_graph_transform(
        certificates_by_maximum_order=(_full(2), _full(4))
    )
    assert skipped.status == "SMOOTH_PROJECTIVE_PREFIX_ORDERS_NOT_CONSECUTIVE_FROM_C2"
    reversed_pair = M.quantitative_smooth_projective_prefix_graph_transform(
        certificates_by_maximum_order=(_full(3), _full(2))
    )
    assert reversed_pair.status == "SMOOTH_PROJECTIVE_PREFIX_ORDERS_NOT_CONSECUTIVE_FROM_C2"


def test_changed_lower_order_map_modulus_breaks_projective_compatibility() -> None:
    tiny = F(1, 1_000_000)
    changed_c3 = _full(
        3, base_map_derivative_bounds=(F(1, 2), 2 * tiny, tiny)
    )
    result = M.quantitative_smooth_projective_prefix_graph_transform(
        certificates_by_maximum_order=(_full(2), changed_c3)
    )
    assert result.status == "SMOOTH_PROJECTIVE_C2_PREFIX_INCOMPATIBLE_WITH_C3"


def test_failed_full_member_is_propagated_and_cannot_be_iterated() -> None:
    failed = _full(3, preimage_value_coupling_upper=F(11, 100))
    result = M.quantitative_smooth_projective_prefix_graph_transform(
        certificates_by_maximum_order=(_full(2), failed)
    )
    assert "FULL_COUPLED_CN_PREIMAGE_COUPLING_MISMATCH" in result.failure_codes
    with pytest.raises(ValueError, match="verified"):
        M.smooth_projective_prefix_iteration_bound(
            result, initial_distance_by_derivative_order=(1, 1, 1, 1), steps=1
        )


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    assert _prefix(4, dimension).cn_graph_real_dimension == dimension


def test_finite_input_cannot_set_any_infinite_order_hypothesis() -> None:
    for maximum in (2, 6):
        result = _prefix(maximum)
        assert not result.every_finite_order_hypothesis_verified
        assert not result.projective_limit_completeness_hypothesis_verified
        assert not result.common_orbit_hypothesis_verified
        assert not result.cinfinity_claim_admitted


@pytest.mark.parametrize("bad", [None, (), (object(),)])
def test_invalid_prefix_containers_and_members_are_rejected(bad) -> None:
    with pytest.raises(ValueError):
        M.quantitative_smooth_projective_prefix_graph_transform(
            certificates_by_maximum_order=bad
        )
