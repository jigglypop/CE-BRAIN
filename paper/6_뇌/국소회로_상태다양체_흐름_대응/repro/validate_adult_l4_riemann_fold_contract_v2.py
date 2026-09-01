from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Any, Iterable

import scipy
import numpy as np
from scipy.integrate import quad
from scipy.stats import beta, binom, chi2, nct, norm, t


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "adult_l4_riemann_fold_contract_v2.json"
DEFAULT_MARKDOWN = HERE.parents[2] / "검증_원장" / "CE_NPF_ADULT_L4_리만접힘_실험계약_v2.md"

CANONICAL_SEMANTIC_SHA256 = "afe1974baeb6a0ba8ea7cd1bd9f8e893131d75f2e045fafd91a8e87df737717c"
CANONICAL_MARKDOWN_SHA256 = "53e7fcb7857201e11981fa78045843b298bbfb91229c1cf5859a671c40107baf"

TOP_LEVEL_KEYS = {
    "schema_version",
    "contract_id",
    "status",
    "execution_authorized",
    "l4_gate_evaluated",
    "biological_endpoint_evaluated",
    "claim_ceiling",
    "normative_markdown",
    "scope",
    "data_budget",
    "source_anchors",
    "biological_starting_mechanism",
    "causal_objects",
    "channels",
    "identity",
    "theta_measurement",
    "measurement_and_analysis",
    "state_chart",
    "temporal_windows_ms",
    "mediator_state",
    "output_model",
    "behavior_endpoint",
    "probe_design",
    "fisher_geometry",
    "fold_summary",
    "cohorts",
    "randomization",
    "interventions",
    "power",
    "estimands",
    "atomic_test_ledger",
    "missingness",
    "causal_assumptions",
    "required_gates",
    "stop_states",
    "forbidden",
}

EXPECTED_CHANNELS = {
    "actuator": "ACTUATOR_LOG",
    "source_state": "SOURCE_STATE_CHANNEL",
    "theta": "THETA_CHANNEL",
    "mediator_state": "MEDIATOR_STATE_CHANNEL",
    "output": "OUTPUT_CHANNEL",
    "behavior": "BEHAVIOR_CHANNEL",
}

EXPECTED_ESTIMANDS: list[dict[str, Any]] = [
    {"id": "E_THETA_TARGET_SHAM", "direction": "TARGET_LT_SHAM", "test_family": "DIRECTIONAL_BETWEEN"},
    {"id": "E_THETA_TARGET_OFFTARGET", "direction": "TARGET_LT_OFFTARGET", "test_family": "DIRECTIONAL_BETWEEN"},
    {"id": "E_MG_TARGET_SHAM", "direction": "TARGET_LT_SHAM", "test_family": "DIRECTIONAL_BETWEEN"},
    {"id": "E_MG_TARGET_OFFTARGET", "direction": "TARGET_LT_OFFTARGET", "test_family": "DIRECTIONAL_BETWEEN"},
    {"id": "E_YA_TARGET_SHAM", "direction": "TARGET_WORSE_THAN_SHAM", "test_family": "DIRECTIONAL_BETWEEN"},
    {"id": "E_YA_TARGET_OFFTARGET", "direction": "TARGET_WORSE_THAN_OFFTARGET", "test_family": "DIRECTIONAL_BETWEEN"},
    {"id": "E_TASK_SPECIFICITY", "direction": "TARGET_EFFECT_A_GREATER_THAN_TARGET_EFFECT_B", "test_family": "DIRECTIONAL_PAIRED"},
    {"id": "E_ACTUATOR_DIRECT_PATH", "direction": "FOUR_STATE_UPPER_EQUIVALENCE", "test_family": "ONE_SAMPLE_UPPER_MARGIN", "upper_margin_sd": 0.5, "elpd_upper_margin_nat_per_trial": 0.01},
    {"id": "E_M_RESTORE_OFF", "direction": "RESTORE_CLOSER_TO_M_PRE_THAN_OFF", "test_family": "DIRECTIONAL_PAIRED"},
    {"id": "E_M_RESTORE_ORTH", "direction": "RESTORE_CLOSER_TO_M_PRE_THAN_ORTHOGONAL", "test_family": "DIRECTIONAL_PAIRED"},
    {"id": "E_MG_RESTORE_OFF", "direction": "RESTORE_GT_OFF", "test_family": "DIRECTIONAL_PAIRED"},
    {"id": "E_MG_RESTORE_ORTH", "direction": "RESTORE_GT_ORTHOGONAL", "test_family": "DIRECTIONAL_PAIRED"},
    {"id": "E_YA_RESTORE_OFF", "direction": "RESTORE_GT_OFF", "test_family": "DIRECTIONAL_PAIRED"},
    {"id": "E_YA_RESTORE_ORTH", "direction": "RESTORE_GT_ORTHOGONAL", "test_family": "DIRECTIONAL_PAIRED"},
    {"id": "E_MG_ORTH_OFF", "direction": "PAIRED_EQUIVALENCE", "test_family": "PAIRED_EQUIVALENCE", "equivalence_margin_sd": 0.5},
    {"id": "E_YA_ORTH_OFF", "direction": "PAIRED_EQUIVALENCE", "test_family": "PAIRED_EQUIVALENCE", "equivalence_margin_sd": 0.5},
    {"id": "E_THETA_CONTROLLER_INVARIANCE", "direction": "PAIRED_EQUIVALENCE", "test_family": "PAIRED_EQUIVALENCE", "equivalence_margin_sd": 0.5},
    {"id": "E_Z_CONTROLLER_INVARIANCE", "direction": "PAIRED_EQUIVALENCE", "test_family": "PAIRED_EQUIVALENCE", "equivalence_margin_sd": 0.5},
    {"id": "E_M_TARGETPROJECTION_ORTH_OFF", "direction": "PAIRED_EQUIVALENCE", "test_family": "PAIRED_EQUIVALENCE", "equivalence_margin_sd": 0.5},
    {"id": "E_CONTROLLER_ARM_INTERACTION", "direction": "THREE_FROZEN_ENDPOINT_RESTORE_MINUS_OFF_TARGET_GT_SHAM", "test_family": "DIRECTIONAL_BETWEEN"},
    {"id": "E_NUISANCE_KERNEL", "direction": "PAIRED_EQUIVALENCE", "test_family": "PAIRED_EQUIVALENCE", "equivalence_margin_sd": 0.5},
    {"id": "E_M_TO_LOCAL_FOLD_MAP", "direction": "THREE_STATE_HELDOUT_SCORE_GT_ZERO", "test_family": "ONE_SAMPLE_LOWER_DIRECTIONAL", "design_alternative_sd": 0.5},
    {"id": "E_M_TO_LOCAL_FOLD_DERIVATIVE", "direction": "THREE_STATE_MIN_TARGET_DERIVATIVE_GT_0.20", "test_family": "ONE_SAMPLE_LOWER_MARGIN", "physical_lower_margin": 0.2, "design_alternative_sd": 0.5},
    {"id": "E_THETA_SAME_CONTACT_RESCUE", "direction": "ABSOLUTE_CONTACT_ERROR_UPPER_EQUIVALENCE", "test_family": "ONE_SAMPLE_UPPER_MARGIN", "upper_margin_sd": 0.5},
    {"id": "E_THETA_CONTACT_FRACTION_RESCUE", "direction": "ANIMAL_PASS_FRACTION_LCL_GE_0.90", "test_family": "BINOMIAL_PASS_FRACTION", "design_pass_fraction": 0.995},
    {"id": "E_MG_RESCUE_CONTROLS", "direction": "RESTORE_GT_RESCUE_SHAM_AND_PASSIVE", "test_family": "DIRECTIONAL_BETWEEN"},
    {"id": "E_YA_RESCUE_CONTROLS", "direction": "RESTORE_GT_RESCUE_SHAM_AND_PASSIVE", "test_family": "DIRECTIONAL_BETWEEN"},
    {"id": "E_OPEN_PATCH_UNIFORM_SPD", "direction": "FOUR_STATE_ANIMAL_CERTIFICATE_FRACTION_LCL_GE_0.90", "test_family": "BINOMIAL_PASS_FRACTION", "design_pass_fraction": 0.995},
    {"id": "E_ORDERED_PATH_DIRECTIONAL_EQUIVALENCE", "direction": "TWENTY_FOUR_STATE_BY_FULL_PHASE_HARMONIC_UPPER_EQUIVALENCE", "test_family": "ONE_SAMPLE_UPPER_MARGIN", "upper_margin_sd": 0.5, "elpd_upper_margin_nat_per_trial": 0.01},
]

EXPECTED_ATOMIC_TEST_LEDGER = [
    {"estimand_id": "E_THETA_TARGET_SHAM", "atomic_tests": 1},
    {"estimand_id": "E_THETA_TARGET_OFFTARGET", "atomic_tests": 1},
    {"estimand_id": "E_MG_TARGET_SHAM", "atomic_tests": 1},
    {"estimand_id": "E_MG_TARGET_OFFTARGET", "atomic_tests": 1},
    {"estimand_id": "E_YA_TARGET_SHAM", "atomic_tests": 1},
    {"estimand_id": "E_YA_TARGET_OFFTARGET", "atomic_tests": 1},
    {"estimand_id": "E_TASK_SPECIFICITY", "atomic_tests": 1},
    {"estimand_id": "E_ACTUATOR_DIRECT_PATH", "atomic_tests": 4},
    {"estimand_id": "E_M_RESTORE_OFF", "atomic_tests": 1},
    {"estimand_id": "E_M_RESTORE_ORTH", "atomic_tests": 1},
    {"estimand_id": "E_MG_RESTORE_OFF", "atomic_tests": 1},
    {"estimand_id": "E_MG_RESTORE_ORTH", "atomic_tests": 1},
    {"estimand_id": "E_YA_RESTORE_OFF", "atomic_tests": 1},
    {"estimand_id": "E_YA_RESTORE_ORTH", "atomic_tests": 1},
    {"estimand_id": "E_MG_ORTH_OFF", "atomic_tests": 1},
    {"estimand_id": "E_YA_ORTH_OFF", "atomic_tests": 1},
    {"estimand_id": "E_THETA_CONTROLLER_INVARIANCE", "atomic_tests": 2},
    {"estimand_id": "E_Z_CONTROLLER_INVARIANCE", "atomic_tests": 2},
    {"estimand_id": "E_M_TARGETPROJECTION_ORTH_OFF", "atomic_tests": 1},
    {"estimand_id": "E_CONTROLLER_ARM_INTERACTION", "atomic_tests": 3},
    {"estimand_id": "E_NUISANCE_KERNEL", "atomic_tests": 16},
    {"estimand_id": "E_M_TO_LOCAL_FOLD_MAP", "atomic_tests": 3},
    {"estimand_id": "E_M_TO_LOCAL_FOLD_DERIVATIVE", "atomic_tests": 3},
    {"estimand_id": "E_THETA_SAME_CONTACT_RESCUE", "atomic_tests": 1},
    {"estimand_id": "E_THETA_CONTACT_FRACTION_RESCUE", "atomic_tests": 1},
    {"estimand_id": "E_MG_RESCUE_CONTROLS", "atomic_tests": 2},
    {"estimand_id": "E_YA_RESCUE_CONTROLS", "atomic_tests": 2},
    {"estimand_id": "E_OPEN_PATCH_UNIFORM_SPD", "atomic_tests": 4},
    {"estimand_id": "E_ORDERED_PATH_DIRECTIONAL_EQUIVALENCE", "atomic_tests": 24},
]

