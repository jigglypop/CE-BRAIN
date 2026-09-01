from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


MODULE_PATH = Path(__file__).with_name("validate_adult_l4_same_contact_lab_handoff_v1.py")
SPEC = importlib.util.spec_from_file_location("lab_handoff_validator", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def _canonical() -> dict:
    return validator.load_json(validator.DEFAULT_HANDOFF)


def test_canonical_handoff_is_external_action_only(monkeypatch, capsys) -> None:
    handoff = _canonical()
    assert validator.validate_handoff(handoff) == []
    monkeypatch.setattr(sys, "argv", ["handoff-validator"])
    assert validator.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "LAB_HANDOFF_SCHEMA_PASS_EXTERNAL_ACTION_REQUIRED"
    assert report["external_stop"] == "ORIGIN_AUTHORITY_UNVERIFIED"
    assert report["execution_authorized"] is False
    assert report["tool_validated"] is False
    assert report["biological_endpoint_evaluated"] is False
    assert report["l4_gate_evaluated"] is False
    assert report["claim_ceiling"] == "BIO_EVIDENCE_L0"


def test_locked_parent_and_development_files_are_rehashed() -> None:
    handoff = _canonical()
    handoff["locks"]["parent_contract"]["file_sha256"] = "0" * 64
    handoff["locks"]["development_preflight"]["file_sha256"] = "1" * 64
    errors = validator.validate_handoff(handoff)
    assert "parent_contract file hash drift" in errors
    assert "development_preflight file hash drift" in errors


def test_parent_preparation_and_operator_order_cannot_drift() -> None:
    handoff = _canonical()
    handoff["preparation"]["region"] = "generic M1"
    handoff["operator_sequence"][4], handoff["operator_sequence"][5] = (
        handoff["operator_sequence"][5], handoff["operator_sequence"][4]
    )
    errors = validator.validate_handoff(handoff)
    assert "parent preparation scope drift" in errors
    assert "operator sequence drift" in errors


def test_handoff_cannot_self_issue_authority_or_promote_claims() -> None:
    handoff = _canonical()
    handoff["external_authority"]["state"] = "TRUSTED"
    handoff["external_authority"]["canonical_lab_authority_lock_sha256"] = "2" * 64
    handoff["execution_authorized"] = True
    handoff["tool_validated"] = True
    handoff["biological_endpoint_evaluated"] = True
    handoff["l4_gate_evaluated"] = True
    handoff["claim_ceiling"] = "BIO_EVIDENCE_L4"
    errors = validator.validate_handoff(handoff)
    assert "external authority must remain pending and non-self-asserted" in errors
    assert "handoff cannot authorize execution" in errors
    assert "handoff cannot claim tool validation" in errors
    assert "handoff cannot claim biological evaluation" in errors
    assert "handoff cannot claim L4 evaluation" in errors
    assert "handoff claim ceiling drift" in errors


def test_public_data_branch_cannot_be_reopened_by_handoff() -> None:
    handoff = _canonical()
    handoff["public_data_policy"]["new_public_downloads_authorized"] = True
    handoff["public_data_policy"]["public_data_sufficiency_reaudit_authorized"] = True
    errors = validator.validate_handoff(handoff)
    assert "public-data freeze drift" in errors


def test_strict_json_rejects_duplicate_and_nonfinite(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"x": 1, "x": 2}', encoding="utf-8")
    with pytest.raises(validator.DuplicateKeyError):
        validator.load_json(duplicate)
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"x": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        validator.load_json(nonfinite)
