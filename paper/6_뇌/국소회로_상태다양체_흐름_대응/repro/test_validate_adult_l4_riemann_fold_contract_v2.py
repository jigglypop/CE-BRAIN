from __future__ import annotations

import copy
import hashlib
import json
import sys

import pytest

import validate_adult_l4_riemann_fold_contract_v2 as validator


def contract() -> dict:
    return validator.load_contract(validator.DEFAULT_CONTRACT)


def errors_after(mutator) -> list[str]:
    mutated = copy.deepcopy(contract())
    mutator(mutated)
    return validator.validate_contract(mutated)


def test_canonical_contract_and_markdown_pass_schema_only() -> None:
    candidate = contract()
    assert validator.validate_contract(candidate) == []
    raw = validator.DEFAULT_CONTRACT.read_bytes()
    markdown = validator.DEFAULT_MARKDOWN.read_text(encoding="utf-8")
    assert validator.validate_markdown(markdown, hashlib.sha256(raw).hexdigest()) == []


def test_main_receipt_never_reports_biological_pass(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["validator"])
    assert validator.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "CONTRACT_SCHEMA_PASS"
    assert report["schema_only"] is True
    assert report["l4_gate_evaluated"] is False
    assert report["biological_endpoint_evaluated"] is False
    assert report["execution_authorized"] is False
    assert report["claim_ceiling"] == "BIO_EVIDENCE_L0"


def test_l4_complete_status_and_execution_authorization_fail_closed() -> None:
    def mutate(value: dict) -> None:
        value["status"] = "BIO_EVIDENCE_L4_COMPLETE"
        value["execution_authorized"] = True
        value["l4_gate_evaluated"] = True
        value["biological_endpoint_evaluated"] = True
        value["claim_ceiling"] = "BIO_EVIDENCE_L4"

    errors = errors_after(mutate)
    assert any("status" in error for error in errors)
    assert any("execution" in error for error in errors)
    assert any("L4 gate" in error for error in errors)
    assert any("biological endpoint" in error for error in errors)
    assert any("claim ceiling" in error for error in errors)


def test_actuator_cannot_masquerade_as_neural_state() -> None:
    def mutate(value: dict) -> None:
        value["state_chart"]["actuator_is_neural_chart"] = True
        value["state_chart"]["primary_likelihood"] = "p_i_t(O_future|a,h,c)"
        value["state_chart"]["actuator_pullback_status"] = "PRIMARY_G4"

    errors = errors_after(mutate)
    assert any("actuator cannot" in error for error in errors)
    assert any("primary likelihood" in error for error in errors)
    assert any("pullback role" in error for error in errors)


def test_metric_measurement_cannot_be_relabelled_as_mediator() -> None:
    def mutate(value: dict) -> None:
        value["causal_objects"]["mediator"] = "m_i_G"
        value["causal_objects"]["metric_is_measurement_not_biological_state"] = False
        value["causal_objects"]["do_m_forbidden"] = False

    errors = errors_after(mutate)
    assert any("mediator must be M" in error for error in errors)
    assert any("metric/state distinction" in error for error in errors)
    assert any("do(g) and do(m)" in error for error in errors)


def test_theta_morphology_only_and_unverified_proxy_fail_closed() -> None:
    def mutate(value: dict) -> None:
        value["theta_measurement"]["morphology_alone_can_pass"] = True
        value["theta_measurement"]["heldout_direct_calibration_required"] = False
        value["theta_measurement"]["presynaptic_event_or_release_verified"] = False

    errors = errors_after(mutate)
    assert any("morphology alone" in error for error in errors)
    assert any("heldout_direct_calibration_required" in error for error in errors)
    assert any("presynaptic_event_or_release_verified" in error for error in errors)


