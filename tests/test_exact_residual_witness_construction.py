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


R = _load("verified_rational_contour", "verified_rational_contour.py")
I = _load("verified_interval_contour", "verified_interval_contour.py")
T = _load("verified_interval_tightening", "verified_interval_tightening.py")
M = _load("ce_exact_residual_witness", "verified_interval_residual.py")


def test_scalar_constructor_returns_four_exact_two_sided_inverses() -> None:
    result = M.exact_nominal_node_inverse_witnesses(
        [[0]], center=0, radius=1, spectral_reference_scale=1
    )
    assert result.status == "VERIFIED_EXACT_NOMINAL_NODE_INVERSE_WITNESSES"
    assert result.validation_level == result.status
    assert result.failing_node_index is None
    assert result.approximate_inverses is not None
    assert len(result.approximate_inverses) == 4
    assert result.inverse_identity_checks == ((True, True),) * 4


def test_diagonal_and_nonnormal_constructors_have_zero_exact_residual() -> None:
    for matrix in ([[0, 0], [0, 10]], [[0, F(1, 25)], [0, 4]]):
        result = M.exact_nominal_node_inverse_witnesses(
            matrix, center=0, radius=1, spectral_reference_scale=1
        )
        assert result.approximate_inverses is not None
        identity = R._identity(2)
        for node, inverse in zip(result.normalized_node_matrices, result.approximate_inverses):
            assert R._matmul(inverse, node) == identity
            residual = tuple(
                tuple(identity[i][j] - R._matmul(inverse, node)[i][j] for j in range(2))
                for i in range(2)
            )
            assert residual == ((R.ZERO, R.ZERO), (R.ZERO, R.ZERO))


def test_constructor_is_deterministic_and_normalize_first_unit_invariant() -> None:
    first = M.exact_nominal_node_inverse_witnesses(
        [[0, F(1, 5)], [0, 4]], center=0, radius=1, spectral_reference_scale=1
    )
    repeat = M.exact_nominal_node_inverse_witnesses(
        [[0, F(1, 5)], [0, 4]], center=0, radius=1, spectral_reference_scale=1
    )
    scaled = M.exact_nominal_node_inverse_witnesses(
        [[0, 7 * F(1, 5)], [0, 28]], center=0, radius=7, spectral_reference_scale=7
    )
    assert repeat == first
    assert scaled.normalized_node_matrices == first.normalized_node_matrices
    assert scaled.approximate_inverses == first.approximate_inverses
    assert scaled.inverse_identity_checks == first.inverse_identity_checks


def test_sampled_contour_eigenvalue_is_named_constructor_failure() -> None:
    result = M.exact_nominal_node_inverse_witnesses(
        [[1]], center=0, radius=1, spectral_reference_scale=1
    )
    assert result.status == "EXACT_NOMINAL_NODE_INVERSE_UNAVAILABLE"
    assert result.validation_level is None
    assert result.failing_node_index == 0
    assert result.approximate_inverses is None


def test_convenience_bridge_passes_structured_box_without_supplied_witnesses() -> None:
    result = M.verified_componentwise_residual_circle_with_exact_witnesses(
        [[0, 0], [0, 10]],
        uncertainty_radii=[[(0, 0), (0, 0)], [(0, 0), (1, 0)]],
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    assert result.status == "VERIFIED_EXACT_CONSTRUCTED_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE"
    assert result.validation_level == result.status
    assert result.circle is not None
    assert result.circle.rank_preserved_for_entire_family is True
    assert all(node.residual == ((R.ZERO, R.ZERO), (R.ZERO, R.ZERO)) for node in result.circle.nodes)


def test_exact_construction_does_not_override_uncertainty_failure() -> None:
    result = M.verified_componentwise_residual_circle_with_exact_witnesses(
        [[0]],
        uncertainty_radii=[[(1, 0)]],
        center=0,
        radius=1,
        spectral_reference_scale=1,
    )
    assert result.construction.validation_level is not None
    assert result.status == "VERIFIED_RESIDUAL_NODE_CONTRACTION_UNAVAILABLE"
    assert result.validation_level is None
    assert result.circle is not None
    assert result.circle.rank_preserved_for_entire_family is False


def test_convenience_bridge_stops_before_family_gate_on_singular_node() -> None:
    result = M.verified_componentwise_residual_circle_with_exact_witnesses(
        [[1]], uncertainty_radii=[[(0, 0)]], center=0, radius=1,
        spectral_reference_scale=1,
    )
    assert result.status == "EXACT_NOMINAL_NODE_INVERSE_UNAVAILABLE"
    assert result.circle is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"nominal_transition": [[0.0]]},
        {"nominal_transition": [[True]]},
        {"nominal_transition": [[0, 1]]},
        {"radius": 0},
        {"spectral_reference_scale": -1},
        {"nodes": 8},
        {"nodes": True},
    ],
)
def test_constructor_inputs_fail_closed(kwargs: dict[str, object]) -> None:
    values = dict(
        nominal_transition=[[0]], center=0, radius=1,
        spectral_reference_scale=1, nodes=4,
    )
    values.update(kwargs)
    with pytest.raises(ValueError):
        M.exact_nominal_node_inverse_witnesses(**values)

