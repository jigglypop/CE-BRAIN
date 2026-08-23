"""BA-SRM9 behavior-blind F2-A screen: 32 candidates to at most 24."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT.parent
OLD = RUN_ROOT.parent / "brain-physical-time-effective-dimension-funnel-20260823" / "artifacts"
OUT = ROOT / "f2a-receipt.json"

# Import the immutable candidate evaluator from BA-SRM8 and the repaired successor
# generator from this directory.  The hashes below are checked before candidate Q.
sys.path.insert(0, str(OLD))
from funnel_core_v2 import causal_q, manifest, sha, spearman  # noqa: E402
sys.path.pop(0)

from f2_common import generate  # noqa: E402


EXPECTED_HASHES = {
    "predecessor_manifest": "58280bb9759549b9f285e95135b5320e44f1d317adf347a065319f367a3e6a0c",
    "predecessor_core": "e685568ad4836dab1f301f69afa2e9c9a4d8fcecd7a1a64fb2bdba830a5ebc65",
    "predecessor_f0_v3": "86b70828449889c1f3bfaf9422a0e41b01655d83bcd7d1c067b3d8da796b1ab7",
    "predecessor_f1_v6_runner": "3ab7eb89d49ae3845a72e5808f0cf9423014f520b961fe7551576be22f1c2be7",
    "predecessor_f1_v6": "8cbdaed43fc861c4696a41a3fd84331fd41727622d848e123b635d8c9ae11cca",
    "predecessor_config_v4": "9248c9fac975ea70ac034d11e45be70eff7abccb13b65eae7be7010850e2de47",
    "predecessor_common_v2": "12200f0f6d2d2db61d1000c40a39049123b5f1e2023ef439f9763ad69794f605",
    "predecessor_fixture_v3": "6346c57cbdc7c8b564b316aca0ba06008ac01c9e66035b7794f8c472612592bf",
    "carry_forward": "08ccdcfb27e9e87e4e8608ea2aafca5871ab9103c3b4730a47126a47e47d5b1e",
    "successor_config": "7ac07dda3e1b077fdeb5d0d4f49693499ab6f89c0f68e3f9a89838aa1987eece",
    "successor_config_receipt": "ec48392bb0343e3a2a20e040e3df61e7c395e0053c2651e0a6d5eaf0c910cb71",
    "successor_common": "f8be7234124abc094b71f0000a775121d939c29013eb42921dad09149c342dca",
    "jump_fixture": "028b24a16cb154fa238b53114de1519fb06531e6436fbf498f5b4d605d34daf4",
    "contract": "e1e24e6c5252b5033f1ebf55ef0fb08fee77918e69d01705f67d4934c96cdb5c",
    "math": "b3f7206ceaddb1c59f830ad2f7a88c3954cc45f3f375e66a973c17a646c769b5",
}

EXPECTED_ENVIRONMENT = {
    "interpreter": r"C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe",
    "python": "3.11.9",
    "numpy": "2.4.6",
    "scipy": "1.17.1",
}


def compact_sha(value: object) -> str:
    payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def input_paths() -> dict[str, Path]:
    return {
        "predecessor_manifest": OLD / "candidate-manifest.json",
        "predecessor_core": OLD / "funnel_core_v2.py",
        "predecessor_f0_v3": OLD / "f0-receipt-v3.json",
        "predecessor_f1_v6_runner": OLD / "run_f1_v6.py",
        "predecessor_f1_v6": OLD / "f1-receipt-v6.json",
        "predecessor_config_v4": OLD / "f2-config-v4.json",
        "predecessor_common_v2": OLD / "f2_common_v2.py",
        "predecessor_fixture_v3": OLD / "f2-generator-fixture-v3.json",
        "carry_forward": ROOT / "carry-forward-receipt.json",
        "successor_config": ROOT / "f2-config.json",
        "successor_config_receipt": ROOT / "f2-config-receipt.json",
        "successor_common": ROOT / "f2_common.py",
        "jump_fixture": ROOT / "jump-fixture-receipt.json",
        "contract": RUN_ROOT / "00-contract.md",
        "math": RUN_ROOT / "11-math.md",
    }


def verify_inputs() -> tuple[dict, list[dict], list[str], dict[str, str]]:
    paths = input_paths()
    actual = {name: sha(path) for name, path in paths.items()}
    if actual != EXPECTED_HASHES:
        mismatches = {
            name: {"expected": EXPECTED_HASHES[name], "actual": actual.get(name)}
            for name in EXPECTED_HASHES
            if actual.get(name) != EXPECTED_HASHES[name]
        }
        raise RuntimeError(f"STOP_RE_RUN_AFFECTED_STAGE: {mismatches}")

    audit_path = RUN_ROOT / "20-audit.md"
    audit_hash = sha(audit_path)
    audit_text = audit_path.read_text(encoding="utf-8")
    runner_hash = sha(Path(__file__))
    actual_environment = {
        "interpreter": str(Path(sys.executable).resolve()),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }
    environment_matches = (
        os.path.normcase(actual_environment["interpreter"])
        == os.path.normcase(EXPECTED_ENVIRONMENT["interpreter"])
        and actual_environment["python"] == EXPECTED_ENVIRONMENT["python"]
        and actual_environment["numpy"] == EXPECTED_ENVIRONMENT["numpy"]
        and actual_environment["scipy"] == EXPECTED_ENVIRONMENT["scipy"]
    )
    if not (
        "Status: COMPLETE" in audit_text
        and "Gate: PASS" in audit_text
        and "Execute numerical F2-A from its first seed" in audit_text
        and f"Runner SHA-256: `{runner_hash}`" in audit_text
        and f"Interpreter: `{EXPECTED_ENVIRONMENT['interpreter']}`" in audit_text
        and f"Python: `{EXPECTED_ENVIRONMENT['python']}`" in audit_text
        and f"NumPy: `{EXPECTED_ENVIRONMENT['numpy']}`" in audit_text
        and f"SciPy: `{EXPECTED_ENVIRONMENT['scipy']}`" in audit_text
        and environment_matches
    ):
        raise RuntimeError(
            "STOP_RE_RUN_AFFECTED_STAGE: exact F2-A runner/environment authorization is not PASS"
        )
    actual["authorization_audit"] = audit_hash

    man, manifest_hash = manifest()
    if manifest_hash != EXPECTED_HASHES["predecessor_manifest"]:
        raise RuntimeError("STOP_RE_RUN_AFFECTED_STAGE: manifest loader mismatch")

    config = json.loads((ROOT / "f2-config.json").read_text(encoding="utf-8"))
    promoted_ids = config["promoted_ids"]
    if (
        len(promoted_ids) != 32
        or len(set(promoted_ids)) != 32
        or compact_sha(promoted_ids)
        != "b4c2ef2e4160711b4b26b35195a3ace8c2376eb32910f9aec008973ff7dc678b"
    ):
        raise RuntimeError("STOP_RE_RUN_AFFECTED_STAGE: promoted ID invariant")

    candidates = [candidate for candidate in man["candidates"] if candidate["id"] in set(promoted_ids)]
    if len(candidates) != 32 or {candidate["id"] for candidate in candidates} != set(promoted_ids):
        raise RuntimeError("STOP_RE_RUN_AFFECTED_STAGE: promoted IDs do not match manifest")

    fixture = json.loads((ROOT / "jump-fixture-receipt.json").read_text(encoding="utf-8"))
    if not (
        fixture["status"] == "PASS"
        and fixture["candidate_Q_run"] is False
        and fixture["numerical_F2A"] is False
        and fixture["behavior_loaded"] is False
        and fixture["model_fit"] is False
    ):
        raise RuntimeError("STOP_RE_RUN_AFFECTED_STAGE: fixture status invariant")
    return config, candidates, promoted_ids, actual


def preprocess_pair(clean: np.ndarray, noisy: np.ndarray, mask: np.ndarray, prefix_end: int):
    if clean.shape != noisy.shape or clean.shape != mask.shape:
        raise ValueError("PREFIX_SHAPE")
    if not (np.isfinite(clean).all() and np.isfinite(noisy).all()):
        raise ValueError("PREFIX_NONFINITE_RAW")

    count = clean.shape[0]
    clean_z = np.zeros_like(clean, dtype=np.float64)
    noisy_z = np.zeros_like(noisy, dtype=np.float64)
    d = np.empty(count, dtype=np.float64)
    prefix_counts = np.empty(count, dtype=np.int64)
    for channel in range(count):
        observed = mask[channel, :prefix_end] == 1
        prefix_counts[channel] = int(observed.sum())
        if prefix_counts[channel] < 2:
            raise ValueError(f"PREFIX_COUNT_CHANNEL_{channel}")
        clean_prefix = clean[channel, :prefix_end][observed]
        noisy_prefix = noisy[channel, :prefix_end][observed]
        clean_sd = float(np.std(clean_prefix, ddof=0))
        noisy_sd = float(np.std(noisy_prefix, ddof=0))
        if not math.isfinite(clean_sd) or clean_sd <= 1e-12:
            raise ValueError(f"PREFIX_CLEAN_SCALE_CHANNEL_{channel}")
        if not math.isfinite(noisy_sd) or noisy_sd <= 1e-12:
            raise ValueError(f"PREFIX_NOISY_SCALE_CHANNEL_{channel}")
        clean_z[channel] = (clean[channel] - float(np.mean(clean_prefix))) / clean_sd
        noisy_z[channel] = (noisy[channel] - float(np.mean(noisy_prefix))) / noisy_sd
        d[channel] = math.sqrt(float(np.mean(mask[channel, :prefix_end])))

    clean_z[mask == 0] = 0.0
    noisy_z[mask == 0] = 0.0
    if not (np.isfinite(clean_z).all() and np.isfinite(noisy_z).all() and np.isfinite(d).all()):
        raise ValueError("PREFIX_NONFINITE_TRANSFORM")
    return clean_z, noisy_z, d, prefix_counts


def build_cache(config: dict) -> tuple[dict, dict]:
    prefix_end = int(config["boundaries"]["T_D"])
    scenarios = {
        "ISO_CAL": [("ISO_NULL", seed) for seed in config["panels"]["S_cal"]],
        "ZERO": [("ZERO_NULL", seed) for seed in config["panels"]["E_A"]],
        "ISO": [("ISO_NULL", seed) for seed in config["panels"]["E_A"]],
        "JUMP": [("JUMP", seed) for seed in config["panels"]["E_A"]],
    }
    cache: dict[tuple[str, int], dict] = {}
    preflight = {"expected_zero_abstentions": [], "valid_nonzero_entries": 0}
    for panel, items in scenarios.items():
        for scenario, seed in items:
            key = (scenario, int(seed))
            raw = generate(scenario, int(seed))
            try:
                clean_z, noisy_z, d, prefix_counts = preprocess_pair(
                    raw["clean"], raw["noisy"], raw["mask"], prefix_end
                )
                prepared = {
                    "status": "VALID",
                    "clean_z": clean_z,
                    "noisy_z": noisy_z,
                    "d": d,
                    "prefix_counts": prefix_counts,
                }
            except ValueError as exc:
                prepared = {"status": "ABSTAIN_PREFIX_SCALE", "reason": str(exc)}

            if panel == "ZERO":
                preflight["expected_zero_abstentions"].append(
                    {"seed": int(seed), "status": prepared["status"], "reason": prepared.get("reason")}
                )
            elif prepared["status"] != "VALID":
                raise RuntimeError(
                    f"SYNTHETIC_DGP_STOP: {scenario} seed {seed}: {prepared.get('reason')}"
                )
            else:
                preflight["valid_nonzero_entries"] += 1
            cache[key] = {"raw": raw, "prepared": prepared}

    # 16 disjoint ISO calibration seeds plus 8 ZERO, 8 ISO, and 8 JUMP E_A seeds.
    if len(cache) != 40:
        raise RuntimeError(f"SYNTHETIC_DGP_STOP: unexpected cache size {len(cache)}")
    preflight["all_zero_expected_abstain"] = all(
        row["status"] == "ABSTAIN_PREFIX_SCALE"
        for row in preflight["expected_zero_abstentions"]
    )
    return cache, preflight


def evaluate_pair(candidate: dict, entry: dict, calibration_end: int) -> dict:
    prepared = entry["prepared"]
    if prepared["status"] != "VALID":
        raise ValueError(prepared.get("reason", "PREPROCESS_ABSTAIN"))
    raw = entry["raw"]
    d = prepared["d"]
    # D is mask-derived, and therefore exactly shared by truth and estimate.
    if not np.array_equal(d, np.sqrt(np.mean(raw["mask"][:, :460], axis=1))):
        raise RuntimeError("D_SHARED_INVARIANT")
    truth = causal_q(
        candidate, prepared["clean_z"], raw["mask"], raw["clock"], d, calibration_end
    )
    estimate = causal_q(
        candidate, prepared["noisy_z"], raw["mask"], raw["clock"], d, calibration_end
    )
    q_truth = truth["Q"]
    q_estimate = estimate["Q"]
    anchor = np.isfinite(q_truth) & np.isfinite(q_estimate)
    derivative_anchor = anchor[1:] & anchor[:-1]
    return {
        "q_truth": q_truth,
        "q_estimate": q_estimate,
        "anchor": anchor,
        "derivative_anchor": derivative_anchor,
        "truth_cG": float(truth["cG"]),
        "estimate_cG": float(estimate["cG"]),
    }


def derivative_magnitude(pair: dict, clock: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    anchor = pair["derivative_anchor"]
    tau0 = float(np.median(np.diff(clock)))
    magnitude = np.abs(np.diff(pair["q_estimate"])[anchor]) / (
        np.diff(clock)[anchor] / tau0
    )
    original_indices = np.where(anchor)[0] + 1
    return magnitude, original_indices


def abstain_row(candidate_id: str, reason: str, started: float, metrics: dict) -> dict:
    return {
        "id": candidate_id,
        "status": "ABSTAIN",
        "reason": reason,
        "metrics": metrics,
        "runtime_seconds": time.perf_counter() - started,
    }


def evaluate_candidate(candidate: dict, config: dict, cache: dict, preflight: dict) -> dict:
    candidate_id = candidate["id"]
    started = time.perf_counter()
    calibration_end = int(config["boundaries"]["T_cal"])
    calibration_rows = []
    pooled_derivatives: list[float] = []

    try:
        for seed in config["panels"]["S_cal"]:
            entry = cache[("ISO_NULL", int(seed))]
            pair = evaluate_pair(candidate, entry, calibration_end)
            anchor_count = int(pair["anchor"].sum())
            derivative_count = int(pair["derivative_anchor"].sum())
            if anchor_count < 100 or derivative_count < 100:
                return abstain_row(
                    candidate_id,
                    "ISO_CALIBRATION_INSUFFICIENT",
                    started,
                    {"calibration_rows": calibration_rows},
                )
            magnitude, _ = derivative_magnitude(pair, entry["raw"]["clock"])
            if not np.isfinite(magnitude).all():
                return abstain_row(
                    candidate_id,
                    "ISO_CALIBRATION_NONFINITE_DERIVATIVE",
                    started,
                    {"calibration_rows": calibration_rows},
                )
            pooled_derivatives.extend(float(value) for value in magnitude)
            calibration_rows.append(
                {
                    "seed": int(seed),
                    "anchor_count": anchor_count,
                    "derivative_anchor_count": derivative_count,
                    "truth_cG": pair["truth_cG"],
                    "estimate_cG": pair["estimate_cG"],
                }
            )
    except ValueError as exc:
        return abstain_row(
            candidate_id,
            "ISO_CALIBRATION_NUMERIC_ABSTAIN",
            started,
            {"detail": str(exc), "calibration_rows": calibration_rows},
        )

    if not pooled_derivatives:
        return abstain_row(candidate_id, "ISO_CALIBRATION_EMPTY", started, {})
    theta = float(np.quantile(pooled_derivatives, 0.95, method="linear"))
    if not math.isfinite(theta):
        return abstain_row(candidate_id, "ISO_CALIBRATION_NONFINITE_THRESHOLD", started, {})

    if not preflight["all_zero_expected_abstain"]:
        return {
            "id": candidate_id,
            "status": "INVALID_KILL",
            "reason": "ZERO_NOT_EXPECTED_ABSTAIN",
            "metrics": {"theta": theta},
            "runtime_seconds": time.perf_counter() - started,
        }

    iso_rows = []
    jump_rows = []
    try:
        for seed in config["panels"]["E_A"]:
            iso_entry = cache[("ISO_NULL", int(seed))]
            iso_pair = evaluate_pair(candidate, iso_entry, calibration_end)
            iso_anchor_count = int(iso_pair["anchor"].sum())
            iso_derivative_count = int(iso_pair["derivative_anchor"].sum())
            if iso_anchor_count < 100 or iso_derivative_count < 100:
                return abstain_row(
                    candidate_id,
                    "E_A_ISO_INSUFFICIENT",
                    started,
                    {"theta": theta, "ISO": iso_rows, "JUMP": jump_rows},
                )
            iso_magnitude, _ = derivative_magnitude(iso_pair, iso_entry["raw"]["clock"])
            iso_rows.append(
                {
                    "seed": int(seed),
                    "anchor_count": iso_anchor_count,
                    "derivative_anchor_count": iso_derivative_count,
                    "nmae": float(
                        np.mean(
                            np.abs(
                                iso_pair["q_truth"][iso_pair["anchor"]]
                                - iso_pair["q_estimate"][iso_pair["anchor"]]
                            )
                        )
                    ),
                    "far": float(np.mean(iso_magnitude > theta)),
                    "truth_cG": iso_pair["truth_cG"],
                    "estimate_cG": iso_pair["estimate_cG"],
                }
            )

            jump_entry = cache[("JUMP", int(seed))]
            jump_pair = evaluate_pair(candidate, jump_entry, calibration_end)
            jump_anchor_count = int(jump_pair["anchor"].sum())
            jump_derivative_count = int(jump_pair["derivative_anchor"].sum())
            if jump_anchor_count < 100 or jump_derivative_count < 100:
                return abstain_row(
                    candidate_id,
                    "E_A_JUMP_INSUFFICIENT",
                    started,
                    {"theta": theta, "ISO": iso_rows, "JUMP": jump_rows},
                )
            jump_rho = spearman(
                jump_pair["q_truth"][jump_pair["anchor"]],
                jump_pair["q_estimate"][jump_pair["anchor"]],
            )
            if not math.isfinite(jump_rho):
                return abstain_row(
                    candidate_id,
                    "ABSTAIN_CONSTANT_TRUTH",
                    started,
                    {"theta": theta, "ISO": iso_rows, "JUMP": jump_rows},
                )
            jump_magnitude, jump_indices = derivative_magnitude(
                jump_pair, jump_entry["raw"]["clock"]
            )
            peak_offset = int(np.argmax(jump_magnitude))
            peak_index = int(jump_indices[peak_offset])
            peak_value = float(jump_magnitude[peak_offset])
            jump_rows.append(
                {
                    "seed": int(seed),
                    "anchor_count": jump_anchor_count,
                    "derivative_anchor_count": jump_derivative_count,
                    "nmae": float(
                        np.mean(
                            np.abs(
                                jump_pair["q_truth"][jump_pair["anchor"]]
                                - jump_pair["q_estimate"][jump_pair["anchor"]]
                            )
                        )
                    ),
                    "rho": float(jump_rho),
                    "peak_index": peak_index,
                    "peak_value": peak_value,
                    "detected": bool(288 <= peak_index <= 480 and peak_value > theta),
                    "truth_cG": jump_pair["truth_cG"],
                    "estimate_cG": jump_pair["estimate_cG"],
                }
            )
    except ValueError as exc:
        return abstain_row(
            candidate_id,
            "E_A_NUMERIC_ABSTAIN",
            started,
            {"detail": str(exc), "theta": theta, "ISO": iso_rows, "JUMP": jump_rows},
        )

    median_iso_nmae = float(np.median([row["nmae"] for row in iso_rows]))
    median_jump_nmae = float(np.median([row["nmae"] for row in jump_rows]))
    median_jump_rho = float(np.median([row["rho"] for row in jump_rows]))
    mean_iso_far = float(np.mean([row["far"] for row in iso_rows]))
    detections = int(sum(row["detected"] for row in jump_rows))
    rank_e = max(median_iso_nmae, median_jump_nmae)
    rank_r = median_jump_rho  # Frozen contract: JUMP is F2-A's only non-null recovery scenario.
    passed = (
        median_jump_rho >= 0.80
        and median_jump_nmae <= 0.20
        and mean_iso_far <= 0.20
        and detections >= 4
    )
    return {
        "id": candidate_id,
        "status": "PASS" if passed else "FUTILITY_KILL",
        "reason": None if passed else "F2A_NUMERIC_FUTILITY",
        "metrics": {
            "theta": theta,
            "calibration_pooled_count": len(pooled_derivatives),
            "calibration_rows": calibration_rows,
            "ISO": iso_rows,
            "JUMP": jump_rows,
            "median_iso_nmae": median_iso_nmae,
            "median_jump_nmae": median_jump_nmae,
            "median_jump_rho": median_jump_rho,
            "mean_iso_far": mean_iso_far,
            "detections": detections,
            "rank_E": rank_e,
            "rank_R": rank_r,
        },
        "runtime_seconds": time.perf_counter() - started,
    }


def write_receipt(value: dict) -> None:
    payload = (
        json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    with OUT.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"one-shot receipt already exists: {OUT}")
    config, candidates, promoted_ids, hashes = verify_inputs()
    cache, preflight = build_cache(config)
    print(
        json.dumps(
            {
                "event": "F2A_PREFLIGHT_PASS",
                "candidates": len(candidates),
                "cache_entries": len(cache),
                "zero_expected_abstain": preflight["all_zero_expected_abstain"],
            },
            sort_keys=True,
        ),
        flush=True,
    )

    rows = []
    for index, candidate in enumerate(candidates, start=1):
        row = evaluate_candidate(candidate, config, cache, preflight)
        rows.append(row)
        summary = {
            "event": "F2A_CANDIDATE_COMPLETE",
            "index": index,
            "total": len(candidates),
            "id": row["id"],
            "status": row["status"],
            "runtime_seconds": row["runtime_seconds"],
        }
        if row["status"] in {"PASS", "FUTILITY_KILL"}:
            summary.update(
                {
                    "rank_E": row["metrics"]["rank_E"],
                    "rank_R": row["metrics"]["rank_R"],
                    "far": row["metrics"]["mean_iso_far"],
                    "detections": row["metrics"]["detections"],
                }
            )
        print(json.dumps(summary, sort_keys=True), flush=True)

    valid = sorted(
        [row for row in rows if row["status"] == "PASS"],
        key=lambda row: (
            row["metrics"]["rank_E"],
            -row["metrics"]["rank_R"],
            row["metrics"]["mean_iso_far"],
            row["runtime_seconds"],
            row["id"],
        ),
    )
    next_ids = [row["id"] for row in valid[:24]]
    for row in rows:
        if row["id"] in next_ids:
            row["status"] = "PROMOTE"
        elif row["status"] == "PASS":
            row["status"] = "DROPPED_BUDGET"
            row["reason"] = "F2A_CAP24"

    receipt = {
        "schema": "BA-SRM9-F2A-v1",
        "stage": "F2-A",
        "candidate_Q_run": True,
        "numerical_F2A": True,
        "behavior_loaded": False,
        "model_fit": False,
        "real_endpoint_opened": False,
        "biological_claim": False,
        "input_hashes": hashes,
        "authorization_audit_sha256": hashes["authorization_audit"],
        "runner_sha256": sha(Path(__file__)),
        "environment": EXPECTED_ENVIRONMENT,
        "input_promoted_ids": promoted_ids,
        "input_promoted_ids_sha256": compact_sha(promoted_ids),
        "preflight": preflight,
        "candidates": rows,
        "promoted_ids": next_ids,
        "promoted_ids_sha256": compact_sha(next_ids),
        "counts": {
            status: sum(row["status"] == status for row in rows)
            for status in [
                "PROMOTE",
                "DROPPED_BUDGET",
                "FUTILITY_KILL",
                "ABSTAIN",
                "INVALID_KILL",
            ]
        },
        "runtime_seconds": float(sum(row["runtime_seconds"] for row in rows)),
        "downstream_authorized": False,
    }
    write_receipt(receipt)
    print(
        json.dumps(
            {
                "event": "F2A_COMPLETE",
                "promoted": len(next_ids),
                "receipt_sha256": sha(OUT),
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