def test_theta_task_summary_repeatability_sigma_and_contact_delta_are_frozen() -> None:
    def mutate(value: dict) -> None:
        theta = value["theta_measurement"]
        theta["task_conditioned_summary"] = "barTheta_OVER_ALL_C0"
        theta["primary_main_theta_endpoint"] = "BEST_CONTACT_SET"
        theta["repeatability_blocks_pre_randomization"] = 2
        theta["sigma_repeat_formula"] = "POOLED_CONTACT_SD"
        theta["delta_contact_formula"] = "POSTHOC_QUANTILE"
        theta["sigma_nonfinite_or_nonpositive_action"] = "ADD_EPSILON"

    errors = errors_after(mutate)
    assert any("task-conditioned theta summary" in error for error in errors)
    assert any("primary task-A theta endpoint" in error for error in errors)
    assert any("repeatability block count" in error for error in errors)
    assert any("repeatability sigma formula" in error for error in errors)
    assert any("same-contact delta formula" in error for error in errors)
    assert any("zero/nonfinite action" in error for error in errors)


def test_disappearing_spine_and_output_cell_replacement_fail_closed() -> None:
    def mutate(value: dict) -> None:
        value["identity"]["disappearing_spine_rule"] = "EXCLUDE_FROM_SURVIVOR_ANALYSIS"
        value["identity"]["output_cells_replaceable"] = True
        value["output_model"]["exact_cell_count"] = 7
        value["output_model"]["lost_cell_action"] = "REPLACE_WITH_NEAREST_CELL"

    errors = errors_after(mutate)
    assert any("spine loss" in error for error in errors)
    assert any("replacement forbidden" in error for error in errors)
    assert any("exact" in error and "output" in error for error in errors)
    assert any("lost-cell action" in error for error in errors)


def test_unvalidated_same_contact_tool_cannot_be_promoted() -> None:
    def mutate(value: dict) -> None:
        value["biological_starting_mechanism"]["tool_validated"] = True
        value["biological_starting_mechanism"]["as_parac1_role"] = "PRIMARY_L4_TOOL"
        value["biological_starting_mechanism"]["same_contact_structural_survival_required"] = False

    errors = errors_after(mutate)
    assert any("unvalidated tool" in error for error in errors)
    assert any("AS-PaRac1 role" in error for error in errors)
    assert any("structural survival" in error for error in errors)


def test_fold_formula_and_coordinate_transforms_are_exact() -> None:
    def mutate(value: dict) -> None:
        value["fold_summary"]["directional_stretch_formula"] = "mean(u_A^T*E*u_A-u_B^T*E*u_B)"
        value["fold_summary"]["fold_formula"] = "nonsense"
        value["fisher_geometry"]["vector_transform"] = "u_tilde=J*u"

    errors = errors_after(mutate)
    assert any("stretch formula" in error for error in errors)
    assert any("fold formula" in error for error in errors)
    assert any("vector transform" in error for error in errors)


def test_state_conditioned_geometry_and_mediator_control_are_exact() -> None:
    def mutate(value: dict) -> None:
        value["causal_objects"]["metric_definition"] = "g_i_t(z)=I_z[p_i_t(O_future|z,h,c)]"
        value["state_chart"]["primary_likelihood"] = "p_i_t(O_future|z,h,c)"
        value["fisher_geometry"]["state_condition_index"] = "k_IN_{BASELINE,STATE_OFF}"
        value["fold_summary"]["state_conditions"] = ["STATE_OFF"]
        value["mediator_state"]["orthogonal_off_target_projection_equivalence_required"] = False

    errors = errors_after(mutate)
    assert any("state-conditioned metric" in error for error in errors)
    assert any("state-conditioned primary likelihood" in error for error in errors)
    assert any("Fisher state-condition" in error for error in errors)
    assert any("fold state-condition" in error for error in errors)
    assert any("target-projection equivalence" in error for error in errors)


