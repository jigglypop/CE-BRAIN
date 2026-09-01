"""Validate the external-lab handoff without authorizing an experiment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_HANDOFF = BASE_DIR / "adult_l4_same_contact_lab_handoff_v1.json"
DEVELOPMENT_PREFLIGHT = BASE_DIR / "preflight_adult_l4_same_contact_tool_development_v1.py"
CANONICAL_HANDOFF_SEMANTIC_SHA256 = "2db6d9b85880fdbebca48efaff1054b24e210c80f38f1acceebc138f1cd11cd9"

TOP_LEVEL_FIELDS = (
    "schema_version", "handoff_id", "status", "execution_authorized",
    "tool_validated", "biological_endpoint_evaluated", "l4_gate_evaluated",
    "claim_ceiling", "public_data_policy", "locks", "preparation",
    "development_cohort", "external_authority", "required_tables",
    "required_supporting_artifacts", "operator_sequence",
    "qualification_evidence_required", "handoff_invariants", "computer_complete",
    "external_actions_remaining", "next_gate",
)

EXPECTED_PREPARATION = {
    "species": "Mus musculus", "age": "ADULT", "age_weeks_inclusive": [12, 20],
    "region": "hindlimb M1", "layer": "L2/3",
    "cell_type": "L2/3 pyramidal neuron", "brain_state": "AWAKE",
}

EXPECTED_SEQUENCE = [
    "01_EXTERNAL_APPROVALS_AND_AUTHORITY_REQUEST",
    "02_PROTOCOL_AND_ANALYSIS_FREEZE_BEFORE_FIRST_ANIMAL",
    "03_CLOCK_SAFETY_NONPLASTIC_AND_SPECTRAL_QUALIFICATION",
    "04_BASELINE_OUTPUT_CELL_CONTACT_AND_ROI_LOCK",
    "05_PRE_EIGHT_BLOCK_REPEATABILITY_ACQUISITION",
    "06_DOWN_TARGET_SHAM_OFFTARGET_NEIGHBOR_OPSIN_NEGATIVE_ACQUISITION",
    "07_SAME_CONTACT_RESTORE_ACQUISITION",
    "08_RAW_SEGMENT_HASH_AND_OUTCOME_BLIND_BUNDLE_SEAL",
    "09_EXTERNAL_AUTHORITY_LOCK_ISSUANCE_OUTSIDE_BUNDLE",
    "10_FAIL_CLOSED_DEVELOPMENT_PREFLIGHT",
    "11_TOOL_VALIDATION_DECISION_UNDER_SEPARATE_PROTOCOL",
]

EXPECTED_QUALIFICATION = [
    "SAME_CONTACT_BIDIRECTIONAL_THETA_PRE_DOWN_RESTORE",
    "SHAM_EQUIVALENT_STRUCTURAL_SURVIVAL",
    "NEIGHBOR_AND_OFFTARGET_THETA_EQUIVALENCE",
    "DEPRESSION_POTENTIATION_SPECTRAL_INDEPENDENCE",
    "AWAKE_ADULT_M1_REPEATABILITY",
]


class DuplicateKeyError(ValueError):
    pass


def _object_pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_object_pairs_no_duplicates,
        parse_constant=_reject_nonfinite,
    )
    if not isinstance(value, dict):
        raise TypeError("top-level JSON value must be an object")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_development_preflight() -> Any:
    spec = importlib.util.spec_from_file_location("adult_l4_development_preflight", DEVELOPMENT_PREFLIGHT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load development preflight")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _exact_fields(value: Any, expected: tuple[str, ...], label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
    elif set(value) != set(expected):
        errors.append(f"{label} field drift")


def validate_handoff(
    handoff: dict[str, Any], *, check_semantic_lock: bool = True,
) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    try:
        _exact_fields(handoff, TOP_LEVEL_FIELDS, "handoff", errors)
        require(handoff.get("schema_version") == 1, "handoff schema version drift")
        require(handoff.get("handoff_id") == "CE_NPF_ADULT_L4_SAME_CONTACT_LAB_HANDOFF_V1", "handoff ID drift")
        require(handoff.get("status") == "LAB_HANDOFF_READY_EXTERNAL_ACTION_REQUIRED", "handoff status drift")
        require(handoff.get("execution_authorized") is False, "handoff cannot authorize execution")
        require(handoff.get("tool_validated") is False, "handoff cannot claim tool validation")
        require(handoff.get("biological_endpoint_evaluated") is False, "handoff cannot claim biological evaluation")
        require(handoff.get("l4_gate_evaluated") is False, "handoff cannot claim L4 evaluation")
        require(handoff.get("claim_ceiling") == "BIO_EVIDENCE_L0", "handoff claim ceiling drift")

        require(handoff.get("public_data_policy") == {
            "status": "PUBLIC_DATA_SUFFICIENCY_FROZEN",
            "new_public_downloads_authorized": False,
            "public_data_sufficiency_reaudit_authorized": False,
            "next_evidence_origin": "NEW_INSTITUTIONALLY_APPROVED_LAB_ACQUISITION_ONLY",
        }, "public-data freeze drift")
        require(handoff.get("preparation") == EXPECTED_PREPARATION, "parent preparation scope drift")
        require(handoff.get("development_cohort") == {
            "role": "TOOL_VALIDATION_ONLY", "minimum_animals": 1, "maximum_animals": 12,
            "reuse_for_model_controller_or_confirmation": False,
            "inferential_claim_authorized": False,
        }, "development cohort drift")

        authority = handoff.get("external_authority")
        require(authority == {
            "state": "PENDING_TRUSTED_INSTITUTIONAL_ISSUANCE",
            "canonical_lab_authority_lock_sha256": None,
            "self_assertion_accepted": False,
            "authority_lock_must_be_outside_acquisition_bundle": True,
            "required_approvals": [
                "INSTITUTIONAL_ANIMAL_APPROVAL", "BIOSAFETY_APPROVAL", "LAB_SAFETY_APPROVAL",
            ],
            "authority_lock_exact_fields": [
                "status", "bundle_id", "acquisition_manifest_sha256", "approval_id", "biosafety_id",
            ],
            "expected_issued_status": "TRUSTED",
            "current_stop": "ORIGIN_AUTHORITY_UNVERIFIED",
        }, "external authority must remain pending and non-self-asserted")

        locks = handoff.get("locks", {})
        _exact_fields(
            locks,
            ("parent_contract", "development_schema", "development_preflight", "development_tests"),
            "locks", errors,
        )
        development_module = _load_development_preflight()
        for label in ("parent_contract", "development_schema", "development_preflight", "development_tests"):
            lock = locks.get(label, {}) if isinstance(locks, dict) else {}
            path_name = lock.get("path") if isinstance(lock, dict) else None
            require(isinstance(path_name, str) and Path(path_name).name == path_name, f"{label} path invalid")
            if isinstance(path_name, str) and Path(path_name).name == path_name:
                path = BASE_DIR / path_name
                require(path.is_file(), f"{label} locked file missing")
                if path.is_file():
                    require(file_sha256(path) == lock.get("file_sha256"), f"{label} file hash drift")

        parent_lock = locks.get("parent_contract", {})
        parent_path = BASE_DIR / parent_lock.get("path", "MISSING")
        if parent_path.is_file():
            parent = load_json(parent_path)
            require(semantic_sha256(parent) == parent_lock.get("semantic_sha256"), "parent semantic hash drift")
            require(parent.get("status") == parent_lock.get("required_status"), "parent status drift")

        development_lock = locks.get("development_schema", {})
        development_path = BASE_DIR / development_lock.get("path", "MISSING")
        if development_path.is_file():
            development = load_json(development_path)
            require(semantic_sha256(development) == development_lock.get("semantic_sha256"), "development semantic hash drift")
            require(development.get("status") == development_lock.get("required_status"), "development status drift")
            require(development_module.validate_contract(development) == [], "development contract no longer validates")
            require(development.get("trusted_authority", {}).get("lab_authority_lock_sha256") is None, "canonical authority unexpectedly issued")
            require(handoff.get("required_tables") == development.get("input_bundle", {}).get("table_filenames"), "required table drift")
            require(handoff.get("required_supporting_artifacts") == development.get("input_bundle", {}).get("supporting_artifact_filenames"), "supporting artifact drift")
            require(handoff.get("qualification_evidence_required") == development.get("qualification_evidence_required"), "qualification evidence drift")

        require(handoff.get("operator_sequence") == EXPECTED_SEQUENCE, "operator sequence drift")
        require(handoff.get("qualification_evidence_required") == EXPECTED_QUALIFICATION, "qualification list drift")
        require(handoff.get("handoff_invariants") == {
            "all_declared_files_rehashed": True,
            "raw_media_segments_rehashed": True,
            "protocol_frozen_before_first_animal": True,
            "sealed_before_outcome_review": True,
            "synthetic_fixture_is_not_lab_input": True,
            "preflight_pass_is_not_tool_validation": True,
            "tool_validation_is_not_l4_confirmation": True,
        }, "handoff invariant drift")
        require(handoff.get("computer_complete") == [
            "PARENT_CONTRACT_LOCKED", "DEVELOPMENT_INPUT_SCHEMA_LOCKED",
            "FAIL_CLOSED_PREFLIGHT_TESTED", "PUBLIC_DATA_BRANCH_FROZEN",
            "LAB_HANDOFF_REQUIREMENTS_MATERIALIZED",
        ], "computer-complete ledger drift")
        require(handoff.get("external_actions_remaining") == [
            "TRUSTED_INSTITUTIONAL_AUTHORITY_LOCK",
            "QUALIFIED_BIDIRECTIONAL_STRUCTURE_PRESERVING_SAME_CONTACT_TOOL",
            "ONE_TO_TWELVE_ANIMAL_TOOL_VALIDATION_ACQUISITION",
            "SEPARATE_TOOL_VALIDATION_DECISION",
        ], "external-action ledger drift")
        require(
            handoff.get("next_gate") == "TRUSTED_INSTITUTIONAL_AUTHORITY_LOCK_THEN_MAX_12_ANIMAL_TOOL_VALIDATION_EXECUTION",
            "next gate drift",
        )
        if check_semantic_lock:
            require(semantic_sha256(handoff) == CANONICAL_HANDOFF_SEMANTIC_SHA256, "canonical handoff semantic fingerprint drift")
    except Exception as exc:
        errors.append(f"structured handoff validation failure: {type(exc).__name__}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("handoff", nargs="?", type=Path, default=DEFAULT_HANDOFF)
    args = parser.parse_args()
    errors: list[str] = []
    handoff: dict[str, Any] = {}
    file_hash: str | None = None
    semantic_hash: str | None = None
    try:
        handoff = load_json(args.handoff)
        file_hash = file_sha256(args.handoff)
        semantic_hash = semantic_sha256(handoff)
        errors = validate_handoff(handoff)
    except Exception as exc:
        errors = [f"structured handoff load failure: {type(exc).__name__}: {exc}"]
    report = {
        "status": "LAB_HANDOFF_SCHEMA_PASS_EXTERNAL_ACTION_REQUIRED" if not errors else "LAB_HANDOFF_SCHEMA_STOP",
        "handoff": str(args.handoff.resolve()),
        "handoff_file_sha256": file_hash,
        "handoff_semantic_sha256": semantic_hash,
        "error_count": len(errors),
        "errors": errors,
        "execution_authorized": False,
        "tool_validated": False,
        "biological_endpoint_evaluated": False,
        "l4_gate_evaluated": False,
        "claim_ceiling": "BIO_EVIDENCE_L0",
        "external_stop": "ORIGIN_AUTHORITY_UNVERIFIED",
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
