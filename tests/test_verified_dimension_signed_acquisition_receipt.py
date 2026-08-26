from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BYTE_TEST = _load_path(
    "dimension_source_bytes_test_fixtures",
    ROOT / "tests" / "test_verified_dimension_source_bytes_receipt.py",
)
S = _load_path(
    "verified_dimension_signed_acquisition_receipt",
    MODULE_DIR / "verified_dimension_signed_acquisition_receipt.py",
)


def _sign_fixture(seed: bytes, message: bytes):
    digest = hashlib.sha512(seed).digest()
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    public_key = S._point_compress(S._point_mul(scalar, S._BASE))
    nonce = int.from_bytes(hashlib.sha512(digest[32:] + message).digest(), "little") % S._L
    r_encoded = S._point_compress(S._point_mul(nonce, S._BASE))
    challenge = int.from_bytes(hashlib.sha512(r_encoded + public_key + message).digest(), "little") % S._L
    signature_scalar = (nonce + challenge * scalar) % S._L
    return public_key, r_encoded + signature_scalar.to_bytes(32, "little")


def _signed_args():
    args = BYTE_TEST._receipt_args()
    contract_hash = hashlib.sha256(b"synthetic-acquisition-contract-v1").hexdigest()
    signer_key_id = "synthetic-rfc8032-fixture-key"
    message = S.canonical_acquisition_signature_message(
        source_bundle_sha256=args["expected_source_bundle_sha256"],
        acquisition_contract_sha256=contract_hash,
        signer_key_id=signer_key_id,
    )
    public_key, signature = _sign_fixture(bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc4" "4449c5697b326919703bac031cae7f60"), message)
    args.update(
        acquisition_contract_sha256=contract_hash,
        signer_key_id=signer_key_id,
        trusted_ed25519_public_key=public_key,
        expected_trusted_public_key_sha256=hashlib.sha256(public_key).hexdigest(),
        detached_ed25519_signature=signature,
    )
    return args


def _run(**overrides):
    args = _signed_args(); args.update(overrides)
    return S.verified_dimension_signed_acquisition_receipt(**args)


def test_rfc8032_ed25519_test_vector_1() -> None:
    public_key = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a" "0ee172f3daa62325af021a68f707511a")
    signature = bytes.fromhex(
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
        "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
    )
    assert S.ed25519_verify_strict(public_key, b"", signature)


def test_rfc8032_ed25519_test_vector_2() -> None:
    public_key = bytes.fromhex("3d4017c3e843895a92b70aa74d1b7ebc" "9c982ccf2ec4968cc0cd55f12af4660c")
    signature = bytes.fromhex(
        "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
        "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"
    )
    assert S.ed25519_verify_strict(public_key, b"\x72", signature)


def test_ed25519_rejects_altered_message_and_signature() -> None:
    args = _signed_args()
    message = S.canonical_acquisition_signature_message(
        source_bundle_sha256=args["expected_source_bundle_sha256"],
        acquisition_contract_sha256=args["acquisition_contract_sha256"],
        signer_key_id=args["signer_key_id"],
    )
    signature = bytearray(args["detached_ed25519_signature"]); signature[0] ^= 1
    assert not S.ed25519_verify_strict(args["trusted_ed25519_public_key"], message + b"x", args["detached_ed25519_signature"])
    assert not S.ed25519_verify_strict(args["trusted_ed25519_public_key"], message, bytes(signature))


def test_ed25519_rejects_noncanonical_scalar() -> None:
    args = _signed_args()
    signature = args["detached_ed25519_signature"][:32] + S._L.to_bytes(32, "little")
    assert not S.ed25519_verify_strict(args["trusted_ed25519_public_key"], b"message", signature)


def test_ed25519_rejects_identity_public_key() -> None:
    identity_encoding = (1).to_bytes(32, "little")
    assert not S.ed25519_verify_strict(identity_encoding, b"", b"\x00" * 64)


def test_signed_bundle_executes_complete_source_chain() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.strict_ed25519_signature_verified
    assert result.cryptographic_bundle_signature_verified
    assert result.source_bytes_receipt.validation_level is not None


def test_frozen_bundle_mismatch_fails_before_source_execution() -> None:
    result = _run(expected_source_bundle_sha256="0" * 64)
    assert result.status == "DIMENSION_SIGNED_RECEIPT_BUNDLE_HASH_MISMATCH"
    assert result.source_bytes_receipt is None


def test_trusted_public_key_fingerprint_mismatch_fails_closed() -> None:
    result = _run(expected_trusted_public_key_sha256="0" * 64)
    assert "DIMENSION_SIGNED_RECEIPT_TRUSTED_KEY_FINGERPRINT_MISMATCH" in result.failure_codes


def test_signer_identity_is_cryptographically_bound() -> None:
    result = _run(signer_key_id="different-key-id")
    assert "DIMENSION_SIGNED_RECEIPT_ED25519_SIGNATURE_INVALID" in result.failure_codes


def test_signature_does_not_prove_external_trust_anchor_device_or_consciousness() -> None:
    result = _run()
    assert not result.externally_frozen_trust_anchor_verified
    assert not result.device_native_converter_receipt_verified
    assert not result.source_locked_empirical_dimension_result
    assert not result.consciousness_dimension_claim_admitted
