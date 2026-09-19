from __future__ import annotations

import copy
import json
from pathlib import Path
from importlib.metadata import distribution

from reality_stone.clarus.local_memory_verifier import (
    CANONICAL_TEXT_SHA256_SCHEME,
    build_verification_artifact,
    canonical_text_sha256,
    verify_confirmation,
)


ROOT = Path(__file__).resolve().parents[1]
PREREGISTRATION = ROOT / "artifacts/agi/local_memory_aml32_preregistration.json"
RESULT_PATHS = {
    1: ROOT / "artifacts/agi/local_memory_aml32_h1_confirmatory.json",
    6: ROOT / "artifacts/agi/local_memory_aml32_h6_confirmatory.json",
}
IMPLEMENTATION = (
    Path(distribution("reality_stone").locate_file("reality_stone/clarus/local_memory.py"))
)
PROOF = ROOT / "artifacts/agi/local_memory_aml32_proof.json"


def _inputs() -> tuple[dict[str, object], dict[int, dict[str, object]], str]:
    preregistration = json.loads(PREREGISTRATION.read_text(encoding="utf-8"))
    results = {
        horizon: json.loads(path.read_text(encoding="utf-8"))
        for horizon, path in RESULT_PATHS.items()
    }
    implementation_hash = canonical_text_sha256(IMPLEMENTATION)
    return preregistration, results, implementation_hash


def test_locked_confirmatory_artifacts_recompute_to_pass() -> None:
    preregistration, results, implementation_hash = _inputs()

    proof = verify_confirmation(
        preregistration,
        results,
        implementation_sha256=implementation_hash,
    )

    assert proof["proof_passed"]
    assert proof["errors"] == []


def test_tampered_threshold_is_rejected() -> None:
    preregistration, results, implementation_hash = _inputs()
    tampered = copy.deepcopy(results)
    tampered[1]["result"]["recordings"][0]["criteria"]["min_memory_delta"] = 0.0

    proof = verify_confirmation(
        preregistration,
        tampered,
        implementation_sha256=implementation_hash,
    )

    assert not proof["proof_passed"]
    assert any("criteria changed" in error for error in proof["errors"])


def test_tampered_implementation_hash_is_rejected() -> None:
    preregistration, results, _ = _inputs()

    proof = verify_confirmation(
        preregistration,
        results,
        implementation_sha256="0" * 64,
    )

    assert not proof["proof_passed"]
    assert "implementation hash differs from preregistration" in proof["errors"]


def test_implementation_lock_is_independent_of_checkout_newlines(tmp_path: Path) -> None:
    source = IMPLEMENTATION.read_text(encoding="utf-8").replace("\r\n", "\n")
    lf_path = tmp_path / "implementation_lf.py"
    crlf_path = tmp_path / "implementation_crlf.py"
    lf_path.write_bytes(source.encode("utf-8"))
    crlf_path.write_bytes(source.replace("\n", "\r\n").encode("utf-8"))

    assert canonical_text_sha256(lf_path) == canonical_text_sha256(crlf_path)
    assert canonical_text_sha256(lf_path) == _inputs()[2]


def test_proof_generator_records_canonical_cross_platform_hashes() -> None:
    proof = build_verification_artifact(
        PREREGISTRATION,
        RESULT_PATHS[1],
        RESULT_PATHS[6],
        IMPLEMENTATION,
    )

    assert proof["proof_passed"]
    assert proof["input_hash_scheme"] == CANONICAL_TEXT_SHA256_SCHEME
    assert proof["inputs"]["implementation"]["sha256"] == _inputs()[2]
    historical = json.loads(PROOF.read_text(encoding="utf-8"))
    # Relocation changes provenance, not implementation bytes or the old receipt.
    assert proof["inputs"]["implementation"]["path"] != historical["inputs"]["implementation"]["path"]
    assert proof["inputs"]["implementation"]["sha256"] == historical["inputs"]["implementation"]["sha256"]
    current_path = proof["inputs"]["implementation"].pop("path")
    historical["inputs"]["implementation"].pop("path")
    assert current_path.endswith("local_memory.py")
    assert proof == historical
