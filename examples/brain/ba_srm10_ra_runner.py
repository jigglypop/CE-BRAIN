"""BA-SRM10 R-A bounded-influence standardization restart.

Contract: paper/검증_원장/BA_SRM10_유효차원_강건성_계약.md (LOCKED_PRE_RESULT).
Reads BA-SRM8/BA-SRM9 frozen artifacts strictly read-only; writes its receipt
only into the session scratchpad. Fresh seed blocks per contract:
calibration 20262001..20262016, evaluation panel 20262101..20262108.

Variants:
  V0_BASELINE   frozen SRM9 moment standardization (negative control)
  V1_ROBUST     median/1.4826*MAD standardization, no clip (decomposition)
  V2_ROBUST_C4  median/1.4826*MAD standardization + clip +-4 (selected R-A)

Frozen gates (SRM9 text): per scenario median rho>=0.80 and NMAE<=0.20 for
ART10/BLOCK30/JUMP; mean ISO FAR<=0.20; JUMP detections>=4/8; ZERO_NULL must
abstain in preprocessing.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SRM9 = REPO / "_workspace/ce/brain-physical-time-effective-dimension-funnel-v2-20260823/artifacts"
SRM8 = REPO / "_workspace/ce/brain-physical-time-effective-dimension-funnel-20260823/artifacts"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "ba-srm10-ra-receipt.json"

sys.path.insert(0, str(SRM8))
sys.path.insert(0, str(SRM9))
from funnel_core_v2 import causal_q, manifest, sha, spearman  # noqa: E402

# SRM9's f2_common prepends the SRM8 path at import time without popping it,
# so load SRM9's run_f2a by explicit path to avoid resolving SRM8's copy.
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("srm9_run_f2a", SRM9 / "run_f2a.py")
_f2a = importlib.util.module_from_spec(_spec)
sys.modules["srm9_run_f2a"] = _f2a
_spec.loader.exec_module(_f2a)
evaluate_pair = _f2a.evaluate_pair
preprocess_pair = _f2a.preprocess_pair
derivative_magnitude = _f2a.derivative_magnitude
generate = sys.modules["f2_common"].generate

S_CAL = list(range(20262001, 20262017))
E10 = list(range(20262101, 20262109))
PREFIX_END = 460
CAL_END = 537
CLIP = 4.0
MAD_CONSISTENCY = 1.4826


def robust_pair(clean, noisy, mask, prefix_end, clip):
    """Mirror of run_f2a.preprocess_pair with median/MAD and optional clip."""
    if clean.shape != noisy.shape or clean.shape != mask.shape:
        raise ValueError("PREFIX_SHAPE")
    if not (np.isfinite(clean).all() and np.isfinite(noisy).all()):
        raise ValueError("PREFIX_NONFINITE_RAW")
    count = clean.shape[0]
    clean_z = np.zeros_like(clean, dtype=np.float64)
    noisy_z = np.zeros_like(noisy, dtype=np.float64)
    d = np.empty(count, dtype=np.float64)
    prefix_counts = np.empty(count, dtype=np.int64)
    for ch in range(count):
        observed = mask[ch, :prefix_end] == 1
        prefix_counts[ch] = int(observed.sum())
        if prefix_counts[ch] < 2:
            raise ValueError(f"PREFIX_COUNT_CHANNEL_{ch}")
        for src, dst in ((clean, clean_z), (noisy, noisy_z)):
            prefix = src[ch, :prefix_end][observed]
            center = float(np.median(prefix))
            scale = MAD_CONSISTENCY * float(np.median(np.abs(prefix - center)))
            if not math.isfinite(scale) or scale <= 1e-12:
                raise ValueError(f"PREFIX_ROBUST_SCALE_CHANNEL_{ch}")
            z = (src[ch] - center) / scale
            dst[ch] = np.clip(z, -clip, clip) if clip is not None else z
        d[ch] = math.sqrt(float(np.mean(mask[ch, :prefix_end])))
    clean_z[mask == 0] = 0.0
    noisy_z[mask == 0] = 0.0
    if not (np.isfinite(clean_z).all() and np.isfinite(noisy_z).all() and np.isfinite(d).all()):
        raise ValueError("PREFIX_NONFINITE_TRANSFORM")
    return clean_z, noisy_z, d, prefix_counts


def preflight_focused():
    """FAST focused checks fixed before evaluation (contract section 5)."""
    rng = np.random.default_rng(1)
    x = rng.standard_normal((1, 2000))
    m = np.ones_like(x, dtype=np.uint8)
    cz, nz, _, _ = robust_pair(x, x, m, 2000, CLIP)
    mz = (x - x.mean()) / x.std()
    agree = float(np.median(np.abs(cz - mz)))
    clip_frac = float(np.mean(np.abs(cz) >= CLIP - 1e-12))
    # Contamination influence bound: one +10-sigma spike must not move the
    # robust scale by more than 5 percent.
    y = x.copy()
    y[0, :20] = 10.0
    cy, _, _, _ = robust_pair(y, y, m, 2000, None)
    scale_shift = abs(float(np.median(np.abs(cy[0, 20:] / cz[0, 20:]))) - 1.0)
    checks = {
        "clean_agreement_median_absdiff": agree,
        "clean_clip_fraction": clip_frac,
        "contaminated_scale_shift": scale_shift,
        "pass": bool(agree < 0.05 and clip_frac < 1e-3 and scale_shift < 0.05),
    }
    if not checks["pass"]:
        raise RuntimeError(f"FOCUSED_PREFLIGHT_FAIL: {checks}")
    return checks


def load_candidates():
    f2b = json.loads((SRM9 / "f2b-receipt.json").read_text(encoding="utf-8"))
    ids = f2b["promoted_ids"]
    if len(ids) != 20 or len(set(ids)) != 20:
        raise RuntimeError("carry invariant failed")
    man, man_sha = manifest()
    rows = [c for c in man["candidates"] if c["id"] in set(ids)]
    if len(rows) != 20:
        raise RuntimeError("manifest/carry mismatch")
    return rows, man_sha


def build_raw_cache():
    cache = {}
    for scenario, seeds in (
        ("ISO_NULL", S_CAL + E10),
        ("JUMP", E10),
        ("ART10", E10),
        ("BLOCK30", E10),
        ("ZERO_NULL", E10),
    ):
        for seed in seeds:
            cache[(scenario, seed)] = generate(scenario, seed)
    return cache


def prepare_variant(raw_cache, variant):
    prepared = {}
    zero_abstain = 0
    for (scenario, seed), raw in raw_cache.items():
        try:
            if variant == "V0_BASELINE":
                cz, nz, d, pc = preprocess_pair(raw["clean"], raw["noisy"], raw["mask"], PREFIX_END)
            elif variant == "V1_ROBUST":
                cz, nz, d, pc = robust_pair(raw["clean"], raw["noisy"], raw["mask"], PREFIX_END, None)
            else:
                cz, nz, d, pc = robust_pair(raw["clean"], raw["noisy"], raw["mask"], PREFIX_END, CLIP)
            entry = {"raw": raw, "prepared": {
                "status": "VALID", "clean_z": cz, "noisy_z": nz, "d": d, "prefix_counts": pc}}
        except ValueError as exc:
            entry = {"raw": raw, "prepared": {"status": "ABSTAIN_PREFIX_SCALE", "reason": str(exc)}}
        if scenario == "ZERO_NULL":
            zero_abstain += entry["prepared"]["status"] == "ABSTAIN_PREFIX_SCALE"
        elif entry["prepared"]["status"] != "VALID":
            raise RuntimeError(f"DGP_STOP {variant} {scenario} {seed}: {entry['prepared'].get('reason')}")
        prepared[(scenario, seed)] = entry
    if zero_abstain != len(E10):
        raise RuntimeError(f"ZERO_NOT_EXPECTED_ABSTAIN {variant}: {zero_abstain}/{len(E10)}")
    return prepared


def scenario_block(candidate, entries, seeds, scenario):
    rows = []
    for seed in seeds:
        pair = evaluate_pair(candidate, entries[(scenario, seed)], CAL_END)
        anchor = pair["anchor"]
        if int(anchor.sum()) < 100:
            return None, f"{scenario}_INSUFFICIENT_ANCHOR"
        rho = spearman(pair["q_truth"][anchor], pair["q_estimate"][anchor])
        if not math.isfinite(rho):
            return None, "ABSTAIN_CONSTANT_TRUTH"
        rows.append({
            "seed": seed,
            "rho": float(rho),
            "nmae": float(np.mean(np.abs(pair["q_truth"][anchor] - pair["q_estimate"][anchor]))),
            "pair": pair,
        })
    return rows, None


def evaluate_candidate(candidate, entries):
    started = time.perf_counter()
    result = {"id": candidate["id"]}
    try:
        pooled = []
        for seed in S_CAL:
            pair = evaluate_pair(candidate, entries[("ISO_NULL", seed)], CAL_END)
            if int(pair["anchor"].sum()) < 100 or int(pair["derivative_anchor"].sum()) < 100:
                return {**result, "status": "ABSTAIN", "reason": "ISO_CALIBRATION_INSUFFICIENT"}
            mag, _ = derivative_magnitude(pair, entries[("ISO_NULL", seed)]["raw"]["clock"])
            if not np.isfinite(mag).all():
                return {**result, "status": "ABSTAIN", "reason": "ISO_CAL_NONFINITE"}
            pooled.extend(float(v) for v in mag)
        theta = float(np.quantile(pooled, 0.95, method="linear"))

        iso_rows, err = scenario_block(candidate, entries, E10, "ISO_NULL")
        if err:
            return {**result, "status": "ABSTAIN", "reason": err}
        for row, seed in zip(iso_rows, E10):
            mag, _ = derivative_magnitude(row.pop("pair"), entries[("ISO_NULL", seed)]["raw"]["clock"])
            row["far"] = float(np.mean(mag > theta))

        jump_rows, err = scenario_block(candidate, entries, E10, "JUMP")
        if err:
            return {**result, "status": "ABSTAIN", "reason": err}
        for row, seed in zip(jump_rows, E10):
            pair = row.pop("pair")
            mag, idx = derivative_magnitude(pair, entries[("JUMP", seed)]["raw"]["clock"])
            peak = int(np.argmax(mag))
            row["detected"] = bool(288 <= int(idx[peak]) <= 480 and float(mag[peak]) > theta)

        blocks = {}
        for scenario in ("ART10", "BLOCK30"):
            rows, err = scenario_block(candidate, entries, E10, scenario)
            if err:
                return {**result, "status": "ABSTAIN", "reason": err}
            for row in rows:
                row.pop("pair")
            blocks[scenario] = rows
    except ValueError as exc:
        return {**result, "status": "ABSTAIN", "reason": f"NUMERIC:{exc}"}

    metrics = {
        "theta": theta,
        "median_art10_rho": float(np.median([r["rho"] for r in blocks["ART10"]])),
        "median_art10_nmae": float(np.median([r["nmae"] for r in blocks["ART10"]])),
        "median_block30_rho": float(np.median([r["rho"] for r in blocks["BLOCK30"]])),
        "median_block30_nmae": float(np.median([r["nmae"] for r in blocks["BLOCK30"]])),
        "median_jump_rho": float(np.median([r["rho"] for r in jump_rows])),
        "median_jump_nmae": float(np.median([r["nmae"] for r in jump_rows])),
        "mean_iso_far": float(np.mean([r["far"] for r in iso_rows])),
        "jump_detections": int(sum(r["detected"] for r in jump_rows)),
        "rows": {"ART10": blocks["ART10"], "BLOCK30": blocks["BLOCK30"],
                 "JUMP": jump_rows, "ISO": iso_rows},
    }
    gates = {
        "art10": metrics["median_art10_rho"] >= 0.80 and metrics["median_art10_nmae"] <= 0.20,
        "block30": metrics["median_block30_rho"] >= 0.80 and metrics["median_block30_nmae"] <= 0.20,
        "jump": metrics["median_jump_rho"] >= 0.80 and metrics["median_jump_nmae"] <= 0.20
                and metrics["jump_detections"] >= 4,
        "iso_far": metrics["mean_iso_far"] <= 0.20,
    }
    status = "PASS" if all(gates.values()) else "FUTILITY_KILL"
    return {**result, "status": status, "gates": gates, "metrics": metrics,
            "runtime_seconds": time.perf_counter() - started}


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    focused = preflight_focused()
    print(json.dumps({"event": "FOCUSED_PREFLIGHT", **focused}), flush=True)
    candidates, man_sha = load_candidates()
    raw_cache = build_raw_cache()
    print(json.dumps({"event": "RAW_CACHE", "entries": len(raw_cache)}), flush=True)

    receipt = {
        "schema": "BA-SRM10-RA-v1",
        "contract": "paper/검증_원장/BA_SRM10_유효차원_강건성_계약.md",
        "manifest_sha256": man_sha,
        "input_hashes": {
            "srm9_f2b_receipt": sha(SRM9 / "f2b-receipt.json"),
            "srm9_f2_common": sha(SRM9 / "f2_common.py"),
            "srm9_run_f2a": sha(SRM9 / "run_f2a.py"),
            "srm8_core": sha(SRM8 / "funnel_core_v2.py"),
        },
        "seeds": {"calibration": S_CAL, "panel": E10},
        "clip": CLIP,
        "focused_preflight": focused,
        "behavior_loaded": False,
        "real_endpoint_opened": False,
        "biological_claim": False,
        "variants": {},
    }
    for variant in ("V0_BASELINE", "V1_ROBUST", "V2_ROBUST_C4"):
        entries = prepare_variant(raw_cache, variant)
        rows = []
        for i, candidate in enumerate(candidates, 1):
            row = evaluate_candidate(candidate, entries)
            rows.append(row)
            print(json.dumps({
                "event": "CANDIDATE", "variant": variant, "index": i,
                "id": row["id"], "status": row["status"],
                "art10_rho": row.get("metrics", {}).get("median_art10_rho"),
            }), flush=True)
        summary = {
            "counts": {s: sum(r["status"] == s for r in rows)
                       for s in ("PASS", "FUTILITY_KILL", "ABSTAIN")},
            "art10_rho_range": [
                float(min(r["metrics"]["median_art10_rho"] for r in rows if "metrics" in r)),
                float(max(r["metrics"]["median_art10_rho"] for r in rows if "metrics" in r)),
            ] if any("metrics" in r for r in rows) else None,
        }
        receipt["variants"][variant] = {"summary": summary, "candidates": rows}
        print(json.dumps({"event": "VARIANT_COMPLETE", "variant": variant, **summary}), flush=True)

    OUT.write_text(json.dumps(receipt, allow_nan=False, sort_keys=True, indent=1),
                   encoding="utf-8")
    print(json.dumps({"event": "COMPLETE", "receipt": str(OUT)}), flush=True)


if __name__ == "__main__":
    main()
