"""BA-SRM15 stage driver: `ab` fits and selects (train+validation behavior only);
`c` performs the single unconditional held-out opening using the frozen stage-b
models. Receipts are one-shot."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("srm15s", HERE / "ba_srm15_stages.py")
S = importlib.util.module_from_spec(_spec)
sys.modules["srm15s"] = S
_spec.loader.exec_module(S)
E, A7, M13 = S.E, S.A7, S.M13

GCAMP_TRAIN = [r for r, x in A7.G.items() if x == "train"]
GCAMP_VAL = [r for r, x in A7.G.items() if x == "validation"]
GCAMP_HELD = [r for r, x in A7.G.items() if x == "held_out"]
GFP_TRAIN = [r for r, x in A7.P.items() if x == "train"]
GFP_VAL = [r for r, x in A7.P.items() if x == "validation"]
GFP_HELD = [r for r, x in A7.P.items() if x == "held_out"]


def model_to_json(m):
    return {k: (v.tolist() if isinstance(v, np.ndarray) else float(v)) for k, v in m.items()}


def model_from_json(m):
    return {k: (np.asarray(v) if isinstance(v, list) else float(v)) for k, v in m.items()}


def cut_of():
    ext = E.REPO / "data/external/ba_srm6/extracted"
    cuts = {}
    for rn, (cls, lg) in A7.ROOTS.items():
        for rid, cut in A7.logrows(ext / rn / lg):
            cuts[rid] = (cut, cls)
    return cuts


def build_all(cand, rids, read_behavior):
    cuts = cut_of()
    out = {}
    for rid in rids:
        cut, cls = cuts[rid]
        role = (A7.G if cls == "gcamp" else A7.P)[rid]
        t0 = time.perf_counter()
        out[rid] = S.build_recording(cand, rid, cut, cls, role, read_behavior)
        print(json.dumps({"event": "BUILD", "id": rid, "abstain": out[rid].get("abstain"),
                          "sec": round(time.perf_counter() - t0, 1)}), flush=True)
    return out


def pooled(recs, rids, split, family, d=None, adverse_kind=None, shift=False):
    xs, ys = [], []
    for rid in rids:
        _, X, y = S.assemble_rows(recs[rid], split, family, d=d,
                                  adverse_kind=adverse_kind, shift=shift)
        if len(y):
            xs.append(X)
            ys.append(y)
    if not xs:
        return np.zeros((0, 4)), np.zeros(0)
    return np.vstack(xs), np.concatenate(ys)


def family_variants(recs, gcamp_ids):
    domains = set(E.FIXED_D_MENU)
    for rid in gcamp_ids:
        domains &= set(recs[rid]["domains"])
    fams = {"AR": [("AR", None, None, False)],
            "CE_SOFT": [("CE_SOFT", None, None, False)],
            "FIXED_4": [("FIXED_4", None, None, False)],
            "PARTICIPATION_RATIO": [("PARTICIPATION_RATIO", None, None, False)],
            "RAW_SPECTRAL": [("RAW_SPECTRAL", None, None, False)],
            "CAUSAL_UNWEIGHTED": [("CAUSAL_UNWEIGHTED", None, None, False)],
            "MASK_ONLY": [("MASK_ONLY", None, None, False)],
            "RED_CHANNEL": [("RED_CHANNEL", None, None, False)],
            "FIXED_D": [("FIXED_D", d, None, False) for d in sorted(domains)],
            "PHASE_RANDOMIZED": [("CE_SOFT", None, "PHASE_RANDOMIZED", False)],
            "TIME_REVERSED": [("CE_SOFT", None, "TIME_REVERSED", False)],
            "CIRCULAR_BEHAVIOR_SHIFT": [("CE_SOFT", None, None, True)]}
    return fams, sorted(domains)


def fit_and_select(recs, train_ids, val_ids, receipt_rows, panel):
    fams, domains = family_variants(recs, train_ids + val_ids) if panel == "gcamp" \
        else (family_variants(recs, train_ids + val_ids)[0], None)
    selections = {}
    for name, variants in fams.items():
        best = None
        for (family, d, adv, shift) in variants:
            Xtr, ytr = pooled(recs, train_ids, "train", family, d, adv, shift)
            if len(ytr) < 100:
                continue
            for lam in S.RIDGES:
                model = S.fit_ridge(Xtr, ytr, lam)
                scores = []
                for rid in val_ids:
                    _, Xv, yv = S.assemble_rows(recs[rid], "validation", family, d, adv, shift)
                    if len(yv) < 2:
                        scores.append(float("nan"))
                    else:
                        scores.append(S.r2(yv, S.predict(model, Xv)))
                mean_r2 = float(np.mean(scores)) if all(map(math.isfinite, scores)) else float("-inf")
                key = (mean_r2, lam) if name != "FIXED_D" else (mean_r2, -(d or 0), lam)
                if best is None or key > best["key"]:
                    best = {"key": key, "family": family, "d": d, "adverse": adv,
                            "shift": shift, "ridge": lam, "mean_val_r2": mean_r2,
                            "val_scores": scores, "model": model,
                            "train_rows": int(len(ytr))}
        if best is None:
            selections[name] = {"status": "ABSTAIN_NO_ROWS"}
            continue
        best.pop("key")
        best["model"] = model_to_json(best["model"])
        selections[name] = best
        receipt_rows.append({"panel": panel, "name": name,
                             "ridge": best["ridge"], "d": best["d"],
                             "mean_val_r2": best["mean_val_r2"],
                             "train_rows": best["train_rows"]})
        print(json.dumps({"event": "SELECT", "panel": panel, "name": name,
                          "ridge": best["ridge"], "d": best["d"],
                          "mean_val_r2": round(best["mean_val_r2"], 5)}), flush=True)
    return selections, domains


def stage_ab():
    out_a, out_b = E.receipt_path("stage-a"), E.receipt_path("stage-b")
    for p in (out_a, out_b):
        if p.exists():
            raise FileExistsError(p)
    cand, man_sha = M13.candidate()
    recs = build_all(cand, GCAMP_TRAIN + GCAMP_VAL + GFP_TRAIN + GFP_VAL, True)
    abstains = {rid: r["abstain"] for rid, r in recs.items() if r.get("abstain")}
    common = {}
    for rid, r in recs.items():
        split = "train" if r["role"] == "train" else "validation"
        counts, ok = S.common_row_check(r, split)
        common[rid] = {"split": split, "min_count": min(counts.values()), "ok": ok}
    rows_a = []
    gsel, domains = fit_and_select(recs, GCAMP_TRAIN, GCAMP_VAL, rows_a, "gcamp")
    fsel, _ = fit_and_select(recs, GFP_TRAIN, GFP_VAL, rows_a, "gfp")
    # secondary pc1_2 targets: CE_SOFT and AR with the primary-selected ridge
    secondary = {}
    for name in ("AR", "CE_SOFT"):
        lam = gsel[name]["ridge"]
        for comp in (0, 1):
            xs, ys = [], []
            for rid in GCAMP_TRAIN:
                r = recs[rid]
                rows, X, _ = S.assemble_rows(r, "train", name if name != "AR" else "AR")
                pc = r["pc"][:, comp]
                keep = [i for i, t in enumerate(rows) if math.isfinite(pc[t + S.H])]
                if keep:
                    xs.append(X[keep])
                    ys.append(np.asarray([pc[rows[i] + S.H] for i in keep]))
            model = S.fit_ridge(np.vstack(xs), np.concatenate(ys), lam)
            secondary[f"{name}_pc{comp}"] = model_to_json(model)
    A7.dump_fsync(out_a, {
        "schema": "ba-srm15-stage-a-v1", "manifest_sha256": man_sha,
        "behavior_read_roles": ["train", "validation"],
        "recording_abstains": abstains, "common_row_check": common,
        "fits": rows_a, "runtime": time.time()})
    A7.dump_fsync(out_b, {
        "schema": "ba-srm15-stage-b-v1",
        "stage_a_sha256": hashlib.sha256(out_a.read_bytes()).hexdigest(),
        "gcamp_selections": gsel, "gfp_selections": fsel,
        "fixed_d_domains": domains, "secondary_models": secondary,
        "held_out_opened": False})
    print(json.dumps({"event": "STAGE_AB_COMPLETE"}), flush=True)


def stage_c():
    out_c = E.receipt_path("stage-c")
    if out_c.exists():
        raise FileExistsError(out_c)
    b = json.loads(E.receipt_path("stage-b").read_text(encoding="utf-8"))
    cand, man_sha = M13.candidate()
    recs = build_all(cand, GCAMP_HELD + GFP_HELD, True)
    scores = {"gcamp": {}, "gfp": {}}
    rmses = {}
    for panel, held, sel in (("gcamp", GCAMP_HELD, b["gcamp_selections"]),
                             ("gfp", GFP_HELD, b["gfp_selections"])):
        for name, info in sel.items():
            if "model" not in info:
                continue
            model = model_from_json(info["model"])
            per = {}
            for rid in held:
                rows, X, y = S.assemble_rows(recs[rid], "test", info["family"],
                                             d=info["d"], adverse_kind=info["adverse"],
                                             shift=info["shift"])
                if len(y) < 2:
                    per[rid] = {"r2": float("nan"), "rmse": float("nan"), "rows": int(len(y))}
                else:
                    yh = S.predict(model, X)
                    per[rid] = {"r2": S.r2(y, yh),
                                "rmse": float(np.sqrt(np.mean((y - yh) ** 2))),
                                "rows": int(len(y))}
            scores[panel][name] = per
    g = scores["gcamp"]
    controls = [c for c in ("AR", "FIXED_D", "FIXED_4", "PARTICIPATION_RATIO",
                            "RAW_SPECTRAL", "CAUSAL_UNWEIGHTED", "MASK_ONLY",
                            "RED_CHANNEL") if c in g]
    delta_r2, rmse_gate = {}, {}
    for rid in GCAMP_HELD:
        best_ctrl_r2 = max(g[c][rid]["r2"] for c in controls)
        best_ctrl_rmse = min(g[c][rid]["rmse"] for c in controls)
        delta_r2[rid] = g["CE_SOFT"][rid]["r2"] - best_ctrl_r2
        rmse_gate[rid] = bool(g["CE_SOFT"][rid]["rmse"] < best_ctrl_rmse)
    primary_pass = all(v > 0 for v in delta_r2.values()) and all(rmse_gate.values())

    def med(vals):
        return float(np.median(vals))
    d_ce = med([g["CE_SOFT"][r]["r2"] - g["AR"][r]["r2"] for r in GCAMP_HELD])
    d_mask = med([g["MASK_ONLY"][r]["r2"] - g["AR"][r]["r2"] for r in GCAMP_HELD])
    d_red = med([g["RED_CHANNEL"][r]["r2"] - g["AR"][r]["r2"] for r in GCAMP_HELD])
    gf = scores["gfp"]
    d_gfp = med([gf["CE_SOFT"][r]["r2"] - gf["AR"][r]["r2"] for r in GFP_HELD]) \
        if "CE_SOFT" in gf and "AR" in gf else float("nan")
    artifact_fired = (d_mask >= d_ce) or (d_red >= d_ce) or (d_gfp >= d_ce)
    temporal_fired = any(
        g[a][r]["r2"] >= g["CE_SOFT"][r]["r2"]
        for a in ("PHASE_RANDOMIZED", "TIME_REVERSED", "CIRCULAR_BEHAVIOR_SHIFT")
        if a in g for r in GCAMP_HELD)
    fixed4_selected = b["gcamp_selections"].get("FIXED_D", {}).get("d") == 4
    fixed4_dominant = all(
        g.get("FIXED_4", {}).get(r, {}).get("r2", float("-inf")) >
        max(g[c][r]["r2"] for c in controls if c != "FIXED_4")
        for r in GCAMP_HELD) if "FIXED_4" in g else False

    rng = np.random.default_rng(S.E.BOOT_SEED)
    boot = []
    per_rec_pairs = {}
    for rid in GCAMP_HELD:
        rows, Xce, yce = S.assemble_rows(recs[rid], "test", "CE_SOFT")
        mce = model_from_json(b["gcamp_selections"]["CE_SOFT"]["model"])
        per_rec_pairs[rid] = (yce, S.predict(mce, Xce))
    for _ in range(S.E.BOOT_N):
        ds = []
        for rid in GCAMP_HELD:
            y, yh = per_rec_pairs[rid]
            n = len(y)
            if n < 2:
                continue
            starts = rng.integers(0, n, size=max(1, n // S.E.BOOT_BLOCK + 1))
            idx = np.concatenate([np.arange(s, s + S.E.BOOT_BLOCK) % n for s in starts])[:n]
            info = b["gcamp_selections"]  # controls fixed; recompute CE-vs-bestctrl on resample
            r2ce = S.r2(y[idx], yh[idx])
            ctrl = []
            for c in controls:
                mc = model_from_json(info[c]["model"])
                _, Xc, yc = S.assemble_rows(recs[rid], "test", info[c]["family"],
                                            d=info[c]["d"], adverse_kind=info[c]["adverse"],
                                            shift=info[c]["shift"])
                ctrl.append(S.r2(yc[idx % len(yc)], S.predict(mc, Xc)[idx % len(yc)]))
            ds.append(r2ce - max(ctrl))
        if ds:
            boot.append(float(np.median(ds)))
    ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))] if boot else None

    codes = []
    if not primary_pass:
        codes.append("SOFT_DIMENSION_INCREMENT_NOT_SUPPORTED")
    if artifact_fired:
        codes.append("MEASUREMENT_ARTIFACT_NOT_EXCLUDED")
    if temporal_fired:
        codes.append("TEMPORAL_ALIGNMENT_NOT_IDENTIFIED")
    if not (fixed4_selected or fixed4_dominant):
        codes.append("FIXED4_NOT_SUPPORTED")
    receipt = {
        "schema": "ba-srm15-stage-c-v1", "manifest_sha256": man_sha,
        "stage_b_sha256": hashlib.sha256(E.receipt_path("stage-b").read_bytes()).hexdigest(),
        "held_out_opened": True, "scores": scores,
        "delta_r2": delta_r2, "rmse_gate": rmse_gate, "primary_pass": primary_pass,
        "delta_medians": {"CE": d_ce, "MASK": d_mask, "RED": d_red, "GFP_CE": d_gfp},
        "temporal_fired": temporal_fired, "artifact_fired": artifact_fired,
        "fixed4": {"selected": fixed4_selected, "dominant": fixed4_dominant},
        "bootstrap_delta_ci_descriptive": ci,
        "result_codes": codes or ["PRIMARY_PREDICTIVE_GATE_PASS"],
        "claim_ceiling": "BIO_EVIDENCE_L3_DEVELOPMENTAL_HELD_OUT at most; developmental corpus",
    }
    A7.dump_fsync(out_c, receipt)
    print(json.dumps({"event": "STAGE_C_COMPLETE", "codes": receipt["result_codes"],
                      "delta_r2": delta_r2}), flush=True)


if __name__ == "__main__":
    {"ab": stage_ab, "c": stage_c}[sys.argv[1]]()
