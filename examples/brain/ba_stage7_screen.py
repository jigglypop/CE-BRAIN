"""BA-STAGE7 threshold-latency discrimination screen (x_thr target).

Relative margin: beats iff improvement/L_T >= 1.77% (frozen from Stage 3
constants 0.005/0.28213) and lo95>0; tie band 0.71%. Crossed-anchor >=2 for
the Huber offset, crossed queries >=3 (contract SMOKE_AMENDMENT).

Contract: paper/검증_원장/BA_STAGE7_문턱지연_계약.md. Scalar adaptation of
the frozen protocol: per-source centering removes intercept and age (both
per-source constants for a scalar target), so T is the pure anchor-offset
baseline. Candidates T, D(+d*r), P(+p*f_pl), DP; nonnegative d,p. Controls:
PERM (f_pl within-source permutation, 499, seed 20260832, DP refit) and RESID
(per-fold distance-residualized f_pl, sign check). Measurability positive
control: D must beat T by the frozen margin, else LATENCY_NOT_MEASURABLE.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy.optimize import lsq_linear

HERE = Path.cwd()
OUT = HERE / "ba-stage7-result.json"
LAT = json.loads((HERE / "ba-stage7-latency-endpoints.json").read_text(encoding="utf-8"))
FEAT = json.loads((HERE / "ba-stage4-anatomy-features.json").read_text(encoding="utf-8"))
EPJ = Path(__file__).resolve().parents[2] / "_workspace/ce/brain-human-ccep-multisubject-precision-retry-20260825/artifacts"

CAND = ("T", "D", "P", "DP")
NONNEG = {"T": (), "D": (0,), "P": (0,), "DP": (0, 1)}
HUBER_DELTA, RIDGE = 0.5, 1.0
REL_MARGIN, REL_TIE = 0.005 / 0.28213, 0.002 / 0.28213
PERM_N, PERM_SEED = 499, 20260834


def huber_location(res):
    v = np.asarray(res, float).reshape(-1)
    lo, hi = float(v.min() - HUBER_DELTA), float(v.max() + HUBER_DELTA)
    for _ in range(80):
        mid = (lo + hi) / 2
        if float(np.sum(np.clip(v - mid, -HUBER_DELTA, HUBER_DELTA))) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def huber_loss(res):
    a = np.abs(res)
    return np.where(a <= HUBER_DELTA, 0.5 * res * res, HUBER_DELTA * (a - 0.5 * HUBER_DELTA))


def fold_of(subject):
    import re
    return (int(re.search(r"(\d+)$", subject).group(1)) - 1) % 5


def load_sources():
    """Join latency table with anatomy features and distances from endpoint tables."""
    rows = []
    drops = {"source_dropped": 0, "anchor_latency": 0, "few_queries": 0}
    for stage in ("d0", "d1", "d2", "d3"):
        d = json.loads((EPJ / f"{stage}-endpoints.json").read_text(encoding="utf-8"))
        for s in d["sources"]:
            lkey = f"{stage.upper()}|{s['subject']}|{s['source_id']}"
            fkey = f"{s['subject']}|{s['source_id']}|{stage}"
            lat = LAT.get(lkey)
            feat = FEAT.get(fkey, {})
            if lat is None or feat.get("__source_dropped__"):
                drops["source_dropped"] += 1
                continue
            lmap = {t["site_id"]: t for t in lat}
            recs = {"anchor": [], "query": []}
            for t in s["targets"]:
                lt = lmap.get(t["site_id"])
                ft = feat.get(t["site_id"])
                if lt is None or lt["x_lat"] is None or ft is None:
                    continue
                r = float(np.linalg.norm(t["delta_over_50mm"]))
                recs[t["role"]].append((lt["x_lat"], r, ft["f_pl"], lt["max_z"]))
            if len(recs["anchor"]) < 2:
                drops["anchor_latency"] += 1
                continue
            if len(recs["query"]) < 3:
                drops["few_queries"] += 1
                continue
            rows.append({
                "subject": s["subject"], "source_id": s["source_id"],
                "anchor": np.asarray(recs["anchor"], float),
                "query": np.asarray(recs["query"], float),
            })
    return rows, drops


def design(cand, mat, pl_override=None):
    r = mat[:, 1]
    pl = pl_override if pl_override is not None else mat[:, 2]
    cols = {"T": np.empty((len(mat), 0)), "D": r[:, None], "P": pl[:, None],
            "DP": np.column_stack((r, pl)), "RESID": np.column_stack((r, pl))}
    return cols[cand]


def fit(sources, cand, pl_key=2):
    Xs, ys = [], []
    for s in sources:
        both = np.vstack((s["anchor"], s["query"]))
        X = design(cand, both) if pl_key == 2 else design(cand, both, both[:, pl_key])
        y = both[:, 0]
        Xs.append(X - X.mean(0, keepdims=True))
        ys.append(y - y.mean())
    X = np.vstack(Xs)
    y = np.concatenate(ys)
    if X.shape[1] == 0:
        return {"coef": np.zeros(0), "scales": np.ones(0)}
    scales = np.sqrt(np.mean(X * X, axis=0))
    scales[scales <= 1e-12] = 1.0
    Xs_ = X / scales
    p = Xs_.shape[1]
    A = np.vstack((Xs_, np.sqrt(RIDGE) * np.eye(p)))
    b = np.concatenate((y, np.zeros(p)))
    lo = np.full(p, -np.inf)
    for i in NONNEG.get(cand, ()):
        lo[i] = 0.0
    sol = lsq_linear(A, b, bounds=(lo, np.full(p, np.inf)), tol=1e-10, lsmr_tol=1e-10)
    if not sol.success or not np.all(np.isfinite(sol.x)):
        raise RuntimeError(f"STAGE6_APPARATUS_STOP: fit {cand}")
    return {"coef": sol.x, "scales": scales}


def evaluate(s, cand, model, pl_key=2):
    both = np.vstack((s["anchor"], s["query"]))
    X = design(cand, both) if pl_key == 2 else design(cand, both, both[:, pl_key])
    X = X - X.mean(0, keepdims=True)
    pred = (X / model["scales"]) @ model["coef"] if X.shape[1] else np.zeros(len(X))
    na = len(s["anchor"])
    offset = huber_location(s["anchor"][:, 0] - pred[:na])
    return float(np.mean(huber_loss(s["query"][:, 0] - (pred[na:] + offset))))


def cv(sources, cand, pl_key=2):
    per = {}
    for f in range(5):
        tr = [s for s in sources if fold_of(s["subject"]) != f]
        te = [s for s in sources if fold_of(s["subject"]) == f]
        m = fit(tr, cand, pl_key)
        for s in te:
            per.setdefault(s["subject"], []).append(evaluate(s, cand, m, pl_key))
    return {k: float(np.mean(v)) for k, v in sorted(per.items())}


def pairwise(losses, left, right, seed_off):
    subs = sorted(set(losses[left]) & set(losses[right]))
    vals = np.asarray([losses[right][s] - losses[left][s] for s in subs])
    rng = np.random.Generator(np.random.PCG64(20260834 + seed_off))
    boots = [float(np.mean(vals[rng.integers(0, len(vals), len(vals))])) for _ in range(4999)]
    return {"mean_improvement": float(vals.mean()), "lower_95": float(np.percentile(boots, 2.5)),
            "positive_participants": int((vals > 0).sum()), "n": len(subs)}


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    t0 = time.time()
    sources, drops = load_sources()
    subs = {s["subject"] for s in sources}
    print(json.dumps({"event": "SOURCES", "kept": len(sources), "drops": drops,
                      "participants": len(subs)}), flush=True)

    losses = {c: cv(sources, c) for c in CAND}
    means = {c: float(np.mean(list(losses[c].values()))) for c in CAND}
    print(json.dumps({"event": "MEANS", **{k: round(v, 6) for k, v in means.items()}}), flush=True)
    pw = {}
    for i, a in enumerate(CAND):
        for j, b in enumerate(CAND):
            if a != b:
                pw[f"{a}>{b}"] = pairwise(losses, a, b, 10 * i + j)

    # RESID: per-fold residualization of f_pl on r, stored in column 3 slot
    for f in range(5):
        tr = [s for s in sources if fold_of(s["subject"]) != f]
        rs, pls = [], []
        for s in tr:
            both = np.vstack((s["anchor"], s["query"]))
            rs.extend(both[:, 1])
            pls.extend(both[:, 2])
        beta = np.linalg.lstsq(np.column_stack((np.ones(len(rs)), rs)),
                               np.asarray(pls), rcond=None)[0]
        for s in sources:
            if fold_of(s["subject"]) == f:
                for part in ("anchor", "query"):
                    m = s[part]
                    resid = m[:, 2] - (beta[0] + beta[1] * m[:, 1])
                    s[part] = np.column_stack((m, resid))
    losses["RESID"] = cv(sources, "RESID", pl_key=4)
    means["RESID"] = float(np.mean(list(losses["RESID"].values())))
    pw["RESID>D"] = pairwise(losses, "RESID", "D", 991)

    perm_means = []
    base_cols = {id(s): (s["anchor"].copy(), s["query"].copy()) for s in sources}
    rng = np.random.Generator(np.random.PCG64(PERM_SEED))
    for k in range(PERM_N):
        for s in sources:
            a0, q0 = base_cols[id(s)]
            na = len(a0)
            allpl = np.concatenate((a0[:, 2], q0[:, 2]))
            p = rng.permutation(len(allpl))
            merged = allpl[p]
            s["anchor"] = a0.copy()
            s["query"] = q0.copy()
            s["anchor"][:, 2] = merged[:na]
            s["query"][:, 2] = merged[na:]
        lp = cv(sources, "DP")
        perm_means.append(float(np.mean(list(lp.values()))))
        if (k + 1) % 100 == 0:
            print(json.dumps({"event": "PERM", "done": k + 1}), flush=True)
    for s in sources:  # restore
        s["anchor"], s["query"] = base_cols[id(s)]
    perm_frac = float(np.mean([means["DP"] < v for v in perm_means]))

    l_t = means["T"]

    def beats(a, b):
        r = pw[f"{a}>{b}"]
        return r["mean_improvement"] >= REL_MARGIN * l_t and r["lower_95"] > 0.0

    if not beats("D", "T"):
        decision = "STAGE7_LATENCY_TRACK_CLOSED"
    elif beats("DP", "D") and perm_frac >= 0.95 and pw["RESID>D"]["mean_improvement"] > 0.0:
        decision = "STAGE7_LATENCY_ANATOMY_SUPPORTED"
    elif beats("DP", "D"):
        decision = "STAGE7_CONTROL_FAILED"
    else:
        decision = "STAGE7_DISTANCE_ONLY"

    result = {
        "schema": "ba-stage7-screen-v1",
        "contract": "paper/검증_원장/BA_STAGE7_문턱지연_계약.md",
        "latency_endpoints_sha256": hashlib.sha256(
            (HERE / "ba-stage7-latency-endpoints.json").read_bytes()).hexdigest(),
        "sources_kept": len(sources), "drops": drops, "participants": len(subs),
        "mean_participant_losses": means,
        "pairwise": pw,
        "perm": {"n": PERM_N, "dp_below_perm_fraction": perm_frac,
                 "perm_mean_med": float(np.median(perm_means))},
        "decision": decision,
        "runtime_seconds": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(result, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"event": "COMPLETE", "decision": decision,
                      "means": {k: round(v, 5) for k, v in means.items()},
                      "perm_frac": perm_frac}), flush=True)


if __name__ == "__main__":
    main()
