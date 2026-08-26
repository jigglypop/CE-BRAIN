from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module); return module


_load("quantitative_graph_transform")
_load("verified_rational_contour"); _load("verified_interval_contour")
_load("verified_interval_tightening"); _load("verified_interval_residual")
_load("verified_algebraic_riesz_projector"); _load("verified_edge_metric_effective_dimension")
_load("verified_nonnormal_edge_disconnection_spectral_rank")
_load("verified_defective_edge_disconnection_spectral_rank")
_load("verified_interval_defective_edge_disconnection_spectral_rank")
COV = _load("verified_split_conformal_matrix_uncertainty_coverage")
C = _load("verified_conformal_interval_defective_edge_disconnection_spectral_rank")
HASH = "a" * 64


def _zero(n): return tuple(tuple(0 for _ in range(n)) for _ in range(n))
def _entry(n, i, j, x):
    a=[list(r) for r in _zero(n)]; a[i][j]=x; return tuple(tuple(r) for r in a)
def _transition(scale=1):
    a=[list(r) for r in _zero(7)]; a[0][1]=scale; a[6][6]=4*scale; return tuple(tuple(r) for r in a)
def _projector(): return tuple(tuple(1 if i==j and i<6 else 0 for j in range(7)) for i in range(7))


def _args():
    calibration=((F(1,200),F(1,500)),)*19
    heldout=((0,0),)*20
    return dict(
        nominal_disconnected_transition=_transition(),
        component_labels=("baseline[2,2]","coupling[0,6]"), component_scales=(F(1,200),F(1,500)),
        calibration_absolute_error_vectors=calibration, heldout_absolute_error_vectors=heldout,
        miscoverage_alpha=F(1,10), heldout_null_coverage_floor=F(4,5), heldout_audit_alpha=F(1,20),
        exchangeability_scope=COV.EXCHANGEABILITY_SCOPE, heldout_sampling_kind=COV.HELDOUT_SAMPLING_KIND,
        provenance_status=COV.SYNTHETIC_FIXTURE,
        calibration_data_sha256=HASH, heldout_data_sha256=HASH, coverage_contract_sha256=HASH,
        disconnected_edge_mask=_zero(7), maximum_connected_edge_mask=_entry(7,0,6,1),
        edge_coupling_operator=_entry(7,0,6,F(1,100)), maximum_coupling_parameter=1,
        normalized_maximum_coupling_norm_upper=F(1,100), projector=_projector(),
        exterior_centered_inverse=_entry(7,6,6,F(1,4)), center=0, radius=2,
        spectral_reference_scale=1, candidate_band=(4,6), sqrt_precision=2,
    )


def _run(**kw):
    a=_args(); a.update(kw); return C.verified_conformal_interval_defective_edge_disconnection_spectral_rank(**a)


def test_split_conformal_radii_compose_to_rank_six_interval_gate():
    r=_run(); assert r.validation_level is not None
    assert r.simultaneous_coverage_lower==F(9,10)
    assert r.baseline_radius_matrix[2][2]==F(1,200)
    assert r.coupling_radius_matrix[0][6]==F(1,500)
    assert r.interval_rank_certificate.fixed_circle_rank==6
    assert r.conditional_simultaneous_rank_coverage_admitted


def test_composed_exact_neumann_outputs_match_idisc_fixture():
    r=_run().interval_rank_certificate
    assert r.total_family_perturbation_norm_upper==F(17,1000)
    assert r.interval_neumann_product_upper==F(51,2000)
    assert r.interval_projector_perturbation_norm_upper==F(153,1949)


def test_undercoverage_falsifier_failure_propagates():
    r=_run(heldout_absolute_error_vectors=((1,1),)*20)
    assert r.validation_level is None
    assert "CONFORMAL_COVERAGE_HELDOUT_UNDERCOVERAGE_FALSIFIER_NOT_REJECTED" in r.failure_codes


def test_exchangeability_contract_failure_propagates():
    r=_run(exchangeability_scope="DEPENDENT_TIME_WINDOWS")
    assert r.validation_level is None
    assert "CONFORMAL_COVERAGE_EXCHANGEABILITY_SCOPE_MISMATCH" in r.failure_codes


def test_calibration_count_too_small_produces_no_interval_certificate():
    r=_run(calibration_absolute_error_vectors=((F(1,200),F(1,500)),)*9, miscoverage_alpha=F(1,100))
    assert r.validation_level is None and r.interval_rank_certificate is None


def test_bad_label_schema_duplicate_and_range_fail_closed():
    with pytest.raises(ValueError, match="must use"):
        _run(component_labels=("U22","coupling[0,6]"))
    with pytest.raises(ValueError, match="unique"):
        _run(component_labels=("baseline[2,2]","baseline[2,2]"))
    with pytest.raises(ValueError, match="exceeds"):
        _run(component_labels=("baseline[9,2]","coupling[0,6]"))


def test_coupling_label_outside_intervention_support_fails():
    with pytest.raises(ValueError, match="support"):
        _run(component_labels=("baseline[2,2]","coupling[1,2]"))


def test_source_locked_label_still_does_not_create_external_receipt():
    r=_run(provenance_status=COV.SOURCE_LOCKED_EMPIRICAL)
    assert r.validation_level is not None
    assert not r.external_source_receipt_verified
    assert not r.source_locked_empirical_rank_result


def test_spectral_scale_covariance_of_composition():
    base=_run().interval_rank_certificate
    scaled=_run(
        nominal_disconnected_transition=_transition(5),
        component_scales=(F(1,40),F(1,100)),
        calibration_absolute_error_vectors=((F(1,40),F(1,100)),)*19,
        edge_coupling_operator=_entry(7,0,6,F(1,20)), radius=10, spectral_reference_scale=5,
    ).interval_rank_certificate
    assert scaled.total_family_perturbation_norm_upper==base.total_family_perturbation_norm_upper
    assert scaled.interval_neumann_product_upper==base.interval_neumann_product_upper


def test_consciousness_claim_remains_false():
    r=_run(); assert not r.consciousness_dimension_claim_admitted
