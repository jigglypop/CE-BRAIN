"""BA-SRM9 behavior-blind F2-C screen: 20 candidates to at most 16."""

from __future__ import annotations

import json
import math
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy

from run_f2a import (
    EXPECTED_ENVIRONMENT,
    OLD,
    ROOT,
    RUN_ROOT,
    compact_sha,
    evaluate_pair,
    generate,
    manifest,
    preprocess_pair,
    sha,
    spearman,
)


OUT = ROOT / "f2c-receipt.json"
EXPECTED_INPUT_HASHES = {
    "predecessor_manifest": "58280bb9759549b9f285e95135b5320e44f1d317adf347a065319f367a3e6a0c",
    "predecessor_core": "e685568ad4836dab1f301f69afa2e9c9a4d8fcecd7a1a64fb2bdba830a5ebc65",
    "successor_config": "7ac07dda3e1b077fdeb5d0d4f49693499ab6f89c0f68e3f9a89838aa1987eece",
    "successor_common": "f8be7234124abc094b71f0000a775121d939c29013eb42921dad09149c342dca",
    "f2a_receipt": "24c1099c63b0e7e59f107788e57bc122c62a267936a0313b03c12d88e2be6aab",
    "f2b_runner": "9a7c93f722521e36311694d9f32359b1abc85cbc5008e9c5c28087a265a91287",
    "f2b_receipt": "ad402c8a872af3461d9600cad4b792eb1440761f5f8222c5b653511cf35f72b2",
    "contract": "e1e24e6c5252b5033f1ebf55ef0fb08fee77918e69d01705f67d4934c96cdb5c",
    "math": "b3f7206ceaddb1c59f830ad2f7a88c3954cc45f3f375e66a973c17a646c769b5",
}


def input_paths() -> dict[str, Path]:
    return {
        "predecessor_manifest": OLD / "candidate-manifest.json",
        "predecessor_core": OLD / "funnel_core_v2.py",
        "successor_config": ROOT / "f2-config.json",
        "successor_common": ROOT / "f2_common.py",
        "f2a_receipt": ROOT / "f2a-receipt.json",
        "f2b_runner": ROOT / "run_f2b.py",
        "f2b_receipt": ROOT / "f2b-receipt.json",
        "contract": RUN_ROOT / "00-contract.md",
        "math": RUN_ROOT / "11-math.md",
    }


def verify_inputs() -> tuple[dict, list[dict], list[str], dict[str, float], dict[str, str]]:
    paths = input_paths()
    actual = {name: sha(path) for name, path in paths.items()}
    if actual != EXPECTED_INPUT_HASHES:
        mismatch = {
            name: {"expected": EXPECTED_INPUT_HASHES[name], "actual": actual.get(name)}
            for name in EXPECTED_INPUT_HASHES
            if actual.get(name) != EXPECTED_INPUT_HASHES[name]
        }
        raise RuntimeError(f"STOP_RE_RUN_AFFECTED_STAGE: {mismatch}")

    config = json.loads((ROOT / "f2-config.json").read_text(encoding="utf-8"))
    f2b = json.loads((ROOT / "f2b-receipt.json").read_text(encoding="utf-8"))
    input_ids = f2b["promoted_ids"]
    if not (
        f2b["schema"] == "BA-SRM9-F2B-v1"
        and f2b["stage"] == "F2-B"
        and f2b["counts"]
        == {
            "ABSTAIN": 0,
            "DROPPED_BUDGET": 4,
            "FUTILITY_KILL": 0,
            "INVALID_KILL": 0,
            "PROMOTE": 20,
        }
        and f2b["candidate_Q_run"] is True
        and f2b["numerical_F2B"] is True
        and f2b["behavior_loaded"] is False
        and f2b["model_fit"] is False
        and f2b["real_endpoint_opened"] is False
        and f2b["biological_claim"] is False
        and f2b["downstream_authorized"] is False
        and len(input_ids) == 20
        and len(set(input_ids)) == 20
        and compact_sha(input_ids)
        == "270a1885fc649e6700065cf2901a72904d1fe345d61d1e37e9c16abca1d4e722"
    ):
        raise RuntimeError("STOP_RE_RUN_AFFECTED_STAGE: invalid F2-B carry")

    man, _ = manifest()
    candidates = [candidate for candidate in man["candidates"] if candidate["id"] in set(input_ids)]
    if len(candidates) != 20 or {candidate["id"] for candidate in candidates} != set(input_ids):
        raise RuntimeError("STOP_RE_RUN_AFFECTED_STAGE: F2-C IDs do not match manifest")
    f2b_rows = {row["id"]: row for row in f2b["candidates"]}
    if any(f2b_rows[candidate_id]["status"] != "PROMOTE" for candidate_id in input_ids):
        raise RuntimeError("STOP_RE_RUN_AFFECTED_STAGE: non-promoted F2-B input")
    frozen_far = {
        candidate_id: float(f2b_rows[candidate_id]["metrics"]["frozen_iso_far"])
        for candidate_id in input_ids
    }

    audit_path = RUN_ROOT / "20-audit.md"
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
    required_audit_tokens = [
        "Status: COMPLETE",
        "Gate: PASS",
        "Execute numerical F2-C from its first seed",
        f"F2-C Runner SHA-256: `{runner_hash}`",
        f"F2-C Interpreter: `{EXPECTED_ENVIRONMENT['interpreter']}`",
        f"F2-C Python: `{EXPECTED_ENVIRONMENT['python']}`",
        f"F2-C NumPy: `{EXPECTED_ENVIRONMENT['numpy']}`",
        f"F2-C SciPy: `{EXPECTED_ENVIRONMENT['scipy']}`",
    ]
    if not environment_matches or any(token not in audit_text for token in required_audit_tokens):
        raise RuntimeError(
            "STOP_RE_RUN_AFFECTED_STAGE: exact F2-C runner/environment authorization is not PASS"
        )
    actual["authorization_audit"] = sha(audit_path)
    return config, candidates, input_ids, frozen_far, actual


