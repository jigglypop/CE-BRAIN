"""Write the frozen BA-SRM8 pre-behavior candidate manifest and receipt."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "candidate-manifest.json"
RECEIPT_PATH = ROOT / "candidate-manifest-receipt.json"


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_fsynced(path: Path, payload: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


KERNELS = [
    ("EXP_theta2", "EXP", {"theta": 2}, "exp(-u/theta)"),
    ("EXP_theta10", "EXP", {"theta": 10}, "exp(-u/theta)"),
    ("BIEXP_theta1_1_theta2_8_a_0p5", "BIEXP", {"a": 0.5, "theta_1": 1, "theta_2": 8}, "a*exp(-u/theta_1)+(1-a)*exp(-u/theta_2)"),
    ("BIEXP_theta1_4_theta2_32_a_0p5", "BIEXP", {"a": 0.5, "theta_1": 4, "theta_2": 32}, "a*exp(-u/theta_1)+(1-a)*exp(-u/theta_2)"),
    ("POWER_theta2_p1p5", "POWER", {"p": 1.5, "theta": 2}, "(1+u/theta)^(-p)"),
    ("POWER_theta8_p2", "POWER", {"p": 2, "theta": 8}, "(1+u/theta)^(-p)"),
    ("COMPACT_L4", "COMPACT", {"L": 4}, "exp(-1/(1-(u/L)^2)) if 0<=u<L else 0"),
    ("COMPACT_L16", "COMPACT", {"L": 16}, "exp(-1/(1-(u/L)^2)) if 0<=u<L else 0"),
]
ROBUST_MAPS = [
    ("identity", {"kind": "identity"}, "x"),
    ("radial_huber_c3", {"c": 3, "kind": "radial_huber"}, "x*min(1,c/r(x)) if r(x)>0 else 0"),
    ("radial_tanh_c3", {"c": 3, "kind": "radial_tanh"}, "x*tanh(r(x)/c)/(r(x)/c) if r(x)>0 else 0"),
]


def build_manifest() -> dict[str, object]:
    candidates: list[dict[str, object]] = []
    for kernel_id, family, parameters, kernel_formula in KERNELS:
        for gamma in (1, 2):
            for robust_id, robust_parameters, robust_formula in ROBUST_MAPS:
                candidates.append(
                    {
                        "formula_components": {
                            "kernel": {"family": family, "formula": kernel_formula, "id": kernel_id, "parameters": parameters},
                            "quality_exponent": gamma,
                            "robust_map": {"formula": robust_formula, "id": robust_id, "parameters": robust_parameters},
                        },
                        "id": f"{kernel_id}__gamma{gamma}__{robust_id}",
                    }
                )
    return {
        "candidate_count_expected": 48,
        "candidate_order": "kernel_then_quality_exponent_then_robust_map",
        "candidates": candidates,
        "common": {
            "calibration_ranges": {
                "cG_feature_scales_ridge_fit": "first_70_percent",
                "measurement": "first_60_percent_neural_only",
                "no_refit_after_small": True,
            },
            "delta_cap": 3,
            "delta_0": 1,
            "features": ["Q", "V", "kappa", "M"],
            "gap_policy": "SOFT_GAP_DOWNWEIGHTING",
            "history_support": {
                "BIEXP": "full_causal_history_no_truncation",
                "COMPACT": "u_lt_L",
                "EXP": "full_causal_history_no_truncation",
                "POWER": "full_causal_history_no_truncation",
            },
            "lambda": 1,
            "n_eff_min": 8,
            "selection_unit": "recording_cluster",
            "stage_allocation_percent": {
                "FINAL": 20,
                "LARGE_A": 2.5,
                "LARGE_B": 2.5,
                "MID": 3,
                "SMALL": 2,
                "calibration_train": 70,
            },
            "stage_minimum_rules": {
                "candidate_coverage": 0.95,
                "final": {"heldout_recordings": 2, "rows_each": 100},
                "nonheldout": {"clusters": 7, "pooled_rows": 100, "rows_per_cluster": 8},
            },
            "final_statistic": "min_recording_delta_r2",
        },
        "funnel": {
            "stage_caps": [48, 32, 16, 8, 4, 2, 1],
            "stages": ["F0", "F1", "F2", "F2R", "SMALL", "MID", "LARGE_A", "LARGE_B", "FINAL"],
            "tie_policies": {
                "F1_F2": ["median_NMAE_ascending", "median_Spearman_descending", "runtime_ascending", "formula_id_lexical"],
                "F2R": ["rho_1_median_Spearman_descending", "NMAE_ascending", "false_alarm_ascending", "runtime_ascending", "formula_id_lexical"],
                "behavior": ["J_descending", "kernel_component_count_ascending", "manifest_id_lexical"],
                "large_b_failure": "no_runner_up_substitution",
            },
        },
        "manifest_version": "BA-SRM8-candidate-manifest-v1",
    }


def main() -> None:
    manifest = build_manifest()
    candidate_ids = [candidate["id"] for candidate in manifest["candidates"]]
    assert len(candidate_ids) == 48
    assert len(set(candidate_ids)) == 48
    assert manifest["candidate_count_expected"] == len(candidate_ids)
    manifest_payload = canonical_bytes(manifest)
    write_fsynced(MANIFEST_PATH, manifest_payload)
    assert MANIFEST_PATH.read_bytes() == manifest_payload
    compact_content = {
        "candidates": manifest["candidates"],
        "common": manifest["common"],
        "funnel": manifest["funnel"],
    }
    receipt = {
        "candidate_count": len(candidate_ids),
        "canonical_compact_content_sha256": sha256_bytes(canonical_bytes(compact_content)),
        "exact_expected_count": len(candidate_ids) == manifest["candidate_count_expected"] == 48,
        "manifest_file_sha256": sha256_bytes(manifest_payload),
        "script_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "unique_ids": len(candidate_ids) == len(set(candidate_ids)),
    }
    receipt_payload = canonical_bytes(receipt)
    write_fsynced(RECEIPT_PATH, receipt_payload)
    assert RECEIPT_PATH.read_bytes() == receipt_payload
    print(json.dumps(receipt, allow_nan=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