def test_jacobian_rank_and_actuator_direct_path_have_numeric_powered_gates() -> None:
    def mutate(value: dict) -> None:
        state = value["state_chart"]
        state["jacobian_sigma_min_simultaneous_lcb"] = 0.0
        state["jacobian_condition_number_simultaneous_ucb_max"] = 1e9
        state["actuator_direct_path_test"] = "AVERAGE_OVER_STATES"
        state["actuator_direct_path_atomic_states"] = ["BEST_STATE"]
        state["actuator_direct_path_primary_arm"] = "POOLED_ARMS"
        state["actuator_direct_path_physical_margin_power_gate"] = "NOT_REQUIRED"

    errors = errors_after(mutate)
    assert any("minimum generalized singular-value" in error for error in errors)
    assert any("condition-number gate" in error for error in errors)
    assert any("actuator direct-path test" in error for error in errors)
    assert any("direct-path atomic state set" in error for error in errors)
    assert any("direct-path primary arm" in error for error in errors)
    assert any("direct-path physical-margin power gate" in error for error in errors)


def test_behavior_endpoint_formula_window_missingness_and_sd_are_exact() -> None:
    def mutate(value: dict) -> None:
        endpoint = value["behavior_endpoint"]
        endpoint["tasks"]["A"] = "UNSPECIFIED"
        endpoint["trial_window_ms_from_cue"] = [0, 1000]
        endpoint["valid_trial_denominator_per_task_time_state"] = 39
        endpoint["formula"] = "Y=MEAN_OF_COMPLETED_TRIALS_ONLY"
        endpoint["hardware_or_clock_loss"] = "DROP_TRIAL"
        endpoint["standardization_sd_between"] = "POOLED_POSTOUTCOME_SD"
        endpoint["standardization_frozen_before_arm_reveal"] = False

    errors = errors_after(mutate)
    assert any("Task-A/B observable" in error for error in errors)
    assert any("behavior trial window" in error for error in errors)
    assert any("denominator" in error for error in errors)
    assert any("behavior formula" in error for error in errors)
    assert any("hardware-loss" in error for error in errors)
    assert any("behavior SD denominator" in error for error in errors)
    assert any("freeze before arm reveal" in error for error in errors)


def test_behavior_zone_crossing_and_primary_task_are_executable() -> None:
    def mutate(value: dict) -> None:
        endpoint = value["behavior_endpoint"]
        endpoint["target_zones"]["L2"] = [-1.0, 1.0]
        endpoint["zone_boundary_rule"] = "VISUAL_JUDGMENT"
        endpoint["zone_entry_rule"] = "ANY_SAMPLE_IN_ZONE"
        endpoint["pre_cue_reset_rule"] = "UNSPECIFIED"
        endpoint["primary_task_for_state_and_rescue"] = "A_OR_B_POSTHOC"
        endpoint["rescue_endpoint"] = "BEST_TASK"

    errors = errors_after(mutate)
    assert any("target-zone boundaries" in error for error in errors)
    assert any("zone-boundary algorithm" in error for error in errors)
    assert any("crossing/debounce" in error for error in errors)
    assert any("pre-cue reset" in error for error in errors)
    assert any("behavior task must be explicit" in error for error in errors)
    assert any("rescue behavior endpoint" in error for error in errors)


def test_grid_patch_selection_and_open_patch_overclaim_fail_closed() -> None:
    def mutate(value: dict) -> None:
        value["fisher_geometry"]["passing_grid_fraction"] = 0.9
        value["scope"]["open_patch_claim_authorized"] = True
        value["fisher_geometry"]["open_patch_status"] = "PROVEN"

    errors = errors_after(mutate)
    assert any("all 25" in error for error in errors)
    assert any("open-patch claim" in error for error in errors)
    assert any("open-patch status" in error for error in errors)


