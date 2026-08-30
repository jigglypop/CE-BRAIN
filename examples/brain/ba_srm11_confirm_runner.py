"""BA-SRM11: robust apparatus through F2-B, F2-D, and synthetic confirmation.

Contract: paper/검증_원장/BA_SRM11_유효차원_합성_확증_계약.md (LOCKED_PRE_RESULT).
No structural change: the BA-SRM10 V2 apparatus and the 14 surviving candidates
are carried verbatim. Only the frozen fresh seed blocks below are new.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
RUNNER10 = REPO / "examples" / "brain" / "ba_srm10_ra_runner.py"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "ba-srm11-confirm-receipt.json"

_spec = importlib.util.spec_from_file_location("ba_srm10_ra_runner", RUNNER10)
R = importlib.util.module_from_spec(_spec)
sys.modules["ba_srm10_ra_runner"] = R
_spec.loader.exec_module(R)

CANDIDATE_IDS_SHA = "b139c56b589b54730b88469bf261f76ae382e17f83d5b93dccb1bd0b43366df2"
S_CAL = list(range(20262501, 20262517))
E_B = list(range(20262201, 20262209))
E_D = list(range(20262301, 20262309))
CONFIRM = list(range(20263001, 20263033))
RECOVERY = ("ROT10", "MISS30", "BLOCK30", "ART10", "REVERSE", "JUMP")
CAL_END = R.CAL_END


CARRIED_IDS = [
    "BIEXP_theta1_1_theta2_8_a_0p5__gamma1__identity",
    "BIEXP_theta1_1_theta2_8_a_0p5__gamma1__radial_huber_c3",
    "POWER_theta2_p1p5__gamma1__identity",
    "POWER_theta2_p1p5__gamma1__radial_huber_c3",
    "POWER_theta2_p1p5__gamma1__radial_tanh_c3",
    "POWER_theta2_p1p5__gamma2__identity",
    "POWER_theta2_p1p5__gamma2__radial_huber_c3",
    "POWER_theta2_p1p5__gamma2__radial_tanh_c3",
    "POWER_theta8_p2__gamma1__identity",
    "POWER_theta8_p2__gamma1__radial_huber_c3",
    "POWER_theta8_p2__gamma1__radial_tanh_c3",
    "POWER_theta8_p2__gamma2__identity",
    "POWER_theta8_p2__gamma2__radial_huber_c3",
    "POWER_theta8_p2__gamma2__radial_tanh_c3",
]


def load_candidates():
    ids = sorted(CARRIED_IDS)
    digest = hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()
    if len(ids) != 14 or digest != CANDIDATE_IDS_SHA:
        raise RuntimeError(f"carry invariant failed: {len(ids)} {digest}")
    man, man_sha = R.manifest()
    rows = [c for c in man["candidates"] if c["id"] in set(ids)]
    if len(rows) != 14:
        raise RuntimeError("manifest/carry mismatch")
    return rows, man_sha


def build_entries():
    plan = {
        "ISO_NULL": S_CAL + E_D + CONFIRM,
        "ROT10": E_B + CONFIRM,
        "MISS30": E_B + CONFIRM,
        "REVERSE": E_D + CONFIRM,
        "ART10": CONFIRM,
        "BLOCK30": CONFIRM,
        "JUMP": CONFIRM,
        "ZERO_NULL": E_D,
    }
    entries = {}
    zero_abstain = 0
    for scenario, seeds in plan.items():
        for seed in seeds:
            raw = R.generate(scenario, seed)
            try:
                cz, nz, d, pc = R.robust_pair(
                    raw["clean"], raw["noisy"], raw["mask"], R.PREFIX_END, R.CLIP
                )
                entry = {"raw": raw, "prepared": {
                    "status": "VALID", "clean_z": cz, "noisy_z": nz, "d": d, "prefix_counts": pc}}
            except ValueError as exc:
                entry = {"raw": raw, "prepared": {
                    "status": "ABSTAIN_PREFIX_SCALE", "reason": str(exc)}}
            if scenario == "ZERO_NULL":
                zero_abstain += entry["prepared"]["status"] == "ABSTAIN_PREFIX_SCALE"
            elif entry["prepared"]["status"] != "VALID":
                raise RuntimeError(f"DGP_STOP {scenario} {seed}: {entry['prepared'].get('reason')}")
            entries[(scenario, seed)] = entry
    if zero_abstain != len(E_D):
        raise RuntimeError(f"ZERO_NOT_EXPECTED_ABSTAIN: {zero_abstain}/{len(E_D)}")
    return entries


def pair_stats(candidate, entries, scenario, seed, want_far_theta=None, want_detect=False):
    entry = entries[(scenario, seed)]
    pair = R.evaluate_pair(candidate, entry, CAL_END)
    anchor = pair["anchor"]
    if int(anchor.sum()) < 100:
        raise ValueError(f"{scenario}_INSUFFICIENT_ANCHOR")
    rho = R.spearman(pair["q_truth"][anchor], pair["q_estimate"][anchor])
    if not math.isfinite(rho):
        raise ValueError("ABSTAIN_CONSTANT_TRUTH")
    row = {
        "seed": seed,
        "rho": float(rho),
        "nmae": float(np.mean(np.abs(pair["q_truth"][anchor] - pair["q_estimate"][anchor]))),
    }
    if want_far_theta is not None or want_detect:
        if int(pair["derivative_anchor"].sum()) < 100:
            raise ValueError(f"{scenario}_INSUFFICIENT_DERIVATIVE")
        mag, idx = R.derivative_magnitude(pair, entry["raw"]["clock"])
        if want_far_theta is not None:
            row["far"] = float(np.mean(mag > want_far_theta))
        if want_detect:
            peak = int(np.argmax(mag))
            row["detected"] = bool(
                288 <= int(idx[peak]) <= 480 and float(mag[peak]) > want_far_theta
            )
    return row


def calibrate_theta(candidate, entries):
    pooled = []
    for seed in S_CAL:
        entry = entries[("ISO_NULL", seed)]
        pair = R.evaluate_pair(candidate, entry, CAL_END)
        if int(pair["anchor"].sum()) < 100 or int(pair["derivative_anchor"].sum()) < 100:
            raise ValueError("ISO_CALIBRATION_INSUFFICIENT")
        mag, _ = R.derivative_magnitude(pair, entry["raw"]["clock"])
        if not np.isfinite(mag).all():
            raise ValueError("ISO_CAL_NONFINITE")
        pooled.extend(float(v) for v in mag)
    return float(np.quantile(pooled, 0.95, method="linear"))


def evaluate_candidate(candidate, entries):
    started = time.perf_counter()
    out = {"id": candidate["id"]}
    try:
        theta = calibrate_theta(candidate, entries)
        out["theta"] = theta

        f2b = {}
        for scenario in ("ROT10", "MISS30"):
            rows = [pair_stats(candidate, entries, scenario, s) for s in E_B]
            f2b[scenario] = {
                "median_rho": float(np.median([r["rho"] for r in rows])),
                "median_nmae": float(np.median([r["nmae"] for r in rows])),
                "rows": rows,
            }
        out["f2b"] = f2b
        if not all(v["median_rho"] >= 0.80 and v["median_nmae"] <= 0.20 for v in f2b.values()):
            return {**out, "status": "FUTILITY_KILL", "stage": "F2-B",
                    "runtime_seconds": time.perf_counter() - started}

        rev_rows = [pair_stats(candidate, entries, "REVERSE", s) for s in E_D]
        iso_rows = [pair_stats(candidate, entries, "ISO_NULL", s, want_far_theta=theta) for s in E_D]
        f2d = {
            "reverse_median_rho": float(np.median([r["rho"] for r in rev_rows])),
            "reverse_median_nmae": float(np.median([r["nmae"] for r in rev_rows])),
            "iso_mean_far": float(np.mean([r["far"] for r in iso_rows])),
            "reverse_rows": rev_rows,
            "iso_rows": iso_rows,
        }
        out["f2d"] = f2d
        if not (f2d["reverse_median_rho"] >= 0.80 and f2d["reverse_median_nmae"] <= 0.20
                and f2d["iso_mean_far"] <= 0.20):
            return {**out, "status": "FUTILITY_KILL", "stage": "F2-D",
                    "runtime_seconds": time.perf_counter() - started}

        confirm = {"scenarios": {}}
        gates_ok = True
        for scenario in RECOVERY:
            rows = [
                pair_stats(candidate, entries, scenario, s,
                           want_far_theta=theta if scenario == "JUMP" else None,
                           want_detect=scenario == "JUMP")
                for s in CONFIRM
            ]
            rhos = [r["rho"] for r in rows]
            stats = {
                "median_rho": float(np.median(rhos)),
                "q05_rho": float(np.quantile(rhos, 0.05, method="linear")),
                "median_nmae": float(np.median([r["nmae"] for r in rows])),
            }
            if scenario == "JUMP":
                stats["detections"] = int(sum(r["detected"] for r in rows))
            confirm["scenarios"][scenario] = {**stats, "rows": rows}
            ok = (stats["median_rho"] >= 0.90 and stats["q05_rho"] >= 0.75
                  and stats["median_nmae"] <= 0.15)
            if scenario == "JUMP":
                ok = ok and stats["detections"] == len(CONFIRM)
            gates_ok = gates_ok and ok
        iso_c = [pair_stats(candidate, entries, "ISO_NULL", s, want_far_theta=theta)
                 for s in CONFIRM]
        confirm["iso"] = {
            "median_nmae": float(np.median([r["nmae"] for r in iso_c])),
            "mean_far": float(np.mean([r["far"] for r in iso_c])),
            "max_far": float(np.max([r["far"] for r in iso_c])),
            "rows": iso_c,
        }
        gates_ok = gates_ok and (confirm["iso"]["median_nmae"] <= 0.15
                                 and confirm["iso"]["mean_far"] <= 0.10
                                 and confirm["iso"]["max_far"] <= 0.20)
        out["confirm"] = confirm
        status = "SYNTHETIC_CONFIRMED_L0" if gates_ok else "FUTILITY_KILL"
        stage = "confirm" if not gates_ok else None
        return {**out, "status": status, "stage": stage,
                "runtime_seconds": time.perf_counter() - started}
    except ValueError as exc:
        return {**out, "status": "ABSTAIN", "reason": str(exc),
                "runtime_seconds": time.perf_counter() - started}


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    candidates, man_sha = load_candidates()
    entries = build_entries()
    print(json.dumps({"event": "ENTRIES_READY", "count": len(entries)}), flush=True)
    rows = []
    for i, candidate in enumerate(candidates, 1):
        row = evaluate_candidate(candidate, entries)
        rows.append(row)
        print(json.dumps({
            "event": "CANDIDATE", "index": i, "id": row["id"],
            "status": row["status"], "stage": row.get("stage"),
        }), flush=True)
    receipt = {
        "schema": "BA-SRM11-CONFIRM-v1",
        "contract": "paper/검증_원장/BA_SRM11_유효차원_합성_확증_계약.md",
        "manifest_sha256": man_sha,
        "carried_ids_sha256": CANDIDATE_IDS_SHA,
        "seeds": {"calibration": S_CAL, "f2b": E_B, "f2d": E_D, "confirm": CONFIRM},
        "behavior_loaded": False,
        "real_endpoint_opened": False,
        "biological_claim": False,
        "candidates": rows,
        "counts": {s: sum(r["status"] == s for r in rows)
                   for s in ("SYNTHETIC_CONFIRMED_L0", "FUTILITY_KILL", "ABSTAIN")},
    }
    OUT.write_text(json.dumps(receipt, allow_nan=False, sort_keys=True, indent=1),
                   encoding="utf-8")
    print(json.dumps({"event": "COMPLETE", "counts": receipt["counts"],
                      "receipt": str(OUT)}), flush=True)


if __name__ == "__main__":
    main()
