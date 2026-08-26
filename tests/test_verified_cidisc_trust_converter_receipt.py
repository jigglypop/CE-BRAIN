from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load_path(name, path):
    spec=importlib.util.spec_from_file_location(name,path); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module
    spec.loader.exec_module(module); return module


S_TEST = _load_path(
    "signed_cidisc_test_fixtures_for_trust_receipt",
    ROOT / "tests" / "test_verified_signed_conformal_interval_defective_edge_rank.py",
)
T = _load_path(
    "verified_cidisc_trust_converter_receipt",
    MODULE_DIR / "verified_cidisc_trust_converter_receipt.py",
)


ROOT_SEED = bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f" "5b8a319f35aba624da8cf6ed4fb8a6fb")


def _args():
    certificate = S_TEST._run()
    signed_args = S_TEST._signed_args()
    coverage_key = signed_args["signer_ed25519_public_key"]
    anchor = T.canonical_cidisc_trust_anchor_message(
        institution_id="synthetic-neural-lab", root_key_id="synthetic-root-2026",
        coverage_signer_key_id=certificate.signer_key_id,
        coverage_signer_public_key=coverage_key,
        valid_from_date="2026-01-01", valid_until_date="2026-12-31",
    )
    root_key, root_signature = S_TEST.DSIGN_TEST._sign_fixture(ROOT_SEED, anchor)
    native_cal = b"synthetic-native-calibration-signal-v1"
    native_hold = b"synthetic-native-heldout-signal-v1"
    converter = b"synthetic-converter-binary-v1"
    contract = b"synthetic-native-to-error-contract-v1"
    converter_message = T.canonical_cidisc_converter_receipt_message(
        trust_anchor_message_sha256=hashlib.sha256(anchor).hexdigest(),
        native_calibration_sha256=hashlib.sha256(native_cal).hexdigest(),
        native_heldout_sha256=hashlib.sha256(native_hold).hexdigest(),
        converter_binary_sha256=hashlib.sha256(converter).hexdigest(),
        converter_contract_sha256=hashlib.sha256(contract).hexdigest(),
        canonical_calibration_output_sha256=certificate.calibration_canonical_bytes_sha256,
        canonical_heldout_output_sha256=certificate.heldout_canonical_bytes_sha256,
    )
    _, converter_signature = S_TEST.DSIGN_TEST._sign_fixture(S_TEST.SEED, converter_message)
    return dict(
        signed_cidisc_certificate=certificate,
        institution_id="synthetic-neural-lab", root_key_id="synthetic-root-2026",
        coverage_signer_key_id=certificate.signer_key_id,
        coverage_signer_public_key=coverage_key,
        valid_from_date="2026-01-01", valid_until_date="2026-12-31",
        evaluation_date="2026-08-26",
        root_ed25519_public_key=root_key,
        expected_root_public_key_sha256=hashlib.sha256(root_key).hexdigest(),
        root_detached_signature=root_signature,
        native_calibration_bytes=native_cal, native_heldout_bytes=native_hold,
        converter_binary_bytes=converter, converter_contract_bytes=contract,
        converter_detached_signature=converter_signature,
    )


def _run(**overrides):
    args=_args(); args.update(overrides); return T.verified_cidisc_trust_converter_receipt(**args)


def test_two_signature_trust_and_converter_content_chain_passes():
    r=_run(); assert r.validation_level is not None
    assert r.root_authorization_signature_verified
    assert r.coverage_key_matches_signed_cidisc
    assert r.converter_content_signature_verified
    assert r.two_signature_content_chain_verified


def test_validity_window_is_inclusive_and_expiry_fails():
    assert _run(evaluation_date="2026-01-01").trust_anchor_time_window_verified
    assert _run(evaluation_date="2026-12-31").trust_anchor_time_window_verified
    r=_run(evaluation_date="2027-01-01")
    assert r.validation_level is None
    assert "CIDISC_TRUST_ANCHOR_OUTSIDE_VALIDITY_WINDOW" in r.failure_codes


def test_root_fingerprint_mismatch_fails_closed():
    r=_run(expected_root_public_key_sha256="0"*64)
    assert "CIDISC_TRUST_ROOT_FINGERPRINT_MISMATCH" in r.failure_codes


def test_root_signature_and_manifest_mutations_fail_closed():
    signature=bytearray(_args()["root_detached_signature"]); signature[0]^=1
    assert "CIDISC_TRUST_ROOT_SIGNATURE_INVALID" in _run(root_detached_signature=bytes(signature)).failure_codes
    assert "CIDISC_TRUST_ROOT_SIGNATURE_INVALID" in _run(institution_id="other-lab").failure_codes


def test_coverage_key_id_or_key_mismatch_fails_chain():
    r=_run(coverage_signer_key_id="other-key")
    assert "CIDISC_TRUST_ROOT_SIGNATURE_INVALID" in r.failure_codes
    assert "CIDISC_TRUST_COVERAGE_KEY_CERTIFICATE_MISMATCH" in r.failure_codes


@pytest.mark.parametrize("field", [
    "native_calibration_bytes", "native_heldout_bytes",
    "converter_binary_bytes", "converter_contract_bytes",
])
def test_converter_bound_content_mutations_break_device_signature(field):
    r=_run(**{field:b"mutated"})
    assert "CIDISC_CONVERTER_CONTENT_SIGNATURE_INVALID" in r.failure_codes


def test_invalid_signed_cidisc_certificate_is_rejected():
    bad=S_TEST._run(expected_signer_public_key_sha256="0"*64)
    r=_run(signed_cidisc_certificate=bad)
    assert "CIDISC_TRUST_BASE_SIGNED_CERTIFICATE_FAILED" in r.failure_codes


def test_date_schema_and_empty_byte_fields_fail_closed():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        _run(evaluation_date="2026/08/26")
    with pytest.raises(ValueError, match="nonempty bytes"):
        _run(converter_binary_bytes=b"")
    with pytest.raises(ValueError, match="real Gregorian"):
        _run(evaluation_date="2026-99-99")


def test_external_distribution_execution_attestation_and_empirical_claims_remain_false():
    r=_run()
    assert not r.externally_distributed_root_fingerprint_verified
    assert not r.converter_execution_attested_by_hardware
    assert not r.source_locked_empirical_rank_result
    assert not r.consciousness_dimension_claim_admitted