EXPECTED_GATES = [
    "G0_SOURCE_PROTOCOL_ANALYSIS_LOCK",
    "G1_APPARATUS_AND_SAFETY",
    "G2_ACTUATOR_STATE_SEPARATION",
    "G3_SAME_CONTACT_THETA_AND_IDENTITY",
    "G4_SAMPLED_RAW_RIEMANN",
    "G4B_OPEN_PATCH_EXTENSION_IF_LOCAL_PATCH_CLAIMED",
    "G5_THETA_TO_GEOMETRY",
    "G6_GEOMETRY_AND_TASK_BEHAVIOR",
    "G7_RANDOMIZED_M_STATE",
    "G8_REVERSIBLE_SAME_CONTACT_RESCUE",
    "G9_HOLDOUT_POWER_MISSINGNESS_ASSUMPTIONS",
]

EXPECTED_STOPS = [
    "REVERSIBLE_SAME_CONTACT_TOOL_STOP",
    "ACTUATOR_STATE_CONFLATION_STOP",
    "SOURCE_STATE_RANK_STOP",
    "STATE_TARGET_OVERLAP_STOP",
    "ACTUATOR_DIRECT_PATH_STOP",
    "SOURCE_CONTACT_IDENTITY_STOP",
    "THETA_DIRECT_ASSAY_STOP",
    "THETA_REPEATABILITY_STOP",
    "OUTPUT_IDENTITY_STOP",
    "BEHAVIOR_ENDPOINT_INTEGRITY_STOP",
    "M_TO_METRIC_LOCAL_IDENTIFICATION_STOP",
    "CONTROLLER_CARRYOVER_STOP",
    "CONTROLLER_EXCLUSION_STOP",
    "RAW_FISHER_NOT_RIEMANN",
    "ORDERED_PATH_MODEL_STOP",
    "REFERENCE_PATCH_GEODESIC_CONVEXITY_STOP",
    "OPEN_PATCH_EXTENSION_STOP",
    "MICRO_TO_GEOMETRY_NOT_SUPPORTED",
    "GEOMETRY_BEHAVIOR_CAUSAL_CONTRIBUTION_NOT_SUPPORTED",
    "SAME_CONTACT_RESCUE_NOT_SUPPORTED",
    "RESCUE_IDENTITY_STOP",
    "ELIGIBILITY_CAP_STOP",
    "ATOMIC_TEST_POWER_STOP",
    "T_MODEL_ASSUMPTION_STOP",
    "MISSINGNESS_STOP",
    "CONFIRMATION_NOT_REPRODUCED",
    "ENDPOINT_NOT_EVALUATED",
]


class DuplicateKeyError(ValueError):
    pass


