from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


for name in (
    "quantitative_graph_transform", "verified_rational_contour", "verified_interval_contour",
    "verified_interval_tightening", "verified_interval_residual", "verified_algebraic_riesz_projector",
    "verified_polynomial_spectral_projector_construction", "verified_complete_q_polynomial_factorization",
    "verified_characteristic_spectral_split_discovery", "verified_interval_characteristic_spectral_split",
    "verified_split_conformal_matrix_uncertainty_coverage",
):
    _load(name)
C = _load("verified_conformal_interval_characteristic_bridge")
S = sys.modules["verified_split_conformal_matrix_uncertainty_coverage"]
HASH = "c" * 64
LABELS = tuple(f"A[{i},{j}].{part}" for i in range(2) for j in range(2) for part in ("real", "imag"))


def _coverage(**overrides):
    scales = (F(1, 100),) * 8
    calibration = tuple(tuple(F(i, 2000) for _ in range(8)) for i in range(1, 20))
    args = dict(
        component_labels=LABELS, component_scales=scales,
        calibration_absolute_error_vectors=calibration,
        heldout_absolute_error_vectors=((0,) * 8,) * 20,
        miscoverage_alpha=F(1, 10), heldout_null_coverage_floor=F(4, 5),
        heldout_audit_alpha=F(1, 20), exchangeability_scope=S.EXCHANGEABILITY_SCOPE,
        heldout_sampling_kind=S.HELDOUT_SAMPLING_KIND, provenance_status=S.SYNTHETIC_FIXTURE,
        calibration_data_sha256=HASH, heldout_data_sha256=HASH, coverage_contract_sha256=HASH,
    )
    args.update(overrides)
    return S.verified_split_conformal_matrix_uncertainty_coverage(**args)


def _run(**overrides):
    args = dict(
        coverage_certificate=_coverage(), center=0, radius=2, spectral_reference_scale=1,
        maximum_partitions=1024, maximum_factor_candidate_value_tuples=1_000_000,
        nodes=4, sqrt_precision=48,
    )
    args.update(overrides)
    return C.verified_conformal_interval_characteristic_bridge(((0, 0), (0, 10)), **args)


def test_complete_conformal_family_composes_with_interval_rank() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.conditional_covered_family_rank == 1
    assert result.conformal_coverage_and_interval_rank_composed
    assert result.conditional_simultaneous_matrix_coverage_lower == F(9, 10)


def test_flat_component_radii_are_reshaped_exactly() -> None:
    result = _run()
    expected = F(9, 1000)
    assert result.conformal_uncertainty_radii == (((expected, expected), (expected, expected)),) * 2


def test_incomplete_or_reordered_component_family_fails_closed() -> None:
    incomplete = _coverage(component_labels=LABELS[:-1], component_scales=(F(1, 100),) * 7,
        calibration_absolute_error_vectors=((0,) * 7,) * 19, heldout_absolute_error_vectors=((0,) * 7,) * 20)
    result = _run(coverage_certificate=incomplete)
    assert "CONFORMAL_INTERVAL_BRIDGE_COMPONENT_FAMILY_INCOMPLETE_OR_UNORDERED" in result.failure_codes


def test_failed_coverage_certificate_is_not_promoted() -> None:
    failed = _coverage(heldout_absolute_error_vectors=((10,) * 8,) * 20)
    result = _run(coverage_certificate=failed)
    assert "CONFORMAL_INTERVAL_BRIDGE_COVERAGE_NOT_VALIDATED" in result.failure_codes


def test_interval_margin_failure_is_not_hidden() -> None:
    large = tuple(tuple(F(i, 2) for _ in range(8)) for i in range(1, 20))
    result = _run(coverage_certificate=_coverage(calibration_absolute_error_vectors=large))
    assert "CONFORMAL_INTERVAL_BRIDGE_IVSPEC_FAILED" in result.failure_codes


def test_scale_covariance_preserves_normalized_rank() -> None:
    base = _run()
    scaled = C.verified_conformal_interval_characteristic_bridge(
        ((0, 0), (0, 70)), coverage_certificate=_coverage(component_scales=(F(7, 100),) * 8),
        center=0, radius=14, spectral_reference_scale=7,
    )
    assert scaled.validation_level is not None
    assert scaled.conditional_covered_family_rank == base.conditional_covered_family_rank


def test_external_empirical_and_consciousness_claims_remain_false() -> None:
    result = _run()
    assert not result.external_source_receipt_verified
    assert not result.source_locked_empirical_rank_result
    assert not result.consciousness_claim_admitted
    assert not result.dimension_4_6_claim_admitted
