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
M = _load("ce_verified_interval_residual", "verified_interval_residual.py")


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


def test_structured_far_eigenvalue_box_passes_when_global_tightening_fails() -> None:
    matrix = [[0, 0], [0, 10]]
    uncertainty = [[(0, 0), (0, 0)], [(0, 0), (1, 0)]]
    result = M.verified_componentwise_residual_circle(
        matrix,
        uncertainty_radii=uncertainty,
        approximate_inverses=_exact_node_inverses(matrix),
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    assert result.tightening.validation_level is None
    assert result.tightening.status == "VERIFIED_TIGHT_INTERVAL_UNCERTAINTY_NOT_BELOW_MARGIN"
    assert result.status == "VERIFIED_RATIONAL_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE"
    assert result.rank_preserved_for_entire_family is True
    assert all(node.contraction_one_upper < 1 for node in result.nodes)
    assert all(node.contraction_infinity_upper < 1 for node in result.nodes)


def test_exact_inverse_zero_uncertainty_has_zero_residuals() -> None:
    witnesses = _exact_node_inverses([[0]])
    result = M.verified_componentwise_residual_circle(
        [[0]], uncertainty_radii=[[(0, 0)]], approximate_inverses=witnesses,
        center=0, radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    assert result.status == "VERIFIED_RATIONAL_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE"
    assert all(node.residual == ((R.ZERO,),) for node in result.nodes)
    assert all(node.contraction_one_upper == 0 for node in result.nodes)
    assert result.projector_perturbation_upper == 0


def test_inexact_rational_witnesses_are_checked_and_can_pass() -> None:
    exact = _exact_node_inverses([[0]])
    inexact = [
        tuple(tuple(entry * F(99, 100) for entry in row) for row in matrix)
        for matrix in exact
    ]
    result = M.verified_componentwise_residual_circle(
        [[0]], uncertainty_radii=[[(0, 0)]], approximate_inverses=inexact,
        center=0, radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    assert result.status == "VERIFIED_RATIONAL_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE"
    assert all(node.residual != ((R.ZERO,),) for node in result.nodes)
    assert all(node.contraction_one_upper < 1 for node in result.nodes)


def test_contraction_equality_is_noncertificate() -> None:
    result = M.verified_componentwise_residual_circle(
        [[0]], uncertainty_radii=[[(1, 0)]],
        approximate_inverses=_exact_node_inverses([[0]]), center=0, radius=1,
        spectral_reference_scale=1, sqrt_precision=40,
    )
    assert result.status == "VERIFIED_RESIDUAL_NODE_CONTRACTION_UNAVAILABLE"
    assert result.validation_level is None
    assert result.rank_preserved_for_entire_family is False
    assert any(node.contraction_one_upper >= 1 for node in result.nodes)


def test_passing_nodes_can_still_fail_full_circle_chord() -> None:
    exact = _exact_node_inverses([[0]])
    coarse = [
        tuple(tuple(entry * F(3, 2) for entry in row) for row in matrix)
        for matrix in exact
    ]
    result = M.verified_componentwise_residual_circle(
        [[0]], uncertainty_radii=[[(0, 0)]], approximate_inverses=coarse,
        center=0, radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    assert all(node.status == "VERIFIED_RESIDUAL_NODE_CONTRACTION" for node in result.nodes)
    assert result.status == "VERIFIED_RESIDUAL_FULL_CIRCLE_LOWER_NONPOSITIVE"
    assert result.normalized_robust_delta_lower is not None
    assert result.normalized_robust_delta_lower <= 0


@pytest.mark.parametrize(
    "witnesses",
    [
        [],
        [[[1]]],
        [[[1]], [[1]], [[1]], [[1, 0], [0, 1]]],
        [[[1.0]], [[1]], [[1]], [[1]]],
        [[[True]], [[1]], [[1]], [[1]]],
    ],
)
def test_witness_count_shape_and_exact_type_fail_closed(witnesses: object) -> None:
    with pytest.raises(ValueError):
        M.verified_componentwise_residual_circle(
            [[0]], uncertainty_radii=[[(0, 0)]], approximate_inverses=witnesses,
            center=0, radius=1, spectral_reference_scale=1,
        )


def test_normalize_first_residual_certificate_is_unit_invariant() -> None:
    matrix = [[0, 0], [0, 10]]
    uncertainty = [[(0, 0), (0, 0)], [(0, 0), (F(1, 10), 0)]]
    witnesses = _exact_node_inverses(matrix)
    base = M.verified_componentwise_residual_circle(
        matrix, uncertainty_radii=uncertainty, approximate_inverses=witnesses,
        center=0, radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    scaled = M.verified_componentwise_residual_circle(
        [[0, 0], [0, 70]],
        uncertainty_radii=[[(0, 0), (0, 0)], [(0, 0), (F(7, 10), 0)]],
        approximate_inverses=witnesses, center=0, radius=7,
        spectral_reference_scale=7, sqrt_precision=40,
    )
    assert scaled.status == base.status
    assert scaled.nodes == base.nodes
    assert scaled.normalized_chord_upper == base.normalized_chord_upper
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert scaled.projector_perturbation_upper == base.projector_perturbation_upper
    assert scaled.raw_robust_delta_lower == 7 * base.raw_robust_delta_lower
    assert scaled.raw_robust_resolvent_upper == base.raw_robust_resolvent_upper / 7


def test_nonnormal_optional_projector_bridge_adds_residual_and_quadrature_errors() -> None:
    matrix = [[0, F(1, 25)], [0, 4]]
    result = M.verified_componentwise_residual_projector(
        matrix,
        uncertainty_radii=[[(0, 0), (F(1, 1000), 0)], [(0, 0), (0, 0)]],
        approximate_inverses=_exact_node_inverses(matrix), center=0, radius=1,
        spectral_reference_scale=1, expansion_factor=F(3, 2),
        eigenvectors=[[1, F(1, 100)], [0, 1]],
        eigenvalues=[[0, 0], [0, 4]], sqrt_precision=40,
    )
    assert result.status == "VERIFIED_RATIONAL_COMPONENTWISE_RESIDUAL_PROJECTOR_BRIDGE"
    assert result.total_projector_error_upper == (
        result.uncertainty_projector_error_upper + result.nominal_quadrature_error_upper
    )


def test_invalid_nominal_strip_and_invalid_uncertainty_fail_closed() -> None:
    witnesses = _exact_node_inverses([[0]])
    invalid_strip = M.verified_componentwise_residual_projector(
        [[0]], uncertainty_radii=[[(0, 0)]], approximate_inverses=witnesses,
        center=0, radius=1, spectral_reference_scale=1, expansion_factor=2,
        eigenvectors=[[1]], eigenvalues=[[1]],
    )
    assert invalid_strip.status == "VERIFIED_NOMINAL_STRIP_CERTIFICATE_UNAVAILABLE"
    assert invalid_strip.total_projector_error_upper is None
    with pytest.raises(ValueError):
        M.verified_componentwise_residual_circle(
            [[0]], uncertainty_radii=[[(-1, 0)]], approximate_inverses=witnesses,
            center=0, radius=1, spectral_reference_scale=1,
        )


def test_unsupported_mesh_is_rejected() -> None:
    with pytest.raises(ValueError, match="four-node"):
        M.verified_componentwise_residual_circle(
            [[0]], uncertainty_radii=[[(0, 0)]],
            approximate_inverses=_exact_node_inverses([[0]]), center=0, radius=1,
            spectral_reference_scale=1, nodes=8,
        )
