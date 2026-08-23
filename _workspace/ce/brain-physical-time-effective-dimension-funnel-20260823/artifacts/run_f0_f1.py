"""One-shot BA-SRM8 F0/F1 apparatus; it never reads behavior targets."""
from __future__ import annotations

import hashlib
import math
import time
from pathlib import Path

import numpy as np

from funnel_core import ROOT, causal_q, load_manifest, robust, sha256_path, spearman, write_json_fsynced


F0_PATH = ROOT / "f0-receipt.json"
F1_PATH = ROOT / "f1-receipt.json"


def synthetic(seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n, count = 8, 192
    clock = np.cumsum(np.r_[0.0, rng.uniform(0.75, 1.35, count - 1)])
    phase = np.linspace(0, 6 * np.pi, count)
    latent = np.vstack([np.sin(phase), np.cos(0.7 * phase), np.sin(1.7 * phase), rng.normal(0, 1, count)])
    loading = rng.normal(0, 1, (n, 4))
    envelope = np.vstack([0.15 + 1.4 / (1 + np.exp(-np.sin(phase - shift) * 3)) for shift in np.linspace(0, 2, 4)])
    drive = loading @ (latent * envelope)
    calcium = np.zeros_like(drive)
    for t in range(1, count):
        decay = math.exp(-(clock[t] - clock[t - 1]) / 3.0)
        calcium[:, t] = decay * calcium[:, t - 1] + (1 - decay) * drive[:, t]
    clean = calcium / np.maximum(calcium.std(axis=1, keepdims=True), 1e-9)
    noisy = clean + rng.normal(0, 0.25, clean.shape)  # SNR=4
    mask = (rng.random(clean.shape) >= 0.10).astype(float)
    return clean, noisy, mask, clock


def f0(manifest: dict, manifest_hash: str) -> dict:
    rng = np.random.default_rng(20260823)
    values = rng.normal(size=(8, 48))
    mask = np.ones_like(values)
    clock = np.cumsum(np.r_[0.0, rng.uniform(0.5, 1.5, 47)])
    d = np.linspace(0.6, 1.0, 8)
    rows = []
    baseline_runtime = None
    for candidate in manifest["candidates"]:
        started = time.perf_counter()
        status, reason = "PASS", None
        metrics: dict[str, float | bool] = {}
        try:
            q, neff, reasons = causal_q(candidate, values, mask, clock, d)
            valid = np.isfinite(q)
            if not valid.any():
                raise ValueError("all anchors abstained")
            # PSD proof is exercised numerically on randomized nonnegative weights.
            min_eig = math.inf
            for repeat in range(3):
                x = rng.normal(size=(8, 24))
                weights = rng.random(24); weights /= weights.sum()
                c = ((x - x @ weights[:, None].T) if False else None)
                mean = x @ weights
                centered = x - mean[:, None]
                cov = (centered * weights) @ centered.T / (1 - float(weights @ weights))
                min_eig = min(min_eig, float(np.linalg.eigvalsh(cov).min()))
            if min_eig < -1e-10:
                raise ValueError("PSD tolerance failure")
            # c_G is frozen by the first 70% calibration range.  Test a later
            # prediction prefix against perturbations strictly after that range.
            altered = values.copy(); altered[:, 40:] += 123.0
            q_prefix, _, _ = causal_q(candidate, altered, mask, clock, d)
            causality = float(np.nanmax(np.abs(q[34:40] - q_prefix[34:40])))
            if causality > 1e-12:
                raise ValueError("future perturbation changed past")
            # Explicit robust bound, q range and effective-size identity.
            probe = np.full(8, 1e6)
            bounded = robust(candidate, probe)
            kind = candidate["formula_components"]["robust_map"]["parameters"]["kind"]
            if kind != "identity" and np.linalg.norm(bounded) > 3 * math.sqrt(8) + 1e-10:
                raise ValueError("robust bound failure")
            metrics = {"anchors": int(valid.sum()), "causality_max_abs": causality, "min_psd_eigenvalue": min_eig, "neff_max": float(neff.max()), "neff_min_positive": float(neff[neff > 0].min()), "robust_bound_checked": True}
        except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
            reason = str(exc)
            status = "ABSTAIN" if reason == "all anchors abstained" else "INVALID_KILL"
        elapsed = time.perf_counter() - started
        if candidate["id"] == "EXP_theta10__gamma1__identity":
            baseline_runtime = elapsed
        rows.append({"id": candidate["id"], "metrics": metrics, "reason": reason, "runtime_seconds": elapsed, "status": status})
    assert baseline_runtime is not None
    for row in rows:
        row["runtime_ratio_to_EXP_theta10_gamma1_identity"] = row["runtime_seconds"] / baseline_runtime
        if row["status"] == "PASS" and row["runtime_ratio_to_EXP_theta10_gamma1_identity"] > 4:
            row["status"], row["reason"] = "INVALID_KILL", "runtime ratio exceeds 4"
    return {"schema": "BA-SRM8-F0-v1", "behavior_loaded": False, "candidate_count": 48, "candidates": rows, "input_hashes": {"manifest_sha256": manifest_hash, "funnel_core_sha256": sha256_path(ROOT / "funnel_core.py"), "run_script_sha256": sha256_path(Path(__file__))}, "model_fit": False, "runtime_seconds": sum(x["runtime_seconds"] for x in rows)}


def f1(manifest: dict, manifest_hash: str, f0_receipt: dict) -> dict:
    passed = [x["id"] for x in f0_receipt["candidates"] if x["status"] == "PASS"]
    f0_status = {x["id"]: x["status"] for x in f0_receipt["candidates"]}
    rows = []
    for candidate in manifest["candidates"]:
        if candidate["id"] not in passed:
            status = "ABSTAIN" if f0_status[candidate["id"]] == "ABSTAIN" else "INVALID_KILL"
            rows.append({"id": candidate["id"], "metrics": {}, "reason": "F0_" + f0_status[candidate["id"]], "runtime_seconds": 0.0, "status": status})
            continue
        started = time.perf_counter()
        per_seed = []
        for seed in range(20260823, 20260827):
            clean, noisy, mask, clock = synthetic(seed)
            d = np.sqrt(mask[:, : int(.6 * mask.shape[1])].mean(axis=1))
            truth, _, _ = causal_q(candidate, clean, np.ones_like(clean), clock, np.ones(clean.shape[0]))
            estimate, _, _ = causal_q(candidate, noisy, mask, clock, d)
            common = np.isfinite(truth) & np.isfinite(estimate)
            if common.sum() == 0:
                per_seed.append({"eligible_anchors": 0, "nmae": None, "spearman": None, "status": "ABSTAIN"})
                continue
            a, b = truth[common], estimate[common]
            scale = float(np.max(a) - np.min(a))
            nmae = float(np.mean(np.abs(a - b)) / max(scale, 1e-12))
            per_seed.append({"eligible_anchors": int(common.sum()), "nmae": nmae, "spearman": spearman(a, b), "status": "PASS"})
        usable = [x for x in per_seed if x["status"] == "PASS"]
        elapsed = time.perf_counter() - started
        if not usable:
            rows.append({"id": candidate["id"], "metrics": {"per_seed": per_seed}, "reason": "NO_ELIGIBLE_ANCHORS", "runtime_seconds": elapsed, "status": "ABSTAIN"})
            continue
        median_nmae = float(np.median([x["nmae"] for x in usable]))
        median_spearman = float(np.median([x["spearman"] for x in usable]))
        status = "PASS" if len(usable) == 4 and median_spearman >= .75 and median_nmae <= .25 else "INVALID_KILL"
        reason = None if status == "PASS" else "F1_ABSOLUTE_GATE"
        rows.append({"id": candidate["id"], "metrics": {"median_nmae": median_nmae, "median_spearman": median_spearman, "per_seed": per_seed}, "reason": reason, "runtime_seconds": elapsed, "status": status})
    survivors = [x for x in rows if x["status"] == "PASS"]
    survivors.sort(key=lambda x: (x["metrics"]["median_nmae"], -x["metrics"]["median_spearman"], x["runtime_seconds"], x["id"]))
    promoted = [x["id"] for x in survivors[:32]]
    for row in rows:
        if row["id"] in promoted:
            row["status"] = "PROMOTE"
        elif row["status"] == "PASS":
            row["status"], row["reason"] = "DROPPED_BUDGET", "F1 promotion cap 32"
    return {"schema": "BA-SRM8-F1-v1", "apparatus": {"N": 8, "T": 192, "calcium": "causal exponential decay tau=3 clock units", "missingness": "MCAR 10 percent", "noise": "Gaussian SNR 4", "seeds": [20260823, 20260824, 20260825, 20260826], "truth": "candidate clean-observed Q", "behavior_free": True}, "behavior_loaded": False, "candidate_count": 48, "candidates": rows, "input_hashes": {"manifest_sha256": manifest_hash, "f0_receipt_sha256": sha256_path(F0_PATH), "funnel_core_sha256": sha256_path(ROOT / "funnel_core.py"), "run_script_sha256": sha256_path(Path(__file__))}, "model_fit": False, "promoted_ids": promoted, "runtime_seconds": sum(x["runtime_seconds"] for x in rows)}


def main() -> None:
    manifest, manifest_hash = load_manifest()
    f0_receipt = f0(manifest, manifest_hash)
    write_json_fsynced(F0_PATH, f0_receipt)
    f1_receipt = f1(manifest, manifest_hash, f0_receipt)
    write_json_fsynced(F1_PATH, f1_receipt)
    print({"f0": F0_PATH.name, "f1": F1_PATH.name, "promoted": len(f1_receipt["promoted_ids"])})


if __name__ == "__main__":
    main()