def build_cache(config: dict) -> tuple[dict, dict]:
    prefix_end = int(config["boundaries"]["T_D"])
    cache = {}
    rows = []
    for scenario in ("BLOCK30", "ART10"):
        for seed in config["panels"]["E_C"]:
            raw = generate(scenario, int(seed))
            try:
                clean_z, noisy_z, d, prefix_counts = preprocess_pair(
                    raw["clean"], raw["noisy"], raw["mask"], prefix_end
                )
            except ValueError as exc:
                raise RuntimeError(f"SYNTHETIC_DGP_STOP: {scenario} seed {seed}: {exc}") from exc
            cache[(scenario, int(seed))] = {
                "raw": raw,
                "prepared": {
                    "status": "VALID",
                    "clean_z": clean_z,
                    "noisy_z": noisy_z,
                    "d": d,
                    "prefix_counts": prefix_counts,
                },
            }
            rows.append(
                {
                    "scenario": scenario,
                    "seed": int(seed),
                    "min_prefix_count": int(prefix_counts.min()),
                }
            )
    if len(cache) != 16:
        raise RuntimeError(f"SYNTHETIC_DGP_STOP: unexpected F2-C cache size {len(cache)}")
    return cache, {"status": "PASS", "entries": len(cache), "rows": rows}


def abstain_row(candidate_id: str, reason: str, started: float, metrics: dict) -> dict:
    return {
        "id": candidate_id,
        "status": "ABSTAIN",
        "reason": reason,
        "metrics": metrics,
        "runtime_seconds": time.perf_counter() - started,
    }


