"""BA-STAGE5 shape-channel anatomy discrimination.

Contract: paper/검증_원장/BA_STAGE5_모양채널_계약.md (LOCKED_PRE_RESULT).
Extends the Stage 4 screen with bin-interaction features: spatial terms may
now multiply log(x_b), opening the profile-shape channel that Stage 3/4's
bin-constant design excluded. Candidates T, E, Ex, EAx; controls PERM
(within-source f_sc permutation, 499, seed 20260831, EAx refit) and RESID.
Interaction coefficients are sign-free; attenuation bounds stay nonnegative.
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
_spec = importlib.util.spec_from_file_location("s4mod", Path(__file__).resolve().parent / "ba_stage4_screen.py")
S4 = importlib.util.module_from_spec(_spec)
sys.modules["s4mod"] = S4
_spec.loader.exec_module(S4)
S3 = S4.S3

OUT = HERE / "ba-stage5-result.json"
CAND = ("T", "E", "Ex", "EAx")
NONNEG5 = {"T": (), "E": (4,), "Ex": (4,), "EAx": (4,), "RESID": (4,)}
PERM_N, PERM_SEED = 499, 20260831
BIN_N = 5


def features5(cand, delta, sc, age_tilde):
    delta = np.asarray(delta, float)
    n = len(delta)
    logx = np.log(S3.BIN_X)
    common = np.tile(np.column_stack((logx, S3.BIN_X, age_tilde * logx, age_tilde * S3.BIN_X)),
                     (n, 1))
    rep = np.repeat(delta, BIN_N, axis=0)
    r = np.linalg.norm(rep, axis=1)
    logx_rep = np.tile(logx, n)
    scv = np.repeat(sc, BIN_N)
    extras = {
        "T": np.empty((len(common), 0)),
        "E": (-r)[:, None],
        "Ex": np.column_stack((-r, r * logx_rep)),
        "EAx": np.column_stack((-r, r * logx_rep, scv, scv * logx_rep)),
        "RESID": np.column_stack((-r, r * logx_rep, scv, scv * logx_rep)),
    }
    return np.column_stack((common, extras[cand]))


def fit5(sources, cand, sc_key="sc"):
    ages = np.asarray([s["age"] for s in sources])
    am, asd = float(ages.mean()), float(ages.std())
    designs, resps = [], []
    for s in sources:
        delta = np.concatenate((s["anchor_delta"], s["query_delta"]))
        sc = (np.concatenate((s[f"anchor_{sc_key}"], s[f"query_{sc_key}"]))
              if cand in ("EAx", "RESID") else np.zeros(len(delta)))
        d = features5(cand, delta, sc, (s["age"] - am) / asd)
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
    for i in NONNEG5[cand]:
        lo[i] = 0.0
    sol = lsq_linear(A, b, bounds=(lo, np.full(p, np.inf)), tol=1e-10, lsmr_tol=1e-10, max_iter=500)
    if not sol.success or not np.all(np.isfinite(sol.x)):
        raise RuntimeError(f"STAGE5_APPARATUS_STOP: fit {cand}")
    return {"coef": sol.x, "scales": scales, "am": am, "asd": asd}


def eval5(s, cand, fit, sc_key="sc"):
    delta = np.concatenate((s["anchor_delta"], s["query_delta"]))
    sc = (np.concatenate((s[f"anchor_{sc_key}"], s[f"query_{sc_key}"]))
          if cand in ("EAx", "RESID") else np.zeros(len(delta)))
    d = features5(cand, delta, sc, (s["age"] - fit["am"]) / fit["asd"])
    d -= d.mean(0, keepdims=True)
    pred = ((d / fit["scales"]) @ fit["coef"]).reshape(len(delta), BIN_N)
    na = len(s["anchor_delta"])
    offset = S3.huber_location(s["anchor_z"] - pred[:na])
    return float(np.mean(S3.huber_loss(s["query_z"] - (pred[na:] + offset))))


def cv5(sources, cand, sc_key="sc"):
    per = {}
    for fold in range(5):
        tr = [s for s in sources if S3.fold_of(s["subject"]) != fold]
        te = [s for s in sources if S3.fold_of(s["subject"]) == fold]
        fit = fit5(tr, cand, sc_key)
        for s in te:
            per.setdefault(s["subject"], []).append(eval5(s, cand, fit, sc_key))
    return {k: float(np.mean(v)) for k, v in sorted(per.items())}


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    t0 = time.time()
    sources, dropped = S4.load_sources4()
    print(json.dumps({"event": "SOURCES", "kept": len(sources), "dropped": dropped}), flush=True)
    # parity check: features5 T/E must be bit-identical to Stage 4's (apparatus check)
    probe = np.random.default_rng(1).standard_normal((16, 3))
    for c in ("T", "E"):
        assert np.array_equal(S4.features4(c, probe, np.zeros(16), np.zeros(16), 0.4),
                              features5(c, probe, np.zeros(16), 0.4)), c

    losses = {c: cv5(sources, c) for c in CAND}
    means = {c: float(np.mean(list(losses[c].values()))) for c in CAND}
    print(json.dumps({"event": "MEANS", **{k: round(v, 6) for k, v in means.items()}}), flush=True)

    pw = {}
    for i, a in enumerate(CAND):
        for j, b in enumerate(CAND):
            if a != b:
                pw[f"{a}>{b}"] = S4.pairwise(losses, a, b, 1000 + 10 * i + j)

    S4.residualize(sources)
    losses["RESID"] = cv5(sources, "RESID", sc_key="scres")
    means["RESID"] = float(np.mean(list(losses["RESID"].values())))
    pw["RESID>Ex"] = S4.pairwise(losses, "RESID", "Ex", 1991)

    rng = np.random.Generator(np.random.PCG64(PERM_SEED))
    perm_means = []
    for k in range(PERM_N):
        for s in sources:
            n_a = len(s["anchor_sc"])
            allv = np.concatenate((s["anchor_sc"], s["query_sc"]))
            p = rng.permutation(len(allv))
            s["anchor_scperm"] = allv[p][:n_a]
            s["query_scperm"] = allv[p][n_a:]
        lp = cv5(sources, "EAx", sc_key="scperm")
        perm_means.append(float(np.mean(list(lp.values()))))
        if (k + 1) % 100 == 0:
            print(json.dumps({"event": "PERM", "done": k + 1}), flush=True)
    perm_frac = float(np.mean([means["EAx"] < v for v in perm_means]))

    def beats(a, b):
        r = pw[f"{a}>{b}"]
        return r["mean_improvement"] >= S3.PRACTICAL_IMPROVEMENT and r["lower_95"] > 0.0

    if beats("EAx", "Ex") and perm_frac >= 0.95 and pw["RESID>Ex"]["mean_improvement"] > 0.0:
        decision = "STAGE5_SHAPE_ANATOMY_SUPPORTED"
    elif beats("EAx", "Ex"):
        decision = "STAGE5_CONTROL_FAILED"
    elif beats("Ex", "E"):
        decision = "STAGE5_SHAPE_CHANNEL_ONLY"
    else:
        decision = "STAGE5_SHAPE_NOT_IDENTIFIED"

    result = {
        "schema": "ba-stage5-screen-v1",
        "contract": "paper/검증_원장/BA_STAGE5_모양채널_계약.md",
        "sources_kept": len(sources), "sources_dropped": dropped,
        "mean_participant_losses": means,
        "pairwise": pw,
        "perm": {"n": PERM_N, "eax_below_perm_fraction": perm_frac,
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
