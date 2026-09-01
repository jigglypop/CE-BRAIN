#!/usr/bin/env python3
"""Fail-closed input preflight for the adult-M1 same-contact tool gate.

The preflight distinguishes synthetic schema fixtures from trusted laboratory
input.  It validates provenance, identity, paired event/no-event acquisition,
phase chronology, morphology and spectral-comparison structure.  It never
validates the biological tool, evaluates an endpoint, authorizes execution, or
raises the evidence ceiling above L0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import sys
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "adult_l4_same_contact_tool_development_schema_v1.json"
CANONICAL_CONTRACT_SEMANTIC_SHA256 = "de6f509f722b23d2636911c0ee00d994196938b4754354cd442fcff6b26809bc"

EXPECTED_CHANNELS = {
    "actuator": "ACTUATOR_LOG",
    "source_state": "SOURCE_STATE_CHANNEL",
    "theta": "THETA_CHANNEL",
    "mediator_state": "MEDIATOR_STATE_CHANNEL",
    "output": "OUTPUT_CHANNEL",
    "behavior": "BEHAVIOR_CHANNEL",
}
CONTACT_KEY_FIELDS = (
    "animal_id",
    "fov_id",
    "source_id",
    "post_cell_id",
    "dendrite_id",
    "spine_id",
)
CONTACT_ROLES = ("TARGET_A", "SHAM", "OFFTARGET_B", "NEIGHBOR", "OPSIN_NEGATIVE")
TABLE_FILENAMES = {
    "output_cell_registry": "output_cell_registry.jsonl",
    "contact_registry": "contact_registry.jsonl",
    "theta_trial": "theta_trial.jsonl",
    "manipulation_log": "manipulation_log.jsonl",
    "morphology_stack": "morphology_stack.jsonl",
    "spectral_calibration": "spectral_calibration.jsonl",
}
SUPPORTING_FILENAMES = {
    "clock_sync": "clock_sync_receipt.json",
    "institutional_approval": "institutional_approval_receipt.json",
    "biosafety": "biosafety_receipt.json",
    "safety": "safety_receipt.json",
    "nonplastic_probe": "nonplastic_probe_receipt.json",
    "depression_protocol": "depression_protocol.json",
    "potentiation_protocol": "potentiation_protocol.json",
    "analysis_protocol": "analysis_protocol.json",
    "registration_receipt": "registration_receipt.json",
    "heldout_direct_calibration": "heldout_direct_calibration.json",
    "censoring_likelihood": "censoring_likelihood.json",
    "raw_media_manifest": "raw_media_manifest.jsonl",
}
TABLE_SCHEMAS = {
    "output_cell_registry": [
        "animal_id", "fov_id", "post_cell_id", "baseline_cell_roi_fingerprint_sha256",
        "output_channel_version", "baseline_contact_required",
    ],
    "contact_registry": [
        *CONTACT_KEY_FIELDS, "episode_id", "target_contact_key", "matched_exposure_id",
        "contact_role", "baseline_locked", "baseline_roi_fingerprint_sha256",
        "neighbor_distance_um", "neighbor_rank",
    ],
    "theta_trial": [
        *CONTACT_KEY_FIELDS, "episode_id", "phase", "repeat_block", "pair_index",
        "matched_pair_id", "h_id", "c_id", "split", "source_event_raw_id",
        "matched_no_event_raw_id", "source_event_verified", "source_absence_verified",
        "event_q_spine", "event_q_parent", "event_q_soma", "no_event_q_spine",
        "no_event_q_parent", "no_event_q_soma", "event_latency_ms",
        "common_mode_removed", "measurement_state", "theta_override",
        "event_sensor_state", "event_censor_lower", "event_censor_upper",
        "no_event_sensor_state", "no_event_censor_lower", "no_event_censor_upper",
        "event_clock_ms", "no_event_clock_ms",
    ],
    "manipulation_log": [
        *CONTACT_KEY_FIELDS, "episode_id", "matched_exposure_id", "phase",
        "actuator_channel", "physical_channel_id", "construct_action",
        "protocol_sha256", "wavelength_nm", "delivered_energy_uj",
        "start_clock_ms", "stop_clock_ms", "structure_preserving_intent",
    ],
    "morphology_stack": [
        *CONTACT_KEY_FIELDS, "episode_id", "phase", "stack_index", "raw_stack_id",
        "parent_visible", "spine_present", "sensor_observable", "roi_fingerprint_sha256",
        "registration_receipt_sha256", "structural_channel_version", "stack_clock_ms",
    ],
    "spectral_calibration": [
        "calibration_id", "session_id", "command", "readout", "replicate",
        "physical_channel_id", "wavelength_nm", "command_energy_uj",
        "readout_device_id", "readout_device_version", "response_unit", "response",
        "temperature_delta_c", "sensor_saturated", "raw_evidence_id",
    ],
}
RAW_MEDIA_SCHEMA = [
    "object_id", "modality", "container_relative_path", "byte_offset", "byte_length", "sha256"
]
MANIFEST_FIELDS = [
    "schema_version", "bundle_id", "input_kind", "parent_contract_file_sha256",
    "preparation", "cohort", "authority", "channels", "channel_versions",
    "channel_units", "construct_version", "optical_actuators",
    "monosynaptic_latency_window_ms", "input_file_sha256",
    "supporting_artifact_sha256", "protocol_frozen_before_first_animal",
    "sealed_before_outcome_review", "tool_validated", "biological_endpoint_evaluated",
]
TOP_LEVEL_KEYS = {
    "schema_version", "contract_id", "status", "execution_authorized", "tool_validated",
    "biological_endpoint_evaluated", "l4_gate_evaluated", "claim_ceiling",
    "parent_contract", "scope", "data_policy", "trusted_authority", "input_bundle",
    "channels", "contact_identity", "phase_and_trial_cardinality", "table_schemas",
    "raw_media_manifest_schema", "acquisition_manifest_fields",
    "qualification_evidence_required", "preflight_semantics", "forbidden",
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(token: str) -> None:
    raise ValueError(f"non-finite JSON constant: {token}")


def _loads_strict(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite_constant,
    )


def load_json(path: Path) -> dict[str, Any]:
    value = _loads_strict(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"top-level JSON object required: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"blank JSONL line: {path.name}:{line_number}")
        value = _loads_strict(line)
        if not isinstance(value, dict):
            raise TypeError(f"JSONL object required: {path.name}:{line_number}")
        rows.append(value)
    if not rows:
        raise ValueError(f"empty JSONL table: {path.name}")
    return rows


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_sha(value: Any) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _contact_key(row: dict[str, Any]) -> tuple[str, ...]:
    values = tuple(row.get(field) for field in CONTACT_KEY_FIELDS)
    if not all(_is_string(value) for value in values):
        raise ValueError("contact key fields must be non-empty strings")
    return values  # type: ignore[return-value]


def canonical_contact_key(key: tuple[str, ...]) -> str:
    return "/".join(key)


def _exact_fields(row: dict[str, Any], fields: Iterable[str], label: str, errors: list[str]) -> None:
    if set(row) != set(fields):
        errors.append(f"{label} exact fields drift")


def validate_contract(
    contract: dict[str, Any], *, check_semantic_lock: bool = True, check_parent: bool = True
) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    try:
        require(set(contract) == TOP_LEVEL_KEYS, "top-level exact schema drift")
        require(contract.get("schema_version") == 1, "schema version drift")
        require(
            contract.get("contract_id") == "CE_NPF_ADULT_L4_SAME_CONTACT_TOOL_DEVELOPMENT_SCHEMA_V1",
            "contract ID drift",
        )
        require(contract.get("status") == "SCHEMA_ONLY_LAB_INPUT_REQUIRED", "status drift")
        require(contract.get("execution_authorized") is False, "schema cannot authorize execution")
        require(contract.get("tool_validated") is False, "schema cannot validate the tool")
        require(contract.get("biological_endpoint_evaluated") is False, "schema cannot evaluate endpoint")
        require(contract.get("l4_gate_evaluated") is False, "schema cannot evaluate L4")
        require(contract.get("claim_ceiling") == "BIO_EVIDENCE_L0", "claim ceiling drift")

        parent = contract.get("parent_contract", {})
        require(parent.get("path") == "adult_l4_riemann_fold_contract_v2.json", "parent path drift")
        require(_is_sha(parent.get("json_file_sha256")), "parent file hash malformed")
        require(_is_sha(parent.get("semantic_sha256")), "parent semantic hash malformed")
        require(parent.get("required_status") == "SCHEMA_FREEZE_CANDIDATE", "parent status drift")
        require(
            contract.get("scope") == {
                "species": "Mus musculus", "age": "ADULT", "age_weeks_inclusive": [12, 20],
                "region": "hindlimb M1", "layer": "L2/3",
                "cell_type": "L2/3 pyramidal neuron", "brain_state": "AWAKE",
                "minimum_age_days_at_first_acquisition": 84,
                "maximum_age_days_at_first_acquisition": 140,
                "cohort_role": "TOOL_VALIDATION_ONLY", "maximum_animals": 12,
                "reuse_for_model_controller_or_confirmation": False,
            },
            "parent preparation scope drift",
        )
        require(
            contract.get("data_policy") == {
                "new_public_payload_required": False, "bulk_download_authorized": False,
                "input_origin": "NEW_INSTITUTIONALLY_APPROVED_LAB_ACQUISITION_ONLY",
            },
            "data policy drift",
        )
        require(
            contract.get("trusted_authority") == {
                "lab_authority_lock_sha256": None,
                "lab_input_allowed_when_lock_is_null": False,
                "authority_lock_must_be_outside_bundle": True,
                "current_external_stop": "ORIGIN_AUTHORITY_UNVERIFIED",
            },
            "trusted-authority stop drift",
        )
        bundle = contract.get("input_bundle", {})
        require(bundle.get("format") == "UTF8_STRICT_JSON_AND_JSONL_NO_NAN_NO_DUPLICATE_KEYS", "input format drift")
        require(bundle.get("manifest_filename") == "acquisition_manifest.json", "manifest filename drift")
        require(bundle.get("table_filenames") == TABLE_FILENAMES, "table filename drift")
        require(bundle.get("supporting_artifact_filenames") == SUPPORTING_FILENAMES, "supporting artifact filename drift")
        require(bundle.get("all_declared_files_rehashed") is True, "declared artifact rehash missing")
        require(bundle.get("raw_media_segments_rehashed") is True, "raw segment rehash missing")
        require(contract.get("channels") == {**EXPECTED_CHANNELS, "all_channels_distinct": True}, "channel separation drift")

        identity = contract.get("contact_identity", {})
        require(identity.get("key_fields") == list(CONTACT_KEY_FIELDS), "contact key drift")
        require(identity.get("contact_roles") == list(CONTACT_ROLES), "contact role drift")
        require(identity.get("one_each_role_per_episode") is True, "episode role conjunction missing")
        require(identity.get("neighbor_rank") == 1, "nearest-neighbor rank drift")
        require(identity.get("baseline_locked_before_manipulation") is True, "baseline lock missing")
        require(identity.get("minimum_target_a_contacts_per_animal_lab") == 20, "lab target floor drift")
        require(identity.get("exact_target_a_contacts_per_animal_synthetic") == 2, "synthetic fixture cardinality drift")
        require(identity.get("exact_output_cells_per_animal") == 8, "output cell count drift")
        require(identity.get("contact_replacement_forbidden") is True, "contact replacement must remain forbidden")
        require(identity.get("phase_raw_stack_and_roi_fingerprint_required") is True, "physical identity lock missing")
        require(identity.get("registration_receipt_required") is True, "registration receipt missing")

        cardinality = contract.get("phase_and_trial_cardinality", {})
        require(cardinality == {
            "phase_order": ["PRE", "DOWN", "RESTORE"], "pre_repeatability_blocks": 8,
            "down_blocks": 1, "restore_blocks": 1,
            "matched_event_no_event_pairs_per_block": 40,
            "calibration_pairs_per_block": 20, "heldout_pairs_per_block": 20,
            "morphology_stacks_per_contact_phase": 2,
            "spectral_replicates_per_command_readout_pair": 8,
        }, "phase/trial cardinality drift")
        require(contract.get("table_schemas") == TABLE_SCHEMAS, "table schema drift")
        require(contract.get("raw_media_manifest_schema") == RAW_MEDIA_SCHEMA, "raw-media schema drift")
        require(contract.get("acquisition_manifest_fields") == MANIFEST_FIELDS, "manifest field drift")
        require(contract.get("qualification_evidence_required") == [
            "SAME_CONTACT_BIDIRECTIONAL_THETA_PRE_DOWN_RESTORE",
            "SHAM_EQUIVALENT_STRUCTURAL_SURVIVAL",
            "NEIGHBOR_AND_OFFTARGET_THETA_EQUIVALENCE",
            "DEPRESSION_POTENTIATION_SPECTRAL_INDEPENDENCE",
            "AWAKE_ADULT_M1_REPEATABILITY",
        ], "five-part qualification drift")
        semantics = contract.get("preflight_semantics", {})
        require(semantics == {
            "schema_only_status": "DEVELOPMENT_SCHEMA_PASS_LAB_INPUT_REQUIRED",
            "synthetic_input_pass_status": "SYNTHETIC_DEVELOPMENT_INPUT_SCHEMA_PASS_NOT_LAB_READY",
            "lab_input_pass_status": "DEVELOPMENT_INPUT_PREFLIGHT_PASS_NOT_TOOL_VALIDATION",
            "input_fail_status": "DEVELOPMENT_INPUT_PREFLIGHT_STOP",
            "authority_unverified_status": "ORIGIN_AUTHORITY_UNVERIFIED",
            "schema_or_input_pass_can_set_tool_validated": False,
            "input_preflight_can_evaluate_biological_endpoint": False,
            "next_external_gate": "TRUSTED_INSTITUTIONAL_AUTHORITY_LOCK_THEN_MAX_12_ANIMAL_TOOL_VALIDATION_EXECUTION",
        }, "preflight semantics drift")
        for item in (
            "CONTACT_REPLACEMENT_ACROSS_PRE_DOWN_RESTORE", "UNPAIRED_EVENT_AND_NO_EVENT_H_C",
            "MISSING_HELDOUT_DIRECT_CALIBRATION", "UNREGISTERED_OR_REUSED_RAW_STACK_ID",
            "UNLINKED_CONTROL_OR_EXPOSURE_EPISODE", "SELF_ASSERTED_AUTHORITY_OR_UNVERIFIED_ARTIFACT_HASH",
            "SYNTHETIC_FIXTURE_AS_LAB_INPUT_OR_TOOL_VALIDATION",
        ):
            require(item in contract.get("forbidden", []), f"forbidden safeguard missing: {item}")

        if check_parent and _is_string(parent.get("path")):
            parent_path = HERE / parent["path"]
            require(parent_path.is_file(), "parent contract missing")
            if parent_path.is_file():
                parent_value = load_json(parent_path)
                require(file_sha256(parent_path) == parent.get("json_file_sha256"), "parent file hash drift")
                require(semantic_sha256(parent_value) == parent.get("semantic_sha256"), "parent semantic hash drift")
                require(parent_value.get("status") == parent.get("required_status"), "live parent status drift")
                require(parent_value.get("execution_authorized") is False, "parent unexpectedly authorizes execution")
                require(parent_value.get("biological_starting_mechanism", {}).get("tool_validated") is False, "parent unexpectedly validates tool")
        if check_semantic_lock:
            require(semantic_sha256(contract) == CANONICAL_CONTRACT_SEMANTIC_SHA256, "canonical development-schema semantic fingerprint drift")
    except Exception as exc:
        errors.append(f"structured contract validation failure: {type(exc).__name__}: {exc}")
        if check_semantic_lock:
            errors.append("canonical development-schema semantic fingerprint drift")
    return errors


def _safe_bundle_path(root: Path, relative: Any) -> Path | None:
    if not _is_string(relative):
        return None
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        return None
    resolved_root = root.resolve()
    candidate = (resolved_root / rel).resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        return None
    return candidate


def _load_and_verify_supporting_artifacts(
    root: Path,
    manifest: dict[str, Any],
    input_kind: str,
    errors: list[str],
) -> tuple[dict[str, Path], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    paths: dict[str, Path] = {}
    json_artifacts: dict[str, dict[str, Any]] = {}
    raw_objects: dict[str, dict[str, Any]] = {}
    hash_map = manifest.get("supporting_artifact_sha256", {})
    if set(hash_map) != set(SUPPORTING_FILENAMES):
        errors.append("supporting-artifact hash map drift")
        return paths, json_artifacts, raw_objects
    for key, filename in SUPPORTING_FILENAMES.items():
        path = root / filename
        if not path.is_file():
            errors.append(f"supporting artifact missing: {filename}")
            continue
        if not _is_sha(hash_map.get(key)) or file_sha256(path) != hash_map.get(key):
            errors.append(f"supporting artifact hash drift: {key}")
            continue
        paths[key] = path
        if key != "raw_media_manifest":
            try:
                artifact = load_json(path)
                if artifact.get("artifact_type") != key:
                    errors.append(f"supporting artifact type drift: {key}")
                if artifact.get("input_kind") != input_kind:
                    errors.append(f"supporting artifact input-kind drift: {key}")
                if input_kind == "SYNTHETIC_SCHEMA_FIXTURE" and artifact.get("synthetic") is not True:
                    errors.append(f"synthetic artifact not marked synthetic: {key}")
                if input_kind == "LAB_ACQUISITION" and artifact.get("synthetic") is not False:
                    errors.append(f"lab artifact is synthetic or unverified: {key}")
                json_artifacts[key] = artifact
            except Exception as exc:
                errors.append(f"supporting artifact load failure {key}: {type(exc).__name__}: {exc}")
    raw_path = paths.get("raw_media_manifest")
    if raw_path is None:
        return paths, json_artifacts, raw_objects
    try:
        rows = load_jsonl(raw_path)
        container_cache: dict[Path, bytes] = {}
        allowed_modalities = {
            "THETA_SOURCE_EVENT_RAW", "THETA_MATCHED_NO_EVENT_RAW",
            "MORPHOLOGY_RAW", "SPECTRAL_RAW",
        }
        for index, row in enumerate(rows, 1):
            _exact_fields(row, RAW_MEDIA_SCHEMA, f"raw-media row {index}", errors)
            object_id = row.get("object_id")
            if not _is_string(object_id) or object_id in raw_objects:
                errors.append(f"raw-media object ID missing or duplicated at row {index}")
                continue
            if row.get("modality") not in allowed_modalities:
                errors.append(f"raw-media modality invalid at row {index}")
            path = _safe_bundle_path(root, row.get("container_relative_path"))
            if path is None or not path.is_file():
                errors.append(f"raw-media container missing or unsafe at row {index}")
                continue
            offset, length = row.get("byte_offset"), row.get("byte_length")
            if not (_is_int(offset) and offset >= 0 and _is_int(length) and length > 0 and _is_sha(row.get("sha256"))):
                errors.append(f"raw-media byte range or hash invalid at row {index}")
                continue
            payload = container_cache.setdefault(path, path.read_bytes())
            if offset + length > len(payload):
                errors.append(f"raw-media byte range exceeds container at row {index}")
                continue
            actual = hashlib.sha256(payload[offset:offset + length]).hexdigest()
            if actual != row["sha256"]:
                errors.append(f"raw-media segment hash drift at row {index}")
                continue
            raw_objects[object_id] = row
    except Exception as exc:
        errors.append(f"raw-media manifest load failure: {type(exc).__name__}: {exc}")
    return paths, json_artifacts, raw_objects


def _sensor_valid(
    prefix: str,
    row: dict[str, Any],
    values: tuple[str, str, str],
    errors: list[str],
    label: str,
) -> bool:
    state = row.get(f"{prefix}_sensor_state")
    lower, upper = row.get(f"{prefix}_censor_lower"), row.get(f"{prefix}_censor_upper")
    if state == "OK":
        if not all(_is_number(row.get(field)) for field in values):
            errors.append(f"{label} OK sensor requires finite q values")
            return False
        if lower is not None or upper is not None:
            errors.append(f"{label} OK sensor cannot carry censor bounds")
            return False
        return True
    if state == "CENSORED":
        if not all(row.get(field) is None for field in values):
            errors.append(f"{label} censored sensor requires null q values")
            return False
        if not (_is_number(lower) and _is_number(upper) and lower < upper):
            errors.append(f"{label} censored sensor requires finite ordered bounds")
            return False
        return True
    errors.append(f"{label} sensor state must be OK or CENSORED")
    return False


def validate_input_bundle(
    root: Path,
    contract: dict[str, Any],
    *,
    authority_lock: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """Public fail-closed entry point; canonical contract and parent lock are mandatory."""
    contract_errors = validate_contract(contract, check_semantic_lock=True, check_parent=True)
    if contract_errors:
        return [f"contract lock failure: {error}" for error in contract_errors], {"input_kind": None}
    return _validate_input_bundle_locked(root, contract, authority_lock=authority_lock)


def _validate_input_bundle_locked(
    root: Path,
    contract: dict[str, Any],
    *,
    authority_lock: Path | None,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    summary: dict[str, Any] = {
        "input_kind": None, "bundle_id": None, "acquisition_manifest_sha256": None,
        "input_file_sha256": None, "supporting_artifact_sha256": None,
        "animal_count": None, "output_cell_count": None, "contact_count": None,
        "episode_count": None, "theta_pair_count": None, "manipulation_count": None,
        "morphology_stack_count": None, "spectral_calibration_count": None,
        "biological_loss_contact_count": None,
    }

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    try:
        require(root.is_dir(), "laboratory input root missing")
        if not root.is_dir():
            return errors, summary
        manifest_path = root / contract["input_bundle"]["manifest_filename"]
        require(manifest_path.is_file(), "acquisition manifest missing")
        if not manifest_path.is_file():
            return errors, summary
        manifest = load_json(manifest_path)
        manifest_hash = file_sha256(manifest_path)
        _exact_fields(manifest, MANIFEST_FIELDS, "acquisition manifest", errors)
        input_kind = manifest.get("input_kind")
        summary.update(
            input_kind=input_kind,
            bundle_id=manifest.get("bundle_id"),
            acquisition_manifest_sha256=manifest_hash,
            input_file_sha256=manifest.get("input_file_sha256"),
            supporting_artifact_sha256=manifest.get("supporting_artifact_sha256"),
        )
        require(input_kind in {"SYNTHETIC_SCHEMA_FIXTURE", "LAB_ACQUISITION"}, "input kind invalid")
        require(manifest.get("schema_version") == 1, "manifest schema version drift")
        require(_is_string(manifest.get("bundle_id")), "bundle ID missing")
        require(manifest.get("parent_contract_file_sha256") == contract["parent_contract"]["json_file_sha256"], "manifest parent hash drift")
        require(manifest.get("preparation") == {
            "species": "Mus musculus", "age": "ADULT", "age_weeks_inclusive": [12, 20],
            "region": "hindlimb M1", "layer": "L2/3",
            "cell_type": "L2/3 pyramidal neuron", "brain_state": "AWAKE",
        }, "preparation must match parent 12-20 week awake hindlimb-M1 L2/3 pyramidal scope")

        cohort = manifest.get("cohort", {})
        _exact_fields(cohort, ("role", "animals", "reuse_for_model_controller_or_confirmation"), "cohort", errors)
        animals = cohort.get("animals", [])
        animal_ids = [item.get("animal_id") for item in animals] if isinstance(animals, list) and all(isinstance(item, dict) for item in animals) else []
        require(cohort.get("role") == "TOOL_VALIDATION_ONLY", "cohort role drift")
        require(1 <= len(animal_ids) <= 12 and all(_is_string(item) for item in animal_ids) and len(set(animal_ids)) == len(animal_ids), "animal IDs must be unique and within cap 12")
        for index, animal in enumerate(animals if isinstance(animals, list) else [], 1):
            if not isinstance(animal, dict):
                errors.append(f"animal record {index} is not an object")
                continue
            _exact_fields(animal, ("animal_id", "age_days", "sex", "strain"), f"animal record {index}", errors)
            require(
                _is_number(animal.get("age_days")) and 84 <= animal["age_days"] <= 140,
                f"animal record {index} is outside parent 12-20 week scope",
            )
            require(_is_string(animal.get("sex")) and _is_string(animal.get("strain")), f"animal record {index} metadata missing")
        require(cohort.get("reuse_for_model_controller_or_confirmation") is False, "tool animals cannot be reused")

        authority = manifest.get("authority", {})
        _exact_fields(authority, ("institutional_approval_status", "approval_id", "biosafety_status", "biosafety_id"), "authority", errors)
        if input_kind == "SYNTHETIC_SCHEMA_FIXTURE":
            require(authority == {
                "institutional_approval_status": "SYNTHETIC_NOT_APPLICABLE",
                "approval_id": "SYNTHETIC_TEST_ONLY",
                "biosafety_status": "SYNTHETIC_NOT_APPLICABLE",
                "biosafety_id": "SYNTHETIC_TEST_ONLY",
            }, "synthetic fixture cannot self-assert institutional approval")
        elif input_kind == "LAB_ACQUISITION":
            require(authority.get("institutional_approval_status") == "APPROVED" and _is_string(authority.get("approval_id")), "institutional approval missing")
            require(authority.get("biosafety_status") == "APPROVED" and _is_string(authority.get("biosafety_id")), "biosafety approval missing")
            trusted_hash = contract["trusted_authority"]["lab_authority_lock_sha256"]
            if trusted_hash is None:
                errors.append("ORIGIN_AUTHORITY_UNVERIFIED: canonical trusted authority lock is not issued")
            elif authority_lock is None or not authority_lock.is_file():
                errors.append("ORIGIN_AUTHORITY_UNVERIFIED: external authority lock missing")
            else:
                resolved_root = root.resolve()
                resolved_lock = authority_lock.resolve()
                require(resolved_lock != resolved_root and resolved_root not in resolved_lock.parents, "authority lock must be outside bundle")
                require(file_sha256(resolved_lock) == trusted_hash, "trusted authority lock hash drift")
                lock = load_json(resolved_lock)
                require(lock == {
                    "status": "TRUSTED", "bundle_id": manifest.get("bundle_id"),
                    "acquisition_manifest_sha256": manifest_hash,
                    "approval_id": authority.get("approval_id"), "biosafety_id": authority.get("biosafety_id"),
                }, "trusted authority lock content drift")

        require(manifest.get("channels") == EXPECTED_CHANNELS, "six-channel manifest drift")
        for field in ("channel_versions", "channel_units"):
            mapping = manifest.get(field, {})
            require(isinstance(mapping, dict) and set(mapping) == set(EXPECTED_CHANNELS), f"{field} keys drift")
            if isinstance(mapping, dict):
                require(all(_is_string(value) for value in mapping.values()), f"{field} values missing")
        require(_is_string(manifest.get("construct_version")), "construct version missing")
        actuators = manifest.get("optical_actuators", {})
        require(set(actuators) == {"DEPRESSION", "POTENTIATION"}, "optical actuator set drift")
        for name in ("DEPRESSION", "POTENTIATION"):
            actuator = actuators.get(name, {})
            _exact_fields(actuator, ("physical_channel_id", "wavelength_nm"), f"{name} actuator", errors)
            require(_is_string(actuator.get("physical_channel_id")), f"{name} physical channel missing")
            require(_is_number(actuator.get("wavelength_nm")) and actuator["wavelength_nm"] > 0, f"{name} wavelength invalid")
        if set(actuators) == {"DEPRESSION", "POTENTIATION"}:
            require(actuators["DEPRESSION"].get("physical_channel_id") != actuators["POTENTIATION"].get("physical_channel_id"), "actuator physical channels must be distinct")
            require(actuators["DEPRESSION"].get("wavelength_nm") != actuators["POTENTIATION"].get("wavelength_nm"), "actuator wavelengths must be distinct")
        latency = manifest.get("monosynaptic_latency_window_ms")
        require(isinstance(latency, list) and len(latency) == 2 and all(_is_number(value) for value in latency) and 0 <= latency[0] < latency[1], "monosynaptic latency window invalid")
        require(manifest.get("protocol_frozen_before_first_animal") is True, "protocol freeze missing")
        require(manifest.get("sealed_before_outcome_review") is True, "outcome-blind seal missing")
        require(manifest.get("tool_validated") is False, "input manifest cannot claim tool validation")
        require(manifest.get("biological_endpoint_evaluated") is False, "input manifest cannot claim endpoint evaluation")

        artifact_paths, artifacts, raw_objects = _load_and_verify_supporting_artifacts(root, manifest, input_kind, errors)
        if input_kind == "SYNTHETIC_SCHEMA_FIXTURE":
            require(artifacts.get("institutional_approval", {}).get("approval_id") == "SYNTHETIC_TEST_ONLY", "synthetic approval receipt mismatch")
            require(artifacts.get("biosafety", {}).get("biosafety_id") == "SYNTHETIC_TEST_ONLY", "synthetic biosafety receipt mismatch")
        elif input_kind == "LAB_ACQUISITION":
            require(artifacts.get("institutional_approval", {}).get("approval_id") == authority.get("approval_id"), "approval receipt ID mismatch")
            require(artifacts.get("biosafety", {}).get("biosafety_id") == authority.get("biosafety_id"), "biosafety receipt ID mismatch")

        table_hashes = manifest.get("input_file_sha256", {})
        require(set(table_hashes) == set(TABLE_FILENAMES), "input table hash map drift")
        tables: dict[str, list[dict[str, Any]]] = {}
        for table_name, filename in TABLE_FILENAMES.items():
            path = root / filename
            require(path.is_file(), f"required table missing: {filename}")
            if not path.is_file():
                continue
            require(_is_sha(table_hashes.get(table_name)) and file_sha256(path) == table_hashes.get(table_name), f"table hash drift: {table_name}")
            try:
                tables[table_name] = load_jsonl(path)
            except Exception as exc:
                errors.append(f"table load failure {table_name}: {type(exc).__name__}: {exc}")
        if set(tables) != set(TABLE_FILENAMES):
            return errors, summary

        output_rows = tables["output_cell_registry"]
        output_cells: dict[tuple[str, str, str], dict[str, Any]] = {}
        for index, row in enumerate(output_rows, 1):
            _exact_fields(row, TABLE_SCHEMAS["output_cell_registry"], f"output-cell row {index}", errors)
            key = (row.get("animal_id"), row.get("fov_id"), row.get("post_cell_id"))
            require(all(_is_string(value) for value in key), f"output-cell key invalid at row {index}")
            require(key not in output_cells, f"duplicate output-cell key: {key}")
            output_cells[key] = row
            require(_is_sha(row.get("baseline_cell_roi_fingerprint_sha256")), f"output-cell fingerprint invalid: {key}")
            require(row.get("output_channel_version") == manifest.get("channel_versions", {}).get("output"), f"output-channel version drift: {key}")
            require(row.get("baseline_contact_required") is True, f"output cell does not require baseline contact: {key}")
        for animal_id in animal_ids:
            require(sum(key[0] == animal_id for key in output_cells) == 8, f"animal {animal_id} must have exactly 8 output cells")

        registry_rows = tables["contact_registry"]
        registry: dict[tuple[str, ...], dict[str, Any]] = {}
        episodes: dict[str, list[tuple[tuple[str, ...], dict[str, Any]]]] = {}
        for index, row in enumerate(registry_rows, 1):
            _exact_fields(row, TABLE_SCHEMAS["contact_registry"], f"contact row {index}", errors)
            try:
                key = _contact_key(row)
            except Exception as exc:
                errors.append(f"contact key invalid at row {index}: {exc}")
                continue
            require(key not in registry, f"duplicate physical contact key: {key}")
            registry[key] = row
            require((key[0], key[1], key[3]) in output_cells, f"contact references unknown output cell: {key}")
            require(_is_string(row.get("episode_id")) and _is_string(row.get("matched_exposure_id")), f"episode/exposure missing: {key}")
            require(row.get("contact_role") in CONTACT_ROLES, f"contact role invalid: {key}")
            require(row.get("baseline_locked") is True, f"contact not baseline locked: {key}")
            require(_is_sha(row.get("baseline_roi_fingerprint_sha256")), f"contact ROI fingerprint invalid: {key}")
            if row.get("contact_role") == "NEIGHBOR":
                require(_is_number(row.get("neighbor_distance_um")) and row["neighbor_distance_um"] > 0, f"neighbor distance invalid: {key}")
                require(row.get("neighbor_rank") == 1, f"neighbor must be frozen rank 1: {key}")
            else:
                require(row.get("neighbor_distance_um") is None and row.get("neighbor_rank") is None, f"non-neighbor carries neighbor fields: {key}")
            if _is_string(row.get("episode_id")):
                episodes.setdefault(row["episode_id"], []).append((key, row))

        require({key[0] for key in registry} == set(animal_ids), "registry animals and manifest animals disagree")
        for output_key, output_row in output_cells.items():
            require(any((key[0], key[1], key[3]) == output_key for key in registry), f"output cell lacks a baseline contact: {output_key}")
        for episode_id, members in episodes.items():
            roles = [row["contact_role"] for _, row in members]
            require(sorted(roles) == sorted(CONTACT_ROLES), f"episode {episode_id} must contain exactly one of each control role")
            require(len({key[0] for key, _ in members}) == 1 and len({key[1] for key, _ in members}) == 1, f"episode {episode_id} crosses animal/FOV")
            targets = [key for key, row in members if row["contact_role"] == "TARGET_A"]
            if len(targets) == 1:
                target_string = canonical_contact_key(targets[0])
                require(all(row.get("target_contact_key") == target_string for _, row in members), f"episode {episode_id} target-contact link drift")
            require(len({row["matched_exposure_id"] for _, row in members}) == 1, f"episode {episode_id} exposure link drift")
        for animal_id in animal_ids:
            target_count = sum(key[0] == animal_id and row["contact_role"] == "TARGET_A" for key, row in registry.items())
            required_targets = 2 if input_kind == "SYNTHETIC_SCHEMA_FIXTURE" else 20
            comparison = target_count == required_targets if input_kind == "SYNTHETIC_SCHEMA_FIXTURE" else target_count >= required_targets
            require(comparison, f"animal {animal_id} target episode count violates {required_targets} minimum/exact gate")

        raw_ids_used: set[str] = set()
        morphology_rows = tables["morphology_stack"]
        morphology: dict[tuple[tuple[str, ...], str, int], dict[str, Any]] = {}
        morphology_clocks: dict[tuple[tuple[str, ...], str], list[float]] = {}
        registration_hash = manifest.get("supporting_artifact_sha256", {}).get("registration_receipt")
        for index, row in enumerate(morphology_rows, 1):
            _exact_fields(row, TABLE_SCHEMAS["morphology_stack"], f"morphology row {index}", errors)
            try:
                key = _contact_key(row)
            except Exception as exc:
                errors.append(f"morphology contact key invalid at row {index}: {exc}")
                continue
            require(key in registry, f"morphology references unknown/replaced contact: {key}")
            require(row.get("episode_id") == registry.get(key, {}).get("episode_id"), f"morphology episode mismatch: {key}")
            phase, stack_index = row.get("phase"), row.get("stack_index")
            require(phase in {"PRE", "DOWN", "RESTORE"} and stack_index in {1, 2}, f"morphology phase/stack invalid: {key}")
            unique = (key, phase, stack_index)
            require(unique not in morphology, f"duplicate morphology stack: {unique}")
            morphology[unique] = row
            raw_id = row.get("raw_stack_id")
            require(_is_string(raw_id) and raw_id not in raw_ids_used, f"raw stack ID missing or reused: {unique}")
            if _is_string(raw_id):
                raw_ids_used.add(raw_id)
                require(raw_objects.get(raw_id, {}).get("modality") == "MORPHOLOGY_RAW", f"raw stack object missing/wrong modality: {unique}")
            require(isinstance(row.get("parent_visible"), bool) and isinstance(row.get("spine_present"), bool) and isinstance(row.get("sensor_observable"), bool), f"morphology visibility flags invalid: {unique}")
            require(row.get("roi_fingerprint_sha256") == registry.get(key, {}).get("baseline_roi_fingerprint_sha256"), f"ROI fingerprint identity drift: {unique}")
            require(row.get("registration_receipt_sha256") == registration_hash, f"registration receipt drift: {unique}")
            require(row.get("structural_channel_version") == manifest.get("channel_versions", {}).get("theta"), f"structural channel version drift: {unique}")
            require(_is_number(row.get("stack_clock_ms")), f"morphology clock invalid: {unique}")
            if _is_number(row.get("stack_clock_ms")):
                morphology_clocks.setdefault((key, phase), []).append(float(row["stack_clock_ms"]))
        morphology_state: dict[tuple[tuple[str, ...], str], str] = {}
        effective_loss: set[tuple[tuple[str, ...], str]] = set()
        biological_loss_contacts: set[tuple[str, ...]] = set()
        for key in registry:
            lost = False
            previous_max = -math.inf
            for phase in ("PRE", "DOWN", "RESTORE"):
                rows = [morphology.get((key, phase, index)) for index in (1, 2)]
                require(all(row is not None for row in rows), f"missing two morphology stacks: {key}/{phase}")
                if not all(row is not None for row in rows):
                    continue
                typed_rows = [row for row in rows if row is not None]
                clocks = [float(row["stack_clock_ms"]) for row in typed_rows if _is_number(row.get("stack_clock_ms"))]
                require(len(clocks) == 2 and clocks[0] < clocks[1] and previous_max < min(clocks), f"morphology timestamp order violated: {key}/{phase}")
                if clocks:
                    previous_max = max(clocks)
                if not all(row["parent_visible"] and row["sensor_observable"] for row in typed_rows):
                    morphology_state[(key, phase)] = "TECHNICAL_NA"
                    errors.append(f"technical NA from parent/sensor loss: {key}/{phase}")
                elif all(row["spine_present"] for row in typed_rows):
                    morphology_state[(key, phase)] = "PRESENT"
                elif not any(row["spine_present"] for row in typed_rows):
                    morphology_state[(key, phase)] = "BIOLOGICAL_LOSS"
                    lost = True
                    biological_loss_contacts.add(key)
                else:
                    morphology_state[(key, phase)] = "AMBIGUOUS"
                    errors.append(f"spine presence inconsistent across consecutive stacks: {key}/{phase}")
                if lost:
                    effective_loss.add((key, phase))
        summary["biological_loss_contact_count"] = len(biological_loss_contacts)

        theta_rows = tables["theta_trial"]
        theta: dict[tuple[tuple[str, ...], str, int, int], dict[str, Any]] = {}
        theta_clocks: dict[tuple[tuple[str, ...], str], list[float]] = {}
        matched_ids: set[str] = set()
        theta_raw_ids: set[str] = set()
        latency_low, latency_high = latency if isinstance(latency, list) and len(latency) == 2 else (0, -1)
        phase_blocks = {"PRE": range(1, 9), "DOWN": range(1, 2), "RESTORE": range(1, 2)}
        for index, row in enumerate(theta_rows, 1):
            _exact_fields(row, TABLE_SCHEMAS["theta_trial"], f"theta row {index}", errors)
            try:
                key = _contact_key(row)
            except Exception as exc:
                errors.append(f"theta contact key invalid at row {index}: {exc}")
                continue
            require(key in registry, f"theta references unknown/replaced contact: {key}")
            require(row.get("episode_id") == registry.get(key, {}).get("episode_id"), f"theta episode mismatch: {key}")
            phase, block, pair_index = row.get("phase"), row.get("repeat_block"), row.get("pair_index")
            require(phase in phase_blocks and _is_int(block) and block in phase_blocks.get(phase, ()) and _is_int(pair_index) and 1 <= pair_index <= 40, f"theta phase/block/pair invalid: {key}")
            unique = (key, phase, block, pair_index)
            require(unique not in theta, f"duplicate theta matched pair: {unique}")
            theta[unique] = row
            pair_id = row.get("matched_pair_id")
            require(_is_string(pair_id) and pair_id not in matched_ids, f"matched pair ID missing/reused: {unique}")
            if _is_string(pair_id):
                matched_ids.add(pair_id)
            require(_is_string(row.get("h_id")) and _is_string(row.get("c_id")), f"matched h,c missing: {unique}")
            expected_split = "CALIBRATION" if _is_int(pair_index) and pair_index <= 20 else "HOLDOUT"
            require(row.get("split") == expected_split, f"calibration/holdout split drift: {unique}")
            clocks = (row.get("event_clock_ms"), row.get("no_event_clock_ms"))
            require(all(_is_number(value) for value in clocks) and clocks[0] < clocks[1], f"event/no-event clock invalid: {unique}")
            if all(_is_number(value) for value in clocks):
                theta_clocks.setdefault((key, phase), []).extend(float(value) for value in clocks)
            loss_coded = (key, phase) in effective_loss
            q_fields = (
                "event_q_spine", "event_q_parent", "event_q_soma",
                "no_event_q_spine", "no_event_q_parent", "no_event_q_soma",
            )
            if loss_coded:
                require(row.get("measurement_state") == "BIOLOGICAL_LOSS_THETA_ZERO" and row.get("theta_override") == 0.0, f"biological loss must remain theta zero: {unique}")
                require(all(row.get(field) is None for field in q_fields), f"biological loss cannot carry q values: {unique}")
                require(row.get("source_event_raw_id") is None and row.get("matched_no_event_raw_id") is None, f"biological loss cannot substitute raw trials: {unique}")
                require(row.get("source_event_verified") is False and row.get("source_absence_verified") is False, f"biological loss verification flags invalid: {unique}")
                require(row.get("event_latency_ms") is None and row.get("common_mode_removed") is False, f"biological loss assay fields invalid: {unique}")
                for prefix in ("event", "no_event"):
                    require(row.get(f"{prefix}_sensor_state") == "NOT_APPLICABLE" and row.get(f"{prefix}_censor_lower") is None and row.get(f"{prefix}_censor_upper") is None, f"biological loss sensor state invalid: {unique}")
            else:
                require(morphology_state.get((key, phase)) == "PRESENT", f"theta present row lacks visible same contact: {unique}")
                require(row.get("measurement_state") == "OBSERVED" and row.get("theta_override") is None, f"observed theta state invalid: {unique}")
                event_id, noevent_id = row.get("source_event_raw_id"), row.get("matched_no_event_raw_id")
                require(_is_string(event_id) and _is_string(noevent_id) and event_id != noevent_id, f"paired raw evidence IDs missing: {unique}")
                for raw_id, modality in ((event_id, "THETA_SOURCE_EVENT_RAW"), (noevent_id, "THETA_MATCHED_NO_EVENT_RAW")):
                    if _is_string(raw_id):
                        require(raw_id not in theta_raw_ids, f"theta raw evidence reused: {raw_id}")
                        theta_raw_ids.add(raw_id)
                        require(raw_objects.get(raw_id, {}).get("modality") == modality, f"theta raw evidence missing/wrong modality: {raw_id}")
                require(row.get("source_event_verified") is True and row.get("source_absence_verified") is True, f"source event/absence not independently verified: {unique}")
                require(_is_number(row.get("event_latency_ms")) and latency_low <= row["event_latency_ms"] <= latency_high, f"event latency outside frozen window: {unique}")
                require(row.get("common_mode_removed") is True, f"common mode not removed: {unique}")
                _sensor_valid("event", row, ("event_q_spine", "event_q_parent", "event_q_soma"), errors, f"event {unique}")
                _sensor_valid("no_event", row, ("no_event_q_spine", "no_event_q_parent", "no_event_q_soma"), errors, f"no-event {unique}")
        for key in registry:
            previous_clock = -math.inf
            for phase, blocks in phase_blocks.items():
                for block in blocks:
                    for pair_index in range(1, 41):
                        unique = (key, phase, block, pair_index)
                        require(unique in theta, f"missing matched h,c event/no-event pair: {unique}")
                        row = theta.get(unique)
                        if row and _is_number(row.get("event_clock_ms")) and _is_number(row.get("no_event_clock_ms")):
                            require(previous_clock < row["event_clock_ms"] < row["no_event_clock_ms"], f"theta block/pair timestamp order violated: {unique}")
                            previous_clock = row["no_event_clock_ms"]

        manipulation_rows = tables["manipulation_log"]
        manipulations: dict[tuple[tuple[str, ...], str], dict[str, Any]] = {}
        for index, row in enumerate(manipulation_rows, 1):
            _exact_fields(row, TABLE_SCHEMAS["manipulation_log"], f"manipulation row {index}", errors)
            try:
                key = _contact_key(row)
            except Exception as exc:
                errors.append(f"manipulation key invalid at row {index}: {exc}")
                continue
            require(key in registry, f"manipulation references unknown/replaced contact: {key}")
            role = registry.get(key, {}).get("contact_role")
            require(role in {"TARGET_A", "SHAM"}, f"manipulation applied to forbidden control: {key}")
            require(row.get("episode_id") == registry.get(key, {}).get("episode_id") and row.get("matched_exposure_id") == registry.get(key, {}).get("matched_exposure_id"), f"manipulation episode/exposure drift: {key}")
            phase = row.get("phase")
            require(phase in {"DOWN", "RESTORE"}, f"manipulation phase invalid: {key}")
            unique = (key, phase)
            require(unique not in manipulations, f"duplicate manipulation: {unique}")
            manipulations[unique] = row
            base = "DEPRESSION" if phase == "DOWN" else "POTENTIATION"
            expected_label = base if role == "TARGET_A" else f"SHAM_{base}"
            expected_action = "ACTIVE" if role == "TARGET_A" else "INERT_SHAM"
            require(row.get("actuator_channel") == expected_label and row.get("construct_action") == expected_action, f"active/sham action drift: {unique}")
            require(row.get("physical_channel_id") == actuators.get(base, {}).get("physical_channel_id"), f"physical actuator channel drift: {unique}")
            protocol_key = "depression_protocol" if phase == "DOWN" else "potentiation_protocol"
            require(row.get("protocol_sha256") == manifest.get("supporting_artifact_sha256", {}).get(protocol_key), f"protocol artifact hash drift: {unique}")
            require(row.get("wavelength_nm") == actuators.get(base, {}).get("wavelength_nm"), f"actuator wavelength drift: {unique}")
            require(_is_number(row.get("delivered_energy_uj")) and row["delivered_energy_uj"] > 0, f"actuator energy invalid: {unique}")
            require(_is_number(row.get("start_clock_ms")) and _is_number(row.get("stop_clock_ms")) and row["start_clock_ms"] < row["stop_clock_ms"], f"actuator clock invalid: {unique}")
            require(row.get("structure_preserving_intent") is True, f"structure-preserving intent missing: {unique}")
        for episode_id, members in episodes.items():
            role_map = {row["contact_role"]: key for key, row in members}
            for phase in ("DOWN", "RESTORE"):
                target = manipulations.get((role_map.get("TARGET_A"), phase))
                sham = manipulations.get((role_map.get("SHAM"), phase))
                require(target is not None and sham is not None, f"episode {episode_id} missing active/sham manipulation in {phase}")
                if target and sham:
                    for field in ("matched_exposure_id", "physical_channel_id", "wavelength_nm", "delivered_energy_uj", "start_clock_ms", "stop_clock_ms"):
                        require(target.get(field) == sham.get(field), f"episode {episode_id} sham is not exposure matched on {field}/{phase}")
                    all_keys = [key for key, _ in members]
                    before_phase = "PRE" if phase == "DOWN" else "DOWN"
                    after_phase = "DOWN" if phase == "DOWN" else "RESTORE"
                    before = [clock for key in all_keys for clock in theta_clocks.get((key, before_phase), []) + morphology_clocks.get((key, before_phase), [])]
                    after = [clock for key in all_keys for clock in theta_clocks.get((key, after_phase), []) + morphology_clocks.get((key, after_phase), [])]
                    if before and after:
                        require(max(before) < target["start_clock_ms"] < target["stop_clock_ms"] < min(after), f"episode {episode_id} manipulation not between matched phase acquisitions/{phase}")

        spectral_rows = tables["spectral_calibration"]
        spectral_seen: set[tuple[str, str, int]] = set()
        spectral_raw_ids: set[str] = set()
        sessions: set[str] = set()
        device_ids: set[str] = set()
        device_versions: set[str] = set()
        response_units: set[str] = set()
        energy_by_command: dict[str, set[float]] = {"DEPRESSION": set(), "POTENTIATION": set()}
        for index, row in enumerate(spectral_rows, 1):
            _exact_fields(row, TABLE_SCHEMAS["spectral_calibration"], f"spectral row {index}", errors)
            command, readout, replicate = row.get("command"), row.get("readout"), row.get("replicate")
            require(command in {"DEPRESSION", "POTENTIATION"} and readout in {"DEPRESSION", "POTENTIATION"} and _is_int(replicate) and 1 <= replicate <= 8, f"spectral command/readout/replicate invalid at row {index}")
            if command in actuators:
                require(row.get("physical_channel_id") == actuators[command].get("physical_channel_id"), f"spectral physical channel drift at row {index}")
                require(row.get("wavelength_nm") == actuators[command].get("wavelength_nm"), f"spectral wavelength drift at row {index}")
            require(_is_number(row.get("command_energy_uj")) and row["command_energy_uj"] > 0, f"spectral energy invalid at row {index}")
            if command in energy_by_command and _is_number(row.get("command_energy_uj")):
                energy_by_command[command].add(float(row["command_energy_uj"]))
            for field, bucket in (("session_id", sessions), ("readout_device_id", device_ids), ("readout_device_version", device_versions), ("response_unit", response_units)):
                require(_is_string(row.get(field)), f"spectral {field} missing at row {index}")
                if _is_string(row.get(field)):
                    bucket.add(row[field])
            require(_is_number(row.get("response")) and _is_number(row.get("temperature_delta_c")), f"spectral response/heat invalid at row {index}")
            require(row.get("sensor_saturated") is False, f"spectral calibration saturated at row {index}")
            raw_id = row.get("raw_evidence_id")
            require(_is_string(raw_id) and raw_id not in spectral_raw_ids, f"spectral raw evidence missing/reused at row {index}")
            if _is_string(raw_id):
                spectral_raw_ids.add(raw_id)
                require(raw_objects.get(raw_id, {}).get("modality") == "SPECTRAL_RAW", f"spectral raw evidence wrong modality at row {index}")
            if command in {"DEPRESSION", "POTENTIATION"} and readout in {"DEPRESSION", "POTENTIATION"} and _is_int(replicate):
                unique = (command, readout, replicate)
                require(unique not in spectral_seen, f"duplicate spectral matrix cell: {unique}")
                spectral_seen.add(unique)
        expected_spectral = {(command, readout, replicate) for command in ("DEPRESSION", "POTENTIATION") for readout in ("DEPRESSION", "POTENTIATION") for replicate in range(1, 9)}
        require(spectral_seen == expected_spectral, "incomplete depression/potentiation cross-talk matrix")
        require(len(sessions) == len(device_ids) == len(device_versions) == len(response_units) == 1, "spectral session/device/version/unit drift")
        require(all(len(values) == 1 for values in energy_by_command.values()), "spectral command energy is not matched across readouts")

        summary.update(
            animal_count=len(set(animal_ids)), output_cell_count=len(output_cells),
            contact_count=len(registry), episode_count=len(episodes), theta_pair_count=len(theta_rows),
            manipulation_count=len(manipulation_rows), morphology_stack_count=len(morphology_rows),
            spectral_calibration_count=len(spectral_rows),
        )
    except Exception as exc:
        errors.append(f"structured input validation failure: {type(exc).__name__}: {exc}")
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--authority-lock", type=Path)
    args = parser.parse_args()
    report: dict[str, Any] = {
        "status": "DEVELOPMENT_SCHEMA_STOP",
        "contract": str(args.contract.resolve()),
        "contract_file_sha256": None,
        "contract_semantic_sha256": None,
        "preflight_file_sha256": file_sha256(Path(__file__).resolve()),
        "input_root": str(args.input_root.resolve()) if args.input_root else None,
        "error_count": 0, "errors": [], "execution_authorized": False,
        "tool_validated": False, "biological_endpoint_evaluated": False,
        "l4_gate_evaluated": False, "claim_ceiling": "BIO_EVIDENCE_L0",
        "environment": {
            "python_executable": str(Path(sys.executable).resolve()),
            "python_version": platform.python_version(), "platform": platform.platform(),
        },
    }
    try:
        contract = load_json(args.contract)
        report["contract_file_sha256"] = file_sha256(args.contract)
        report["contract_semantic_sha256"] = semantic_sha256(contract)
        errors = validate_contract(contract)
        summary: dict[str, Any] | None = None
        if not errors and args.input_root is not None:
            errors, summary = validate_input_bundle(args.input_root, contract, authority_lock=args.authority_lock)
            report["input_summary"] = summary
        report["errors"] = errors
        report["error_count"] = len(errors)
        if errors:
            if any("ORIGIN_AUTHORITY_UNVERIFIED" in error for error in errors):
                report["status"] = contract["preflight_semantics"]["authority_unverified_status"]
            elif args.input_root is not None:
                report["status"] = contract["preflight_semantics"]["input_fail_status"]
        elif args.input_root is None:
            report["status"] = contract["preflight_semantics"]["schema_only_status"]
        elif summary and summary.get("input_kind") == "SYNTHETIC_SCHEMA_FIXTURE":
            report["status"] = contract["preflight_semantics"]["synthetic_input_pass_status"]
        else:
            report["status"] = contract["preflight_semantics"]["lab_input_pass_status"]
    except Exception as exc:
        report["errors"] = [f"structured preflight failure: {type(exc).__name__}: {exc}"]
        report["error_count"] = 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