def test_open_patch_transport_and_ordered_path_models_are_exact() -> None:
    def mutate(value: dict) -> None:
        fisher = value["fisher_geometry"]
        fisher["reference_connection"] = "EUCLIDEAN_SUBTRACTION"
        fisher["fiber_comparison"] = "COMPARE_COMPONENTS_DIRECTLY"
        fisher["lipschitz_formula"] = "COORDINATEWISE_MAX"
        fisher["ordered_path_base_model"] = "UNDEFINED"
        fisher["ordered_path_alternative_model"] = "UNDEFINED"
        fisher["ordered_path_estimand"] = "UNDEFINED"

    errors = errors_after(mutate)
    assert any("reference connection" in error for error in errors)
    assert any("fiber comparison" in error for error in errors)
    assert any("coordinate-invariant Lipschitz" in error for error in errors)
    assert any("ordered-path base model" in error for error in errors)
    assert any("ordered-path alternative model" in error for error in errors)
    assert any("ordered-path estimand" in error for error in errors)


def test_open_patch_domain_reference_tensor_and_fill_distance_are_intrinsic() -> None:
    def mutate(value: dict) -> None:
        fisher = value["fisher_geometry"]
        fisher["reference_metric_formula"] = "r=inverse(coordinate_covariance)"
        fisher["reference_metric_extension"] = "LOG_EUCLIDEAN_COMPONENT_SPLINE"
        fisher["candidate_open_patch"] = "P_i_IS_THE_25_POINT_SET"
        fisher["open_patch_primary_arm"] = "ALL_ARMS_POOLED"
        fisher["candidate_patch_nondegeneracy_gate"] = "NOT_REQUIRED"
        fisher["reference_distance_formula"] = "EUCLIDEAN_COORDINATE_DISTANCE"
        fisher["fill_distance_formula"] = "h_P_i=sup_(z_in_P_i)min_j_d(z,z_i_j)"

    errors = errors_after(mutate)
    assert any("reference metric formula" in error for error in errors)
    assert any("reference metric extension" in error for error in errors)
    assert any("candidate open-patch domain" in error for error in errors)
    assert any("primary arm/scope" in error for error in errors)
    assert any("nondegeneracy gate" in error for error in errors)
    assert any("geodesic-distance formula" in error for error in errors)
    assert any("nonzero-domain fill-distance" in error for error in errors)


def test_finsler_competitor_covers_odd_and_reversible_even_without_global_overclaim() -> None:
    def mutate(value: dict) -> None:
        fisher = value["fisher_geometry"]
        value["probe_design"]["ordered_path_directions"] = [
            "u_A", "u_B", "(u_A+u_B)/sqrt(2)", "(u_A-u_B)/sqrt(2)"
        ]
        value["probe_design"]["ordered_path_primary_arm"] = "ALL_ARMS_POOLED"
        fisher["ordered_path_alternative_model"] = "FOUR_ODD_IN_V_TERMS_ONLY"
        fisher["ordered_path_harmonic_design_rank"] = 1
        fisher["ordered_path_estimand"] = "AVERAGE_OVER_TARGETS_AND_STATES"
        fisher["ordered_path_atomic_components"] = "FOUR_ODD_TESTS"
        fisher["ordered_path_pass_rule"] = "ODD_ONLY"
        fisher["global_finsler_exclusion_claim"] = True
        fisher["finsler_competitor_scope"] = "ALL_FINSLER_GEOMETRIES"

    errors = errors_after(mutate)
    assert any("ordered-path directions" in error for error in errors)
    assert any("ordered-path primary arm" in error for error in errors)
    assert any("ordered-path alternative model" in error for error in errors)
    assert any("design-rank" in error for error in errors)
    assert any("ordered-path estimand" in error for error in errors)
    assert any("atomic-component count" in error for error in errors)
    assert any("exact pass rule" in error for error in errors)
    assert any("global Finsler exclusion" in error for error in errors)
    assert any("competitor scope" in error for error in errors)


def test_fisher_thresholds_require_finite_exact_values() -> None:
    def mutate(value: dict) -> None:
        value["fisher_geometry"]["common_support_floor"] = -1.0
        value["fisher_geometry"]["coordinate_covariance_relative_error_max"] = 99.0
        value["fisher_geometry"]["directional_elpd_gain_upper95_max_nat_per_trial"] = float("nan")

    errors = errors_after(mutate)
    assert any("support floor" in error for error in errors)
    assert any("coordinate covariance" in error for error in errors)
    assert any("directional ELPD" in error for error in errors)
    assert any("non-finite" in error for error in errors)


