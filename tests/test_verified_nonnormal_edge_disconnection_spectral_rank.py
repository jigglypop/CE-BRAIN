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


_load("verified_edge_metric_effective_dimension", "verified_edge_metric_effective_dimension.py")
N = _load("verified_nonnormal_edge_disconnection_spectral_rank", "verified_nonnormal_edge_disconnection_spectral_rank.py")


def _zero(size: int):
    return tuple(tuple(0 for _ in range(size)) for _ in range(size))


def _directed_edge(size: int):
    rows = [list(row) for row in _zero(size)]; rows[0][1] = 1
    return tuple(tuple(row) for row in rows)


def _coupling(size: int, value):
    rows = [list(row) for row in _zero(size)]; rows[0][1] = value
    return tuple(tuple(row) for row in rows)


def _shear_basis(size: int, shear=1):
    rows = [list(row) for row in _zero(size)]
    for i in range(size):
        rows[i][i] = 1
    rows[0][1] = shear
    return tuple(tuple(row) for row in rows)


def _args():
    size = 7
    return dict(
        disconnected_edge_mask=_zero(size),
        maximum_connected_edge_mask=_directed_edge(size),
        disconnected_eigenvalues=(0, 3, F(1, 2), F(-1, 2), F(1, 4), F(-1, 4), F(3, 4)),
        eigenvector_matrix=_shear_basis(size),
        edge_coupling_operator=_coupling(size, F(1, 100)),
        maximum_coupling_parameter=1,
        fixed_circle_center=0,
        fixed_circle_radius=1,
        eigenvector_condition_frobenius_upper=8,
        maximum_coupling_norm_upper=F(1, 100),
        candidate_band=(4, 6),
    )


def _run(**overrides):
    args = _args(); args.update(overrides)
    return N.verified_nonnormal_edge_disconnection_spectral_rank(**args)


def test_nonnormal_directed_disconnection_preserves_robust_rank_six() -> None:
    result = _run()
    assert not result.disconnected_operator_is_normal
    assert result.nominal_fixed_circle_rank == 6
    assert result.fixed_circle_rank_preservation_admitted
    assert result.robust_candidate_band_verified
    assert not result.eigenvalue_distance_only_certificate_admitted


def test_exact_condition_resolvent_neumann_and_projector_bounds() -> None:
    result = _run()
    assert result.fixed_circle_spectral_gap == F(1, 4)
    assert result.eigenvector_condition_frobenius_squared == 64
    assert result.uniform_disconnected_resolvent_norm_upper == 32
    assert result.maximum_coupling_frobenius_squared == F(1, 10000)
    assert result.neumann_product_upper == F(8, 25)
    assert result.neumann_margin == F(17, 25)
    assert result.projector_perturbation_norm_upper == F(256, 17)


def test_normal_diagonal_reduction_also_passes_conservative_frobenius_gate() -> None:
    result = _run(
        disconnected_edge_mask=_zero(2), maximum_connected_edge_mask=_directed_edge(2),
        disconnected_eigenvalues=(0, 3), eigenvector_matrix=((1, 0), (0, 1)),
        edge_coupling_operator=_coupling(2, F(1, 10)), fixed_circle_radius=1,
        eigenvector_condition_frobenius_upper=2, maximum_coupling_norm_upper=F(1, 10),
        candidate_band=(0, 2),
    )
    assert result.disconnected_operator_is_normal
    assert result.neumann_product_upper == F(1, 5)
    assert result.fixed_circle_rank_preservation_admitted


def test_large_shear_defeats_eigenvalue_distance_only_intuition() -> None:
    result = _run(
        disconnected_edge_mask=_zero(2), maximum_connected_edge_mask=_directed_edge(2),
        disconnected_eigenvalues=(0, 3), eigenvector_matrix=_shear_basis(2, 20),
        edge_coupling_operator=_coupling(2, F(1, 100)), fixed_circle_radius=1,
        eigenvector_condition_frobenius_upper=402, maximum_coupling_norm_upper=F(1, 100),
        candidate_band=(0, 2),
    )
    assert result.fixed_circle_spectral_gap == 1
    assert result.neumann_product_upper == F(201, 50) > 1
    assert not result.fixed_circle_rank_preservation_admitted
    assert result.projector_perturbation_norm_upper is None


def test_neumann_equality_is_not_accepted() -> None:
    result = _run(
        disconnected_edge_mask=_zero(2), maximum_connected_edge_mask=_directed_edge(2),
        disconnected_eigenvalues=(0, 3), eigenvector_matrix=((1, 0), (0, 1)),
        edge_coupling_operator=_coupling(2, F(1, 2)), fixed_circle_radius=1,
        eigenvector_condition_frobenius_upper=2, maximum_coupling_norm_upper=F(1, 2),
        candidate_band=(0, 2),
    )
    assert result.neumann_product_upper == 1
    assert result.neumann_margin == 0
    assert not result.fixed_circle_rank_preservation_admitted


def test_spectral_scale_covariance_preserves_neumann_and_projector_outputs() -> None:
    original = _run()
    args = _args()
    args["disconnected_eigenvalues"] = tuple(3 * F(value) for value in args["disconnected_eigenvalues"])
    args["edge_coupling_operator"] = tuple(tuple(3 * F(value) for value in row) for row in args["edge_coupling_operator"])
    args["fixed_circle_radius"] = 3
    args["maximum_coupling_norm_upper"] = F(3, 100)
    scaled = N.verified_nonnormal_edge_disconnection_spectral_rank(**args)
    assert scaled.neumann_product_upper == original.neumann_product_upper
    assert scaled.projector_perturbation_norm_upper == original.projector_perturbation_norm_upper
    assert scaled.nominal_fixed_circle_rank == original.nominal_fixed_circle_rank


def test_directed_coupling_support_must_equal_added_edge_mask() -> None:
    with pytest.raises(ValueError, match="support"):
        _run(maximum_connected_edge_mask=_zero(7))
    with pytest.raises(ValueError, match="support"):
        _run(edge_coupling_operator=_zero(7))


def test_singular_basis_and_contour_equality_fail_closed() -> None:
    singular = [list(row) for row in _shear_basis(7)]; singular[1] = [0] * 7
    with pytest.raises(ValueError, match="invertible"):
        _run(eigenvector_matrix=tuple(tuple(row) for row in singular))
    with pytest.raises(ValueError, match="may not contain"):
        _run(fixed_circle_radius=3)


def test_underreported_condition_or_coupling_bound_fails_closed() -> None:
    with pytest.raises(ValueError, match="condition upper"):
        _run(eigenvector_condition_frobenius_upper=7)
    with pytest.raises(ValueError, match="coupling norm"):
        _run(maximum_coupling_norm_upper=F(1, 200))


def test_diagonalizable_branch_does_not_claim_defective_or_consciousness_result() -> None:
    result = _run()
    assert not result.defective_operator_branch_verified
    assert not result.consciousness_dimension_claim_admitted
