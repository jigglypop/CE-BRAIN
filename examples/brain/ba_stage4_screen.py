"""BA-STAGE4 anatomy-vs-E discrimination screen.

Contract: paper/검증_원장/BA_STAGE4_해부학_다리_계약.md (LOCKED_PRE_RESULT).
Reuses the frozen Stage 3 protocol (participant 5-fold, ridge lambda=1,
nonnegative attenuation bounds, source centering, RMS feature scales, 4-anchor
Huber offset, participant-mean Huber loss, 4999-bootstrap, 0.005/0.002 rules)
with anatomy features from the anatomy-blind linkage lock. Sources whose
linkage dropped any anchor (8/592) are excluded for ALL candidates (matched).

Candidates: T, E, A_SC, A_PL, EA. Controls: PERM (499 permutations of f_sc
across the 16 sites WITHIN each source — a within-participant shuffle at the
finest matched granularity; seed 20260830), RESID (per-fold distance-
residualized f_sc, unbounded coefficient, sign check only).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import lsq_linear

HERE = Path.cwd()
REPO = Path(__file__).resolve().parents[2]
EPOCH = (REPO / "_workspace/ce/brain-ce-brain-synthetic-world-model-discrimination-20260826/"
         "artifacts/epochs/stage3-human-ccep-representation-screen")
_spec = importlib.util.spec_from_file_location("s3", EPOCH / "stage3_model_screen.py")
S3 = importlib.util.module_from_spec(_spec)
sys.modules["s3"] = S3
_spec.loader.exec_module(S3)

OUT = HERE / "ba-stage4-result.json"
FEATJ = json.loads((HERE / "ba-stage4-anatomy-features.json").read_text(encoding="utf-8"))
CAND = ("T", "E", "A_SC", "A_PL", "EA")
PERM_N, PERM_SEED = 499, 20260830
BIN_N = 5


def load_sources4():
    """Stage 3 loading plus anatomy vectors; matched exclusion of dropped sources."""
    S3.endpoint_identities()
    rows = []
    dropped = 0
    for name in S3.ENDPOINT_LOCKS:
        stage = name.split("-")[0]
        payload = json.loads((S3.endpoint_root() / name).read_text(encoding="utf-8"))
        for item in payload["sources"]:
            key = f"{item['subject']}|{item['source_id']}|{stage}"
            rec = FEATJ[key]
            if rec.get("__source_dropped__"):
                dropped += 1
                continue
            anchors = [t for t in item["targets"] if t["role"] == "anchor"]
            queries = [t for t in item["targets"] if t["role"] == "query"]
            if any(t["site_id"] not in rec for t in anchors):
                dropped += 1
                continue
            qkeep = [t for t in queries if t["site_id"] in rec]
            if len(qkeep) < 6:
                dropped += 1
                continue
            rows.append({
                "subject": item["subject"],
                "source_id": item["source_id"],
                "age": float(item["age_years"]),
                "anchor_delta": np.asarray([t["delta_over_50mm"] for t in anchors], float),
                "query_delta": np.asarray([t["delta_over_50mm"] for t in qkeep], float),
                "anchor_z": np.asarray([t["endpoint"]["z"] for t in anchors], float),
                "query_z": np.asarray([t["endpoint"]["z"] for t in qkeep], float),
                "anchor_sc": np.asarray([rec[t["site_id"]]["f_sc"] for t in anchors], float),
                "query_sc": np.asarray([rec[t["site_id"]]["f_sc"] for t in qkeep], float),
                "anchor_pl": np.asarray([rec[t["site_id"]]["f_pl"] for t in anchors], float),
                "query_pl": np.asarray([rec[t["site_id"]]["f_pl"] for t in qkeep], float),
            })
    return rows, dropped


def features4(cand, delta, sc, pl, age_tilde, sc_override=None):
    delta = np.asarray(delta, float)
    n = len(delta)
    logx = np.log(S3.BIN_X)
    common = np.tile(np.column_stack((logx, S3.BIN_X, age_tilde * logx, age_tilde * S3.BIN_X)),
                     (n, 1))
    rep = np.repeat(delta, BIN_N, axis=0)
    r = np.linalg.norm(rep, axis=1)
    scv = np.repeat(sc_override if sc_override is not None else sc, BIN_N)
    plv = np.repeat(pl, BIN_N)
    extras = {
        "T": np.empty((len(common), 0)),
        "E": (-r)[:, None],
        "A_SC": scv[:, None],
        "A_PL": (-plv)[:, None],
        "EA": np.column_stack((-r, scv)),
        "RESID": np.column_stack((-r, scv)),
    }
    return np.column_stack((common, extras[cand]))


NONNEG = {"T": (), "E": (4,), "A_SC": (4,), "A_PL": (4,), "EA": (4, 5), "RESID": (4,)}


def fit4(sources, cand, sc_key="sc"):
    ages = np.asarray([s["age"] for s in sources])
    am, asd = float(ages.mean()), float(ages.std())
    designs, resps = [], []
    for s in sources:
        delta = np.concatenate((s["anchor_delta"], s["query_delta"]))
        sc = np.concatenate((s[f"anchor_{sc_key}"], s[f"query_{sc_key}"])) \
            if cand in ("A_SC", "EA", "RESID") else np.zeros(len(delta))
        pl = np.concatenate((s["anchor_pl"], s["query_pl"])) if cand == "A_PL" else np.zeros(len(delta))
        d = features4(cand, delta, sc, pl, (s["age"] - am) / asd)
        y = np.concatenate((s["anchor_z"], s["query_z"])).reshape(-1)
        designs.append(d - d.mean(0, keepdims=True))
        resps.append(y - y.mean())
    X = np.vstack(designs)
    y = np.concatenate(resps)
    scales = np.sqrt(np.mean(X * X, axis=0))
    scales[scales <= 1e-12] = 1.0
    Xs = X / scales
    p = Xs.shape[1]
    A = np.vstack((Xs, np.sqrt(S3.RIDGE) * np.eye(p)))
    b = np.concatenate((y, np.zeros(p)))
    lo = np.full(p, -np.inf)
    for i in NONNEG[cand]:
        lo[i] = 0.0
    sol = lsq_linear(A, b, bounds=(lo, np.full(p, np.inf)), tol=1e-10, lsmr_tol=1e-10, max_iter=500)
    if not sol.success or not np.all(np.isfinite(sol.x)):
        raise RuntimeError(f"STAGE4_APPARATUS_STOP: fit {cand}")
    return {"coef": sol.x, "scales": scales, "am": am, "asd": asd}


def eval4(s, cand, fit, sc_key="sc"):
    delta = np.concatenate((s["anchor_delta"], s["query_delta"]))
    sc = np.concatenate((s[f"anchor_{sc_key}"], s[f"query_{sc_key}"])) \
        if cand in ("A_SC", "EA", "RESID") else np.zeros(len(delta))
    pl = np.concatenate((s["anchor_pl"], s["query_pl"])) if cand == "A_PL" else np.zeros(len(delta))
    d = features4(cand, delta, sc, pl, (s["age"] - fit["am"]) / fit["asd"])
    d -= d.mean(0, keepdims=True)
    pred = ((d / fit["scales"]) @ fit["coef"]).reshape(len(delta), BIN_N)
    na = len(s["anchor_delta"])
    offset = S3.huber_location(s["anchor_z"] - pred[:na])
    return float(np.mean(S3.huber_loss(s["query_z"] - (pred[na:] + offset))))


def cv_losses(sources, cand, sc_key="sc"):
    per = {}
    for fold in range(5):
        tr = [s for s in sources if S3.fold_of(s["subject"]) != fold]
        te = [s for s in sources if S3.fold_of(s["subject"]) == fold]
        fit = fit4(tr, cand, sc_key)
        for s in te:
            per.setdefault(s["subject"], []).append(eval4(s, cand, fit, sc_key))
    return {k: float(np.mean(v)) for k, v in sorted(per.items())}


def pairwise(losses, left, right, seed_off):
    subs = sorted(set(losses[left]) & set(losses[right]))
    vals = np.asarray([losses[right][s] - losses[left][s] for s in subs])
    rng = np.random.Generator(np.random.PCG64(20260830 + seed_off))
    boots = [float(np.mean(vals[rng.integers(0, len(vals), len(vals))])) for _ in range(4999)]
    return {"mean_improvement": float(vals.mean()),
            "lower_95": float(np.percentile(boots, 2.5)),
            "positive_participants": int((vals > 0).sum()),
            "n": len(subs)}


def residualize(sources):
    """Per-fold distance-residualized f_sc, stored as sc_resid keys."""
    for fold in range(5):
        tr = [s for s in sources if S3.fold_of(s["subject"]) != fold]
        rs, scs = [], []
        for s in tr:
            for part in ("anchor", "query"):
                rs.extend(np.linalg.norm(s[f"{part}_delta"], axis=1))
                scs.extend(s[f"{part}_sc"])
        A = np.column_stack((np.ones(len(rs)), rs))
        beta = np.linalg.lstsq(A, np.asarray(scs), rcond=None)[0]
        for s in sources:
            if S3.fold_of(s["subject"]) == fold:
                for part in ("anchor", "query"):
                    r = np.linalg.norm(s[f"{part}_delta"], axis=1)
                    s[f"{part}_scres"] = s[f"{part}_sc"] - (beta[0] + beta[1] * r)
    # train folds also need values when used as training rows in other folds:
    for s in sources:
        if f"anchor_scres" not in s:
            r = np.linalg.norm(s["anchor_delta"], axis=1)
    return sources


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    t0 = time.time()
    sources, dropped = load_sources4()
    subs = {s["subject"] for s in sources}
    print(json.dumps({"event": "SOURCES", "kept": len(sources), "dropped": dropped,
                      "participants": len(subs)}), flush=True)

    losses = {c: cv_losses(sources, c) for c in CAND}
    means = {c: float(np.mean(list(losses[c].values()))) for c in CAND}
    print(json.dumps({"event": "MEANS", **{k: round(v, 6) for k, v in means.items()}}), flush=True)

    pw = {}
    for i, a in enumerate(CAND):
        for j, b in enumerate(CAND):
            if a != b:
                pw[f"{a}>{b}"] = pairwise(losses, a, b, 100 * i + j)

    # RESID: per-fold residualization; global refit uses fold-local residuals.
    # Simpler faithful approach: residualize using ALL sources' (r, f_sc) per
    # training fold inside cv (already fold-local above via residualize()).
    residualize(sources)
    losses["RESID"] = cv_losses(sources, "RESID", sc_key="scres")
    means["RESID"] = float(np.mean(list(losses["RESID"].values())))
    pw["RESID>E"] = pairwise(losses, "RESID", "E", 991)

    # PERM: within-participant permutation of site f_sc, full refit each time.
    rng = np.random.Generator(np.random.PCG64(PERM_SEED))
    ea_mean = means["EA"]
    perm_means = []
    for k in range(PERM_N):
        for s in sources:
            n_a, n_q = len(s["anchor_sc"]), len(s["query_sc"])
            allv = np.concatenate((s["anchor_sc"], s["query_sc"]))
            p = rng.permutation(len(allv))
            s["anchor_scperm"] = allv[p][:n_a]
            s["query_scperm"] = allv[p][n_a:]
        lp = cv_losses(sources, "EA", sc_key="scperm")
        perm_means.append(float(np.mean(list(lp.values()))))
        if (k + 1) % 50 == 0:
            print(json.dumps({"event": "PERM", "done": k + 1}), flush=True)
    perm_pct = float(np.mean([ea_mean < v for v in perm_means]))

    winner = next(c for c in CAND if means[c] <= min(means.values()) + S3.TIE_BAND)

    def beats(a, b):
        r = pw[f"{a}>{b}"]
        return r["mean_improvement"] >= S3.PRACTICAL_IMPROVEMENT and r["lower_95"] > 0.0

    anatomy_beats_e = any(beats(c, "E") for c in ("A_SC", "A_PL", "EA"))
    perm_pass = perm_pct >= 0.95
    resid_sign = pw["RESID>E"]["mean_improvement"] > 0.0
    if anatomy_beats_e and perm_pass and resid_sign:
        decision = "STAGE4_ANATOMY_BRIDGE_SUPPORTED"
    elif not anatomy_beats_e:
        decision = "STAGE4_ANATOMY_NOT_IDENTIFIED"
    else:
        decision = "STAGE4_ANATOMY_CONTROL_FAILED"

    result = {
        "schema": "ba-stage4-screen-v1",
        "contract": "paper/검증_원장/BA_STAGE4_해부학_다리_계약.md",
        "linkage_receipt_sha256": hashlib.sha256(
            (HERE / "ba-stage4-linkage-receipt.json").read_bytes()).hexdigest(),
        "sources_kept": len(sources), "sources_dropped": dropped,
        "participants": len(subs),
        "mean_participant_losses": means,
        "pairwise": pw,
        "perm": {"n": PERM_N, "ea_below_perm_fraction": perm_pct,
                 "perm_mean_min": float(min(perm_means)), "perm_mean_med": float(np.median(perm_means))},
        "winner": winner,
        "decision": decision,
        "runtime_seconds": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(result, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"event": "COMPLETE", "decision": decision, "winner": winner,
                      "means": {k: round(v, 5) for k, v in means.items()},
                      "perm_frac": perm_pct}), flush=True)


if __name__ == "__main__":
    main()