def test_regularization_and_animal_pooling_cannot_create_spd() -> None:
    def mutate(value: dict) -> None:
        value["fisher_geometry"]["ridge_can_pass"] = True
        value["fisher_geometry"]["eigenvalue_clipping_can_pass"] = True
        value["fisher_geometry"]["animal_pooling_can_create_spd"] = True

    errors = errors_after(mutate)
    assert any("regularization" in error for error in errors)
    assert any("animal-level" in error for error in errors)


def test_static_fisher_cannot_be_used_to_reject_finsler() -> None:
    def mutate(value: dict) -> None:
        value["fisher_geometry"]["static_fisher_alone_can_reject_finsler"] = True
        value["probe_design"]["both_arrival_directions_required"] = False

    errors = errors_after(mutate)
    assert any("static Fisher" in error for error in errors)
    assert any("both ordered" in error for error in errors)


def test_randomization_blinding_and_controller_contrasts_fail_closed() -> None:
    def mutate(value: dict) -> None:
        value["randomization"]["main_mechanism_randomized"] = False
        value["randomization"]["controller_order_randomized"] = False
        value["randomization"]["blinded_registration"] = False
        value["interventions"]["restore_must_beat_off"] = False
        value["interventions"]["orthogonal_must_equal_off_on_target_projection_m_G_and_Y"] = False

    errors = errors_after(mutate)
    assert any("main_mechanism_randomized" in error for error in errors)
    assert any("controller_order_randomized" in error for error in errors)
    assert any("blinded_registration" in error for error in errors)
    assert any("restore_must_beat_off" in error for error in errors)
    assert any("orthogonal_must_equal" in error for error in errors)


def test_controller_interaction_has_three_frozen_dependent_endpoints() -> None:
    def mutate(value: dict) -> None:
        value["interventions"]["controller_arm_interaction_endpoints"] = {
            "BEST_AFTER_UNBLINDING": "RESTORE_MINUS_OFF_TARGET_GT_SHAM"
        }
        value["interventions"]["controller_arm_interaction_logic"] = "ANY_ONE_PASSES"

    errors = errors_after(mutate)
    assert any("arm-interaction endpoint set" in error for error in errors)
    assert any("arm-interaction conjunction" in error for error in errors)


def test_global_retraining_cannot_count_as_same_contact_rescue() -> None:
    def mutate(value: dict) -> None:
        value["interventions"]["retraining_or_global_repotentiation_can_count_as_rescue"] = True
        value["interventions"]["same_contact_rescue_primary"] = "DIRECTION_RECOVERY_OR_BASELINE"

    errors = errors_after(mutate)
    assert any("global retraining" in error for error in errors)
    assert any("same-contact rescue criterion" in error for error in errors)


def test_per_contact_rescue_task_sets_and_development_firewall_are_exact() -> None:
    def mutate(value: dict) -> None:
        value["identity"]["task_contact_sets"] = "POOLED_C0"
        value["theta_measurement"]["signed_contact_error_cancellation_can_pass"] = True
        development = value["cohorts"]["development"]
        development["tool_validation_may_read_contact_level_bidirectional_theta_fidelity"] = False
        development["allowed_uses"].remove("mechanism_fidelity")

    errors = errors_after(mutate)
    assert any("task source-contact set" in error for error in errors)
    assert any("signed rescue error" in error for error in errors)
    assert any("contact-level bidirectional" in error for error in errors)
    assert any("allowed-use" in error for error in errors)