def evaluate_candidate(
    candidate: dict, config: dict, cache: dict, frozen_iso_far: float
) -> dict:
    candidate_id = candidate["id"]
    started = time.perf_counter()
    calibration_end = int(config["boundaries"]["T_cal"])
    scenario_rows = {}
    medians = {}
    try:
        for scenario in ("BLOCK30", "ART10"):
            rows = []
            for seed in config["panels"]["E_C"]:
                entry = cache[(scenario, int(seed))]
                pair = evaluate_pair(candidate, entry, calibration_end)
                anchor_count = int(pair["anchor"].sum())
                if anchor_count < 100:
                    return abstain_row(
                        candidate_id,
                        f"{scenario}_INSUFFICIENT_ANCHOR",
                        started,
                        {"scenarios": scenario_rows},
                    )
                recovery_rho = spearman(
                    pair["q_truth"][pair["anchor"]], pair["q_estimate"][pair["anchor"]]
                )
                if not math.isfinite(recovery_rho):
                    return abstain_row(
                        candidate_id,
                        "ABSTAIN_CONSTANT_TRUTH",
                        started,
                        {"scenario": scenario, "scenarios": scenario_rows},
                    )
                rows.append(
                    {
                        "seed": int(seed),
                        "anchor_count": anchor_count,
                        "nmae": float(
                            np.mean(
                                np.abs(
                                    pair["q_truth"][pair["anchor"]]
                                    - pair["q_estimate"][pair["anchor"]]
                                )
                            )
                        ),
                        "rho": float(recovery_rho),
                        "truth_cG": pair["truth_cG"],
                        "estimate_cG": pair["estimate_cG"],
                    }
                )
            scenario_rows[scenario] = rows
            medians[scenario] = {
                "median_nmae": float(np.median([row["nmae"] for row in rows])),
                "median_rho": float(np.median([row["rho"] for row in rows])),
            }
    except ValueError as exc:
        return abstain_row(
            candidate_id,
            "F2C_NUMERIC_ABSTAIN",
            started,
            {"detail": str(exc), "scenarios": scenario_rows},
        )

    rank_e = max(value["median_nmae"] for value in medians.values())
    rank_r = min(value["median_rho"] for value in medians.values())
    passed = all(
        value["median_rho"] >= 0.80 and value["median_nmae"] <= 0.20
        for value in medians.values()
    )
    return {
        "id": candidate_id,
        "status": "PASS" if passed else "FUTILITY_KILL",
        "reason": None if passed else "F2C_NUMERIC_FUTILITY",
        "metrics": {
            "scenarios": scenario_rows,
            "scenario_medians": medians,
            "rank_E": rank_e,
            "rank_R": rank_r,
            "frozen_iso_far": float(frozen_iso_far),
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
    config, candidates, input_ids, frozen_far, hashes = verify_inputs()
    cache, preflight = build_cache(config)
    print(
        json.dumps(
            {
                "event": "F2C_PREFLIGHT_PASS",
                "candidates": len(candidates),
                "cache_entries": len(cache),
            },
            sort_keys=True,
        ),
        flush=True,
    )

    rows = []
    for index, candidate in enumerate(candidates, start=1):
        row = evaluate_candidate(candidate, config, cache, frozen_far[candidate["id"]])
        rows.append(row)
        summary = {
            "event": "F2C_CANDIDATE_COMPLETE",
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
                }
            )
        print(json.dumps(summary, sort_keys=True), flush=True)

    valid = sorted(
        [row for row in rows if row["status"] == "PASS"],
        key=lambda row: (
            row["metrics"]["rank_E"],
            -row["metrics"]["rank_R"],
            row["metrics"]["frozen_iso_far"],
            row["runtime_seconds"],
            row["id"],
        ),
    )
    promoted_ids = [row["id"] for row in valid[:16]]
    for row in rows:
        if row["id"] in promoted_ids:
            row["status"] = "PROMOTE"
        elif row["status"] == "PASS":
            row["status"] = "DROPPED_BUDGET"
            row["reason"] = "F2C_CAP16"

    receipt = {
        "schema": "BA-SRM9-F2C-v1",
        "stage": "F2-C",
        "candidate_Q_run": True,
        "numerical_F2C": True,
        "behavior_loaded": False,
        "model_fit": False,
        "real_endpoint_opened": False,
        "biological_claim": False,
        "downstream_authorized": False,
        "input_hashes": hashes,
        "authorization_audit_sha256": hashes["authorization_audit"],
        "runner_sha256": sha(Path(__file__)),
        "environment": EXPECTED_ENVIRONMENT,
        "input_promoted_ids": input_ids,
        "input_promoted_ids_sha256": compact_sha(input_ids),
        "preflight": preflight,
        "candidates": rows,
        "promoted_ids": promoted_ids,
        "promoted_ids_sha256": compact_sha(promoted_ids),
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
    }
    write_receipt(receipt)
    print(
        json.dumps(
            {
                "event": "F2C_COMPLETE",
                "promoted": len(promoted_ids),
                "receipt_sha256": sha(OUT),
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
