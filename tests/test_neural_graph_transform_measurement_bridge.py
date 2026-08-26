from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("quantitative_graph_transform", "quantitative_graph_transform.py")
_load("quantitative_c1_graph_transform", "quantitative_c1_graph_transform.py")
_load("quantitative_c2_graph_transform", "quantitative_c2_graph_transform.py")
_load("quantitative_c3_graph_transform", "quantitative_c3_graph_transform.py")
_load("quantitative_c4_graph_transform", "quantitative_c4_graph_transform.py")
_load("quantitative_arbitrary_order_graph_transform", "quantitative_arbitrary_order_graph_transform.py")
_load("quantitative_coupled_arbitrary_order_implicit_jet", "quantitative_coupled_arbitrary_order_implicit_jet.py")
_load("quantitative_coupled_graph_transform", "quantitative_coupled_graph_transform.py")
_load("quantitative_coupled_arbitrary_order_graph_transform", "quantitative_coupled_arbitrary_order_graph_transform.py")
_load("quantitative_local_coupled_arbitrary_order_graph_transform", "quantitative_local_coupled_arbitrary_order_graph_transform.py")
_load("quantitative_full_coupled_arbitrary_order_graph_transform", "quantitative_full_coupled_arbitrary_order_graph_transform.py")
E1 = _load("e1_metadata_receipt", "e1_metadata_receipt.py")
DIM = _load("conscious_moment_dimension_protocol", "conscious_moment_dimension_protocol.py")
M = _load("ce_neural_graph_transform_measurement_bridge", "neural_graph_transform_measurement_bridge.py")


def _parameters(order: int = 2, **overrides):
    tiny = F(1, 1_000_000)
    values = dict(
        base_reference_scale=1, fiber_reference_scale=1, fiber_radius=1,
        forcing_at_zero_upper=F(1, 10), base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 200), base_self_lipschitz=F(1, 100),
        fiber_to_base_lipschitz=F(9, 100), base_to_fiber_lipschitz=0,
        fiber_self_lipschitz=F(1, 200), graph_slope_upper=1,
        base_invertibility_lower=F(9, 10), preimage_value_coupling_upper=F(1, 10),
        input_base_domain_radius=1, output_base_domain_radius=1,
        uniform_inverse_base_image_radius_upper=1,
        input_extension_collar_radius=F(1, 10), output_extension_collar_radius=F(1, 20),
        uniform_inverse_collar_image_radius_upper=F(21, 20),
        uniform_inverse_base_image_radius_exact=1,
        uniform_forward_base_image_radius_exact=1,
        graph_boundary_value_upper=0, fiber_boundary_forcing_upper=0,
    )
    graph = (1, 1, 10, 100, 1000, 10000, 100000)
    for index in range(1, order + 2):
        values[f"graph_D{index}"] = F(graph[index - 1])
    for index in range(1, order + 1):
        values[f"base_K{index}"] = F(1, 2) if index == 1 else tiny
        values[f"base_H{index}"] = tiny
        values[f"fiber_K{index}"] = F(1, 100) if index == 1 else tiny
        values[f"fiber_H{index}"] = tiny
    values.update(overrides)
    return values


def _contract(order: int = 2, dimension: int = 4, level: str = M.MATCHED_LEVEL, **overrides):
    parameters = _parameters(order, **overrides)
    if level == M.GLOBAL_LEVEL:
        for name in (
            "input_base_domain_radius", "output_base_domain_radius",
            "input_extension_collar_radius", "output_extension_collar_radius",
            "uniform_inverse_base_image_radius_upper", "uniform_inverse_collar_image_radius_upper",
            "uniform_inverse_base_image_radius_exact", "uniform_forward_base_image_radius_exact",
            "graph_boundary_value_upper", "fiber_boundary_forcing_upper",
        ):
            parameters.pop(name)
    elif level == M.LOCAL_LEVEL:
        for name in (
            "uniform_inverse_base_image_radius_exact", "uniform_forward_base_image_radius_exact",
            "graph_boundary_value_upper", "fiber_boundary_forcing_upper",
        ):
            parameters.pop(name)
    return M.frozen_neural_graph_transform_measurement_contract(
        base_dimension=dimension, maximum_order=order,
        requested_theorem_level=level, parameters=parameters,
    )


def _specimens_by_split():
    result = {name: [] for name in ("calibration", "development", "held_out")}
    candidate = 0
    while min(len(values) for values in result.values()) < 3:
        split = E1.specimen_split(candidate)
        if len(result[split]) < 3:
            result[split].append(candidate)
        candidate += 1
    return result


