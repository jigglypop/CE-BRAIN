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
D = _load("verified_edge_disconnection_spectral_rank", "verified_edge_disconnection_spectral_rank.py")


def _zero(size: int):
    return tuple(tuple(0 for _ in range(size)) for _ in range(size))


def _one_edge_adjacency(size: int):
    rows = [list(row) for row in _zero(size)]
    rows[0][1] = rows[1][0] = 1
    return tuple(tuple(row) for row in rows)


def _coupling(size: int, value):
    rows = [list(row) for row in _zero(size)]
    rows[0][1] = rows[1][0] = value
    return tuple(tuple(row) for row in rows)


def _basis(size: int):
    rows = [list(row) for row in _zero(size)]
    rows[0][0], rows[0][1] = F(3, 5), F(-4, 5)
    rows[1][0], rows[1][1] = F(4, 5), F(3, 5)
    for i in range(2, size):
        rows[i][i] = 1
    return tuple(tuple(row) for row in rows)


def _stable_args():
    size = 7
    return dict(
        disconnected_adjacency=_zero(size),
        connected_adjacency=_one_edge_adjacency(size),
        disconnected_eigenvalues=(F(7, 25), F(-7, 25), 0, 0, 0, 0, 5),
        edge_coupling_in_disconnected_eigenbasis=_coupling(size, F(-24, 25)),
        maximum_coupling_parameter=1,
        connected_eigenvalues=(-1, 1, 0, 0, 0, 0, 5),
        connected_eigenbasis_columns=_basis(size),
        fixed_contour_radius=2,
        candidate_band=(4, 6),
    )


def _crossing_args():
    return dict(
        disconnected_adjacency=_zero(2),
        connected_adjacency=_one_edge_adjacency(2),
        disconnected_eigenvalues=(F(14, 25), F(-14, 25)),
        edge_coupling_in_disconnected_eigenbasis=_coupling(2, F(-48, 25)),
        maximum_coupling_parameter=1,
        connected_eigenvalues=(-2, 2),
        connected_eigenbasis_columns=_basis(2),
        fixed_contour_radius=1,
        candidate_band=(4, 6),
    )


def _run(args=None, **overrides):
    values = _stable_args() if args is None else dict(args)
    values.update(overrides)
    return D.verified_edge_disconnection_spectral_rank(**values)


def test_topological_disconnection_can_preserve_robust_six_mode_rank() -> None:
    result = _run()
    assert result.topological_disconnection_verified
    assert result.connected_adjacency_components == 6
    assert result.disconnected_adjacency_components == 7
    assert result.connected_fixed_contour_rank == result.disconnected_fixed_contour_rank == 6
    assert result.fixed_contour_rank_preservation_admitted
    assert result.robust_candidate_band_verified


def test_strict_frobenius_gap_budget_is_exact() -> None:
    result = _run()
    assert result.disconnected_spectral_gap == F(43, 25)
    assert result.coupling_frobenius_norm_squared == F(1152, 625)
    assert result.robust_gap_squared == F(697, 625) > 0
    assert result.strict_uniform_no_crossing_bound_verified


def test_endpoint_rank_change_requires_intermediate_contour_crossing() -> None:
    result = _run(_crossing_args())
    assert result.disconnected_fixed_contour_rank == 2
    assert result.connected_fixed_contour_rank == 0
    assert result.endpoint_rank_change_verified
    assert result.intermediate_contour_crossing_mathematically_required
    assert not result.crossing_location_computed
    assert not result.fixed_contour_rank_preservation_admitted


def test_failed_gap_bound_with_equal_endpoint_rank_remains_unresolved() -> None:
    args = _stable_args()
    args.update(
        disconnected_adjacency=_zero(2), connected_adjacency=_one_edge_adjacency(2),
        disconnected_eigenvalues=(F(7, 25), F(-7, 25)),
        edge_coupling_in_disconnected_eigenbasis=_coupling(2, F(-24, 25)),
        connected_eigenvalues=(-1, 1), connected_eigenbasis_columns=_basis(2),
        fixed_contour_radius=F(6, 5), candidate_band=(0, 2),
    )
    result = _run(args)
    assert result.disconnected_fixed_contour_rank == result.connected_fixed_contour_rank == 2
    assert not result.strict_uniform_no_crossing_bound_verified
    assert result.status == "VERIFIED_DISCONNECTION_SPECTRAL_GAP_UNRESOLVED"


def test_spectral_scale_covariance_preserves_all_decisions() -> None:
    original = _run()
    args = _stable_args()
    args["disconnected_eigenvalues"] = tuple(3 * F(value) for value in args["disconnected_eigenvalues"])
    args["connected_eigenvalues"] = tuple(3 * F(value) for value in args["connected_eigenvalues"])
    args["edge_coupling_in_disconnected_eigenbasis"] = tuple(tuple(3 * F(value) for value in row) for row in args["edge_coupling_in_disconnected_eigenbasis"])
    args["fixed_contour_radius"] = 6
    scaled = _run(args)
    assert scaled.disconnected_fixed_contour_rank == original.disconnected_fixed_contour_rank
    assert scaled.robust_gap_squared == 9 * original.robust_gap_squared
    assert scaled.robust_candidate_band_verified


def test_wrong_connected_eigenwitness_fails_closed() -> None:
    eigenvalues = list(_stable_args()["connected_eigenvalues"])
    eigenvalues[0] = -2
    with pytest.raises(ValueError, match="does not diagonalize"):
        _run(connected_eigenvalues=tuple(eigenvalues))
    bad_basis = [list(row) for row in _basis(7)]; bad_basis[0][0] = 1
    with pytest.raises(ValueError, match="orthonormal"):
        _run(connected_eigenbasis_columns=tuple(tuple(row) for row in bad_basis))


def test_endpoint_eigenvalue_on_fixed_contour_is_rejected() -> None:
    with pytest.raises(ValueError, match="may not contain"):
        _run(fixed_contour_radius=5)


def test_operator_coupling_must_match_removed_adjacency_edges() -> None:
    with pytest.raises(ValueError, match="correspond"):
        _run(connected_adjacency=_zero(7))
    with pytest.raises(ValueError, match="needs a nonzero"):
        _run(edge_coupling_in_disconnected_eigenbasis=_zero(7))


def test_invalid_adjacency_fails_closed() -> None:
    bad = [list(row) for row in _one_edge_adjacency(7)]; bad[0][1] = 2
    with pytest.raises(ValueError, match="binary"):
        _run(connected_adjacency=tuple(tuple(row) for row in bad))
    bad = [list(row) for row in _one_edge_adjacency(7)]; bad[1][0] = 0
    with pytest.raises(ValueError, match="symmetric"):
        _run(connected_adjacency=tuple(tuple(row) for row in bad))


def test_topological_change_never_directly_becomes_consciousness_rank_claim() -> None:
    result = _run()
    assert result.topological_disconnection_verified
    assert not result.topological_disconnection_causes_rank_change_claim_admitted
    assert not result.consciousness_dimension_claim_admitted
