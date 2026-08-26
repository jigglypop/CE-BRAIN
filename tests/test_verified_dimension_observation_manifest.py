from __future__ import annotations

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
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FIX = _load_path("dimension_preprocessing_test_fixtures", ROOT / "tests" / "test_verified_dimension_preprocessing_execution.py")
M = _load_path("verified_dimension_observation_manifest", MODULE_DIR / "verified_dimension_observation_manifest.py")


def _development_ids(observations):
    return tuple(tuple(f"dev-{s}-{i}" for i in range(len(rows))) for s, rows in enumerate(observations))


def _window_ids(observations, prefix: str):
    return tuple(
        tuple(tuple(f"{prefix}-{s}-{w}-{i}" for i in range(len(rows))) for w, rows in enumerate(windows))
        for s, windows in enumerate(observations)
    )


def _manifest_args():
    source = FIX._args()
    ids = source["session_ids"]
    development = source["raw_development_observations_by_session"]
    conscious = source["raw_conscious_heldout_observations_by_session"]
    control = source["raw_control_heldout_observations_by_session"]
    development_ids = _development_ids(development)
    conscious_ids = _window_ids(conscious, "conscious")
    control_ids = _window_ids(control, "control")
    expected_development = M.canonical_exact_sha256(("CE-DIM-DEVELOPMENT-v1", ids, development_ids, development))
    expected_heldout = M.canonical_exact_sha256(("CE-DIM-HELDOUT-v1", ids, conscious_ids, conscious, control_ids, control))
    expected_preprocessing = M.canonical_exact_sha256(("CE-DIM-PREPROCESSING-v1", ids, source["coordinate_reference_scales_by_session"]))
    expected_eigenbasis = M.canonical_exact_sha256(("CE-DIM-EIGENBASIS-v1", ids, source["covariance_eigenbasis_witnesses_by_session"]))
    expected_bootstrap = M.canonical_exact_sha256(("CE-DIM-BOOTSTRAP-v1", ids, source["frozen_block_length"], source["bootstrap_window_indices_by_session"]))
    base = source["base_dimension_certificate"]
    expected_contract = M.canonical_exact_sha256((
        "CE-DIM-EXECUTION-CONTRACT-v1", base.frozen_dimension_menu, base.candidate_band,
        base.selected_signal_rank, source["complexity_penalty"], source["window_partition_kind"],
        source["block_bootstrap_kind"], source["minimum_conscious_band_window_fraction"],
        source["minimum_selected_rank_window_fraction"], source["maximum_conscious_rank_transition_fraction"],
        source["minimum_selected_rank_longest_dwell_fraction"], source["minimum_conscious_control_band_gap"],
        source["minimum_bootstrap_band_fraction"], source["minimum_bootstrap_selected_rank_fraction"],
    ))
    for key in (
        "raw_development_sha256", "raw_heldout_sha256", "preprocessing_contract_sha256",
        "eigenbasis_witness_sha256", "bootstrap_schedule_sha256", "execution_contract_sha256",
    ):
        source.pop(key)
    source.update(
        development_observation_ids_by_session=development_ids,
        conscious_heldout_observation_ids_by_session=conscious_ids,
        control_heldout_observation_ids_by_session=control_ids,
        expected_development_payload_sha256=expected_development,
        expected_heldout_payload_sha256=expected_heldout,
        expected_preprocessing_payload_sha256=expected_preprocessing,
        expected_eigenbasis_payload_sha256=expected_eigenbasis,
        expected_bootstrap_payload_sha256=expected_bootstrap,
        expected_execution_contract_sha256=expected_contract,
    )
    return source


def _run(**overrides):
    args = _manifest_args(); args.update(overrides)
    return M.verified_dimension_observation_manifest(**args)


def test_canonical_hashes_and_disjoint_ids_compose_full_chain() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.expected_hashes_match_computed_payloads
    assert result.observation_id_shapes_match_payloads
    assert result.observation_ids_globally_unique_across_splits
    assert result.preprocessing_execution.validation_level is not None


def test_canonical_exact_hash_normalizes_integer_and_fraction_values() -> None:
    assert M.canonical_exact_sha256((1, F(2, 2))) == M.canonical_exact_sha256((F(1), 1))
    assert M.canonical_exact_sha256({"b": 2, "a": 1}) == M.canonical_exact_sha256({"a": 1, "b": 2})


def test_float_and_boolean_are_forbidden_in_canonical_payloads() -> None:
    with pytest.raises(ValueError, match="forbid"):
        M.canonical_exact_sha256((0.1,))
    with pytest.raises(ValueError, match="forbid"):
        M.canonical_exact_sha256((True,))


def test_expected_hash_mismatch_fails_before_preprocessing() -> None:
    result = _run(expected_development_payload_sha256="0" * 64)
    assert result.status == "DIMENSION_MANIFEST_EXPECTED_HASH_MISMATCH"
    assert result.preprocessing_execution is None


def test_payload_mutation_invalidates_frozen_hash() -> None:
    args = _manifest_args()
    development = [list(rows) for rows in args["raw_development_observations_by_session"]]
    row = list(development[0][0]); row[0] += 1; development[0][0] = tuple(row)
    result = _run(raw_development_observations_by_session=tuple(tuple(rows) for rows in development))
    assert "DIMENSION_MANIFEST_EXPECTED_HASH_MISMATCH" in result.failure_codes


def test_observation_id_shape_mismatch_fails_closed() -> None:
    ids = list(_manifest_args()["development_observation_ids_by_session"])
    ids[0] = ids[0][:-1]
    result = _run(development_observation_ids_by_session=tuple(ids))
    assert "DIMENSION_MANIFEST_OBSERVATION_ID_SHAPE_MISMATCH" in result.failure_codes


def test_cross_split_observation_id_overlap_fails_closed() -> None:
    args = _manifest_args()
    control_ids = [[list(window) for window in session] for session in args["control_heldout_observation_ids_by_session"]]
    control_ids[0][0][0] = args["development_observation_ids_by_session"][0][0]
    result = _run(control_heldout_observation_ids_by_session=tuple(tuple(tuple(window) for window in session) for session in control_ids))
    assert "DIMENSION_MANIFEST_OBSERVATION_ID_SPLIT_OVERLAP" in result.failure_codes


def test_content_hash_is_not_an_external_source_signature() -> None:
    result = _run()
    assert result.canonical_exact_payload_encoding_verified
    assert result.content_addressed_dimension_chain_composed
    assert not result.external_source_signature_verified
    assert not result.source_locked_empirical_dimension_result
    assert not result.consciousness_dimension_claim_admitted
