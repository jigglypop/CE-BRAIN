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
_load("verified_defective_edge_disconnection_spectral_rank", "verified_defective_edge_disconnection_spectral_rank.py")
I = _load("verified_interval_defective_edge_disconnection_spectral_rank", "verified_interval_defective_edge_disconnection_spectral_rank.py")


def _zero(n): return tuple(tuple(0 for _ in range(n)) for _ in range(n))


def _entry(n, i, j, value):
    rows = [list(row) for row in _zero(n)]; rows[i][j] = value
    return tuple(tuple(row) for row in rows)


def _transition(scale=1):
    rows = [list(row) for row in _zero(7)]; rows[0][1] = scale; rows[6][6] = 4 * scale
    return tuple(tuple(row) for row in rows)


def _projector():
    return tuple(tuple(1 if i == j and i < 6 else 0 for j in range(7)) for i in range(7))


def _inverse(): return _entry(7, 6, 6, F(1, 4))


def _args():
    return dict(
        nominal_disconnected_transition=_transition(),
        disconnected_edge_mask=_zero(7),
        maximum_connected_edge_mask=_entry(7, 0, 6, 1),
        edge_coupling_operator=_entry(7, 0, 6, F(1, 100)),
        maximum_coupling_parameter=1,
        normalized_maximum_coupling_norm_upper=F(1, 100),
        baseline_operator_uncertainty_radius=_entry(7, 2, 2, F(1, 200)),
        normalized_baseline_uncertainty_norm_upper=F(1, 200),
        edge_coupling_uncertainty_radius=_entry(7, 0, 6, F(1, 500)),
        normalized_maximum_coupling_uncertainty_norm_upper=F(1, 500),
        projector=_projector(), exterior_centered_inverse=_inverse(),
        center=0, radius=2, spectral_reference_scale=1,
        candidate_band=(4, 6), sqrt_precision=2,
    )


def _run(**overrides):
    args = _args(); args.update(overrides)
    return I.verified_interval_defective_edge_disconnection_spectral_rank(**args)


def test_entire_interval_defective_family_preserves_rank_six() -> None:
    result = _run()
    assert result.entire_interval_family_rank_preserved
    assert result.fixed_circle_rank == 6
    assert result.robust_candidate_band_verified


def test_exact_total_neumann_margin_and_projector_bound() -> None:
    result = _run()
    assert result.total_family_perturbation_norm_upper == F(17, 1000)
    assert result.interval_neumann_product_upper == F(51, 2000)
    assert result.interval_neumann_margin == F(1949, 2000)
    assert result.interval_projector_perturbation_norm_upper == F(153, 1949)


def test_zero_uncertainty_reduces_to_nominal_certificate() -> None:
    result = _run(
        baseline_operator_uncertainty_radius=_zero(7),
        normalized_baseline_uncertainty_norm_upper=0,
        edge_coupling_uncertainty_radius=_zero(7),
        normalized_maximum_coupling_uncertainty_norm_upper=0,
    )
    nominal = result.nominal_certificate
    assert result.total_family_perturbation_norm_upper == nominal.normalized_maximum_coupling_norm_upper
    assert result.interval_neumann_product_upper == nominal.neumann_product_upper


def test_interval_neumann_equality_fails_closed() -> None:
    result = _run(
        baseline_operator_uncertainty_radius=_entry(7, 2, 2, F(197, 300)),
        normalized_baseline_uncertainty_norm_upper=F(197, 300),
        edge_coupling_uncertainty_radius=_zero(7),
        normalized_maximum_coupling_uncertainty_norm_upper=0,
    )
    assert result.total_family_perturbation_norm_upper == F(2, 3)
    assert result.interval_neumann_product_upper == 1
    assert result.validation_level is None


def test_coupling_uncertainty_cannot_escape_directed_intervention_support() -> None:
    with pytest.raises(ValueError, match="support"):
        _run(edge_coupling_uncertainty_radius=_entry(7, 1, 2, F(1, 500)))
    with pytest.raises(ValueError, match="support"):
        _run(edge_coupling_uncertainty_radius=_entry(7, 0, 0, F(1, 500)))


def test_underreported_interval_norms_fail_closed() -> None:
    with pytest.raises(ValueError, match="baseline uncertainty"):
        _run(normalized_baseline_uncertainty_norm_upper=F(1, 201))
    with pytest.raises(ValueError, match="coupling uncertainty"):
        _run(normalized_maximum_coupling_uncertainty_norm_upper=F(1, 501))


def test_negative_or_inexact_radius_entries_fail_closed() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        _run(baseline_operator_uncertainty_radius=_entry(7, 2, 2, F(-1, 200)))
    with pytest.raises(ValueError):
        _run(edge_coupling_uncertainty_radius=_entry(7, 0, 6, 0.002))


def test_spectral_scale_covariance() -> None:
    base = _run()
    scaled = _run(
        nominal_disconnected_transition=_transition(5),
        edge_coupling_operator=_entry(7, 0, 6, F(1, 20)),
        baseline_operator_uncertainty_radius=_entry(7, 2, 2, F(1, 40)),
        edge_coupling_uncertainty_radius=_entry(7, 0, 6, F(1, 100)),
        radius=10, spectral_reference_scale=5,
    )
    assert scaled.total_family_perturbation_norm_upper == base.total_family_perturbation_norm_upper
    assert scaled.interval_neumann_product_upper == base.interval_neumann_product_upper
    assert scaled.interval_projector_perturbation_norm_upper == base.interval_projector_perturbation_norm_upper


def test_nominal_algebraic_failure_propagates() -> None:
    bad = [list(row) for row in _projector()]; bad[0][0] = F(1, 2)
    result = _run(projector=tuple(tuple(row) for row in bad))
    assert result.validation_level is None
    assert "ALGEBRAIC_PROJECTOR_NOT_IDEMPOTENT" in result.failure_codes


def test_empirical_coverage_replication_and_consciousness_remain_false() -> None:
    result = _run()
    assert not result.empirical_interval_coverage_verified
    assert not result.held_out_intervention_replication_verified
    assert not result.consciousness_dimension_claim_admitted
