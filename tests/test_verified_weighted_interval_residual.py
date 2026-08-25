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
V = _load("verified_interval_residual", "verified_interval_residual.py")
M = _load("ce_verified_weighted_residual", "verified_weighted_interval_residual.py")


def _exact_node_inverses(matrix, *, center=0, radius=1, scale=1):
    u_raw = R._matrix(matrix, "matrix")
    scale_q = R._fraction(scale, "scale")
    u = tuple(tuple(entry / scale_q for entry in row) for row in u_raw)
    c = R.parse_qcomplex(center) / scale_q
    r = R._fraction(radius, "radius") / scale_q
    directions = (R.ONE, R.QComplex(0, 1), R.QComplex(-1), R.QComplex(0, -1))
    witnesses = []
    for direction in directions:
        z = c + r * direction
        a = tuple(
            tuple((z if i == j else R.ZERO) - u[i][j] for j in range(len(u)))
            for i in range(len(u))
        )
        inverse = R._inverse(a)
        assert inverse is not None
        witnesses.append(inverse)
    return witnesses


def _structured(**overrides):
    values = dict(
        nominal_transition=[[0, 0], [0, 10]],
        uncertainty_radii=[[(0, 0), (0, 0)], [(0, 0), (1, 0)]],
        approximate_inverses=_exact_node_inverses([[0, 0], [0, 10]]),
        diagonal_weights=[1, 1],
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    values.update(overrides)
    return M.verified_weighted_componentwise_residual_circle(**values)


def test_equal_weights_reproduce_unweighted_nodes_and_full_circle() -> None:
    result = _structured()
    assert result.status == "VERIFIED_RATIONAL_WEIGHTED_RESIDUAL_CONTOUR_BRIDGE"
    assert result.validation_level == result.status
    assert result.weight_condition_two == 1
    assert result.normalized_weights == (1, 1)
    assert result.base_circle.validation_level is not None
    for node in result.nodes:
        assert node.weighted == node.unweighted
        assert node.selected_method == "UNWEIGHTED"
        assert node.selected_node_sigma_lower == node.unweighted.node_sigma_lower
    assert result.normalized_robust_delta_lower == result.base_circle.normalized_robust_delta_lower


def test_common_weight_scaling_is_exactly_invariant() -> None:
    base = _structured(diagonal_weights=[1, 2])
    scaled = _structured(diagonal_weights=[7, 14])
    assert scaled.normalized_weights == base.normalized_weights
    assert scaled.weight_condition_two == base.weight_condition_two
    assert scaled.nodes == base.nodes
    assert scaled.status == base.status


def test_weighted_nodes_can_contract_when_unweighted_nodes_fail() -> None:
    matrix = [[0, 5], [0, 10]]
    result = _structured(
        nominal_transition=matrix,
        uncertainty_radii=[[(0, 0), (0, 0)], [(0, 0), (2, 0)]],
        approximate_inverses=_exact_node_inverses(matrix),
        diagonal_weights=[2, 1],
    )
    assert result.base_circle.status == "VERIFIED_RESIDUAL_NODE_CONTRACTION_UNAVAILABLE"
    assert all(node.unweighted.node_sigma_lower is None for node in result.nodes)
    assert all(node.weighted.node_sigma_lower is not None for node in result.nodes)
    assert all(node.selected_method == "WEIGHTED_TRANSLATED" for node in result.nodes)
    assert result.status == "VERIFIED_WEIGHTED_RESIDUAL_FULL_CIRCLE_LOWER_NONPOSITIVE"
    assert result.validation_level is None


def test_conditioning_penalty_is_applied_before_full_circle_gate() -> None:
    matrix = [[0, 5], [0, 10]]
    result = _structured(
        nominal_transition=matrix,
        uncertainty_radii=[[(0, 0), (0, 0)], [(0, 0), (2, 0)]],
        approximate_inverses=_exact_node_inverses(matrix),
        diagonal_weights=[2, 1],
    )
    assert result.weight_condition_two == 2
    for node in result.nodes:
        assert node.weighted.node_sigma_lower is not None
        assert node.translated_weighted_node_sigma_lower == node.weighted.node_sigma_lower / 2
    assert result.normalized_robust_delta_lower <= 0


def test_worse_weight_cannot_replace_a_better_unweighted_lower() -> None:
    result = _structured(diagonal_weights=[100, 1])
    assert result.validation_level is not None
    assert all(node.selected_method == "UNWEIGHTED" for node in result.nodes)
    assert all(
        node.selected_node_sigma_lower == node.unweighted.node_sigma_lower
        for node in result.nodes
    )
    assert result.normalized_robust_delta_lower == result.base_circle.normalized_robust_delta_lower


def test_inexact_witness_is_still_checked_after_similarity() -> None:
    exact = _exact_node_inverses([[0]])
    inexact = [
        tuple(tuple(entry * F(99, 100) for entry in row) for row in matrix)
        for matrix in exact
    ]
    result = M.verified_weighted_componentwise_residual_circle(
        [[0]], uncertainty_radii=[[(0, 0)]], approximate_inverses=inexact,
        diagonal_weights=[3], center=0, radius=1, spectral_reference_scale=1,
        sqrt_precision=40,
    )
    assert result.validation_level is not None
    assert all(node.weighted.residual != ((R.ZERO,),) for node in result.nodes)


def test_raw_spectral_unit_rescaling_preserves_normalized_weighted_result() -> None:
    base = _structured(diagonal_weights=[2, 1])
    scaled = _structured(
        nominal_transition=[[0, 0], [0, 70]],
        uncertainty_radii=[[(0, 0), (0, 0)], [(0, 0), (7, 0)]],
        approximate_inverses=_exact_node_inverses([[0, 0], [0, 70]], radius=7, scale=7),
        diagonal_weights=[2, 1],
        radius=7,
        spectral_reference_scale=7,
    )
    assert scaled.status == base.status
    assert scaled.normalized_weights == base.normalized_weights
    assert scaled.nodes == base.nodes
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert scaled.raw_robust_delta_lower == 7 * base.raw_robust_delta_lower


@pytest.mark.parametrize(
    "weights",
    [[], [1], [1, 1, 1], [0, 1], [-1, 1], [1.0, 1], [True, 1], ["01", 1]],
)
def test_invalid_weights_fail_closed(weights: object) -> None:
    with pytest.raises(ValueError):
        _structured(diagonal_weights=weights)


def test_weight_condition_counterexample_grows_in_original_coordinates() -> None:
    for condition in (2, 10, 100):
        transformed = ((R.ONE, R.ONE), (R.ZERO, R.ONE))
        weights = (F(condition), F(1))
        original = tuple(
            tuple(transformed[i][j] * weights[i] / weights[j] for j in range(2))
            for i in range(2)
        )
        inverse = R._inverse(original)
        assert inverse is not None
        image = (inverse[0][1], inverse[1][1])
        norm_squared = image[0].abs_squared() + image[1].abs_squared()
        assert norm_squared == condition * condition + 1

