"""Preregistered Stage 3H structural-operator/response relation test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from examples.brain.ce_brain_stage3f_optofmri_state_rdm import exact_signflip_p
from examples.brain.ce_brain_stage3g_optofmri_physical_distance import (
    exact_source_permutation_p,
)


PRIMARY_ORDER = {"Thy1": 1, "VGAT": 3}


def analyze(structural: dict[str, object], physical: dict[str, object]) -> dict[str, object]:
    if structural.get("response_data_used") is not False:
        raise ValueError("structural operator was not outcome-blind")
    rows = list(physical["subjects"])
    structural_rdms = {
        order: np.asarray(structural["structural_rdms"][f"incremental_order_{order}"], dtype=float)
        for order in (1, 2, 3)
    }
    subject_rows = []
    for row in rows:
        response = np.asarray(row["cross_half_rdm"], dtype=float)
        scores = {
            order: float(spearmanr(structural_rdms[order], response).statistic)
            for order in (1, 2, 3)
        }
        subject_rows.append(
            {
                "subject": row["subject"],
                "genotype": row["genotype"],
                "repeat_reliability": row["repeat_reliability"],
                "response_rdm": response.tolist(),
                "structural_rho": {str(order): score for order, score in scores.items()},
            }
        )

    gates = {}
    for genotype in ("Thy1", "VGAT"):
        selected = [row for row in subject_rows if row["genotype"] == genotype]
        primary_order = PRIMARY_ORDER[genotype]
        reliability = np.asarray([row["repeat_reliability"] for row in selected], dtype=float)
        primary = np.asarray(
            [row["structural_rho"][str(primary_order)] for row in selected], dtype=float
        )
        responses = np.asarray([row["response_rdm"] for row in selected], dtype=float)
        fixed = np.stack([structural_rdms[primary_order]] * len(selected))
        reliability_p = exact_signflip_p(reliability)
        association_p = exact_signflip_p(primary)
        source_p = exact_source_permutation_p(fixed, responses)
        reliability_pass = bool(np.median(reliability) >= 0.30 and reliability_p <= 0.05)
        association_pass = bool(
            np.median(primary) >= 0.30 and association_p <= 0.05 and source_p <= 0.05
        )
        specificity = {}
        specificity_pass = True
        for alternative in (order for order in (1, 2, 3) if order != primary_order):
            alternative_scores = np.asarray(
                [row["structural_rho"][str(alternative)] for row in selected], dtype=float
            )
            differences = primary - alternative_scores
            p_value = exact_signflip_p(differences)
            passed = bool(np.median(differences) >= 0.10 and p_value <= 0.05)
            specificity[str(alternative)] = {
                "primary_minus_alternative": differences.tolist(),
                "median": float(np.median(differences)),
                "signflip_p": p_value,
                "passed": passed,
            }
            specificity_pass &= passed
        gates[genotype] = {
            "primary_order": primary_order,
            "repeat_reliability": {
                "values": reliability.tolist(),
                "median": float(np.median(reliability)),
                "signflip_p": reliability_p,
                "passed": reliability_pass,
            },
            "structural_relation": {
                "values": primary.tolist(),
                "median": float(np.median(primary)),
                "signflip_p": association_p,
                "source_permutation_p": source_p,
                "passed": association_pass,
            },
            "order_specificity": specificity,
            "order_specific": specificity_pass,
            "passed": reliability_pass and association_pass,
        }

    passed_count = sum(bool(gate["passed"]) for gate in gates.values())
    if passed_count == 2:
        status = "STRUCTURAL_OPERATOR_RELATION_CANDIDATE"
    elif passed_count == 1:
        status = "CONDITION_LIMITED_STRUCTURAL_OPERATOR_CANDIDATE"
    else:
        status = "STRUCTURAL_OPERATOR_RELATION_NOT_ESTABLISHED"
    return {
        "status": status,
        "gates": gates,
        "subjects": subject_rows,
        "calibration_confirmation_opened": False,
        "claim_ceiling": "fixed six-source by 136-target structural propagation profile relation",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--structural", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    structural = json.loads(args.structural.read_text(encoding="utf-8"))
    physical = json.loads(args.response.read_text(encoding="utf-8"))
    result = analyze(structural, physical)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