def _unique_object_pairs(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant rejected: {value}")


def load_contract_text(text: str) -> dict[str, Any]:
    value = json.loads(
        text,
        object_pairs_hook=_unique_object_pairs,
        parse_constant=_reject_nonstandard_json_constant,
    )
    if not isinstance(value, dict):
        raise ValueError("top-level JSON value must be an object")
    return value


def load_contract(path: Path) -> dict[str, Any]:
    return load_contract_text(path.read_text(encoding="utf-8"))


def semantic_sha256(contract: dict[str, Any]) -> str:
    canonical = json.dumps(
        contract,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def between_arm_power(alpha: float, effect: float, n_per_group: int) -> float:
    df = 2 * n_per_group - 2
    critical = t.ppf(1.0 - alpha, df)
    noncentrality = effect * math.sqrt(n_per_group / 2.0)
    return float(1.0 - nct.cdf(critical, df, noncentrality))


def paired_directional_power(alpha: float, effect: float, n_pairs: int) -> float:
    df = n_pairs - 1
    critical = t.ppf(1.0 - alpha, df)
    noncentrality = effect * math.sqrt(n_pairs)
    return float(1.0 - nct.cdf(critical, df, noncentrality))


def one_sample_lower_directional_power(alpha: float, effect: float, n: int) -> float:
    """One-sided t power for H0: standardized endpoint or margin distance <= 0."""
    df = n - 1
    critical = t.ppf(1.0 - alpha, df)
    noncentrality = effect * math.sqrt(n)
    return float(1.0 - nct.cdf(critical, df, noncentrality))


def one_sample_upper_margin_power(alpha: float, margin: float, n: int) -> float:
    """One-sided t power for H0: mean >= margin at a true standardized mean of zero."""
    df = n - 1
    lower_critical = t.ppf(alpha, df)
    noncentrality = -margin * math.sqrt(n)
    return float(nct.cdf(lower_critical, df, noncentrality))


def clopper_pearson_lcl(successes: int, n: int, alpha: float) -> float:
    if successes == 0:
        return 0.0
    return float(beta.ppf(alpha, successes, n - successes + 1))


def binomial_pass_fraction_power(
    alpha: float,
    null_fraction: float,
    true_fraction: float,
    n: int,
) -> tuple[int, float, float]:
    minimum_successes = next(
        successes
        for successes in range(n + 1)
        if clopper_pearson_lcl(successes, n, alpha) >= null_fraction
    )
    lcl = clopper_pearson_lcl(minimum_successes, n, alpha)
    power = float(binom.sf(minimum_successes - 1, n, true_fraction))
    return minimum_successes, lcl, power


def paired_equivalence_power_at_zero(alpha: float, margin: float, n_pairs: int) -> float:
    """Exact normal-theory paired TOST power, integrating over sample variance."""
    df = n_pairs - 1
    critical = t.ppf(1.0 - alpha, df)
    upper = chi2.ppf(0.999999999999, df)

    def integrand(q: float) -> float:
        sample_sd = math.sqrt(q / df)
        standardized_room = margin * math.sqrt(n_pairs) - critical * sample_sd
        conditional = max(0.0, 2.0 * norm.cdf(standardized_room) - 1.0)
        return float(conditional * chi2.pdf(q, df))

    return float(quad(integrand, 0.0, upper, epsabs=1e-13, epsrel=1e-13)[0])


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _validate_contract_impl(contract: dict[str, Any], *, check_semantic_lock: bool = True) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(set(contract) == TOP_LEVEL_KEYS, "top-level exact schema drift or unknown key")
    require(contract.get("schema_version") == 2, "schema_version must be exactly 2")
    require(contract.get("contract_id") == "CE_NPF_ADULT_L4_RIEMANN_FOLD_V2", "contract_id drift")
    require(contract.get("status") == "SCHEMA_FREEZE_CANDIDATE", "status must remain schema-freeze candidate")
    require(contract.get("execution_authorized") is False, "execution must remain unauthorized")
    require(contract.get("l4_gate_evaluated") is False, "L4 gate must remain unevaluated")
    require(contract.get("biological_endpoint_evaluated") is False, "biological endpoint must remain unevaluated")
    require(contract.get("claim_ceiling") == "BIO_EVIDENCE_L0", "claim ceiling must remain BIO_EVIDENCE_L0")
    require(
        contract.get("normative_markdown") == "paper/검증_원장/CE_NPF_ADULT_L4_리만접힘_실험계약_v2.md",
        "normative markdown path drift",
    )

    scope = contract.get("scope", {})
    require(scope.get("adult_only") is True, "adult-only scope required")
    require(scope.get("age_weeks") == [12, 20], "adult age window drift")
    require(scope.get("primary_unit") == "animal", "primary unit must be animal")
    require(scope.get("physical_lorentz_spacetime_claim") is False, "physical spacetime claim forbidden")
    require(scope.get("open_patch_claim_authorized") is False, "open-patch claim cannot be pre-authorized")
    require(scope.get("global_brain_manifold_claim") is False, "global brain manifold claim forbidden")

    budget = contract.get("data_budget", {})
    require(budget.get("metadata_before_payload") is True, "metadata-before-payload required")
    require(budget.get("sample_download_max_mb") == 100, "sample payload cap must be 100 MB")
    require(budget.get("explicit_approval_above_mb") == 500, "approval threshold must be 500 MB")
    require(budget.get("bulk_download_authorized") is False, "bulk download must remain unauthorized")
    require(budget.get("new_payload_required_for_contract_repair") is False, "contract repair must not require a new payload")

    sources = contract.get("source_anchors", [])
    require(isinstance(sources, list) and len(sources) == 7, "exactly seven scoped primary source anchors required")
    if isinstance(sources, list):
        require(all(isinstance(item, dict) and set(item) == {"doi", "module"} for item in sources), "source schema drift")
        require(all(str(item.get("doi", "")).startswith("10.") for item in sources if isinstance(item, dict)), "every source requires DOI")

    mechanism = contract.get("biological_starting_mechanism", {})
    require(mechanism.get("primary_tool_class") == "BIDIRECTIONAL_STRUCTURE_PRESERVING_SAME_CONTACT_EFFICACY_TOOL", "primary tool class drift")
    require(mechanism.get("tool_validated") is False, "unvalidated tool cannot be marked validated")
    require(mechanism.get("validation_required_before_confirmation") is True, "tool validation must precede confirmation")
    require(mechanism.get("as_parac1_role") == "SUPPORTING_POSITIVE_CONTROL_NOT_PRIMARY_L4_TOOL", "AS-PaRac1 role overclaim")
    require(mechanism.get("same_contact_bidirectional_effect_required") is True, "same-contact bidirectionality required")
    require(mechanism.get("same_contact_structural_survival_required") is True, "same-contact structural survival required")
    require(mechanism.get("stop_code_if_unavailable") == "REVERSIBLE_SAME_CONTACT_TOOL_STOP", "tool stop code drift")

    causal = contract.get("causal_objects", {})
    require(causal.get("dag") == "Z_THETA_MINUS->THETA;A->Z;(Z,THETA)->M;M->O_FUTURE;M->Y;THETA->O_FUTURE;THETA->Y;Z_M->M;Z_M->O_FUTURE;Z_M->Y;Z_THETA_PLUS->THETA;U_PRE->(M,O_FUTURE,Y)", "causal DAG drift")
    require(causal.get("metric_definition") == "g_i_t_k(z)=I_z[p_i_t_k(O_future|z,h,c)]", "state-conditioned metric definition drift")
    require(causal.get("fold_measurement") == "m_i_k_G=s_pre(g_i_PRE_BASELINE,g_i_POST_k)", "state-conditioned fold measurement role drift")
    require(causal.get("mediator") == "M", "biological mediator must be M")
    require(causal.get("metric_is_measurement_not_biological_state") is True, "metric/state distinction missing")
    require(causal.get("do_g_forbidden") is True and causal.get("do_m_forbidden") is True, "do(g) and do(m) must be forbidden")
    require(causal.get("direct_paths_audited_not_assumed_zero") is True, "direct paths must be audited, not assumed zero")
    require(causal.get("complete_mediation_claim") is False, "complete mediation cannot be implied by DAG")

    channels = contract.get("channels", {})
    channel_values = {key: channels.get(key) for key in EXPECTED_CHANNELS}
    require(channel_values == EXPECTED_CHANNELS, "channel identities drift")
    require(channels.get("all_channels_distinct") is True, "channel distinctness flag required")
    require(len(set(channel_values.values())) == len(EXPECTED_CHANNELS), "all six biological channels must be distinct")

    identity = contract.get("identity", {})
    require(identity.get("baseline_contact_key") == "animal/FOV/source_cell_or_bouton/post_cell/dendrite/spine", "contact identity key drift")
    require(identity.get("contact_denominator") == "C0_LOCKED_BEFORE_RANDOMIZATION", "C0 must freeze before randomization")
    require(identity.get("task_contact_sets") == "C_A0_AND_C_B0_LOCKED_BY_NONOVERLAPPING_TASK_TAG_WINDOWS_AND_FUNCTIONAL_SOURCE_MAPPING_BEFORE_RANDOMIZATION", "task source-contact set definition drift")
    require(identity.get("dual_tag_contacts_in_primary_sets") is False, "dual-tag contacts cannot enter primary sets")
    require(identity.get("target_tag_recall_simultaneous_lcl_min") == 0.8, "target-tag recall gate drift")
    require(identity.get("offtarget_activation_fraction_simultaneous_ucl_max") == 0.15, "off-target activation gate drift")
    require(identity.get("task_tag_overlap_fraction_simultaneous_ucl_max") == 0.15, "tag-overlap gate drift")
    require(identity.get("presynaptic_source_identity_overlap_simultaneous_lcl_min") == 0.8, "presynaptic source-overlap gate drift")
    require(identity.get("exact_output_cell_count") == 8, "exactly eight output cells required")
    require(identity.get("output_cells_replaceable") is False, "output-cell replacement forbidden")
    require(identity.get("new_or_reappearing_spine_counts_as_rescue") is False, "new/reappearing spine cannot count as rescue")
    require("THETA=0" in str(identity.get("disappearing_spine_rule")), "biological spine loss must set theta to zero")
    require("ITT_MISSING_NOT_ZERO" in str(identity.get("technical_loss_rule")), "technical loss must be ITT missing, not zero")

    theta = contract.get("theta_measurement", {})
    require(theta.get("estimand_name") == "SOURCE_CONDITIONED_CONTACT_TRANSMISSION_EFFICACY", "theta estimand drift")
    require(theta.get("formula") == "Theta_p_s=E[Q_spine-Q_parent|verified_source_event_p,h,c]-E[Q_spine-Q_parent|matched_no_event,h,c]", "theta formula drift")
    for key in (
        "presynaptic_event_or_release_verified",
        "monosynaptic_latency_window_frozen",
        "parent_dendrite_and_somatic_common_mode_removed",
        "heldout_direct_calibration_required",
        "nearest_nontarget_source_control",
        "opsin_negative_control",
    ):
        require(theta.get(key) is True, f"theta direct-assay requirement missing: {key}")
    require(theta.get("morphology_alone_can_pass") is False, "morphology alone cannot pass theta")
    require(theta.get("as_parac1_intensity_alone_can_pass") is False, "AS-PaRac1 intensity alone cannot pass theta")
    require(theta.get("same_contact_rescue_absolute_error") == "R_Theta_i=(1/abs(C_A0))*sum_(s in C_A0)(abs(Theta_i_RESCUE_s-Theta_i_PRE_s)/sigma_repeat_i_s)", "same-contact absolute-error formula drift")
    require(theta.get("same_contact_rescue_contact_fraction") == "F_Theta_i=(1/abs(C_A0))*sum_(s in C_A0)I[abs(Theta_i_RESCUE_s-Theta_i_PRE_s)<=delta_contact_i_s]", "same-contact fidelity-fraction formula drift")
    require(theta.get("task_conditioned_summary") == "barTheta_i_t_q=(1/abs(C_q0))*sum_(s in C_q0)I_present_s_t*Theta_i_s_t_FOR_q_IN_{A,B}", "task-conditioned theta summary drift")
    require(theta.get("primary_main_theta_endpoint") == "barTheta_i_t_A_ON_C_A0_WITH_C_B0_AS_FROZEN_SPECIFICITY_CONTROL", "primary task-A theta endpoint drift")
    require(theta.get("repeatability_blocks_pre_randomization") == 8, "theta repeatability block count drift")
    require(theta.get("repeatability_block_content") == "40_VERIFIED_SOURCE_EVENT_AND_40_MATCHED_NO_EVENT_TRIALS_PER_CONTACT_WITH_IDENTICAL_FROZEN_ESTIMATOR", "theta repeatability block content drift")
    require(theta.get("sigma_repeat_formula") == "sigma_repeat_i_s=sqrt((1/7)*sum_(b=1)^8(Theta_i_PRE_s_b-mean_b_Theta_i_PRE_s_b)^2)", "theta repeatability sigma formula drift")
    require(theta.get("delta_contact_formula") == "delta_contact_i_s=0.5*sigma_repeat_i_s", "same-contact delta formula drift")
    require(theta.get("sigma_delta_freeze_time") == "BEFORE_ANY_RANDOMIZATION_OR_CONFIRMATION_ARM_REVEAL", "theta sigma/delta freeze time drift")
    require(theta.get("sigma_nonfinite_or_nonpositive_action") == "THETA_REPEATABILITY_STOP_NO_FLOOR_NO_POOLED_CONTACT_SD", "theta repeatability zero/nonfinite action drift")
    require(theta.get("minimum_C_A0_contacts_per_animal") == 20, "same-contact minimum denominator drift")
    require(theta.get("contact_fraction_population_gate") == "C_Theta_i=I[F_Theta_i>=0.90_AND_abs(C_A0)>=20];ONE_SIDED_CLOPPER_PEARSON_LCL_FOR_Pr(C_Theta_i=1)>=0.90", "same-contact population-fraction gate drift")
    require(theta.get("same_contact_rescue_fraction_lcl_min") == 0.9, "same-contact rescue fraction gate drift")
    require(theta.get("contact_loss_counts_as_rescue_failure") is True, "contact loss must count as rescue failure")
    require(theta.get("signed_contact_error_cancellation_can_pass") is False, "signed rescue error cancellation forbidden")

    measurement = contract.get("measurement_and_analysis", {})
    require(measurement.get("likelihood_family") == "FOUR_CATEGORY_MULTINOMIAL_LOGIT_C2_INTRINSIC_HEAT_KERNEL_BASIS_OF_FROZEN_LAPLACE_BELTRAMI_r_i_WITH_FROZEN_H_C_EFFECTS", "likelihood family drift")
    require(measurement.get("intrinsic_basis_boundary_condition") == "NEUMANN_ON_closure(U_i)", "intrinsic likelihood boundary condition drift")
    require(measurement.get("likelihood_basis_rank_penalty_bandwidth_selection") == "DEVELOPMENT_ONLY_WITHOUT_Y_OR_MECHANISM_EFFECT_DIRECTION", "likelihood selection firewall drift")
    require(measurement.get("confirmation_parameter_fit") == "PER_ANIMAL_PER_TIME_PER_STATE_CONDITION_CALIBRATION_TRIALS_ONLY", "confirmation parameter-fit contract drift")
    require(measurement.get("primary_score_evaluation") == "SEALED_HOLDOUT_OUT_OF_FOLD_TRIALS_ONLY", "primary score holdout drift")
    require(measurement.get("residual_rule") == "HELDOUT_MULTINOMIAL_CALIBRATION_AND_SCORE_RESIDUAL_BAND_FAILS_CLOSED_WITHOUT_MODEL_REVISION", "residual rule drift")
    require(measurement.get("model_selection_rule") == "NO_CONFIRMATION_OUTCOME_OR_ARM_LABEL_CAN_SELECT_STRUCTURE_KNOTS_PENALTY_BANDWIDTH_OR_WINDOWS", "model selection rule drift")
    require(measurement.get("revision_trigger") == "ANY_SENSOR_ENCODER_LIKELIHOOD_ENDPOINT_THRESHOLD_OR_WINDOW_CHANGE_REQUIRES_V3_AND_NO_CONFIRMATION_REUSE", "revision trigger drift")
    require(measurement.get("execution_provenance_required") == ["interpreter_path", "python_version", "scipy_version", "construct_version", "protocol_hash", "analysis_hash", "randomization_hash"], "execution provenance set drift")

    state = contract.get("state_chart", {})
    require(state.get("actuator_symbol") == "a" and state.get("neural_state_symbol") == "z", "a/z symbol contract drift")
    require(state.get("actuator_is_neural_chart") is False, "actuator cannot be neural-state chart")
    require(state.get("encoder_inputs") == "PRESYNAPTIC_SOURCE_IDS_AND_SOURCE_STATE_CHANNEL_ONLY", "state encoder input drift")
    require(set(state.get("encoder_forbidden_inputs", [])) == {"a", "O_future", "Theta", "M", "Y", "arm", "POST_outcome"}, "state encoder forbidden-input set drift")
    require(state.get("encoder_frozen_before_randomization") is True, "state encoder must freeze before randomization")
    require(state.get("actuator_to_state_map") == "Phi_i_t(a;h,c)=E[z_trial|do(A=a),h,c,i,t]", "actuator-to-state map drift")
    require(state.get("primary_likelihood") == "p_i_t_k(O_future|z,h,c)", "state-conditioned primary likelihood must use z")
    require(state.get("forbidden_primary_likelihood") == "p_i_t_k(O_future|a,h,c)", "forbidden state-conditioned actuator likelihood drift")
    require(state.get("actuator_pullback_status") == "DIAGNOSTIC_ONLY_NEVER_G4_OR_M_G", "actuator pullback role drift")
    require(state.get("jacobian_rank") == 2, "actuator-to-state Jacobian must be rank two")
    require(state.get("actuator_reference_metric") == "c_a_i=diag(inverse(PRE_HARDWARE_COMMAND_REPEATABILITY_VARIANCE))_FROZEN_BEFORE_RANDOMIZATION", "actuator reference metric drift")
    require(state.get("jacobian_generalized_singular_value_formula") == "eigenvalues_of(inverse(c_a_i)*(D_a_Phi_i_t)^T*r_i*(D_a_Phi_i_t))=singular_value_squared", "Jacobian generalized singular-value formula drift")
    require(state.get("jacobian_sigma_min_simultaneous_lcb") == 0.2, "Jacobian minimum generalized singular-value gate drift")
    require(state.get("jacobian_condition_number_simultaneous_ucb_max") == 10.0, "Jacobian condition-number gate drift")
    require(state.get("errors_in_variables_calibration") is True, "errors-in-variables calibration required")
    require(state.get("same_source_ids_pre_post") is True, "source IDs must remain identical")
    require(state.get("state_target_count") == 25 and state.get("same_state_targets_pre_post") is True, "same 25 state targets required")
    require(_is_finite_number(state.get("target_reach_tolerance_r_distance")) and state.get("target_reach_tolerance_r_distance") == 0.1, "state-target tolerance drift")
    require(state.get("unreachable_point_action") == "STATE_TARGET_OVERLAP_STOP_NO_PATCH_SHRINK", "unreachable state must stop without patch shrink")
    require(state.get("actuator_direct_path_test") == "D_A_i_k=max_over_25_targets_heldout_ELPD_gain_of_adding_a_given_z_h_c;for_each_4_states_upper95_D_A_lt_0.5_SD_AND_0.01_nat_per_trial", "state-conditioned actuator direct-path test drift")
    require(state.get("actuator_direct_path_atomic_states") == ["BASELINE", "STATE_OFF", "STATE_RESTORE", "STATE_ORTHOGONAL"], "actuator direct-path atomic state set drift")
    require(state.get("actuator_direct_path_primary_arm") == "TARGET_A", "actuator direct-path primary arm drift")
    require(state.get("actuator_direct_path_physical_margin_power_gate") == "PRE_RANDOMIZATION_SD_D_A_i_k<=0.02_NAT_PER_TRIAL_OTHERWISE_ATOMIC_TEST_POWER_STOP", "actuator direct-path physical-margin power gate drift")

    windows = contract.get("temporal_windows_ms", {})
    require(windows == {
        "history": [-200, -100],
        "source_state": [-100, 0],
        "mediator_state": [0, 50],
        "future_output": [50, 150],
        "strict_order": "W_H<W_Z<W_M<W_O",
    }, "temporal windows or causal ordering drift")

    mediator = contract.get("mediator_state", {})
    require(mediator.get("symbol") == "M", "mediator symbol drift")
    require(mediator.get("definition") == "M=B_M^T*X_post_cells[W_M]", "mediator definition drift")
    require(mediator.get("dimension") == 2, "mediator dimension must be two")
    require(mediator.get("basis_source") == "DEVELOPMENT_NEURAL_DATA_ONLY", "mediator basis source drift")
    require(set(mediator.get("basis_forbidden_inputs", [])) == {"Y", "mechanism_arm", "effect_direction", "confirmation_output"}, "mediator basis forbidden-input drift")
    require(mediator.get("basis_frozen_before_confirmation") is True, "mediator basis must freeze before confirmation")
    require(mediator.get("local_map_to_fold_required") == "ell_i_k(z_j)=q_dev(M_i_POST_k(z_j),z_j,h,c)+epsilon_AND_m_i_k_G=(1/25)*sum_j_ell_i_k(z_j)", "state-conditioned M-to-fold local identification drift")
    require(mediator.get("local_map_family") == "C2_EUCLIDEAN_M_TIMES_INTRINSIC_HEAT_KERNEL_z_MODEL_q_dev_FOR_PER_TARGET_FOLD_CONTRIBUTION_ell=e_A-e_B", "M-to-fold local model family drift")
    require(mediator.get("local_map_fit_set") == "MODEL_CONTROLLER_DEVELOPMENT_ANIMALS_ONLY_WITH_RANDOMIZED_SUBTHRESHOLD_M_PERTURBATIONS", "M-to-fold fitting-set firewall drift")
    require(set(mediator.get("local_map_forbidden_inputs", [])) == {"Y", "confirmation_arm", "confirmation_outcome", "effect_direction"}, "M-to-fold forbidden-input set drift")
    require(mediator.get("local_map_null_model") == "q0_dev(z,h,c)_SAME_DEVELOPMENT_DATA_AND_INTRINSIC_z_BASIS_WITHOUT_M_FROZEN_WITH_q_dev", "M-to-fold null model drift")
    require(mediator.get("local_map_confirmation_score") == "L_i_k=(1/25)*sum_j[(ell_i_k(z_j)-q0_dev(z_j,h,c))^2-(ell_i_k(z_j)-q_dev(M_i_POST_k(z_j),z_j,h,c))^2]", "M-to-fold heldout score estimand drift")
    require(mediator.get("local_map_atomic_states") == ["STATE_OFF", "STATE_RESTORE", "STATE_ORTHOGONAL"], "M-to-fold atomic state set drift")
    require(mediator.get("local_map_directional_derivative_gate") == "SIMULTANEOUS_95_LCB_abs(D_u_M_restore_q_dev)>=0.20_STANDARDIZED_FOLD_PER_STANDARDIZED_M_AT_ALL_25_TARGETS", "M-to-fold derivative gate drift")
    require(mediator.get("local_map_derivative_endpoint") == "B_i_k=min_over_25_targets_abs(D_u_M_restore_q_dev(M_i_POST_k(z_j),z_j,h,c))", "M-to-fold derivative endpoint drift")
    require(mediator.get("local_map_derivative_physical_margin_power_gate") == "PRE_RANDOMIZATION_SD_B_i_k<=0.40_SO_0.20_THRESHOLD_IS_AT_LEAST_0.5_SD_OTHERWISE_ATOMIC_TEST_POWER_STOP", "M-to-fold derivative power gate drift")
    require(mediator.get("local_map_design_alternative_sd") == 0.5, "M-to-fold design alternative drift")
    require(mediator.get("reference_metric") == "r_M_i(z)=inverse(Sigma_M_i_PRE_repeatability(z))_FROZEN_BEFORE_RANDOMIZATION", "mediator reference metric drift")
    require(mediator.get("target_distance") == "d_M_i_k=(1/25)*sum_(j=1)^25_norm_r_M(M_i_POST_k(z_i_j)-M_i_PRE(z_i_j))", "mediator target-distance formula drift")
    require(mediator.get("restore_axis_projection") == "P_M_i_k=(1/25)*sum_(j=1)^25_inner_r_M(u_M_restore_i(z_i_j),M_i_POST_k(z_i_j)-M_i_POST_OFF(z_i_j))", "mediator restore-axis projection drift")
    require(mediator.get("state_conditions") == ["STATE_OFF", "STATE_RESTORE", "STATE_ORTHOGONAL"], "mediator state-condition set drift")
    require(mediator.get("orthogonal_off_target_projection_equivalence_required") is True, "M orthogonal/off target-projection equivalence required")
    require(mediator.get("failure_stop") == "M_TO_METRIC_LOCAL_IDENTIFICATION_STOP", "mediator identification stop drift")

    output = contract.get("output_model", {})
    require(output.get("same_postsynaptic_cells_as_contacts") is True, "output must use the same postsynaptic cells")
    require(output.get("exact_cell_count") == 8, "output dimension must be exact, not minimum")
    require(output.get("fixed_subensembles") == {"F_A": 4, "F_B": 4}, "fixed output subensembles drift")
    require(output.get("future_output_formula") == "O_future=(I[N_F_A(W_O)>0],I[N_F_B(W_O)>0])", "future-output formula drift")
    require(output.get("output_alphabet") == ["00", "01", "10", "11"], "output alphabet drift")
    require(output.get("base_measure") == "COUNTING_MEASURE_ON_OMEGA", "output base measure drift")
    require(output.get("same_cells_threshold_window_alphabet_pre_post") is True, "PRE/POST observation space must be identical")
    require(output.get("behavior_excluded") is True and output.get("theta_sensor_excluded") is True, "output channel independence failed")
    require(output.get("lost_cell_action") == "OUTPUT_IDENTITY_STOP_NO_REPLACEMENT_NO_DIMENSION_REDUCTION", "lost-cell action drift")

    behavior = contract.get("behavior_endpoint", {})
    require(behavior.get("tasks") == {"A": "CUE_A_THEN_LEVER_TARGET_SEQUENCE_L1_L2_L3", "B": "CUE_B_THEN_LEVER_TARGET_SEQUENCE_L3_L2_L1"}, "Task-A/B observable definition drift")
    require(behavior.get("lever_coordinate") == "CALIBRATED_NORMALIZED_DISPLACEMENT_X_IN_[-1,1]_SAMPLED_AT_GE_1000_HZ_AND_FROZEN_BEFORE_RANDOMIZATION", "behavior lever coordinate/calibration drift")
    require(behavior.get("target_zones") == {"L1": [-0.9, -0.6], "L2": [-0.15, 0.15], "L3": [0.6, 0.9]}, "behavior target-zone boundaries drift")
    require(behavior.get("zone_boundary_rule") == "CLOSED_INTERVAL_WITH_ENTRY_TIME_LINEARLY_INTERPOLATED_BETWEEN_ADJACENT_SAMPLES", "behavior zone-boundary algorithm drift")
    require(behavior.get("zone_entry_rule") == "FIRST_INWARD_BOUNDARY_CROSSING_FOLLOWED_BY_GE_30_MS_CONTINUOUS_OCCUPANCY;EARLY_ENTRY_INTO_ANY_LATER_REQUIRED_ZONE_IS_OUT_OF_ORDER_FAILURE", "behavior crossing/debounce algorithm drift")
    require(behavior.get("pre_cue_reset_rule") == "TASK_A_X_IN_[-1.00,-0.95]_AND_TASK_B_X_IN_[0.95,1.00]_FOR_GE_200_MS_BEFORE_CUE_OTHERWISE_NONINITIATION_FAILURE", "behavior pre-cue reset rule drift")
    require(behavior.get("trial_window_ms_from_cue") == [0, 2000], "behavior trial window drift")
    require(behavior.get("valid_trial_denominator_per_task_time_state") == 40, "behavior denominator must be exactly 40")
    require(behavior.get("success_rule") == "ALL_THREE_TARGET_ZONES_CROSSED_IN_PRESCRIBED_ORDER_WITHIN_2000_MS_AND_NO_OUT_OF_ORDER_CROSSING", "behavior success rule drift")
    require(behavior.get("formula") == "Y_i_t_k_q=(1/40)*sum_(trial=1)^40_I_success_i_t_k_q_trial", "behavior formula drift")
    require(behavior.get("unit") == "PROPORTION_IN_[0,1]", "behavior unit drift")
    require(behavior.get("main_mechanism_endpoint") == "Delta_Y_i_OFF_q=Y_i_POST_STATE_OFF_q-Y_i_PRE_BASELINE_q", "main behavior contrast drift")
    require(behavior.get("task_specificity_endpoint") == "S_i=(Delta_Y_i_OFF_A-Delta_Y_i_OFF_B)_TARGET_A", "task-specificity behavior endpoint drift")
    require(behavior.get("primary_task_for_state_and_rescue") == "A", "state/rescue behavior task must be explicit")
    require(behavior.get("state_endpoint") == "Y_i_POST_k_A_FOR_k_IN_OFF_RESTORE_ORTHOGONAL", "state behavior endpoint drift")
    require(behavior.get("rescue_endpoint") == "Y_i_POST_RESCUE_ARM_STATE_RESTORE_A", "rescue behavior endpoint drift")
    require(behavior.get("probe_light_present") is False, "geometry probe light must be absent from behavior endpoint")
    require(behavior.get("state_controller_present_as_randomized") is True, "randomized state controller status missing from behavior endpoint")
    require(behavior.get("noninitiation_timeout_or_incorrect_trial") == "COUNT_AS_FAILURE_IN_FIXED_DENOMINATOR", "behavior failure/denominator rule drift")
    require(behavior.get("hardware_or_clock_loss") == "TECHNICAL_NA_AT_ANIMAL_ENDPOINT_NOT_TRIAL_EXCLUSION", "behavior hardware-loss rule drift")
    require(behavior.get("standardization_sd_between") == "BLINDED_PRE_RANDOMIZATION_ANIMAL_SD_OF_EACH_EXACT_BEHAVIOR_ESTIMAND_WITH_STRATUM_FIXED_EFFECTS", "between-arm behavior SD denominator drift")
    require(behavior.get("standardization_sd_paired") == "BLINDED_PRE_RANDOMIZATION_SD_OF_EACH_EXACT_PAIRED_BEHAVIOR_ESTIMAND_FROM_INERT_CONTROLLER_REPEATS", "paired behavior SD denominator drift")
    require(behavior.get("standardization_frozen_before_arm_reveal") is True, "behavior SD denominators must freeze before arm reveal")
    require(behavior.get("behavior_used_in_metric_or_controller_training") is False, "behavior cannot enter metric/controller training")

    probe = contract.get("probe_design", {})
    require(probe.get("state_target_shape") == [5, 5], "state target grid must be 5x5")
    require(probe.get("trials_per_target") == 96, "trials per target drift")
    require(probe.get("calibration_trials_per_target") == 48 and probe.get("sealed_holdout_trials_per_target") == 48, "48/48 trial split required")
    require(probe.get("calibration_trials_per_target", 0) + probe.get("sealed_holdout_trials_per_target", 0) == probe.get("trials_per_target"), "trial split must exhaust trials")
    require(probe.get("target_order_randomized") is True and probe.get("probe_nonplasticity_required") is True, "randomized nonplastic probe required")
    require(probe.get("ordered_path_directions") == ["u_A", "u_B", "(u_A+u_B)/sqrt(2)", "(u_A-u_B)/sqrt(2)", "cos(pi/8)*u_A+sin(pi/8)*u_B", "cos(3*pi/8)*u_A+sin(3*pi/8)*u_B"], "ordered-path directions drift")
    frozen_axis_angles = np.array([0.0, math.pi / 2.0, math.pi / 4.0, -math.pi / 4.0, math.pi / 8.0, 3.0 * math.pi / 8.0])
    arrival_angles = np.concatenate([frozen_axis_angles, frozen_axis_angles + math.pi])
    harmonic_design = np.column_stack([
        np.cos(arrival_angles),
        np.sin(arrival_angles),
        np.cos(3.0 * arrival_angles),
        np.sin(3.0 * arrival_angles),
        np.cos(4.0 * arrival_angles),
        np.sin(4.0 * arrival_angles),
    ])
    require(int(np.linalg.matrix_rank(harmonic_design)) == 6, "ordered-path frozen harmonic design is not full rank")
    require(probe.get("both_arrival_directions_required") is True, "both ordered arrival directions required")
    require(probe.get("ordered_path_target_set") == "EXACT_CENTRAL_3x3_TARGETS_ROWS_2_TO_4_COLUMNS_2_TO_4_OF_FROZEN_5x5_GRID", "ordered-path target set drift")
    require(probe.get("ordered_path_state_set") == ["BASELINE", "STATE_OFF", "STATE_RESTORE", "STATE_ORTHOGONAL"], "ordered-path state set drift")
    require(probe.get("ordered_path_primary_arm") == "TARGET_A", "ordered-path primary arm drift")
    require(probe.get("ordered_path_trials_per_arrival") == 24, "ordered-path trial count drift")
    require(probe.get("matched_endpoint_duration_energy_reset_history_context") is True, "ordered-path matching incomplete")
    require(probe.get("extension_validation_lattice_shape") == [9, 9], "open-patch validation lattice drift")
    require(probe.get("extension_anchor_targets") == 25 and probe.get("extension_interleaved_validation_targets") == 56, "25+56 extension target split drift")
    require(probe.get("extension_validation_trials_per_target") == 48, "extension validation trial count drift")
    require(probe.get("extension_targets_used_to_choose_model") is False, "sealed extension targets cannot choose model")

    fisher = contract.get("fisher_geometry", {})
    require(fisher.get("state_condition_index") == "k_IN_{BASELINE,STATE_OFF,STATE_RESTORE,STATE_ORTHOGONAL}", "Fisher state-condition index drift")
    require(fisher.get("score_formula") == "s_i_t_k(o;z,h,c)=partial_z_log_p_i_t_k(o|z,h,c)", "state-conditioned score formula drift")
    require(fisher.get("fisher_formula") == "g_i_t_k(z)=sum_(h,c)Q_i0(h,c)*sum_(o_in_Omega)p_i_t_k(o|z,h,c)*s_i_t_k(o;z,h,c)*s_i_t_k(o;z,h,c)^T", "state-conditioned Fisher formula drift")
    require(fisher.get("history_context_measure") == "Q_i0(h,c)_LOCKED_FROM_PRE_RANDOMIZATION_BASELINE", "history/context measure drift")
    require(fisher.get("animal_level_first") is True and fisher.get("animal_pooling_can_create_spd") is False, "Fisher must be animal-level before population inference")
    require(fisher.get("primary_estimator") == "ANIMAL_LEVEL_CROSS_FIT_HELDOUT_RAW_SCORE_OUTER_PRODUCT", "raw estimator drift")
    require(fisher.get("crossfit_folds") == 4, "crossfit fold count drift")
    require(fisher.get("ridge_can_pass") is False and fisher.get("eigenvalue_clipping_can_pass") is False, "regularization cannot create SPD evidence")
    require(fisher.get("regularized_working_metric_role") == "CONTROLLER_DIAGNOSTIC_ONLY", "working metric role drift")
    support_floor = fisher.get("common_support_floor")
    require(_is_finite_number(support_floor) and support_floor == 0.01 and 0 < support_floor < 0.25, "common-support floor must be finite 0.01")
    require(fisher.get("support_test") == "SIMULTANEOUS_HELDOUT_95_LCB_FOR_ALL_FOUR_OUTPUT_CATEGORIES", "support test drift")
    require(fisher.get("pseudocount_can_pass_support") is False, "pseudocount cannot pass common support")
    require(fisher.get("reference_repeatability_likelihood") == "q_i_PRE(Z_obs|z,h,c)_C3_WITH_STRUCTURE_FROZEN_IN_DEVELOPMENT_AND_PARAMETERS_FIT_FROM_ANIMAL_PRE_RANDOMIZATION_REPEATS", "reference repeatability likelihood drift")
    require(fisher.get("reference_metric_formula") == "r_i(z)=sum_(h,c)Q_i0(h,c)*E_q[(partial_z_log_q_i_PRE(Z_obs|z,h,c))*(partial_z_log_q_i_PRE(Z_obs|z,h,c))^T]", "reference metric formula drift")
    require(fisher.get("reference_metric_estimator") == "ANIMAL_LEVEL_CROSS_FIT_HELDOUT_RAW_SCORE_OUTER_PRODUCT_NO_RIDGE_NO_EIGEN_CLIPPING", "reference metric estimator drift")
    require(fisher.get("reference_metric_frozen_pre") is True and fisher.get("reference_metric_post_update_forbidden") is True, "reference metric must freeze at PRE")
    require(fisher.get("generalized_eigenvalue_formula") == "det(g_i_t_k(z_j)-lambda*r_i(z_j))=0", "state-conditioned generalized eigenvalue formula drift")
    require(_is_finite_number(fisher.get("generalized_lambda_min_simultaneous_lcb")) and fisher.get("generalized_lambda_min_simultaneous_lcb") == 0.02, "generalized lambda bound drift")
    require(_is_finite_number(fisher.get("generalized_condition_number_simultaneous_ucb_max")) and fisher.get("generalized_condition_number_simultaneous_ucb_max") == 50.0, "generalized condition bound drift")
    require(fisher.get("passing_grid_fraction") == 1.0, "all 25 grid points must pass")
    require(fisher.get("chart_change") == "z=phi(z_tilde);J=partial_z/partial_z_tilde", "chart convention drift")
    require(fisher.get("metric_transform") == "g_tilde=J^T*g*J", "metric transform drift")
    require(fisher.get("reference_transform") == "r_tilde=J^T*r*J", "reference transform drift")
    require(fisher.get("vector_transform") == "u_tilde=J^-1*u", "vector transform drift")
    require(_is_finite_number(fisher.get("coordinate_covariance_relative_error_max")) and fisher.get("coordinate_covariance_relative_error_max") == 0.05, "coordinate covariance tolerance drift")
    require(fisher.get("finsler_test_status") == "ORDERED_PATH_TEST_REQUIRED_NOT_EVALUATED", "Finsler status drift")
    require(fisher.get("ordered_path_base_model") == "p_R_i_t_k(O_future|z,h,c,vTg_i_t_k(z)v)_RIEMANN_QUADRATIC_NO_ODD_OR_ANGULAR_HARMONIC_GE4", "ordered-path base model drift")
    require(fisher.get("ordered_path_alternative_model") == "p_D_i_t_k(O_future|z,v,h,c)_SAME_BASE_PLUS_FULL_RANK_FROZEN_HARMONICS_{cos1,sin1,cos3,sin3,cos4,sin4}", "ordered-path alternative model drift")
    require(fisher.get("ordered_path_estimand") == "D_i_k_h=max_over_exact_9_targets_HELDOUT_LOG_SCORE_GAIN_OF_FULL_p_D_VS_DROP_h_MODEL_FOR_h_IN_{cos1,sin1,cos3,sin3,cos4,sin4}", "ordered-path estimand drift")
    require(fisher.get("ordered_path_harmonic_design_rank") == 6, "ordered-path harmonic design-rank drift")
    require(fisher.get("ordered_path_atomic_components") == "SIX_HARMONICS_TIMES_FOUR_STATES_EQUALS_24_WITH_TARGET_MAX_NO_LOCATION_AVERAGING", "ordered-path atomic-component count drift")
    require(fisher.get("ordered_path_standardized_upper_margin_sd") == 0.5, "ordered-path standardized margin drift")
    require(_is_finite_number(fisher.get("directional_elpd_gain_upper95_max_nat_per_trial")) and fisher.get("directional_elpd_gain_upper95_max_nat_per_trial") == 0.01, "directional ELPD margin drift")
    require(fisher.get("ordered_path_physical_margin_power_gate") == "PRE_RANDOMIZATION_SD_D_i_k_h<=0.02_NAT_PER_TRIAL_SO_0.01_NAT_MARGIN_IS_AT_LEAST_0.5_SD_OTHERWISE_ATOMIC_TEST_POWER_STOP", "ordered-path physical-margin power gate drift")
    require(fisher.get("ordered_path_pass_rule") == "EACH_OF_24_STATE_BY_HARMONIC_ATOMIC_COMPONENTS_REQUIRES_UPPER95_D_STANDARDIZED_LT_0.5_AND_UPPER95_D_LT_0.01_NAT_PER_TRIAL", "ordered-path exact pass rule drift")
    require(fisher.get("static_fisher_alone_can_reject_finsler") is False, "static Fisher cannot reject Finsler")
    require(fisher.get("global_finsler_exclusion_claim") is False, "global Finsler exclusion cannot be claimed")
    require(fisher.get("finsler_competitor_scope") == "FULL_PHASE_n1_n3_ODD_AND_n4_REVERSIBLE_EVEN_DEVIATIONS_AT_EXACT_9_TARGETS_AND_4_STATES_ONLY_NOT_ALL_FINSLER_GEOMETRIES", "Finsler competitor scope drift")
    require(fisher.get("sampled_grid_claim_only_without_extension") is True, "sampled-grid claim limit missing")
    require(fisher.get("reference_metric_extension") == "INTRINSIC_FISHER_TENSOR_FIELD_OF_C3_PRE_REPEATABILITY_LIKELIHOOD_NO_COMPONENTWISE_OR_LOG_EUCLIDEAN_TENSOR_INTERPOLATION", "reference metric extension drift")
    require(fisher.get("reference_connection") == "LEVI_CIVITA_CONNECTION_OF_FROZEN_r_i", "reference connection drift")
    require(fisher.get("candidate_open_patch") == "U_i=INTERIOR_OF_FIXED_32_TRIANGLE_COMPLEX_SPANNED_BY_5x5_ANCHORS_WITH_CONNECTIVITY_FROZEN_PRE_RANDOMIZATION", "candidate open-patch domain drift")
    require(fisher.get("candidate_patch_nondegeneracy_gate") == "ALL_32_TRIANGLES_SIMULTANEOUS_95_LCB_r_i_INRADIUS>=0.05_AND_TOTAL_r_i_AREA_LCB>=0.25_AND_0<LCB_h_U_i<=UCB_h_U_i<=0.50", "candidate open-patch nondegeneracy gate drift")
    require(fisher.get("candidate_patch_nondegeneracy_failure_action") == "REFERENCE_PATCH_GEODESIC_CONVEXITY_STOP", "candidate open-patch nondegeneracy action drift")
    require(fisher.get("reference_distance_formula") == "d_r_i(z,zprime)=inf_gamma_integral_0^1_sqrt(dot_gamma(s)^T*r_i(gamma(s))*dot_gamma(s))ds", "reference geodesic-distance formula drift")
    require(fisher.get("reference_patch_requirement") == "closure(U_i)_IS_r_i_GEODESICALLY_CONVEX_WITH_UNIQUE_SHORTEST_r_i_GEODESIC_BETWEEN_COMPARISON_POINTS", "reference patch convexity requirement drift")
    require(fisher.get("reference_patch_certificate_method") == "INTERVAL_NEWTON_UNIQUENESS_AND_POSITIVE_SECOND_VARIATION_FOR_RIEMANNIAN_ENERGY_ON_ALL_32_CELLS_PLUS_INTERVAL_INWARD_BOUNDARY_CONVEXITY", "reference patch convexity certificate drift")
    require(fisher.get("endomorphism_formula") == "A_i_t_k(z)=inverse(r_i(z))*g_i_t_k(z)", "open-patch endomorphism formula drift")
    require(fisher.get("fiber_comparison") == "PARALLEL_TRANSPORT_A_i_t_k_WITH_LEVI_CIVITA_r_i_ALONG_UNIQUE_SHORTEST_r_i_GEODESIC", "open-patch fiber comparison drift")
    require(fisher.get("fill_distance_formula") == "h_U_i=sup_(z_in_closure(U_i))min_(j=1,...,25)d_r_i(z,z_i_j)", "nonzero-domain fill-distance formula drift")
    require(fisher.get("lipschitz_formula") == "L_A_i_t_k=sup_(z_not_equal_zprime)norm_op_r(Pi_zprime_to_z*A_i_t_k(zprime)*Pi_z_to_zprime-A_i_t_k(z))/d_r_i(z,zprime)", "coordinate-invariant Lipschitz formula drift")
    require(fisher.get("lipschitz_bound_method") == "SIMULTANEOUS_95_UCB_FROM_INTRINSIC_HEAT_KERNEL_LIKELIHOOD_COEFFICIENT_SET_WITH_INTERVAL_ARITHMETIC_ON_32_CELLS_AND_56_SEALED_INTERLEAVED_TARGETS", "Lipschitz bound method drift")
    require(fisher.get("open_patch_extension_formula") == "rho_LCB_i_t_k=min_j_LCB_lambda_min(A_i_t_k(z_i_j))-UCB_L_A_i_t_k*h_U_i>0", "open-patch extension formula drift")
    require(fisher.get("open_patch_regularity_required") == "r_i_C2_AND_g_i_t_k_C1_WITH_INTERVAL_BOUNDS", "open-patch regularity requirement drift")
    require(fisher.get("open_patch_requires_all_state_conditions") is True, "open-patch certificate must cover all state conditions")
    require(fisher.get("open_patch_primary_arm") == "TARGET_A_WITH_SHAM_AND_OFFTARGET_LIMITED_TO_SAMPLED_GRID_CONTROLS", "open-patch primary arm/scope drift")
    require(fisher.get("open_patch_population_gate") == "C_GEO_i_t_k=I[PATCH_NONDEGENERATE_AND_COMMON_SUPPORT_AND_GENERALIZED_CONDITION_AND_COORDINATE_COVARIANCE_AND_rho_LCB_i_t_k>0_AND_REFERENCE_PATCH_CERTIFIED];ONE_SIDED_CLOPPER_PEARSON_LCL_FOR_Pr(C_GEO_i_t_k=1)>=0.90_FOR_EACH_OF_4_STATES", "open-patch population gate drift")
    require(fisher.get("open_patch_status") == "NOT_EVALUATED", "open-patch status must remain unevaluated")

    fold = contract.get("fold_summary", {})
    require(fold.get("reference_directions") == "u_A_u_B_are_r_orthonormalized_columns_of_D_a_Phi_i_PRE_and_frozen_before_randomization", "reference direction definition drift")
    require(fold.get("state_conditions") == ["STATE_OFF", "STATE_RESTORE", "STATE_ORTHOGONAL"], "fold state-condition set drift")
    require(fold.get("directional_stretch_formula") == "e_i_k_d(z_j)=0.5*log((u_i_d(z_j)^T*g_i_POST_k(z_j)*u_i_d(z_j))/(u_i_d(z_j)^T*g_i_PRE_BASELINE(z_j)*u_i_d(z_j)))", "state-conditioned coordinate-invariant stretch formula drift")
    require(fold.get("sampling_measure") == "mu_i0=(1/25)*sum_(j=1)^25_delta_(z_i_j)", "sampling measure drift")
    weights = fold.get("weights", [])
    require(isinstance(weights, list) and len(weights) == 25, "exactly 25 fold weights required")
    if isinstance(weights, list):
        require(all(_is_finite_number(weight) and weight == 0.04 for weight in weights), "every fold weight must equal 0.04")
        require(math.isclose(sum(weights), 1.0, rel_tol=0.0, abs_tol=1e-12), "fold weights must sum to one")
    require(fold.get("fold_formula") == "m_i_k_G=(1/25)*sum_(j=1)^25(e_i_k_A(z_i_j)-e_i_k_B(z_i_j))", "state-conditioned fold formula drift")
    require(fold.get("main_mechanism_fold") == "m_i_STATE_OFF_G", "main mechanism fold alias drift")
    require(fold.get("behavior_free") is True and fold.get("physical_curvature") is False, "fold interpretation drift")
    require(fold.get("old_matrix_log_contraction_forbidden") is True, "old matrix-log contraction must remain forbidden")

    cohorts = contract.get("cohorts", {})
    development = cohorts.get("development", {})
    confirmation = cohorts.get("confirmation", {})
    require(development.get("tool_validation_max_animals") == 12, "tool-validation cohort cap drift")
    require(development.get("model_controller_max_animals") == 24, "model/controller development cap drift")
    require(development.get("max_animals_total") == 36 and development.get("inferential") is False, "development cohort total/inferential contract drift")
    require(development.get("behavior_effect_tuning_forbidden") is True, "development cannot tune behavior effects")
    require(development.get("task_geometry_behavior_effect_direction_tuning_forbidden") is True, "development cannot tune task/geometry/behavior effect directions")
    require(development.get("tool_validation_may_read_contact_level_bidirectional_theta_fidelity") is True, "tool validation must be allowed to read contact-level bidirectional theta fidelity")
    require(development.get("tool_validation_animals_reused_for_model_or_confirmation") is False, "tool-validation animals cannot be reused")
    require("mechanism_fidelity" in development.get("allowed_uses", []), "development allowed-use must include mechanism fidelity")
    require(confirmation.get("eligible_randomized_total") == 540, "confirmation randomized total drift")
    main_arms = confirmation.get("main_arms", {})
    rescue_arms = confirmation.get("second_randomization_within_target", {})
    require(main_arms == {"TARGET_A": 324, "SHAM": 108, "OFFTARGET_B": 108}, "main-arm sizes drift")
    require(sum(main_arms.values()) == confirmation.get("eligible_randomized_total"), "main-arm sizes must sum to randomized total")
    require(rescue_arms == {"SAME_CONTACT_RESTORE": 108, "RESCUE_SHAM": 108, "PASSIVE_RECOVERY": 108}, "rescue-arm sizes drift")
    require(sum(rescue_arms.values()) == main_arms.get("TARGET_A"), "rescue arms must exhaust TARGET_A")
    require(confirmation.get("screen_cap_total") == 680, "screen cap drift")
    require(confirmation.get("screen_cap_total", 0) >= confirmation.get("eligible_randomized_total", math.inf), "screen cap cannot be below exact randomized N")
    require(confirmation.get("screen_then_randomize_exact_n") is True, "screening must finish before exact randomization")
    require(confirmation.get("replacement_after_randomization") is False, "postrandomization replacement forbidden")
    require(confirmation.get("animal_level_development_confirmation_holdout") is True, "animal-level holdout required")
    require(confirmation.get("model_frozen_before_randomization") is True, "model must freeze before randomization")
    require(confirmation.get("controller_target") == "EACH_ANIMALS_PRE_RANDOMIZATION_PRE_LESION_M_PRE_WITH_DEVELOPMENT_FROZEN_ALGORITHM", "controller target source drift")
    require(confirmation.get("confirmation_sham_output_as_target_forbidden") is True, "confirmation SHAM output cannot define target")

    randomization = contract.get("randomization", {})
    for key in (
        "main_mechanism_randomized",
        "controller_order_randomized",
        "controller_washout_required",
        "rescue_randomized",
        "blinded_registration",
        "blinded_outcome_analysis",
        "posthoc_conditioning_on_achieved_m_forbidden",
    ):
        require(randomization.get(key) is True, f"randomization/blinding requirement missing: {key}")
    require(randomization.get("main_allocation") == "3:1:1", "main allocation drift")
    require(randomization.get("main_strata") == ["site", "sex", "litter", "surgery_batch"], "main randomization strata drift")
    require(randomization.get("controller_conditions") == ["STATE_OFF", "STATE_RESTORE", "STATE_ORTHOGONAL"], "controller conditions drift")
    require(randomization.get("controller_sequence") == "SIX_SEQUENCE_WILLIAMS_BALANCED", "controller sequence drift")
    require(randomization.get("controller_carryover_failure_action") == "CONTROLLER_CARRYOVER_STOP_NEW_PARALLEL_CONTRACT_REQUIRED", "controller carryover action drift")
    require(randomization.get("rescue_allocation") == "1:1:1_WITHIN_TARGET_A", "rescue allocation drift")

    interventions = contract.get("interventions", {})
    require(interventions.get("mechanism") == ["TARGET_A", "SHAM", "OFFTARGET_B"], "mechanism interventions drift")
    require(interventions.get("state") == ["STATE_OFF", "STATE_RESTORE", "STATE_ORTHOGONAL"], "state interventions drift")
    require(interventions.get("rescue") == ["SAME_CONTACT_RESTORE", "RESCUE_SHAM", "PASSIVE_RECOVERY"], "rescue interventions drift")
    require(interventions.get("state_restore_target") == "M_PRE_NOT_CONFIRMATION_SHAM_OUTPUT", "state restore target drift")
    require(interventions.get("state_orthogonal_definition") == "SAME_PHOTON_DOSE_CELLS_TIMING_AND_INDUCED_SPIKE_NORM_WITH_R_ORTHOGONAL_TARGET_DISPLACEMENT", "orthogonal state definition drift")
    for key in (
        "restore_must_beat_off",
        "restore_must_beat_orthogonal",
        "mediator_target_projection_orthogonal_must_equal_off",
        "orthogonal_must_equal_off_on_target_projection_m_G_and_Y",
        "theta_must_remain_lesioned_during_state_intervention",
        "source_z_must_remain_equivalent_during_state_intervention",
    ):
        require(interventions.get(key) is True, f"causal-state contrast missing: {key}")
    require(interventions.get("controller_arm_interaction_endpoints") == {
        "M_TARGET_DISTANCE": "[(d_M_OFF-d_M_RESTORE)_TARGET_A-(d_M_OFF-d_M_RESTORE)_SHAM]>0",
        "M_G": "[(m_G_RESTORE-m_G_OFF)_TARGET_A-(m_G_RESTORE-m_G_OFF)_SHAM]>0",
        "Y_A": "[(Y_A_RESTORE-Y_A_OFF)_TARGET_A-(Y_A_RESTORE-Y_A_OFF)_SHAM]>0",
    }, "controller arm-interaction endpoint set drift")
    require(interventions.get("controller_arm_interaction_logic") == "ALL_THREE_ENDPOINTS_MUST_PASS_NO_POSTHOC_SELECTION", "controller arm-interaction conjunction drift")
    require(interventions.get("nuisance_kernel") == ["photon_dose", "heat", "pupil", "arousal", "locomotion", "stimulated_cell_count", "induced_spike_count", "latency"], "nuisance kernel drift")
    require(interventions.get("same_contact_rescue_primary") == "R_THETA_ABSOLUTE_CONTACT_ERROR_UPPER_EQUIVALENCE_AND_F_THETA_CONTACT_FRACTION_LCL_GE_0.90", "same-contact rescue criterion drift")
    require(interventions.get("rescue_secondary") == "M_G_AND_Y_DIRECTIONAL_RECOVERY_VS_RESCUE_SHAM_AND_PASSIVE_RECOVERY", "rescue secondary criterion drift")
    require(interventions.get("retraining_or_global_repotentiation_can_count_as_rescue") is False, "global retraining cannot count as same-contact rescue")

    power = contract.get("power", {})
    require(power.get("scipy_version_receipt") == "1.17.1", "SciPy receipt drift")
    require(scipy.__version__ == power.get("scipy_version_receipt"), "runtime SciPy differs from power receipt")
    require(power.get("alpha_one_sided") == 0.05, "alpha drift")
    require(power.get("randomized_atomic_parallel_cell_n") == 108, "randomized atomic parallel-cell N drift")
    require(power.get("actual_min_complete_cases_at_missingness_cap") == 108, "actual minimum complete-case N drift")
    require(power.get("conservative_power_receipt_n") == 100, "conservative power-receipt N drift")
    require(power.get("max_required_atomic_tests") == 83, "atomic test cap drift")
    require(power.get("atomic_ledger_scope") == "ALL_POSTRANDOMIZATION_CONFIRMATORY_DECISIONS;PRE_RANDOMIZATION_ELIGIBILITY_AND_MEASUREMENT_QC_ARE_STOP_GATES;G4_G4B_STRUCTURAL_COMPONENTS_ENTER_THROUGH_FOUR_C_GEO_DECISIONS", "atomic ledger scope drift")
    require(power.get("standardization_denominator_rule") == "EACH_ENDPOINT_USES_ITS_OWN_BLINDED_PRE_RANDOMIZATION_REPEATABILITY_SD_FROZEN_WITHIN_STRATA_BEFORE_ARM_REVEAL", "endpoint standardization denominator rule drift")
    require(power.get("zero_or_unstable_standardization_sd_action") == "ATOMIC_TEST_POWER_STOP_NO_POOLED_POSTOUTCOME_SD", "unstable standardization-SD action drift")
    require(power.get("continuous_endpoint_sampling_model") == "INDEPENDENT_ANIMALS_WITH_GAUSSIAN_STRATUM_RESIDUALS_FOR_T_TOST_POWER_RECEIPTS_FROZEN_BEFORE_ARM_REVEAL", "continuous endpoint sampling model drift")
    require(power.get("absolute_error_endpoint_model") == "R_THETA_IS_AN_ANIMAL_LEVEL_LATENT_EXPECTATION_ENDPOINT;CONTACTS_ARE_NOT_INDEPENDENT_UNITS", "absolute-error endpoint sampling model drift")
    require(power.get("sampling_model_failure_action") == "T_MODEL_ASSUMPTION_STOP_NEW_CONTRACT_NO_POSTHOC_RANK_TEST_SWITCH", "sampling-model failure action drift")

    between = power.get("directional_between_arm", {})
    require(between.get("null") == "standardized_effect<=0", "between-arm null drift")
    require(between.get("design_alternative_sd") == 0.7, "between-arm design alternative drift")
    require(between.get("n_per_group_for_receipt") == 100, "between-arm N receipt drift")
    require(between.get("sesoi_pass_threshold") is None, "design alternative cannot masquerade as SESOI threshold")
    between_computed = between_arm_power(0.05, 0.7, 100)
    require(abs(between_computed - between.get("expected_power", math.nan)) < 1e-12, "between-arm power receipt drift")

    paired = power.get("directional_paired", {})
    require(paired.get("null") == "standardized_paired_effect<=0", "paired directional null drift")
    require(paired.get("design_alternative_sd") == 0.5, "paired design alternative drift")
    require(paired.get("n_pairs") == 100, "paired directional N drift")
    require(paired.get("sesoi_pass_threshold") is None, "paired design alternative cannot be a SESOI threshold")
    paired_computed = paired_directional_power(0.05, 0.5, 100)
    require(abs(paired_computed - paired.get("expected_power", math.nan)) < 1e-12, "paired directional power receipt drift")

    equivalence = power.get("paired_equivalence", {})
    require(equivalence.get("test") == "TOST_PAIRED_NORMAL_DIFFERENCE_EXACT_CHI_SQUARE_INTEGRATION", "equivalence test drift")
    require(equivalence.get("null") == "effect<=-0.5_or_effect>=0.5", "equivalence null drift")
    require(equivalence.get("true_effect_for_design") == 0.0, "equivalence design effect drift")
    require(equivalence.get("equivalence_margin_sd") == 0.5, "equivalence margin drift")
    require(equivalence.get("n_pairs") == 100, "equivalence N drift")
    equivalence_computed = paired_equivalence_power_at_zero(0.05, 0.5, 100)
    require(abs(equivalence_computed - equivalence.get("expected_power", math.nan)) < 1e-12, "paired equivalence power receipt drift")

    upper_margin = power.get("one_sample_upper_margin", {})
    require(upper_margin.get("test") == "ONE_SAMPLE_UPPER_T_MARGIN", "one-sample upper-margin test drift")
    require(upper_margin.get("null") == "standardized_endpoint>=0.5", "one-sample upper-margin null drift")
    require(upper_margin.get("true_effect_for_design") == 0.0, "one-sample upper-margin design effect drift")
    require(upper_margin.get("upper_margin_sd") == 0.5, "one-sample upper-margin drift")
    require(upper_margin.get("n") == 100, "one-sample upper-margin N drift")
    upper_margin_computed = one_sample_upper_margin_power(0.05, 0.5, 100)
    require(abs(upper_margin_computed - upper_margin.get("expected_power", math.nan)) < 1e-12, "one-sample upper-margin power receipt drift")

    lower_directional = power.get("one_sample_lower_directional", {})
    require(lower_directional.get("test") == "ONE_SAMPLE_LOWER_T_DIRECTIONAL_OR_MARGIN", "one-sample lower-directional test drift")
    require(lower_directional.get("null") == "standardized_endpoint_or_margin_distance<=0", "one-sample lower-directional null drift")
    require(lower_directional.get("design_alternative_sd") == 0.5, "one-sample lower-directional design alternative drift")
    require(lower_directional.get("n") == 100, "one-sample lower-directional N drift")
    lower_directional_computed = one_sample_lower_directional_power(0.05, 0.5, 100)
    require(abs(lower_directional_computed - lower_directional.get("expected_power", math.nan)) < 1e-12, "one-sample lower-directional power receipt drift")

    binomial_fraction = power.get("binomial_pass_fraction", {})
    require(binomial_fraction.get("test") == "ONE_SIDED_EXACT_CLOPPER_PEARSON_LCL", "binomial pass-fraction test drift")
    require(binomial_fraction.get("null_pass_fraction") == 0.9, "binomial null pass fraction drift")
    require(binomial_fraction.get("true_pass_fraction_for_design") == 0.995, "binomial design pass fraction drift")
    require(binomial_fraction.get("n") == 100, "binomial pass-fraction N drift")
    binomial_min_successes, binomial_lcl, binomial_power = binomial_pass_fraction_power(0.05, 0.9, 0.995, 100)
    require(binomial_fraction.get("minimum_successes") == binomial_min_successes == 96, "binomial minimum-success receipt drift")
    require(abs(binomial_lcl - binomial_fraction.get("lcl_at_minimum_successes", math.nan)) < 1e-12, "binomial LCL receipt drift")
    require(abs(binomial_power - binomial_fraction.get("expected_power", math.nan)) < 1e-12, "binomial power receipt drift")

    require(power.get("primary_logic") == "INTERSECTION_UNION_CONJUNCTION", "primary logic must be conjunction")
    require(power.get("joint_power_bound_method") == "BONFERRONI_FAILURE_UNION_BOUND_NO_DEPENDENCE_ASSUMPTION", "joint power method drift")
    joint_computed = 1.0 - 83 * (
        1.0
        - min(
            between_computed,
            paired_computed,
            equivalence_computed,
            upper_margin_computed,
            lower_directional_computed,
            binomial_power,
        )
    )
    require(abs(joint_computed - power.get("joint_power_lower_bound", math.nan)) < 1e-12, "joint power receipt drift")
    require(joint_computed >= 0.9, "joint design power lower bound below 0.90")
    require(power.get("missingness_power_rule") == "ANY_TECHNICAL_NA_STOPS_PRIMARY_DECISION;COMPLETE_N_IS_108_AND_POWER_RECEIPTS_USE_CONSERVATIVE_N_100", "missingness power rule drift")
    require(power.get("equivalence_interpretation") == "EXCLUDES_MODERATE_OR_LARGER_CHANGE_NOT_EXACT_ZERO", "equivalence interpretation drift")
    require(power.get("smaller_effect_interpretation") == "A_POSITIVE_EFFECT_BELOW_THE_DESIGN_ALTERNATIVE_CAN_PASS_IF_ITS_FROZEN_CI_EXCLUDES_ZERO;DESIGN_ALTERNATIVE_IS_POWER_ONLY_NOT_SESOI", "smaller-effect interpretation drift")

    require(contract.get("estimands") == EXPECTED_ESTIMANDS, "estimand IDs, directions, families, or margins drift")
    require(contract.get("atomic_test_ledger") == EXPECTED_ATOMIC_TEST_LEDGER, "atomic-test ledger drift")
    atomic_total = sum(item["atomic_tests"] for item in EXPECTED_ATOMIC_TEST_LEDGER)
    require(atomic_total == 83 and atomic_total == power.get("max_required_atomic_tests"), "atomic-test total must equal frozen power cap 83")

    missingness = contract.get("missingness", {})
    require(missingness.get("all_randomized_animals_in_itt") is True, "all randomized animals must remain in ITT")
    require(missingness.get("postrandomization_replacement") is False, "postrandomization replacement forbidden")
    require(missingness.get("lost_output_cell_metric_action") == "ANIMAL_ENDPOINT_MISSING_NOT_REDUCED_DIMENSION", "lost-output-cell action drift")
    require(missingness.get("lost_contact_theta_action") == "BIOLOGICAL_LOSS_THETA_ZERO_IF_PARENT_VISIBLE", "lost-contact theta action drift")
    require(missingness.get("technical_na_action") == "ANY_PRIMARY_ENDPOINT_TECHNICAL_NA_CAUSES_MISSINGNESS_STOP_NO_PRIMARY_DECISION", "technical-NA action drift")
    require(missingness.get("primary_missing_data_model") == "NO_PRIMARY_IMPUTATION_COMPLETE_RANDOMIZED_CELL_REQUIRED_FOR_ANY_PASS_DECISION", "primary missing-data model drift")
    require(missingness.get("stopped_run_sensitivity") == "DESCRIPTIVE_ENDPOINT_SPECIFIC_WORST_CASE_BOUNDS_REPORTED_AFTER_STOP_WITHOUT_PASS_OR_RESCUE", "stopped-run sensitivity rule drift")
    require(missingness.get("sensitivity_can_rescue_primary") is False, "missingness sensitivity cannot rescue primary decision")
    require(missingness.get("max_postrandomization_missing_fraction_per_atomic_cell") == 0.0, "missingness fraction drift")
    require(missingness.get("max_differential_missingness_fraction") == 0.0, "differential missingness threshold drift")
    require(missingness.get("required_complete_cases_per_atomic_cell_for_any_decision") == 108, "required complete-case N for any decision drift")
    require(missingness.get("power_or_missingness_failure_action") == "MISSINGNESS_STOP_NO_EFFECTIVE_N_REPLACEMENT", "power/missingness failure action drift")
    require(missingness.get("threshold_failure_stop") == "MISSINGNESS_STOP", "missingness stop drift")
    randomized_n = power.get("randomized_atomic_parallel_cell_n", 0)
    missing_cap = missingness.get("max_postrandomization_missing_fraction_per_atomic_cell", 1.0)
    actual_min_complete = randomized_n - math.floor(missing_cap * randomized_n)
    require(actual_min_complete == power.get("actual_min_complete_cases_at_missingness_cap"), "actual complete-case floor and missingness cap disagree")
    require(actual_min_complete == missingness.get("required_complete_cases_per_atomic_cell_for_any_decision"), "zero-missingness decision N and randomized N disagree")
    require(actual_min_complete >= power.get("conservative_power_receipt_n", math.inf), "randomized N and allowed missingness do not preserve conservative power N")

    assumptions = contract.get("causal_assumptions", {})
    for key in (
        "positivity",
        "consistency",
        "randomized_mechanism",
        "randomized_mediator_state",
        "randomized_rescue",
        "mediator_outcome_confounding_audit",
        "controller_exclusion_is_conditional_not_proven",
        "independent_animal_holdout",
        "no_complete_mediation_claim",
    ):
        require(assumptions.get(key) is True, f"causal assumption/control missing: {key}")

    require(contract.get("required_gates") == EXPECTED_GATES, "required-gate sequence drift")
    require(contract.get("stop_states") == EXPECTED_STOPS, "stop-state sequence drift")

    forbidden = set(contract.get("forbidden", []))
    required_forbidden = {
        "adolescence_as_primary_gate",
        "physical_spacetime_claim",
        "actuator_as_neural_state_chart",
        "actuator_pullback_as_intrinsic_metric",
        "do_g_or_do_m",
        "behavior_inside_metric_or_controller_training",
        "ridge_or_eigen_clipping_to_create_spd",
        "pooled_animals_to_create_spd",
        "post_result_patch_selection",
        "posthoc_conditioning_on_achieved_m",
        "confirmation_sham_output_as_controller_target",
        "survivor_only_contact_analysis",
        "signed_contact_rescue_error_cancellation",
        "replacement_output_cells",
        "retraining_or_global_repotentiation_as_same_contact_rescue",
        "as_parac1_shrinkage_alone_as_reversible_tool",
        "static_fisher_as_finsler_rejection",
        "sampled_grid_as_unconditional_open_patch_proof",
        "complete_mediation_assumed_from_dag",
        "post_outcome_threshold_change",
        "pooled_postoutcome_sd_for_power_rescue",
        "blocked_dataset_rescue",
        "cross_paper_l4_synthesis",
        "bulk_download_without_explicit_approval",
    }
    require(forbidden == required_forbidden, "forbidden-action set drift or unknown entry")

    if check_semantic_lock:
        try:
            semantic_lock_matches = semantic_sha256(contract) == CANONICAL_SEMANTIC_SHA256
        except (TypeError, ValueError):
            semantic_lock_matches = False
        require(
            semantic_lock_matches,
            "canonical semantic fingerprint drift (unknown, missing, non-finite, or modified field)",
        )

    return errors


def validate_contract(contract: dict[str, Any], *, check_semantic_lock: bool = True) -> list[str]:
    """Validate fail-closed and return errors instead of leaking type/value exceptions."""
    try:
        return _validate_contract_impl(contract, check_semantic_lock=check_semantic_lock)
    except Exception as exc:
        errors = [f"structured validation failure: {type(exc).__name__}: {exc}"]
        if check_semantic_lock:
            errors.append(
                "canonical semantic fingerprint drift (unknown, missing, non-finite, or modified field)"
            )
        return errors


def validate_markdown(
    markdown_text: str,
    json_file_sha256: str,
) -> list[str]:
    required = [
        f"Machine contract SHA-256: `{json_file_sha256}`",
        "`STATUS_SENTINEL=SCHEMA_FREEZE_CANDIDATE`",
        "`L4_GATE_EVALUATED=false`",
        "`BIOLOGICAL_ENDPOINT_EVALUATED=false`",
        "`EXECUTION_AUTHORIZED=false`",
        "`CLAIM_CEILING=BIO_EVIDENCE_L0`",
        "`REVERSIBLE_SAME_CONTACT_TOOL_STOP`",
        "`open_patch_claim_authorized=false`",
    ]
    errors = [f"markdown parity missing: {snippet}" for snippet in required if snippet not in markdown_text]
    markdown_file_sha256 = hashlib.sha256(markdown_text.encode("utf-8")).hexdigest()
    if markdown_file_sha256 != CANONICAL_MARKDOWN_SHA256:
        errors.append("canonical markdown full-file SHA-256 drift")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", nargs="?", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()

    contract: dict[str, Any] = {}
    errors: list[str] = []
    file_sha: str | None = None
    try:
        raw = args.contract.read_bytes()
        file_sha = hashlib.sha256(raw).hexdigest()
        contract = load_contract_text(raw.decode("utf-8"))
        errors.extend(validate_contract(contract))
    except Exception as exc:
        errors.append(f"structured validation failure: {type(exc).__name__}: {exc}")

    try:
        if args.markdown.exists():
            markdown_raw = args.markdown.read_bytes()
            markdown_text = markdown_raw.decode("utf-8")
            errors.extend(
                validate_markdown(
                    markdown_text,
                    file_sha if file_sha is not None else "UNAVAILABLE",
                )
            )
        else:
            errors.append(f"markdown contract missing: {args.markdown}")
    except Exception as exc:
        errors.append(f"structured markdown validation failure: {type(exc).__name__}: {exc}")

    try:
        semantic_receipt = semantic_sha256(contract) if contract else None
    except (TypeError, ValueError):
        semantic_receipt = None

    report = {
        "status": "CONTRACT_SCHEMA_PASS" if not errors else "CONTRACT_SCHEMA_FAIL",
        "schema_only": True,
        "contract": str(args.contract),
        "markdown": str(args.markdown),
        "json_file_sha256": file_sha,
        "semantic_sha256": semantic_receipt,
        "error_count": len(errors),
        "errors": errors,
        "l4_gate_evaluated": False,
        "biological_endpoint_evaluated": False,
        "execution_authorized": False,
        "claim_ceiling": "BIO_EVIDENCE_L0",
        "python_version": platform.python_version(),
        "scipy_version": scipy.__version__,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
