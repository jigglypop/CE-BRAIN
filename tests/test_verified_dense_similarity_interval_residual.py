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
_load("verified_interval_contour", "verified_interval_contour.py")
_load("verified_interval_tightening", "verified_interval_tightening.py")
V = _load("verified_interval_residual", "verified_interval_residual.py")
W = _load("verified_weighted_interval_residual", "verified_weighted_interval_residual.py")
M = _load("ce_verified_dense_similarity", "verified_dense_similarity_interval_residual.py")


def _exact_node_inverses(matrix, *, center=0, radius=1, scale=1):
    raw = R._matrix(matrix, "matrix")
    scale_q = R._fraction(scale, "scale")
    u = tuple(tuple(entry / scale_q for entry in row) for row in raw)
    c = R.parse_qcomplex(center) / scale_q
    r = R._fraction(radius, "radius") / scale_q
    directions = (R.ONE, R.QComplex(0, 1), R.QComplex(-1), R.QComplex(0, -1))
    witnesses = []
    for direction in directions:
        z = c + r * direction
        node = tuple(
            tuple((z if i == j else R.ZERO) - u[i][j] for j in range(len(u)))
            for i in range(len(u))
        )
        inverse = R._inverse(node)
        assert inverse is not None
        witnesses.append(inverse)
    return tuple(witnesses)


def _structured(**overrides):
    matrix = overrides.pop("nominal_transition", ((0, 0), (0, 10)))
    values = dict(
        nominal_transition=matrix,
        uncertainty_radii=(((0, 0), (0, 0)), ((0, 0), (1, 0))),
        approximate_inverses=_exact_node_inverses(matrix),
        similarity=((1, 0), (0, 1)),
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    values.update(overrides)
    return M.verified_dense_similarity_componentwise_residual_circle(**values)


def test_identity_similarity_exactly_reproduces_untransformed_certificate() -> None:
    result = _structured()
    assert result.validation_level is not None
    assert result.similarity_condition_two_upper == 1
    assert result.inverse_identity_checks == (True, True)
    assert result.transformed_uncertainty_upper == (
        (F(0), F(0)), (F(0), F(1))
    )
    for node in result.nodes:
        assert node.transformed == node.untransformed
        assert node.translated_transformed_node_sigma_lower == node.untransformed.node_sigma_lower
        assert node.selected_method == "UNTRANSFORMED"
    assert result.normalized_robust_delta_lower == result.base_circle.normalized_robust_delta_lower


def test_positive_diagonal_dense_route_reduces_to_diagonal_weighted_route() -> None:
    matrix = ((0, 5), (0, 10))
    witnesses = _exact_node_inverses(matrix)
    uncertainty = (((0, 0), (0, 0)), ((0, 0), (2, 0)))
    dense = _structured(
        nominal_transition=matrix,
        uncertainty_radii=uncertainty,
        approximate_inverses=witnesses,
        similarity=((2, 0), (0, 1)),
    )
    diagonal = W.verified_weighted_componentwise_residual_circle(
        matrix,
        uncertainty_radii=uncertainty,
        approximate_inverses=witnesses,
        diagonal_weights=(2, 1),
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    assert dense.similarity_condition_two_upper == diagonal.weight_condition_two == 2
    assert tuple(node.transformed for node in dense.nodes) == tuple(
        node.weighted for node in diagonal.nodes
    )
    assert tuple(node.translated_transformed_node_sigma_lower for node in dense.nodes) == tuple(
        node.translated_weighted_node_sigma_lower for node in diagonal.nodes
    )
    assert dense.normalized_robust_delta_lower == diagonal.normalized_robust_delta_lower


def test_nontrivial_exact_dense_rotation_can_certify_its_own_full_circle() -> None:
    rotation = ((F(2499, 2501), F(-100, 2501)), (F(100, 2501), F(2499, 2501)))
    result = _structured(
        uncertainty_radii=(((0, 0), (0, 0)), ((0, 0), (0, 0))),
        similarity=rotation,
    )
    assert result.validation_level == "VERIFIED_RATIONAL_DENSE_SIMILARITY_RESIDUAL_CONTOUR_BRIDGE"
    assert result.similarity_condition_two_upper > 1
    assert result.dense_only_robust_delta_lower is not None
    assert result.dense_only_robust_delta_lower > 0
    assert all(node.transformed.node_sigma_lower is not None for node in result.nodes)
    assert all(
        node.translated_transformed_node_sigma_lower
        == node.transformed.node_sigma_lower / result.similarity_condition_two_upper
        for node in result.nodes
    )


def test_dense_uncertainty_transform_is_componentwise_outward() -> None:
    transform = ((1, 1), (0, 1))
    result = _structured(
        uncertainty_radii=(((1, 0), (2, 0)), ((3, 0), (4, 0))),
        similarity=transform,
    )
    transform_q = R._matrix(transform, "transform")
    inverse = R._inverse(transform_q)
    assert inverse is not None
    abs_transform = tuple(tuple(F(abs(entry.real)) for entry in row) for row in transform_q)
    abs_inverse = tuple(tuple(F(abs(entry.real)) for entry in row) for row in inverse)
    uncertainty = ((F(1), F(2)), (F(3), F(4)))
    expected = V._nonnegative_matmul(
        abs_inverse, V._nonnegative_matmul(uncertainty, abs_transform)
    )
    assert result.transformed_uncertainty_upper == expected


def test_condition_penalty_is_not_optional() -> None:
    result = _structured(similarity=((1, 1), (0, 1)))
    assert result.similarity_condition_two_upper > 1
    for node in result.nodes:
        if node.transformed.node_sigma_lower is not None:
            assert node.translated_transformed_node_sigma_lower == (
                node.transformed.node_sigma_lower / result.similarity_condition_two_upper
            )
            assert node.translated_transformed_node_sigma_lower < node.transformed.node_sigma_lower


def test_raw_spectral_rescaling_preserves_normalized_dense_result() -> None:
    rotation = ((F(2499, 2501), F(-100, 2501)), (F(100, 2501), F(2499, 2501)))
    base = _structured(
        uncertainty_radii=(((0, 0), (0, 0)), ((0, 0), (0, 0))),
        similarity=rotation,
    )
    matrix = ((0, 0), (0, 70))
    scaled = _structured(
        nominal_transition=matrix,
        uncertainty_radii=(((0, 0), (0, 0)), ((0, 0), (0, 0))),
        approximate_inverses=_exact_node_inverses(matrix, radius=7, scale=7),
        similarity=rotation,
        radius=7,
        spectral_reference_scale=7,
    )
    assert scaled.status == base.status
    assert scaled.nodes == base.nodes
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert scaled.raw_robust_delta_lower == 7 * base.raw_robust_delta_lower


def test_singular_or_dimension_mismatched_similarity_fails_closed() -> None:
    with pytest.raises(ValueError, match="invertible"):
        _structured(similarity=((1, 2), (2, 4)))
    with pytest.raises(ValueError, match="dimension"):
        _structured(similarity=((1,),))


@pytest.mark.parametrize(
    "similarity",
    [((1.0, 0), (0, 1)), ((True, 0), (0, 1)), (("01", 0), (0, 1))],
)
def test_inexact_or_noncanonical_similarity_entries_fail_closed(similarity: object) -> None:
    with pytest.raises(ValueError):
        _structured(similarity=similarity)


def test_provenance_and_optimization_flags_remain_false() -> None:
    result = _structured()
    assert not result.empirical_matrix_provenance_verified
    assert not result.dense_similarity_selected_from_data
    assert result.supplied_similarity_not_optimized