def _receipt():
    rows = []
    session = 100
    for split, specimens in _specimens_by_split().items():
        for specimen in specimens:
            assert E1.specimen_split(specimen) == split
            rows.append(dict(
                ecephys_session_id=session,
                specimen_id=specimen,
                session_type="fixture",
                date_of_acquisition="2026-08-26T00:00:00Z",
            ))
            session += 1
    return E1.build_local_metadata_receipt(rows)


def _sessions(contract=None, receipt=None):
    contract = _contract() if contract is None else contract
    receipt = _receipt() if receipt is None else receipt
    p = dict(contract.parameters)
    result = []
    for line in receipt.assignment_jsonl.splitlines():
        import json
        assignment = json.loads(line)
        result.append(M.neural_map_session_envelope(
            ecephys_session_id=assignment["ecephys_session_id"],
            specimen_id=assignment["specimen_id"], split=assignment["split"],
            upper_envelopes={name: p[name] for name in contract.required_upper_envelope_names},
            lower_envelopes={name: p[name] for name in contract.required_lower_envelope_names},
        ))
    return tuple(result)


def _bridge(**overrides):
    contract = overrides.pop("frozen_contract", _contract())
    receipt = overrides.pop("metadata_receipt", _receipt())
    sessions = overrides.pop("session_envelopes", _sessions(contract, receipt))
    family_size = len(sessions) * (
        len(contract.required_upper_envelope_names) + len(contract.required_lower_envelope_names)
    )
    values = dict(
        metadata_receipt=receipt, frozen_contract=contract, session_envelopes=sessions,
        neural_observation_sha256="a" * 64, analysis_contract_sha256="b" * 64,
        preprocessing_sha256="c" * 64, model_family_sha256="d" * 64,
        simultaneous_coverage_kind=M.SIMULTANEOUS_COVERAGE_KIND,
        familywise_error_upper=F(1, 100), coverage_family_size=family_size,
        provenance_status=M.SYNTHETIC_FIXTURE,
    )
    values.update(overrides)
    return M.neural_graph_transform_measurement_bridge(**values)


def test_synthetic_measurement_bridge_routes_every_layer_without_empirical_promotion() -> None:
    result = _bridge()
    assert result.validation_level is not None
    assert result.all_session_envelopes_within_frozen_family is True
    assert result.full_global_certificate.validation_level is not None
    assert result.full_local_certificate.validation_level is not None
    assert result.full_matched_certificate.validation_level is not None
    assert result.source_locked_empirical_neural_graph_result is False
    assert result.consciousness_claim_admitted is False
    assert result.dimension_4_6_claim_admitted is False
    assert result.specimen_count_by_split == (("calibration", 3), ("development", 3), ("held_out", 3))


def test_source_locked_label_cannot_replace_a_remote_execution_receipt() -> None:
    result = _bridge(provenance_status=M.SOURCE_LOCKED_EMPIRICAL)
    assert result.validation_level is not None
    assert result.external_remote_metadata_receipt_verified is False
    assert result.source_locked_empirical_neural_graph_result is False
    assert result.status == "VALIDATED_DECLARED_SOURCE_LOCKED_NEURAL_GRAPH_SUMMARY_APPARATUS_ONLY"
    assert result.consciousness_claim_admitted is False
    assert result.dimension_4_6_claim_admitted is False


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    contract = _contract(dimension=dimension)
    result = _bridge(frozen_contract=contract, session_envelopes=_sessions(contract))
    assert result.full_matched_certificate.full_matched_local_cn_graph_real_dimension == dimension
    assert result.dimension_4_6_claim_admitted is False


def test_upper_and_lower_heldout_violations_fail_closed_with_session_and_quantity() -> None:
    contract = _contract()
    receipt = _receipt()
    sessions = list(_sessions(contract, receipt))
    target = next(index for index, row in enumerate(sessions) if row.split == "held_out")
    row = sessions[target]
    upper = dict(row.upper_envelopes)
    upper["fiber_K1"] += F(1, 1000)
    sessions[target] = M.neural_map_session_envelope(
        ecephys_session_id=row.ecephys_session_id, specimen_id=row.specimen_id, split=row.split,
        upper_envelopes=upper, lower_envelopes=dict(row.lower_envelopes),
    )
    failed = _bridge(frozen_contract=contract, metadata_receipt=receipt, session_envelopes=tuple(sessions))
    assert any("fiber_K1_UPPER_VIOLATION" in code for code in failed.failure_codes)
    lower = dict(row.lower_envelopes)
    lower["base_invertibility_lower"] -= F(1, 100)
    sessions[target] = M.neural_map_session_envelope(
        ecephys_session_id=row.ecephys_session_id, specimen_id=row.specimen_id, split=row.split,
        upper_envelopes=dict(row.upper_envelopes), lower_envelopes=lower,
    )
    failed = _bridge(frozen_contract=contract, metadata_receipt=receipt, session_envelopes=tuple(sessions))
    assert any("base_invertibility_lower_LOWER_VIOLATION" in code for code in failed.failure_codes)