def test_same_contact_absolute_error_and_fraction_have_distinct_powered_tests() -> None:
    def mutate(value: dict) -> None:
        value["theta_measurement"]["minimum_C_A0_contacts_per_animal"] = 1
        value["theta_measurement"]["contact_fraction_population_gate"] = "CONTACTS_ARE_INDEPENDENT"
        value["estimands"] = [
            item for item in value["estimands"]
            if item["id"] != "E_THETA_CONTACT_FRACTION_RESCUE"
        ]
        value["atomic_test_ledger"] = [
            item for item in value["atomic_test_ledger"]
            if item["estimand_id"] != "E_THETA_CONTACT_FRACTION_RESCUE"
        ]

    errors = errors_after(mutate)
    assert any("minimum denominator" in error for error in errors)
    assert any("population-fraction gate" in error for error in errors)
    assert any("estimand IDs" in error for error in errors)
    assert any("atomic-test ledger" in error for error in errors)


def test_m_to_fold_local_model_fit_score_derivative_and_states_are_frozen() -> None:
    def mutate(value: dict) -> None:
        mediator = value["mediator_state"]
        mediator["local_map_family"] = "UNSPECIFIED"
        mediator["local_map_fit_set"] = "CONFIRMATION_OUTCOMES"
        mediator["local_map_null_model"] = "BEST_INSAMPLE_MODEL"
        mediator["local_map_confirmation_score"] = "INSAMPLE_R2"
        mediator["local_map_atomic_states"] = ["BEST_STATE"]
        mediator["local_map_directional_derivative_gate"] = "NONZERO_BY_EYE"
        mediator["local_map_derivative_endpoint"] = "AVERAGE_SIGNED_DERIVATIVE"

    errors = errors_after(mutate)
    assert any("local model family" in error for error in errors)
    assert any("fitting-set firewall" in error for error in errors)
    assert any("null model" in error for error in errors)
    assert any("heldout score estimand" in error for error in errors)
    assert any("atomic state set" in error for error in errors)
    assert any("derivative gate" in error for error in errors)
    assert any("derivative endpoint" in error for error in errors)


def test_dag_cannot_silently_assert_complete_mediation() -> None:
    def mutate(value: dict) -> None:
        value["causal_objects"]["dag"] = "Z_THETA_MINUS->THETA;A->Z;(Z,THETA)->M;M->O_FUTURE;M->Y"
        value["causal_objects"]["complete_mediation_claim"] = True
        value["causal_assumptions"]["no_complete_mediation_claim"] = False

    errors = errors_after(mutate)
    assert any("causal DAG" in error for error in errors)
    assert any("complete mediation" in error for error in errors)
    assert any("no_complete_mediation_claim" in error for error in errors)


def test_screen_randomize_itt_contract_is_cross_field_locked() -> None:
    def mutate(value: dict) -> None:
        value["cohorts"]["confirmation"]["eligible_randomized_total"] = 419
        value["cohorts"]["confirmation"]["replacement_after_randomization"] = True
        value["missingness"]["postrandomization_replacement"] = True
        value["missingness"]["all_randomized_animals_in_itt"] = False

    errors = errors_after(mutate)
    assert any("randomized total" in error for error in errors)
    assert any("sum to randomized total" in error for error in errors)
    assert any("replacement forbidden" in error for error in errors)
    assert any("remain in ITT" in error for error in errors)


def test_confirmation_sham_output_cannot_define_controller_target() -> None:
    def mutate(value: dict) -> None:
        value["cohorts"]["confirmation"]["controller_target"] = "CONFIRMATION_SHAM_POST_OUTPUT"
        value["cohorts"]["confirmation"]["confirmation_sham_output_as_target_forbidden"] = False
        value["interventions"]["state_restore_target"] = "CONFIRMATION_SHAM_OUTPUT"

    errors = errors_after(mutate)
    assert any("controller target source" in error for error in errors)
    assert any("SHAM output" in error for error in errors)
    assert any("state restore target" in error for error in errors)


