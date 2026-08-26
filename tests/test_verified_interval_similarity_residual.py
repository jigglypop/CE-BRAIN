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
M = _load("ce_verified_interval_similarity", "verified_interval_similarity_residual.py")


ZERO_RADII = (((0, 0), (0, 0)), ((0, 0), (0, 0)))


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


def _certificate(**overrides):
    matrix = overrides.pop("nominal_transition", ((0, 0), (0, 10)))
    values = dict(
        nominal_transition=matrix,
        uncertainty_radii=ZERO_RADII,
        approximate_inverses=_exact_node_inverses(matrix),
        nominal_similarity=((1, 0), (0, 1)),
        similarity_uncertainty_radii=ZERO_RADII,
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    values.update(overrides)
    return M.verified_interval_similarity_componentwise_residual_circle(**values)


def _real_matrix(matrix):
    return tuple(tuple(entry.real for entry in row) for row in matrix)


def test_zero_transform_uncertainty_reduces_to_fixed_identity_route() -> None:
    result = _certificate()
    assert result.validation_level is not None
    assert result.relative_infinity_contraction_upper == 0
    assert result.inverse_similarity_magnitude_upper == ((F(1), F(0)), (F(0), F(1)))
    assert result.transformed_uncertainty_upper == ((F(0), F(0)), (F(0), F(0)))
    assert result.similarity_condition_two_upper == 1
    assert tuple(node.transformed for node in result.nodes) == result.base_circle.nodes
    assert result.normalized_robust_delta_lower == result.base_circle.normalized_robust_delta_lower


def test_small_interval_similarity_family_is_certified() -> None:
    eps = F(1, 1000)
    radii = (((eps, 0), (eps, 0)), ((eps, 0), (eps, 0)))
    result = _certificate(similarity_uncertainty_radii=radii)
    assert result.validation_level == "VERIFIED_RATIONAL_INTERVAL_SIMILARITY_RESIDUAL_CONTOUR_BRIDGE"
    assert 0 < result.relative_infinity_contraction_upper < 1
    assert result.similarity_condition_two_upper is not None
    assert result.similarity_condition_two_upper > 1
    assert result.rank_preserved_for_entire_family


def test_neumann_boundary_fails_closed() -> None:
    radii = (((F(1), 0), (0, 0)), ((0, 0), (0, 0)))
    result = _certificate(similarity_uncertainty_radii=radii)
    assert result.status == "INTERVAL_SIMILARITY_INVERTIBILITY_UNAVAILABLE"
    assert result.relative_infinity_contraction_upper == 1
    assert result.inverse_similarity_magnitude_upper is None
    assert result.nodes == ()
    assert not result.rank_preserved_for_entire_family


def test_componentwise_envelope_contains_an_exact_sample() -> None:
    eps = F(1, 100)
    radii = (((eps, 0), (eps, 0)), ((eps, 0), (eps, 0)))
    result = _certificate(
        uncertainty_radii=(((F(1, 200), 0), (0, 0)), ((0, 0), (0, 0))),
        nominal_similarity=((1, F(1, 5)), (0, 1)),
        similarity_uncertainty_radii=radii,
    )
    assert result.transformed_uncertainty_upper is not None
    a0 = R._matrix(((0, 0), (0, 10)), "a0")
    a = R._matrix(((F(1, 200), 0), (0, 10)), "a")
    t0 = R._matrix(((1, F(1, 5)), (0, 1)), "t0")
    t = R._matrix(((1 + eps, F(1, 5) - eps), (eps, 1 - eps)), "t")
    t0_inverse = R._inverse(t0)
    t_inverse = R._inverse(t)
    assert t0_inverse is not None and t_inverse is not None
    nominal_transformed = R._matmul(t0_inverse, R._matmul(a0, t0))
    sampled_transformed = R._matmul(t_inverse, R._matmul(a, t))
    difference = tuple(
        tuple(sampled_transformed[i][j] - nominal_transformed[i][j] for j in range(2))
        for i in range(2)
    )
    for i in range(2):
        for j in range(2):
            assert difference[i][j].imag == 0
            assert abs(difference[i][j].real) <= result.transformed_uncertainty_upper[i][j]


def test_inverse_envelope_contains_exact_sample_inverse() -> None:
    eps = F(1, 20)
    radii = (((eps, 0), (eps, 0)), ((eps, 0), (eps, 0)))
    result = _certificate(similarity_uncertainty_radii=radii)
    assert result.inverse_similarity_magnitude_upper is not None
    sample = R._matrix(((1 + eps, -eps), (eps, 1 - eps)), "sample")
    sample_inverse = R._inverse(sample)
    assert sample_inverse is not None
    for i in range(2):
        for j in range(2):
            assert sample_inverse[i][j].imag == 0
            assert abs(sample_inverse[i][j].real) <= result.inverse_similarity_magnitude_upper[i][j]


def test_raw_rescaling_preserves_normalized_interval_similarity_result() -> None:
    eps = F(1, 1000)
    radii = (((eps, 0), (eps, 0)), ((eps, 0), (eps, 0)))
    base = _certificate(similarity_uncertainty_radii=radii)
    matrix = ((0, 0), (0, 70))
    scaled = _certificate(
        nominal_transition=matrix,
        approximate_inverses=_exact_node_inverses(matrix, radius=7, scale=7),
        similarity_uncertainty_radii=radii,
        radius=7,
        spectral_reference_scale=7,
    )
    assert scaled.status == base.status
    assert scaled.transformed_uncertainty_upper == base.transformed_uncertainty_upper
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert scaled.raw_robust_delta_lower == 7 * base.raw_robust_delta_lower


def test_bad_nominal_or_inexact_interval_input_fails_closed() -> None:
    with pytest.raises(ValueError, match="invertible"):
        _certificate(nominal_similarity=((1, 2), (2, 4)))
    with pytest.raises(ValueError):
        _certificate(
            similarity_uncertainty_radii=(((0.1, 0), (0, 0)), ((0, 0), (0, 0)))
        )


def test_provenance_and_optimization_flags_remain_false() -> None:
    result = _certificate()
    assert not result.empirical_matrix_provenance_verified
    assert not result.interval_similarity_selected_from_data
    assert result.supplied_interval_similarity_not_optimized