def test_metadata_assignment_and_complete_session_set_are_mandatory() -> None:
    sessions = list(_sessions())
    row = sessions[0]
    sessions[0] = M.neural_map_session_envelope(
        ecephys_session_id=row.ecephys_session_id, specimen_id=row.specimen_id,
        split="held_out" if row.split != "held_out" else "calibration",
        upper_envelopes=dict(row.upper_envelopes), lower_envelopes=dict(row.lower_envelopes),
    )
    mismatch = _bridge(session_envelopes=tuple(sessions))
    assert any("ASSIGNMENT_MISMATCH" in code for code in mismatch.failure_codes)
    missing = _bridge(session_envelopes=tuple(_sessions())[:-1])
    assert "NEURAL_BRIDGE_SESSION_SET_DOES_NOT_MATCH_METADATA_RECEIPT" in missing.failure_codes


def test_duplicate_session_envelope_is_rejected() -> None:
    sessions = _sessions()
    result = _bridge(session_envelopes=sessions + (sessions[0],))
    assert result.status == "NEURAL_BRIDGE_DUPLICATE_SESSION_ENVELOPE"


def test_envelope_schema_must_be_exact() -> None:
    sessions = list(_sessions())
    row = sessions[0]
    upper = dict(row.upper_envelopes)
    upper.pop("fiber_H2")
    sessions[0] = M.neural_map_session_envelope(
        ecephys_session_id=row.ecephys_session_id, specimen_id=row.specimen_id, split=row.split,
        upper_envelopes=upper, lower_envelopes=dict(row.lower_envelopes),
    )
    result = _bridge(session_envelopes=tuple(sessions))
    assert any("ENVELOPE_SCHEMA_MISMATCH" in code for code in result.failure_codes)


def test_coverage_method_and_complete_family_count_fail_independently() -> None:
    wrong_method = _bridge(simultaneous_coverage_kind="POINTWISE_INTERVAL")
    assert "NEURAL_BRIDGE_COVERAGE_NOT_FAMILYWISE_SIMULTANEOUS" in wrong_method.failure_codes
    wrong_count = _bridge(coverage_family_size=1)
    assert "NEURAL_BRIDGE_COVERAGE_FAMILY_SIZE_MISMATCH" in wrong_count.failure_codes


@pytest.mark.parametrize("error", [0, F(1, 20), F(1, 10), 0.01])
def test_familywise_error_must_be_exact_positive_and_strictly_below_five_percent(error) -> None:
    with pytest.raises(ValueError):
        _bridge(familywise_error_upper=error)


def test_invalid_hash_is_rejected() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        _bridge(neural_observation_sha256="not-a-hash")


def test_theorem_chain_failure_is_not_hidden_by_valid_measurement_envelopes() -> None:
    contract = _contract(graph_D2=0)
    result = _bridge(frozen_contract=contract, session_envelopes=_sessions(contract))
    assert result.validation_level is None
    assert any("GRAPH_JET_CLASS_NOT_INVARIANT" in code for code in result.failure_codes)


def test_contract_schema_rejects_missing_and_extra_parameters() -> None:
    missing = _parameters()
    missing.pop("fiber_H2")
    with pytest.raises(ValueError, match="schema mismatch"):
        M.frozen_neural_graph_transform_measurement_contract(
            base_dimension=4, maximum_order=2,
            requested_theorem_level=M.MATCHED_LEVEL, parameters=missing
        )
    extra = _parameters()
    extra["post_hoc_parameter"] = 1
    with pytest.raises(ValueError, match="schema mismatch"):
        M.frozen_neural_graph_transform_measurement_contract(
            base_dimension=4, maximum_order=2,
            requested_theorem_level=M.MATCHED_LEVEL, parameters=extra
        )


@pytest.mark.parametrize(
    "level,expected",
    [(M.GLOBAL_LEVEL, M.GLOBAL_LEVEL), (M.LOCAL_LEVEL, M.LOCAL_LEVEL), (M.MATCHED_LEVEL, M.MATCHED_LEVEL)],
)
def test_predeclared_global_local_and_matched_routes_require_only_their_level(level, expected) -> None:
    contract = _contract(level=level)
    result = _bridge(frozen_contract=contract, session_envelopes=_sessions(contract))
    assert result.validation_level is not None
    assert result.requested_theorem_level == level
    assert result.highest_verified_theorem_level == expected
    if level == M.GLOBAL_LEVEL:
        assert result.full_local_certificate is None
        assert result.full_matched_certificate is None
    elif level == M.LOCAL_LEVEL:
        assert result.full_local_certificate.validation_level is not None
        assert result.full_matched_certificate is None