def test_old_n28_power_and_sesoi_conflation_fail_closed() -> None:
    def mutate(value: dict) -> None:
        value["power"]["randomized_atomic_parallel_cell_n"] = 28
        value["power"]["actual_min_complete_cases_at_missingness_cap"] = 27
        value["power"]["conservative_power_receipt_n"] = 28
        value["power"]["directional_between_arm"]["n_per_group_for_receipt"] = 28
        value["power"]["directional_between_arm"]["sesoi_pass_threshold"] = 0.7
        value["power"]["directional_between_arm"]["expected_power"] = 0.905

    errors = errors_after(mutate)
    assert any("atomic parallel-cell N" in error for error in errors)
    assert any("actual minimum complete-case N" in error for error in errors)
    assert any("conservative power-receipt N" in error for error in errors)
    assert any("between-arm N" in error for error in errors)
    assert any("SESOI" in error for error in errors)
    assert any("power receipt" in error for error in errors)


def test_atomic_ledger_and_postmissingness_power_are_cross_locked() -> None:
    def mutate(value: dict) -> None:
        value["atomic_test_ledger"][-1]["atomic_tests"] = 3
        value["power"]["max_required_atomic_tests"] = 82
        value["power"]["randomized_atomic_parallel_cell_n"] = 95
        value["missingness"]["required_complete_cases_per_atomic_cell_for_any_decision"] = 95

    errors = errors_after(mutate)
    assert any("atomic-test ledger" in error for error in errors)
    assert any("atomic test cap" in error for error in errors)
    assert any("atomic-test total" in error for error in errors)
    assert any("required complete-case N" in error for error in errors)
    assert any("complete-case floor" in error for error in errors)
    assert any("do not preserve conservative power N" in error for error in errors)


def test_endpoint_specific_upper_margin_binomial_and_physical_margin_power_are_locked() -> None:
    def mutate(value: dict) -> None:
        value["power"]["one_sample_upper_margin"]["n"] = 28
        value["power"]["one_sample_lower_directional"]["n"] = 28
        value["power"]["binomial_pass_fraction"]["minimum_successes"] = 80
        value["power"]["binomial_pass_fraction"]["expected_power"] = 1.0
        value["fisher_geometry"]["ordered_path_physical_margin_power_gate"] = "NOT_REQUIRED"

    errors = errors_after(mutate)
    assert any("upper-margin N" in error for error in errors)
    assert any("lower-directional N" in error for error in errors)
    assert any("binomial minimum-success" in error for error in errors)
    assert any("binomial power receipt" in error for error in errors)
    assert any("physical-margin power gate" in error for error in errors)


def test_t_sampling_model_and_design_alternative_interpretation_are_explicit() -> None:
    def mutate(value: dict) -> None:
        value["power"]["continuous_endpoint_sampling_model"] = "UNSPECIFIED"
        value["power"]["absolute_error_endpoint_model"] = "CONTACTS_AS_INDEPENDENT_UNITS"
        value["power"]["sampling_model_failure_action"] = "SWITCH_TO_RANK_TEST_POSTHOC"
        value["power"]["smaller_effect_interpretation"] = "CANNOT_PASS"

    errors = errors_after(mutate)
    assert any("continuous endpoint sampling model" in error for error in errors)
    assert any("absolute-error endpoint sampling model" in error for error in errors)
    assert any("sampling-model failure action" in error for error in errors)
    assert any("smaller-effect interpretation" in error for error in errors)


def test_any_technical_missingness_stops_without_imputation_rescue() -> None:
    def mutate(value: dict) -> None:
        missingness = value["missingness"]
        missingness["technical_na_action"] = "MULTIPLE_IMPUTATION_PRIMARY"
        missingness["primary_missing_data_model"] = "ARM_BLIND_MI"
        missingness["stopped_run_sensitivity"] = "CAN_RESCUE_PASS"
        missingness["sensitivity_can_rescue_primary"] = True
        missingness["max_postrandomization_missing_fraction_per_atomic_cell"] = 0.05

    errors = errors_after(mutate)
    assert any("technical-NA action" in error for error in errors)
    assert any("primary missing-data model" in error for error in errors)
    assert any("stopped-run sensitivity" in error for error in errors)
    assert any("cannot rescue" in error for error in errors)
    assert any("missingness fraction" in error for error in errors)


