from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


MAN_TEST = _load_path(
    "dimension_manifest_test_fixtures",
    ROOT / "tests" / "test_verified_dimension_observation_manifest.py",
)
M = MAN_TEST.M
R = _load_path("verified_dimension_source_bytes_receipt", MODULE_DIR / "verified_dimension_source_bytes_receipt.py")


def _payload_values():
    source = MAN_TEST._manifest_args()
    base = source["base_dimension_certificate"]
    ids = source["session_ids"]
    return source, (
        (
            "CE-DIM-DEVELOPMENT-v1", ids,
            source["development_observation_ids_by_session"],
            source["raw_development_observations_by_session"],
        ),
        (
            "CE-DIM-HELDOUT-v1", ids,
            source["conscious_heldout_observation_ids_by_session"],
            source["raw_conscious_heldout_observations_by_session"],
            source["control_heldout_observation_ids_by_session"],
            source["raw_control_heldout_observations_by_session"],
        ),
        ("CE-DIM-PREPROCESSING-v1", ids, source["coordinate_reference_scales_by_session"]),
        ("CE-DIM-EIGENBASIS-v1", ids, source["covariance_eigenbasis_witnesses_by_session"]),
        (
            "CE-DIM-BOOTSTRAP-v1", ids, source["frozen_block_length"],
            source["bootstrap_window_indices_by_session"],
        ),
        (
            "CE-DIM-EXECUTION-CONTRACT-v1", base.frozen_dimension_menu, base.candidate_band,
            base.selected_signal_rank, source["complexity_penalty"], source["window_partition_kind"],
            source["block_bootstrap_kind"], source["minimum_conscious_band_window_fraction"],
            source["minimum_selected_rank_window_fraction"],
            source["maximum_conscious_rank_transition_fraction"],
            source["minimum_selected_rank_longest_dwell_fraction"],
            source["minimum_conscious_control_band_gap"], source["minimum_bootstrap_band_fraction"],
            source["minimum_bootstrap_selected_rank_fraction"],
        ),
    )


def _receipt_args(values=None):
    source, default_values = _payload_values()
    values = default_values if values is None else values
    payloads = tuple(M.canonical_exact_bytes(value) for value in values)
    return {
        "base_dimension_certificate": source["base_dimension_certificate"],
        "development_archive_bytes": payloads[0],
        "heldout_archive_bytes": payloads[1],
        "preprocessing_archive_bytes": payloads[2],
        "eigenbasis_archive_bytes": payloads[3],
        "bootstrap_archive_bytes": payloads[4],
        "execution_contract_archive_bytes": payloads[5],
        "expected_source_bundle_sha256": R.canonical_dimension_source_bundle_sha256(*payloads),
    }


def _run(values=None, **overrides):
    args = _receipt_args(values); args.update(overrides)
    return R.verified_dimension_source_bytes_receipt(**args)


def test_canonical_archive_bytes_reconstruct_and_execute_full_chain() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.canonical_archive_bytes_verified
    assert result.canonical_source_archive_receipt_verified
    assert result.observation_manifest.validation_level is not None


def test_canonical_decoder_round_trips_exact_payload() -> None:
    value = ("영역", 1, {"b": 2, "a": 3})
    encoded = M.canonical_exact_bytes(value)
    assert M.canonical_exact_from_bytes(encoded) == value


def test_semantically_valid_noncanonical_whitespace_is_rejected() -> None:
    args = _receipt_args()
    args["development_archive_bytes"] += b" "
    with pytest.raises(ValueError, match="byte-for-byte"):
        R.verified_dimension_source_bytes_receipt(**args)


def test_unreduced_rational_archive_token_is_rejected() -> None:
    with pytest.raises(ValueError, match="reduced"):
        M.canonical_exact_from_bytes(b'["q","2","2"]')


def test_frozen_bundle_root_mismatch_fails_before_manifest() -> None:
    result = _run(expected_source_bundle_sha256="0" * 64)
    assert result.status == "DIMENSION_SOURCE_BUNDLE_HASH_MISMATCH"
    assert result.observation_manifest is None


def test_wrong_domain_tag_fails_closed_even_with_recomputed_bundle_root() -> None:
    _, values = _payload_values()
    changed = list(values); changed[0] = ("CE-DIM-WRONG-v1", *changed[0][1:])
    result = _run(tuple(changed))
    assert "DIMENSION_SOURCE_DOMAIN_OR_SHAPE_MISMATCH" in result.failure_codes


def test_cross_domain_session_identity_mismatch_fails_closed() -> None:
    _, values = _payload_values()
    changed = list(values)
    heldout = list(changed[1]); heldout[1] = ("other-session", *heldout[1][1:]); changed[1] = tuple(heldout)
    result = _run(tuple(changed))
    assert "DIMENSION_SOURCE_SESSION_ID_MISMATCH" in result.failure_codes


def test_archive_contract_must_match_base_dimension_certificate() -> None:
    _, values = _payload_values()
    changed = list(values)
    contract = list(changed[5]); contract[3] = 4; changed[5] = tuple(contract)
    result = _run(tuple(changed))
    assert "DIMENSION_SOURCE_BASE_CONTRACT_MISMATCH" in result.failure_codes


def test_archive_receipt_is_not_external_acquisition_or_consciousness_evidence() -> None:
    result = _run()
    assert not result.external_acquisition_signature_verified
    assert not result.original_device_byte_parser_verified
    assert not result.source_locked_empirical_dimension_result
    assert not result.consciousness_dimension_claim_admitted