@pytest.mark.parametrize(
    "session_id,specimen_id,split",
    [("01", "1", "calibration"), ("1", "-1", "calibration"), ("1", "1", "train")],
)
def test_session_identity_and_split_are_canonical(session_id, specimen_id, split) -> None:
    with pytest.raises(ValueError):
        M.neural_map_session_envelope(
            ecephys_session_id=session_id, specimen_id=specimen_id, split=split,
            upper_envelopes={"x": 1}, lower_envelopes={"y": 1},
        )


def _scores(winner: int):
    return {
        dimension: tuple(F(100) - 10 * abs(dimension - winner) - F(dimension, 100) for _ in range(4))
        for dimension in DIM.FROZEN_DIMENSION_MENU
    }


def _dimension_certificate(winner: int = 5, provenance_status: str = DIM.SYNTHETIC_FIXTURE):
    spectrum = (F(1),) * winner + (F(0),) * (12 - winner)
    return DIM.conscious_moment_dimension_identification_protocol(
        signal_covariance_spectra=(spectrum, spectrum, spectrum),
        ridge_regularization=F(1, 10), rank_tolerance=0,
        estimator_agreement_tolerance=1,
        conscious_fold_scores_by_dimension=_scores(winner),
        control_fold_scores_by_dimension={d: (0, 0, 0, 0) for d in DIM.FROZEN_DIMENSION_MENU},
        permutation_exceedances=0, permutation_repetitions=1000,
        permutation_alpha=F(1, 20), provenance_status=provenance_status,
        spectrum_kind=DIM.SIGNAL_SPECTRUM_KIND, permutation_scope=DIM.PERMUTATION_SCOPE,
    )


def _heldout_ids(measurement):
    return tuple(session for session, _specimen, split in measurement.session_assignments if split == "held_out")


def test_joint_adapter_matches_dimension_sessions_but_forbids_dimension_identity() -> None:
    measurement = _bridge()
    dimension = _dimension_certificate(5)
    result = M.neural_graph_and_signal_rank_joint_certificate(
        measurement_certificate=measurement, dimension_certificate=dimension,
        dimension_session_ids=_heldout_ids(measurement),
    )
    assert result.validation_level is not None
    assert result.graph_base_dimension == 4
    assert result.selected_neural_signal_rank == 5
    assert result.graph_dimension_equals_signal_rank_numerically is False
    assert result.graph_dimension_signal_rank_identity_claim_admitted is False
    assert result.source_locked_joint_empirical_result is False
    assert result.consciousness_claim_admitted is False


def test_even_numerically_equal_graph_and_signal_dimensions_are_not_identified() -> None:
    measurement = _bridge()
    result = M.neural_graph_and_signal_rank_joint_certificate(
        measurement_certificate=measurement, dimension_certificate=_dimension_certificate(4),
        dimension_session_ids=_heldout_ids(measurement),
    )
    assert result.graph_dimension_equals_signal_rank_numerically is True
    assert result.graph_dimension_signal_rank_identity_claim_admitted is False


def test_joint_adapter_rejects_session_count_set_and_provenance_mismatches() -> None:
    measurement = _bridge()
    heldout = _heldout_ids(measurement)
    missing = M.neural_graph_and_signal_rank_joint_certificate(
        measurement_certificate=measurement, dimension_certificate=_dimension_certificate(),
        dimension_session_ids=heldout[:-1],
    )
    assert "NEURAL_JOINT_DIMENSION_SESSIONS_DO_NOT_MATCH_HELDOUT_SPLIT" in missing.failure_codes
    assert "NEURAL_JOINT_DIMENSION_SESSION_COUNT_MISMATCH" in missing.failure_codes
    provenance = M.neural_graph_and_signal_rank_joint_certificate(
        measurement_certificate=measurement,
        dimension_certificate=_dimension_certificate(provenance_status=DIM.SOURCE_LOCKED_EMPIRICAL),
        dimension_session_ids=heldout,
    )
    assert "NEURAL_JOINT_PROVENANCE_STATUS_MISMATCH" in provenance.failure_codes


def test_matching_declared_source_labels_still_cannot_create_joint_empirical_evidence() -> None:
    measurement = _bridge(provenance_status=M.SOURCE_LOCKED_EMPIRICAL)
    result = M.neural_graph_and_signal_rank_joint_certificate(
        measurement_certificate=measurement,
        dimension_certificate=_dimension_certificate(provenance_status=DIM.SOURCE_LOCKED_EMPIRICAL),
        dimension_session_ids=_heldout_ids(measurement),
    )
    assert result.validation_level is not None
    assert result.source_locked_joint_empirical_result is False
    assert result.consciousness_claim_admitted is False
