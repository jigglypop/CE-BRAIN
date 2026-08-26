from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("quantitative_graph_transform")
C = _load("verified_split_conformal_matrix_uncertainty_coverage")
HASH = "a" * 64


def _run(**overrides):
    calibration = tuple((F(i, 10), F(i, 5), F(3 * i, 10)) for i in range(1, 20))
    heldout = tuple((1, 2, 3) for _ in range(20))
    args = dict(
        component_labels=("A00.real", "A00.imag", "A01.real"),
        component_scales=(1, 2, 3),
        calibration_absolute_error_vectors=calibration,
        heldout_absolute_error_vectors=heldout,
        miscoverage_alpha=F(1, 10),
        heldout_null_coverage_floor=F(4, 5),
        heldout_audit_alpha=F(1, 20),
        exchangeability_scope=C.EXCHANGEABILITY_SCOPE,
        heldout_sampling_kind=C.HELDOUT_SAMPLING_KIND,
        provenance_status=C.SYNTHETIC_FIXTURE,
        calibration_data_sha256=HASH, heldout_data_sha256=HASH,
        coverage_contract_sha256=HASH,
    )
    args.update(overrides)
    return C.verified_split_conformal_matrix_uncertainty_coverage(**args)


def test_exact_max_score_quantile_and_simultaneous_radii() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.conformal_order_index == 18
    assert result.finite_sample_coverage_lower == F(9, 10)
    assert result.conformal_score_threshold == F(9, 5)
    assert result.simultaneous_component_radii == (F(9, 5), F(18, 5), F(27, 5))


def test_max_score_means_whole_component_family_is_covered_together() -> None:
    result = _run()
    assert result.simultaneous_family_coverage_verified_conditionally
    assert result.heldout_covered_count == 20
    assert result.heldout_empirical_coverage == 1


def test_exact_binomial_undercoverage_audit_rejects_floor() -> None:
    result = _run()
    assert result.heldout_undercoverage_audit_p_upper == F(4, 5) ** 20
    assert result.heldout_undercoverage_falsifier_rejected


def test_heldout_undercoverage_fails_closed() -> None:
    result = _run(heldout_absolute_error_vectors=((100, 200, 300),) * 20)
    assert result.validation_level is None
    assert "CONFORMAL_COVERAGE_HELDOUT_UNDERCOVERAGE_FALSIFIER_NOT_REJECTED" in result.failure_codes


def test_calibration_count_must_support_requested_alpha() -> None:
    result = _run(
        calibration_absolute_error_vectors=((1, 2, 3),) * 9,
        miscoverage_alpha=F(1, 100),
    )
    assert result.validation_level is None
    assert "CONFORMAL_COVERAGE_CALIBRATION_COUNT_TOO_SMALL_FOR_ALPHA" in result.failure_codes


def test_exchangeability_and_heldout_sampling_contracts_are_separate() -> None:
    exchange = _run(exchangeability_scope="TIME_SERIES_ASSUMED_IID_POST_HOC")
    audit = _run(heldout_sampling_kind="DEPENDENT_WINDOWS")
    assert "CONFORMAL_COVERAGE_EXCHANGEABILITY_SCOPE_MISMATCH" in exchange.failure_codes
    assert "CONFORMAL_COVERAGE_HELDOUT_SAMPLING_KIND_MISMATCH" in audit.failure_codes


def test_source_locked_label_is_not_an_external_receipt() -> None:
    result = _run(provenance_status=C.SOURCE_LOCKED_EMPIRICAL)
    assert result.validation_level is not None
    assert result.external_source_receipt_verified is False
    assert result.source_locked_empirical_coverage_result is False


def test_scale_covariance_preserves_scores_and_rescales_radii() -> None:
    base = _run()
    # Supply the scaled raw vectors explicitly; score thresholds must be invariant.
    calibration = tuple((F(7 * i, 10), F(7 * i, 5), F(21 * i, 10)) for i in range(1, 20))
    heldout = ((7, 14, 21),) * 20
    scaled = _run(component_scales=(7, 14, 21), calibration_absolute_error_vectors=calibration, heldout_absolute_error_vectors=heldout)
    assert scaled.conformal_score_threshold == base.conformal_score_threshold
    assert scaled.simultaneous_component_radii == tuple(7 * value for value in base.simultaneous_component_radii)


def test_invalid_schema_probabilities_hashes_and_float_fail_closed() -> None:
    with pytest.raises(ValueError, match="unique"):
        _run(component_labels=("x", "x", "y"))
    with pytest.raises(ValueError, match="below"):
        _run(heldout_null_coverage_floor=F(9, 10))
    with pytest.raises(ValueError, match="SHA-256"):
        _run(calibration_data_sha256="bad")
    with pytest.raises(ValueError):
        _run(miscoverage_alpha=0.1)


def test_consciousness_and_dimension_claims_remain_false() -> None:
    result = _run()
    assert not result.consciousness_claim_admitted
    assert not result.dimension_4_6_claim_admitted
