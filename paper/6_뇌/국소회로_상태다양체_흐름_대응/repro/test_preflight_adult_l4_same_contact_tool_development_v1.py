from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name("preflight_adult_l4_same_contact_tool_development_v1.py")
SPEC = importlib.util.spec_from_file_location("same_contact_preflight", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _refresh_table_hash(bundle: Path, table_name: str) -> None:
    manifest_path = bundle / "acquisition_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    table_path = bundle / preflight.TABLE_FILENAMES[table_name]
    manifest["input_file_sha256"][table_name] = hashlib.sha256(table_path.read_bytes()).hexdigest()
    _write_json(manifest_path, manifest)


def _copy_bundle(source: Path, tmp_path: Path) -> Path:
    destination = tmp_path / "bundle"
    shutil.copytree(source, destination)
    return destination


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _make_valid_synthetic_bundle(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    input_kind = "SYNTHETIC_SCHEMA_FIXTURE"

    supporting_hashes: dict[str, str] = {}
    for key, filename in preflight.SUPPORTING_FILENAMES.items():
        if key == "raw_media_manifest":
            continue
        artifact = {
            "artifact_type": key,
            "input_kind": input_kind,
            "synthetic": True,
        }
        if key == "institutional_approval":
            artifact["approval_id"] = "SYNTHETIC_TEST_ONLY"
        if key == "biosafety":
            artifact["biosafety_id"] = "SYNTHETIC_TEST_ONLY"
        path = root / filename
        _write_json(path, artifact)
        supporting_hashes[key] = hashlib.sha256(path.read_bytes()).hexdigest()

    output_rows = [
        {
            "animal_id": "animal_01",
            "fov_id": "fov_01",
            "post_cell_id": f"cell_{index:02d}",
            "baseline_cell_roi_fingerprint_sha256": _sha_text(f"cell-{index}"),
            "output_channel_version": "output-v1",
            "baseline_contact_required": True,
        }
        for index in range(8)
    ]
    _write_jsonl(root / "output_cell_registry.jsonl", output_rows)

    registry: list[dict] = []
    for episode_index in range(2):
        episode_id = f"episode_{episode_index:02d}"
        exposure_id = f"exposure_{episode_index:02d}"
        target_key = (
            "animal_01", "fov_01", f"source_{episode_index:02d}_TARGET_A",
            f"cell_{(episode_index * 5) % 8:02d}", f"dendrite_{episode_index:02d}_TARGET_A",
            f"spine_{episode_index:02d}_TARGET_A",
        )
        target_string = preflight.canonical_contact_key(target_key)
        for role_index, role in enumerate(preflight.CONTACT_ROLES):
            global_index = episode_index * len(preflight.CONTACT_ROLES) + role_index
            key = (
                "animal_01", "fov_01", f"source_{episode_index:02d}_{role}",
                f"cell_{global_index % 8:02d}", f"dendrite_{episode_index:02d}_{role}",
                f"spine_{episode_index:02d}_{role}",
            )
            registry.append(
                {
                    **dict(zip(preflight.CONTACT_KEY_FIELDS, key)),
                    "episode_id": episode_id,
                    "target_contact_key": target_string,
                    "matched_exposure_id": exposure_id,
                    "contact_role": role,
                    "baseline_locked": True,
                    "baseline_roi_fingerprint_sha256": _sha_text(preflight.canonical_contact_key(key)),
                    "neighbor_distance_um": 2.0 if role == "NEIGHBOR" else None,
                    "neighbor_rank": 1 if role == "NEIGHBOR" else None,
                }
            )
    _write_jsonl(root / "contact_registry.jsonl", registry)

    raw_container = bytearray()
    raw_manifest: list[dict] = []
    raw_ids: set[str] = set()

    def add_raw(object_id: str, modality: str) -> str:
        assert object_id not in raw_ids
        raw_ids.add(object_id)
        payload = (object_id + "\n").encode("utf-8")
        offset = len(raw_container)
        raw_container.extend(payload)
        raw_manifest.append(
            {
                "object_id": object_id,
                "modality": modality,
                "container_relative_path": "raw_media.bin",
                "byte_offset": offset,
                "byte_length": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
        return object_id

    morphology_rows: list[dict] = []
    role_index_by_role = {role: index for index, role in enumerate(preflight.CONTACT_ROLES)}
    for contact in registry:
        key = {field: contact[field] for field in preflight.CONTACT_KEY_FIELDS}
        episode_index = int(contact["episode_id"].split("_")[-1])
        role_index = role_index_by_role[contact["contact_role"]]
        base = episode_index * 100000.0
        for phase, phase_offset in (("PRE", 8000.0), ("DOWN", 28000.0), ("RESTORE", 48000.0)):
            for stack_index in (1, 2):
                raw_id = add_raw(
                    f"morph:{contact['spine_id']}:{phase}:{stack_index}", "MORPHOLOGY_RAW"
                )
                morphology_rows.append(
                    {
                        **key,
                        "episode_id": contact["episode_id"],
                        "phase": phase,
                        "stack_index": stack_index,
                        "raw_stack_id": raw_id,
                        "parent_visible": True,
                        "spine_present": True,
                        "sensor_observable": True,
                        "roi_fingerprint_sha256": contact["baseline_roi_fingerprint_sha256"],
                        "registration_receipt_sha256": supporting_hashes["registration_receipt"],
                        "structural_channel_version": "theta-v1",
                        "stack_clock_ms": base + phase_offset + role_index * 10 + stack_index,
                    }
                )
    _write_jsonl(root / "morphology_stack.jsonl", morphology_rows)

    theta_rows: list[dict] = []
    for contact in registry:
        key = {field: contact[field] for field in preflight.CONTACT_KEY_FIELDS}
        episode_index = int(contact["episode_id"].split("_")[-1])
        role_index = role_index_by_role[contact["contact_role"]]
        base = episode_index * 100000.0
        for phase, phase_offset, blocks in (
            ("PRE", 0.0, range(1, 9)),
            ("DOWN", 20000.0, range(1, 2)),
            ("RESTORE", 40000.0, range(1, 2)),
        ):
            phase_start = base + phase_offset + role_index * 700.0
            for block in blocks:
                for pair_index in range(1, 41):
                    ordinal = (block - 1) * 40 + pair_index - 1
                    event_clock = phase_start + ordinal * 2.0 + 1.0
                    no_event_clock = event_clock + 0.5
                    pair_id = f"pair:{contact['spine_id']}:{phase}:{block}:{pair_index}"
                    event_raw = add_raw(pair_id + ":event", "THETA_SOURCE_EVENT_RAW")
                    no_event_raw = add_raw(pair_id + ":noevent", "THETA_MATCHED_NO_EVENT_RAW")
                    theta_rows.append(
                        {
                            **key,
                            "episode_id": contact["episode_id"],
                            "phase": phase,
                            "repeat_block": block,
                            "pair_index": pair_index,
                            "matched_pair_id": pair_id,
                            "h_id": f"h_{pair_index % 4}",
                            "c_id": f"c_{pair_index % 3}",
                            "split": "CALIBRATION" if pair_index <= 20 else "HOLDOUT",
                            "source_event_raw_id": event_raw,
                            "matched_no_event_raw_id": no_event_raw,
                            "source_event_verified": True,
                            "source_absence_verified": True,
                            "event_q_spine": 1.25,
                            "event_q_parent": 0.25,
                            "event_q_soma": 0.1,
                            "no_event_q_spine": 0.3,
                            "no_event_q_parent": 0.2,
                            "no_event_q_soma": 0.1,
                            "event_latency_ms": 2.0,
                            "common_mode_removed": True,
                            "measurement_state": "OBSERVED",
                            "theta_override": None,
                            "event_sensor_state": "OK",
                            "event_censor_lower": None,
                            "event_censor_upper": None,
                            "no_event_sensor_state": "OK",
                            "no_event_censor_lower": None,
                            "no_event_censor_upper": None,
                            "event_clock_ms": event_clock,
                            "no_event_clock_ms": no_event_clock,
                        }
                    )
    _write_jsonl(root / "theta_trial.jsonl", theta_rows)

    manipulation_rows: list[dict] = []
    for episode_index in range(2):
        episode_id = f"episode_{episode_index:02d}"
        base = episode_index * 100000.0
        for role in ("TARGET_A", "SHAM"):
            contact = next(
                row for row in registry
                if row["episode_id"] == episode_id and row["contact_role"] == role
            )
            key = {field: contact[field] for field in preflight.CONTACT_KEY_FIELDS}
            for phase, base_name, start_offset in (
                ("DOWN", "DEPRESSION", 10000.0),
                ("RESTORE", "POTENTIATION", 30000.0),
            ):
                manipulation_rows.append(
                    {
                        **key,
                        "episode_id": episode_id,
                        "matched_exposure_id": contact["matched_exposure_id"],
                        "phase": phase,
                        "actuator_channel": base_name if role == "TARGET_A" else f"SHAM_{base_name}",
                        "physical_channel_id": "dep-channel" if base_name == "DEPRESSION" else "pot-channel",
                        "construct_action": "ACTIVE" if role == "TARGET_A" else "INERT_SHAM",
                        "protocol_sha256": supporting_hashes[
                            "depression_protocol" if base_name == "DEPRESSION" else "potentiation_protocol"
                        ],
                        "wavelength_nm": 500.0 if base_name == "DEPRESSION" else 600.0,
                        "delivered_energy_uj": 1.0,
                        "start_clock_ms": base + start_offset,
                        "stop_clock_ms": base + start_offset + 1.0,
                        "structure_preserving_intent": True,
                    }
                )
    _write_jsonl(root / "manipulation_log.jsonl", manipulation_rows)

    spectral_rows: list[dict] = []
    for command, wavelength, physical_channel in (
        ("DEPRESSION", 500.0, "dep-channel"),
        ("POTENTIATION", 600.0, "pot-channel"),
    ):
        for readout in ("DEPRESSION", "POTENTIATION"):
            for replicate in range(1, 9):
                raw_id = add_raw(f"spectral:{command}:{readout}:{replicate}", "SPECTRAL_RAW")
                spectral_rows.append(
                    {
                        "calibration_id": "synthetic-spectral-calibration",
                        "session_id": "spectral-session-01",
                        "command": command,
                        "readout": readout,
                        "replicate": replicate,
                        "physical_channel_id": physical_channel,
                        "wavelength_nm": wavelength,
                        "command_energy_uj": 1.0,
                        "readout_device_id": "spectrometer-01",
                        "readout_device_version": "v1",
                        "response_unit": "synthetic-unit",
                        "response": 1.0 if command == readout else 0.0,
                        "temperature_delta_c": 0.0,
                        "sensor_saturated": False,
                        "raw_evidence_id": raw_id,
                    }
                )
    _write_jsonl(root / "spectral_calibration.jsonl", spectral_rows)

    (root / "raw_media.bin").write_bytes(bytes(raw_container))
    raw_manifest_path = root / preflight.SUPPORTING_FILENAMES["raw_media_manifest"]
    _write_jsonl(raw_manifest_path, raw_manifest)
    supporting_hashes["raw_media_manifest"] = hashlib.sha256(raw_manifest_path.read_bytes()).hexdigest()

    table_hashes = {
        table_name: hashlib.sha256((root / filename).read_bytes()).hexdigest()
        for table_name, filename in preflight.TABLE_FILENAMES.items()
    }
    manifest = {
        "schema_version": 1,
        "bundle_id": "SYNTHETIC_SCHEMA_FIXTURE_NOT_BIOLOGICAL_DATA",
        "input_kind": input_kind,
        "parent_contract_file_sha256": preflight.load_json(preflight.DEFAULT_CONTRACT)["parent_contract"]["json_file_sha256"],
        "preparation": {
            "species": "Mus musculus", "age": "ADULT", "age_weeks_inclusive": [12, 20],
            "region": "hindlimb M1", "layer": "L2/3",
            "cell_type": "L2/3 pyramidal neuron", "brain_state": "AWAKE",
        },
        "cohort": {
            "role": "TOOL_VALIDATION_ONLY",
            "animals": [{"animal_id": "animal_01", "age_days": 90, "sex": "F", "strain": "SYNTHETIC_TEST_ONLY"}],
            "reuse_for_model_controller_or_confirmation": False,
        },
        "authority": {
            "institutional_approval_status": "SYNTHETIC_NOT_APPLICABLE",
            "approval_id": "SYNTHETIC_TEST_ONLY",
            "biosafety_status": "SYNTHETIC_NOT_APPLICABLE",
            "biosafety_id": "SYNTHETIC_TEST_ONLY",
        },
        "channels": preflight.EXPECTED_CHANNELS,
        "channel_versions": {
            channel: ("theta-v1" if channel == "theta" else f"{channel}-v1")
            for channel in preflight.EXPECTED_CHANNELS
        },
        "channel_units": {channel: "synthetic-unit" for channel in preflight.EXPECTED_CHANNELS},
        "construct_version": "synthetic-construct",
        "optical_actuators": {
            "DEPRESSION": {"physical_channel_id": "dep-channel", "wavelength_nm": 500.0},
            "POTENTIATION": {"physical_channel_id": "pot-channel", "wavelength_nm": 600.0},
        },
        "monosynaptic_latency_window_ms": [1.0, 5.0],
        "input_file_sha256": table_hashes,
        "supporting_artifact_sha256": supporting_hashes,
        "protocol_frozen_before_first_animal": True,
        "sealed_before_outcome_review": True,
        "tool_validated": False,
        "biological_endpoint_evaluated": False,
    }
    _write_json(root / "acquisition_manifest.json", manifest)
    return root


@pytest.fixture(scope="session")
def valid_bundle(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _make_valid_synthetic_bundle(tmp_path_factory.mktemp("same_contact_bundle"))


def test_canonical_schema_passes_without_authorizing_or_evaluating(monkeypatch, capsys) -> None:
    contract = preflight.load_json(preflight.DEFAULT_CONTRACT)
    assert preflight.validate_contract(contract) == []
    monkeypatch.setattr(sys, "argv", ["preflight"])
    assert preflight.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "DEVELOPMENT_SCHEMA_PASS_LAB_INPUT_REQUIRED"
    assert report["execution_authorized"] is False
    assert report["tool_validated"] is False
    assert report["biological_endpoint_evaluated"] is False
    assert report["l4_gate_evaluated"] is False
    assert report["claim_ceiling"] == "BIO_EVIDENCE_L0"


def test_public_input_validator_always_enforces_canonical_parent_lock(valid_bundle: Path) -> None:
    contract = preflight.load_json(preflight.DEFAULT_CONTRACT)
    contract["contact_identity"]["minimum_target_a_contacts_per_animal_lab"] = 1
    contract["parent_contract"]["json_file_sha256"] = "0" * 64
    errors, _ = preflight.validate_input_bundle(valid_bundle, contract)
    assert any("contract lock failure" in error for error in errors)
    assert any("semantic fingerprint drift" in error for error in errors)


def test_valid_fixture_gets_only_synthetic_not_lab_status(valid_bundle: Path, monkeypatch, capsys) -> None:
    contract = preflight.load_json(preflight.DEFAULT_CONTRACT)
    errors, summary = preflight.validate_input_bundle(valid_bundle, contract)
    assert errors == []
    assert summary["input_kind"] == "SYNTHETIC_SCHEMA_FIXTURE"
    assert summary["animal_count"] == 1
    assert summary["output_cell_count"] == 8
    assert summary["contact_count"] == 10
    assert summary["episode_count"] == 2
    assert summary["theta_pair_count"] == 4000
    assert summary["manipulation_count"] == 8
    assert summary["morphology_stack_count"] == 60
    assert summary["spectral_calibration_count"] == 32
    assert summary["biological_loss_contact_count"] == 0

    monkeypatch.setattr(sys, "argv", ["preflight", "--input-root", str(valid_bundle)])
    assert preflight.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "SYNTHETIC_DEVELOPMENT_INPUT_SCHEMA_PASS_NOT_LAB_READY"
    assert report["tool_validated"] is False
    assert report["biological_endpoint_evaluated"] is False


def test_self_asserted_lab_authority_stops(valid_bundle: Path, tmp_path: Path) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    path = bundle / "acquisition_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["input_kind"] = "LAB_ACQUISITION"
    manifest["authority"] = {
        "institutional_approval_status": "APPROVED",
        "approval_id": "SELF_ASSERTED",
        "biosafety_status": "APPROVED",
        "biosafety_id": "SELF_ASSERTED",
    }
    _write_json(path, manifest)
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("ORIGIN_AUTHORITY_UNVERIFIED" in error for error in errors)


@pytest.mark.parametrize("age_days", [83, 141])
def test_parent_preparation_and_age_scope_are_exact(
    valid_bundle: Path, tmp_path: Path, age_days: int,
) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    path = bundle / "acquisition_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["preparation"]["region"] = "generic M1"
    manifest["cohort"]["animals"][0]["age_days"] = age_days
    _write_json(path, manifest)
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("must match parent 12-20 week" in error for error in errors)
    assert any("outside parent 12-20 week scope" in error for error in errors)


def test_supporting_artifact_and_raw_segment_are_rehashed(valid_bundle: Path, tmp_path: Path) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    safety = bundle / preflight.SUPPORTING_FILENAMES["safety"]
    safety.write_bytes(safety.read_bytes() + b"drift")
    raw = bundle / "raw_media.bin"
    payload = bytearray(raw.read_bytes())
    payload[0] ^= 1
    raw.write_bytes(bytes(payload))
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("supporting artifact hash drift: safety" in error for error in errors)
    assert any("raw-media segment hash drift" in error for error in errors)


def test_episode_target_and_exposure_links_fail_closed(valid_bundle: Path, tmp_path: Path) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    path = bundle / "contact_registry.jsonl"
    rows = _read_jsonl(path)
    rows[2]["target_contact_key"] = "wrong/target/key"
    rows[3]["matched_exposure_id"] = "unmatched-exposure"
    _write_jsonl(path, rows)
    _refresh_table_hash(bundle, "contact_registry")
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("target-contact link drift" in error for error in errors)
    assert any("exposure link drift" in error for error in errors)


def test_contact_replacement_roi_and_registration_drift_stop(valid_bundle: Path, tmp_path: Path) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    theta_path = bundle / "theta_trial.jsonl"
    theta = _read_jsonl(theta_path)
    theta[0]["spine_id"] = "replacement-spine"
    _write_jsonl(theta_path, theta)
    _refresh_table_hash(bundle, "theta_trial")
    morph_path = bundle / "morphology_stack.jsonl"
    morph = _read_jsonl(morph_path)
    morph[0]["roi_fingerprint_sha256"] = "0" * 64
    morph[1]["registration_receipt_sha256"] = "1" * 64
    _write_jsonl(morph_path, morph)
    _refresh_table_hash(bundle, "morphology_stack")
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("unknown/replaced contact" in error for error in errors)
    assert any("ROI fingerprint identity drift" in error for error in errors)
    assert any("registration receipt drift" in error for error in errors)


def test_matched_h_c_holdout_and_raw_evidence_cannot_be_reused(valid_bundle: Path, tmp_path: Path) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    path = bundle / "theta_trial.jsonl"
    rows = _read_jsonl(path)
    rows[0]["h_id"] = ""
    rows[0]["split"] = "HOLDOUT"
    rows[1]["matched_pair_id"] = rows[0]["matched_pair_id"]
    rows[1]["source_event_raw_id"] = rows[0]["source_event_raw_id"]
    _write_jsonl(path, rows)
    _refresh_table_hash(bundle, "theta_trial")
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("matched h,c missing" in error for error in errors)
    assert any("split drift" in error for error in errors)
    assert any("matched pair ID missing/reused" in error for error in errors)
    assert any("theta raw evidence reused" in error for error in errors)


def test_biological_loss_is_zero_and_technical_loss_stops(valid_bundle: Path, tmp_path: Path) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    path = bundle / "morphology_stack.jsonl"
    rows = _read_jsonl(path)
    for row in rows:
        if row["spine_id"] == "spine_00_TARGET_A" and row["phase"] == "DOWN":
            row["spine_present"] = False
        if row["spine_id"] == "spine_00_SHAM" and row["phase"] == "PRE":
            row["parent_visible"] = False
    _write_jsonl(path, rows)
    _refresh_table_hash(bundle, "morphology_stack")
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("technical NA from parent/sensor loss" in error for error in errors)
    assert any("biological loss must remain theta zero" in error for error in errors)


def test_timestamp_order_and_sham_exposure_matching_are_locked(valid_bundle: Path, tmp_path: Path) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    theta_path = bundle / "theta_trial.jsonl"
    theta = _read_jsonl(theta_path)
    theta[1]["event_clock_ms"] = theta[0]["event_clock_ms"]
    _write_jsonl(theta_path, theta)
    _refresh_table_hash(bundle, "theta_trial")
    manipulation_path = bundle / "manipulation_log.jsonl"
    manipulations = _read_jsonl(manipulation_path)
    sham_down = next(row for row in manipulations if row["spine_id"] == "spine_00_SHAM" and row["phase"] == "DOWN")
    sham_down["delivered_energy_uj"] = 2.0
    _write_jsonl(manipulation_path, manipulations)
    _refresh_table_hash(bundle, "manipulation_log")
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("theta block/pair timestamp order violated" in error for error in errors)
    assert any("sham is not exposure matched" in error for error in errors)


def test_spectral_session_device_unit_energy_and_raw_identity_are_locked(valid_bundle: Path, tmp_path: Path) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    path = bundle / "spectral_calibration.jsonl"
    rows = _read_jsonl(path)
    rows[0]["session_id"] = "other-session"
    rows[1]["command_energy_uj"] = 2.0
    rows[2]["raw_evidence_id"] = rows[1]["raw_evidence_id"]
    rows[3]["sensor_saturated"] = True
    _write_jsonl(path, rows)
    _refresh_table_hash(bundle, "spectral_calibration")
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("spectral session/device/version/unit drift" in error for error in errors)
    assert any("energy is not matched" in error for error in errors)
    assert any("spectral raw evidence missing/reused" in error for error in errors)
    assert any("spectral calibration saturated" in error for error in errors)


def test_input_manifest_cannot_self_promote(valid_bundle: Path, tmp_path: Path) -> None:
    bundle = _copy_bundle(valid_bundle, tmp_path)
    path = bundle / "acquisition_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["tool_validated"] = True
    manifest["biological_endpoint_evaluated"] = True
    _write_json(path, manifest)
    errors, _ = preflight.validate_input_bundle(bundle, preflight.load_json(preflight.DEFAULT_CONTRACT))
    assert any("cannot claim tool validation" in error for error in errors)
    assert any("cannot claim endpoint evaluation" in error for error in errors)


def test_strict_json_rejects_duplicates_and_nonfinite() -> None:
    with pytest.raises(preflight.DuplicateKeyError):
        preflight._loads_strict('{"x": 1, "x": 2}')
    with pytest.raises(ValueError, match="non-finite"):
        preflight._loads_strict('{"x": NaN}')
