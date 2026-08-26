from __future__ import annotations

import hashlib
import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module); return module


DSIGN_TEST = _load_path(
    "signed_dimension_test_fixtures_for_cidisc",
    ROOT / "tests" / "test_verified_dimension_signed_acquisition_receipt.py",
)
CIDISC_TEST = _load_path(
    "conformal_idisc_test_fixtures_for_signed_receipt",
    ROOT / "tests" / "test_verified_conformal_interval_defective_edge_disconnection_spectral_rank.py",
)
S = _load_path(
    "verified_signed_conformal_interval_defective_edge_rank",
    MODULE_DIR / "verified_signed_conformal_interval_defective_edge_rank.py",
)


SEED = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc4" "4449c5697b326919703bac031cae7f60")


def _signed_args(**base_overrides):
    args = CIDISC_TEST._args(); args.update(base_overrides)
    args.pop("calibration_data_sha256"); args.pop("heldout_data_sha256")
    args.pop("coverage_contract_sha256")
    contract = b"synthetic-cidisc-coverage-contract-v1"
    calibration_bytes = S.canonical_exact_error_vectors_bytes(
        vector_role="calibration", component_labels=args["component_labels"],
        component_scales=args["component_scales"],
        absolute_error_vectors=args["calibration_absolute_error_vectors"],
    )
    heldout_bytes = S.canonical_exact_error_vectors_bytes(
        vector_role="heldout", component_labels=args["component_labels"],
        component_scales=args["component_scales"],
        absolute_error_vectors=args["heldout_absolute_error_vectors"],
    )
    calibration_hash = hashlib.sha256(calibration_bytes).hexdigest()
    heldout_hash = hashlib.sha256(heldout_bytes).hexdigest()
    contract_hash = hashlib.sha256(contract).hexdigest()
    key_id = "synthetic-cidisc-rfc8032-fixture"
    message = S.canonical_signed_coverage_message(
        calibration_data_sha256=calibration_hash,
        heldout_data_sha256=heldout_hash,
        coverage_contract_sha256=contract_hash,
        signer_key_id=key_id,
    )
    public_key, signature = DSIGN_TEST._sign_fixture(SEED, message)
    args.update(
        coverage_contract_bytes=contract,
        expected_calibration_data_sha256=calibration_hash,
        expected_heldout_data_sha256=heldout_hash,
        expected_coverage_contract_sha256=contract_hash,
        signer_key_id=key_id,
        signer_ed25519_public_key=public_key,
        expected_signer_public_key_sha256=hashlib.sha256(public_key).hexdigest(),
        detached_ed25519_signature=signature,
    )
    return args


def _run(**overrides):
    args = _signed_args(); args.update(overrides)
    return S.verified_signed_conformal_interval_defective_edge_rank(**args)


def test_canonical_exact_vector_codec_is_deterministic_and_role_separated() -> None:
    args = _signed_args()
    cal = S.canonical_exact_error_vectors_bytes(
        vector_role="calibration", component_labels=args["component_labels"],
        component_scales=args["component_scales"],
        absolute_error_vectors=args["calibration_absolute_error_vectors"],
    )
    assert cal == S.canonical_exact_error_vectors_bytes(
        vector_role="calibration", component_labels=args["component_labels"],
        component_scales=args["component_scales"],
        absolute_error_vectors=args["calibration_absolute_error_vectors"],
    )
    held = S.canonical_exact_error_vectors_bytes(
        vector_role="heldout", component_labels=args["component_labels"],
        component_scales=args["component_scales"],
        absolute_error_vectors=args["calibration_absolute_error_vectors"],
    )
    assert cal != held


def test_signed_content_bundle_executes_conformal_interval_rank_six_chain() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.content_hashes_match_expected
    assert result.strict_ed25519_signature_verified
    assert result.cryptographic_coverage_bundle_verified
    rank = result.conformal_rank_certificate.interval_rank_certificate.fixed_circle_rank
    assert rank == 6


def test_calibration_mutation_breaks_hash_and_signature_before_execution() -> None:
    args = _signed_args()
    changed = list(args["calibration_absolute_error_vectors"])
    changed[0] = (F(1, 199), F(1, 500))
    result = _run(calibration_absolute_error_vectors=tuple(changed))
    assert result.validation_level is None
    assert "SIGNED_CIDISC_CONTENT_HASH_MISMATCH" in result.failure_codes
    assert result.conformal_rank_certificate is None


def test_heldout_and_contract_mutations_fail_closed() -> None:
    held = list(_signed_args()["heldout_absolute_error_vectors"]); held[0] = (1, 1)
    assert _run(heldout_absolute_error_vectors=tuple(held)).validation_level is None
    assert _run(coverage_contract_bytes=b"mutated-contract").validation_level is None


def test_signer_fingerprint_mismatch_fails_before_rank_execution() -> None:
    result = _run(expected_signer_public_key_sha256="0" * 64)
    assert "SIGNED_CIDISC_SIGNER_KEY_FINGERPRINT_MISMATCH" in result.failure_codes
    assert result.conformal_rank_certificate is None


def test_signature_and_key_id_domain_mutations_fail_closed() -> None:
    signature = bytearray(_signed_args()["detached_ed25519_signature"]); signature[0] ^= 1
    assert "SIGNED_CIDISC_ED25519_SIGNATURE_INVALID" in _run(detached_ed25519_signature=bytes(signature)).failure_codes
    assert "SIGNED_CIDISC_ED25519_SIGNATURE_INVALID" in _run(signer_key_id="other-key").failure_codes


def test_validly_signed_undercoverage_still_fails_downstream() -> None:
    args = _signed_args(heldout_absolute_error_vectors=((1, 1),) * 20)
    result = S.verified_signed_conformal_interval_defective_edge_rank(**args)
    assert result.strict_ed25519_signature_verified
    assert result.validation_level is None
    assert "CONFORMAL_COVERAGE_HELDOUT_UNDERCOVERAGE_FALSIFIER_NOT_REJECTED" in result.failure_codes


def test_float_negative_and_noncanonical_text_inputs_fail_codec() -> None:
    args = _signed_args()
    with pytest.raises(ValueError):
        S.canonical_exact_error_vectors_bytes(
            vector_role="calibration", component_labels=args["component_labels"],
            component_scales=args["component_scales"], absolute_error_vectors=((0.1, 0),),
        )
    with pytest.raises(ValueError, match="nonnegative"):
        S.canonical_exact_error_vectors_bytes(
            vector_role="calibration", component_labels=args["component_labels"],
            component_scales=args["component_scales"], absolute_error_vectors=((-1, 0),),
        )


def test_source_locked_label_does_not_establish_external_trust_or_empirical_rank() -> None:
    result = S.verified_signed_conformal_interval_defective_edge_rank(
        **_signed_args(provenance_status=CIDISC_TEST.COV.SOURCE_LOCKED_EMPIRICAL)
    )
    assert result.cryptographic_coverage_bundle_verified
    assert not result.externally_frozen_trust_anchor_verified
    assert not result.device_native_error_converter_verified
    assert not result.source_locked_empirical_rank_result


def test_consciousness_claim_remains_false() -> None:
    assert not _run().consciousness_dimension_claim_admitted