def test_estimand_any_direction_zero_or_huge_margin_fail_closed() -> None:
    def mutate(value: dict) -> None:
        for item in value["estimands"]:
            item["direction"] = "ANY"
            if "equivalence_margin_sd" in item:
                item["equivalence_margin_sd"] = 99.0

    errors = errors_after(mutate)
    assert any("estimand IDs, directions" in error for error in errors)


def test_download_budget_cannot_reopen_bulk_payloads() -> None:
    def mutate(value: dict) -> None:
        value["data_budget"]["sample_download_max_mb"] = 1000
        value["data_budget"]["bulk_download_authorized"] = True
        value["data_budget"]["new_payload_required_for_contract_repair"] = True

    errors = errors_after(mutate)
    assert any("100 MB" in error for error in errors)
    assert any("bulk download" in error for error in errors)
    assert any("must not require" in error for error in errors)


def test_unknown_top_level_or_nested_key_changes_semantic_lock() -> None:
    def mutate(value: dict) -> None:
        value["unknown_top_level"] = True
        value["scope"]["unknown_nested"] = True

    errors = errors_after(mutate)
    assert any("top-level exact schema" in error for error in errors)
    assert any("semantic fingerprint" in error for error in errors)


def test_duplicate_json_keys_are_rejected_before_validation() -> None:
    with pytest.raises(validator.DuplicateKeyError, match="duplicate JSON key"):
        validator.load_contract_text('{"schema_version":2,"schema_version":2}')


def test_nonstandard_json_constants_are_rejected_before_validation() -> None:
    for token in ("NaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="non-standard JSON constant rejected"):
            validator.load_contract_text(f'{{"value":{token}}}')


def test_wrong_nested_type_yields_structured_cli_failure(tmp_path, monkeypatch, capsys) -> None:
    candidate = contract()
    candidate["scope"] = None
    path = tmp_path / "wrong-type.json"
    path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["validator", str(path), "--markdown", str(validator.DEFAULT_MARKDOWN)],
    )

    assert validator.main() == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "CONTRACT_SCHEMA_FAIL"
    assert any("structured validation failure" in error for error in report["errors"])
    assert report["schema_only"] is True
    assert report["biological_endpoint_evaluated"] is False


def test_missing_contract_file_yields_structured_cli_failure(tmp_path, monkeypatch, capsys) -> None:
    missing = tmp_path / "absent.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["validator", str(missing), "--markdown", str(validator.DEFAULT_MARKDOWN)],
    )

    assert validator.main() == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "CONTRACT_SCHEMA_FAIL"
    assert report["json_file_sha256"] is None
    assert any("structured validation failure: FileNotFoundError" in error for error in report["errors"])


def test_markdown_json_hash_and_full_content_lock_fail_closed() -> None:
    raw_hash = hashlib.sha256(validator.DEFAULT_CONTRACT.read_bytes()).hexdigest()
    markdown = validator.DEFAULT_MARKDOWN.read_text(encoding="utf-8")
    errors = validator.validate_markdown(markdown, "0" * 64)
    assert any("Machine contract SHA-256" in error for error in errors)

    mutations = [
        ("`STATUS_SENTINEL=SCHEMA_FREEZE_CANDIDATE`", "`STATUS_SENTINEL=BIO_EVIDENCE_L4_COMPLETE`"),
        (r"m_{i,k}^G=\frac1{25}", r"m_{i,k}^G=0\cdot\frac1{25}"),
        ("exact 540 eligible animals", "exact 28 eligible animals"),
        (r"Y^{(q)}_{i,t,k}=\frac1{40}", r"Y^{(q)}_{i,t,k}=\frac1{1}"),
    ]
    for old, new in mutations:
        assert old in markdown
        drifted = markdown.replace(old, new, 1)
        errors = validator.validate_markdown(drifted, raw_hash)
        assert any("canonical markdown full-file SHA-256 drift" in error for error in errors)
