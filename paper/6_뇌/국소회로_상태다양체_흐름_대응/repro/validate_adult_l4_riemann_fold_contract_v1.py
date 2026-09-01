from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from scipy.stats import nct, t


DEFAULT_CONTRACT = Path(__file__).with_name("adult_l4_riemann_fold_contract_v1.json")

REQUIRED_GATES = {
    "G0_SOURCE_LOCK",
    "G1_APPARATUS",
    "G2_IDENTITY",
    "G3_THETA_FIDELITY",
    "G4_RAW_RIEMANN",
    "G5_MICRO_TO_METRIC",
    "G6_METRIC_TO_BEHAVIOR",
    "G7_MEDIATOR_STATE",
    "G8_SELECTIVE_RESCUE",
    "G9_HOLDOUT_ASSUMPTIONS",
}
REQUIRED_STOPS = {
    "APPARATUS_INTEGRATION_STOP",
    "ENDPOINT_NOT_EVALUATED",
    "RAW_FISHER_NOT_RIEMANN",
    "MICRO_TO_METRIC_NOT_SUPPORTED",
    "METRIC_BEHAVIOR_MEDIATION_NOT_SUPPORTED",
    "INTERVENTION_EXCLUSION_FAILED",
    "RESCUE_NOT_SUPPORTED",
    "CONFIRMATION_NOT_REPRODUCED",
    "MISSINGNESS_STOP",
}
REQUIRED_ALTERNATIVES = {"RIEMANN", "FINSLER_RANDERS", "STRATIFIED", "DISCRETE_GRAPH"}
REQUIRED_ESTIMANDS = {
    "E_THETA",
    "E_METRIC",
    "E_BEHAVIOR",
    "E_STATE",
    "E_DIRECT",
    "E_UPSTREAM_RESCUE",
}


def between_arm_power(alpha: float, effect: float, n_per_arm: int) -> float:
    df = 2 * n_per_arm - 2
    critical = t.ppf(1.0 - alpha, df)
    noncentrality = effect * math.sqrt(n_per_arm / 2.0)
    return float(1.0 - nct.cdf(critical, df, noncentrality))


def paired_power(alpha: float, effect: float, n_pairs: int) -> float:
    df = n_pairs - 1
    critical = t.ppf(1.0 - alpha, df)
    noncentrality = effect * math.sqrt(n_pairs)
    return float(1.0 - nct.cdf(critical, df, noncentrality))


def validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(contract.get("schema_version") == 1, "schema_version must be 1")
    require(contract.get("contract_id") == "CE_NPF_ADULT_L4_RIEMANN_FOLD_V1", "contract_id drift")
    require(contract.get("execution_authorized") is False, "execution must remain unauthorized")
    require(contract.get("claim_ceiling") == "BIO_EVIDENCE_L0", "candidate must remain BIO_EVIDENCE_L0")

    scope = contract.get("scope", {})
    require(scope.get("adult_only") is True, "adult_only must be true")
    require(scope.get("physical_lorentz_spacetime_claim") is False, "physical spacetime claim forbidden")
    require(scope.get("primary_unit") == "animal", "primary unit must be animal")
    require(scope.get("age_weeks") == [12, 20], "adult age window drift")

    budget = contract.get("data_budget", {})
    require(budget.get("metadata_before_payload") is True, "metadata must precede payload")
    require(budget.get("sample_download_max_mb") == 100, "sample budget must remain 100 MB")
    require(budget.get("explicit_approval_above_mb") == 500, "approval boundary must remain 500 MB")
    require(budget.get("bulk_download_authorized") is False, "bulk download must not be authorized")

    sources = contract.get("source_anchors", [])
    require(len(sources) >= 6, "at least six primary source anchors required")
    require(all(str(item.get("doi", "")).startswith("10.") for item in sources), "all sources require DOI")

    cohorts = contract.get("cohorts", {})
    development = cohorts.get("development", {})
    confirmation = cohorts.get("confirmation", {})
    require(development.get("max_animals") == 12, "development cap drift")
    require(development.get("inferential") is False, "development cannot be inferential")
    require(development.get("outcome_effects_forbidden") is True, "development outcome effects must be forbidden")
    require(confirmation.get("arms") == ["TARGET_A", "SHAM", "OFFTARGET_B"], "confirmation arms drift")
    require(confirmation.get("evaluable_per_arm") == 28, "confirmation evaluable N drift")
    require(confirmation.get("max_enrollment_per_arm") == 35, "confirmation enrollment cap drift")
    require(confirmation.get("model_frozen_before_randomization") is True, "model must freeze before randomization")
    require(confirmation.get("animal_level_holdout") is True, "animal-level holdout required")

    power = contract.get("power", {})
    between = power.get("between_arm", {})
    paired = power.get("paired_state_rescue", {})
    if all(key in between for key in ("alpha", "sesoi_standardized", "n_per_arm", "target_power", "expected_power")):
        computed = between_arm_power(between["alpha"], between["sesoi_standardized"], between["n_per_arm"])
        require(computed >= between["target_power"], "between-arm power below target")
        require(abs(computed - between["expected_power"]) < 1e-12, "between-arm power receipt drift")
    else:
        errors.append("between-arm power fields missing")
    if all(key in paired for key in ("alpha", "sesoi_standardized", "n_pairs", "target_power", "expected_power")):
        computed = paired_power(paired["alpha"], paired["sesoi_standardized"], paired["n_pairs"])
        require(computed >= paired["target_power"], "paired power below target")
        require(abs(computed - paired["expected_power"]) < 1e-12, "paired power receipt drift")
    else:
        errors.append("paired power fields missing")
    require(power.get("primary_logic") == "intersection_union_conjunction", "primary logic must be conjunction")

    measurements = contract.get("measurements", {})
    channels = [measurements.get(name, {}).get("channel_id") for name in ("theta", "output", "behavior")]
    require(None not in channels and len(set(channels)) == 3, "theta/output/behavior channels must be distinct")
    require(measurements.get("output", {}).get("excludes_theta_sensor") is True, "output must exclude theta sensor")
    require(measurements.get("behavior", {}).get("excluded_from_metric_definition") is True, "behavior cannot define metric")
    require(measurements.get("output", {}).get("minimum_stable_cells", 0) >= 8, "at least eight stable output cells required")

    probe = contract.get("probe", {})
    require(probe.get("dimension") == 2, "probe dimension must be 2")
    require(probe.get("grid_shape") == [5, 5], "probe grid must be 5x5")
    require(probe.get("trials_per_grid_point") == 48, "48 trials per point required")
    require(probe.get("calibration_trials_per_point", 0) + probe.get("holdout_trials_per_point", 0) == probe.get("trials_per_grid_point"), "probe split must exhaust trials")
    require(probe.get("holdout_trials_per_point", 0) >= 24, "at least 24 holdout trials per point required")

    fisher = contract.get("fisher", {})
    require(fisher.get("raw_metric_required") is True, "raw metric required")
    require(fisher.get("regularized_metric_can_pass") is False, "regularized metric cannot pass")
    require(fisher.get("lambda_min_lower_bound", 0) > 0, "positive raw lambda lower bound required")
    require(fisher.get("max_condition_number", math.inf) <= 50, "condition-number ceiling drift")
    require(fisher.get("minimum_passing_grid_fraction", 0) >= 0.9, "grid pass fraction below 0.9")
    require(set(fisher.get("alternatives", [])) == REQUIRED_ALTERNATIVES, "geometry alternatives incomplete")

    fold = contract.get("fold_summary", {})
    require(fold.get("behavior_free") is True, "fold summary must be behavior-free")
    require(fold.get("physical_curvature") is False, "fold summary cannot be physical curvature")

    interventions = contract.get("interventions", {})
    require(interventions.get("mechanism") == ["TARGET_A", "SHAM", "OFFTARGET_B"], "mechanism controls incomplete")
    require(interventions.get("causal_state") == ["STATE_OFF", "STATE_RESTORE", "STATE_ORTHOGONAL"], "causal-state controls incomplete")
    require(bool(interventions.get("upstream_rescue")), "upstream rescue missing")
    require(interventions.get("theta_must_remain_lesioned_during_state_rescue") is True, "state rescue must not restore theta")
    require(interventions.get("energy_matched_orthogonal_control") is True, "energy-matched orthogonal control missing")
    require(interventions.get("recovery_control") is True, "recovery control missing")

    assumptions = contract.get("causal_assumptions", {})
    for key in (
        "positivity",
        "consistency",
        "mediator_outcome_confounding_audit",
        "exclusion_direct_path_controls",
        "tensor_do_operator_forbidden",
        "independent_holdout_or_replication",
    ):
        require(assumptions.get(key) is True, f"causal assumption/control missing: {key}")

    require({item.get("id") for item in contract.get("estimands", [])} == REQUIRED_ESTIMANDS, "estimand set drift")
    require(set(contract.get("required_gates", [])) == REQUIRED_GATES, "required L4 gates incomplete")
    require(set(contract.get("stop_states", [])) == REQUIRED_STOPS, "stop-state set incomplete")

    forbidden = set(contract.get("forbidden", []))
    require("physical_spacetime_claim" in forbidden, "physical spacetime prohibition missing")
    require("ridge_to_create_spd_evidence" in forbidden, "ridge prohibition missing")
    require("behavior_inside_metric" in forbidden, "circular metric prohibition missing")
    require("post_outcome_threshold_change" in forbidden, "post-outcome change prohibition missing")

    return errors


def load_contract(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", nargs="?", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    raw = args.contract.read_bytes()
    contract = json.loads(raw.decode("utf-8"))
    errors = validate_contract(contract)
    report = {
        "status": "PASS" if not errors else "FAIL",
        "contract": str(args.contract),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "error_count": len(errors),
        "errors": errors,
        "biological_endpoint_evaluated": False,
        "execution_authorized": contract.get("execution_authorized"),
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
