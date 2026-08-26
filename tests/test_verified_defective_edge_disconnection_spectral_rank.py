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


_load("verified_rational_contour", "verified_rational_contour.py")
_load("verified_interval_contour", "verified_interval_contour.py")
_load("verified_interval_tightening", "verified_interval_tightening.py")
_load("verified_interval_residual", "verified_interval_residual.py")
_load("verified_algebraic_riesz_projector", "verified_algebraic_riesz_projector.py")
_load("verified_edge_metric_effective_dimension", "verified_edge_metric_effective_dimension.py")
_load("verified_nonnormal_edge_disconnection_spectral_rank", "verified_nonnormal_edge_disconnection_spectral_rank.py")
D = _load("verified_defective_edge_disconnection_spectral_rank", "verified_defective_edge_disconnection_spectral_rank.py")


def _zero(size: int):
    return tuple(tuple(0 for _ in range(size)) for _ in range(size))


def _directed_edge(size: int):
    rows = [list(row) for row in _zero(size)]; rows[0][-1] = 1
    return tuple(tuple(row) for row in rows)


def _coupling(size: int, value):
    rows = [list(row) for row in _zero(size)]; rows[0][-1] = value
    return tuple(tuple(row) for row in rows)


def _transition(scale=1):
    rows = [list(row) for row in _zero(7)]
    rows[0][1] = scale
    rows[6][6] = 4 * scale
    return tuple(tuple(row) for row in rows)


def _projector():
    return tuple(tuple(1 if i == j and i < 6 else 0 for j in range(7)) for i in range(7))


def _exterior_inverse(scale=1):
    rows = [list(row) for row in _zero(7)]; rows[6][6] = F(1, 4 * scale)
    return tuple(tuple(row) for row in rows)


def _args():
    return dict(
        nominal_disconnected_transition=_transition(),
        disconnected_edge_mask=_zero(7),
        maximum_connected_edge_mask=_directed_edge(7),
        edge_coupling_operator=_coupling(7, F(1, 100)),
        maximum_coupling_parameter=1,
        normalized_maximum_coupling_norm_upper=F(1, 100),
        projector=_projector(),
        exterior_centered_inverse=_exterior_inverse(),
        center=0,
        radius=2,
        spectral_reference_scale=1,
        candidate_band=(4, 6),
        sqrt_precision=2,
    )


def _run(**overrides):
    args = _args(); args.update(overrides)
    return D.verified_defective_edge_disconnection_spectral_rank(**args)


def test_defective_jordan_block_directed_edge_preserves_rank_six() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.nominal_fixed_circle_rank == 6
    assert result.defective_operator_admitted
    assert result.fixed_circle_rank_preservation_admitted
    assert result.robust_candidate_band_verified
    assert not result.diagonalization_witness_required


def test_exact_algebraic_resolvent_neumann_and_projector_bounds() -> None:
    result = _run()
    assert result.inside_gap_lower == 1
    assert result.exterior_reciprocal_gap_lower == F(1, 2)
    assert result.projector_norm_upper == 1
    assert result.disconnected_resolvent_norm_upper == F(3, 2)
    assert result.neumann_product_upper == F(3, 200)
    assert result.neumann_margin == F(197, 200)
    assert result.projector_perturbation_norm_upper == F(9, 197)


def test_neumann_equality_fails_closed_without_claiming_crossing() -> None:
    result = _run(
        edge_coupling_operator=_coupling(7, F(2, 3)),
        normalized_maximum_coupling_norm_upper=F(2, 3),
    )
    assert result.neumann_product_upper == 1
    assert result.validation_level is None
    assert "DEFECTIVE_EDGE_NEUMANN_MARGIN_NONPOSITIVE" in result.failure_codes
    assert not result.eigenvalue_distance_only_certificate_admitted


def test_invalid_algebraic_projector_is_propagated_fail_closed() -> None:
    bad = [list(row) for row in _projector()]; bad[0][0] = F(1, 2)
    result = _run(projector=tuple(tuple(row) for row in bad))
    assert result.validation_level is None
    assert "ALGEBRAIC_PROJECTOR_NOT_IDEMPOTENT" in result.failure_codes


def test_directed_support_must_match_added_edge() -> None:
    with pytest.raises(ValueError, match="support"):
        _run(maximum_connected_edge_mask=_zero(7))
    with pytest.raises(ValueError, match="support"):
        _run(edge_coupling_operator=_zero(7))


def test_underreported_coupling_upper_fails_closed() -> None:
    with pytest.raises(ValueError, match="underreports"):
        _run(normalized_maximum_coupling_norm_upper=F(1, 200))


def test_spectral_scale_covariance_preserves_normalized_certificate() -> None:
    base = _run()
    scaled = _run(
        nominal_disconnected_transition=_transition(5),
        edge_coupling_operator=_coupling(7, F(1, 20)),
        exterior_centered_inverse=_exterior_inverse(),
        radius=10,
        spectral_reference_scale=5,
    )
    assert scaled.disconnected_resolvent_norm_upper == base.disconnected_resolvent_norm_upper
    assert scaled.neumann_product_upper == base.neumann_product_upper
    assert scaled.projector_perturbation_norm_upper == base.projector_perturbation_norm_upper


def test_zero_and_full_candidate_boundary_ranks_remain_algebraically_available() -> None:
    result = _run(candidate_band=(6, 6))
    assert result.robust_candidate_band_verified
    outside = _run(candidate_band=(0, 5))
    assert outside.fixed_circle_rank_preservation_admitted
    assert not outside.robust_candidate_band_verified


def test_bad_scale_radius_and_candidate_band_fail_closed() -> None:
    with pytest.raises(ValueError):
        _run(spectral_reference_scale=0)
    with pytest.raises(ValueError):
        _run(radius=0)
    with pytest.raises(ValueError, match="candidate_band"):
        _run(candidate_band=(6, 4))


def test_empirical_and_consciousness_claims_remain_false() -> None:
    result = _run()
    assert not result.empirical_operator_provenance_verified
    assert not result.consciousness_dimension_claim_admitted
