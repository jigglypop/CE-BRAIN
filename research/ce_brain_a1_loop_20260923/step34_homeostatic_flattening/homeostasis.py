"""A1 step 34: does homeostatic synaptic scaling (Renart, Song & Wang 2003) flatten the connectome ring's wells? (CONTRACT.md)

Model: step 33 (sigmoid, homeostatic tonic level beta=-1, g=1.05, signed synapse counts, expanded network).
Experience: a weak visual cue steers the bump through all 16 headings; each neuron scales its excitatory (positive)
incoming weights so that its heading-averaged activity approaches the mean of its cell type:
s_i <- s_i * (mean_type / r_i)^ETA. Continuity is measured in darkness before and after learning.

python homeostasis.py              full run; refuses unless CONTRACT.md lists this code hash
python homeostasis.py --synthetic  noisy synthetic ring (pre-freeze, writes nothing)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sel = load("selection", LOOP / "step33_selection/selection.py")
su = sel.su
BETA, G = sel.BETA, sel.G
HEADINGS = np.arange(16) * 22.5
EPOCHS, ETA, CUE_TRAIN, T_TRAIN, T_AVG = 20, 0.5, 1.0, 30.0, 20.0
T_CUE, T_DARK = 20.0, 100.0
DT = sel.DT


def operating(W, epg, ang):
    lam1 = su.lambda1(W, epg, ang)
    w0 = G / (lam1 * su.sig(BETA) * (1 - su.sig(BETA)))
    bias = BETA - w0 * (W @ np.full(W.shape[0], su.sig(BETA)))
    return w0, bias


def cue_vec(n, epg, ang, deg, amp):
    v = np.zeros(n)
    v[epg] = amp * np.maximum(np.cos(ang - np.radians(deg)), 0)
    return v


def run(W, w0, bias, phases, record_from=None):
    x = np.full(W.shape[0], su.sig(BETA))
    acc, cnt, t = np.zeros_like(x), 0, 0.0
    for dur, inp in phases:
        for _ in range(int(dur / DT)):
            x = x + DT * (-x + su.sig(w0 * (W @ x) + bias + (0.0 if inp is None else inp)))
            t += DT
            if record_from is not None and t >= record_from:
                acc += x
                cnt += 1
    return x, (acc / cnt if cnt else None)


def continuity(W, epg, ang):
    w0, bias = operating(W, epg, ang)
    n = W.shape[0]
    finals, widths = [], []
    for h in HEADINGS:
        x, _ = run(W, w0, bias, [(T_CUE, cue_vec(n, epg, ang, h, 3.0)), (T_DARK, None)])
        finals.append(sel.centre_deg(x, epg, ang))
        widths.append(su.width_of(x, epg, ang)[0])
    err = np.abs(sel.wrapd(np.array(finals) - HEADINGS))
    wells = []
    for f in sorted(np.mod(finals, 360)):
        if not wells or min(abs(sel.wrapd(f - w)) for w in wells) > 22.5:
            wells.append(f)
    return {"final_deg": [float(v) for v in finals], "abs_error_deg": err.tolist(), "retention": float(np.mean(err <= 22.5)),
            "median_error_deg": float(np.median(err)), "distinct_end_positions": len(wells),
            "median_fwhm": float(np.median([w for w in widths if w is not None])) if any(w is not None for w in widths) else None}


def learn(W, epg, ang, kind):
    W = W.copy()
    exc = W > 0
    s = np.ones(W.shape[0])
    types = np.array(kind)
    history = []
    for ep in range(EPOCHS):
        Ws = np.where(exc, W * s[:, None], W)
        w0, bias = operating(Ws, epg, ang)
        n = W.shape[0]
        r = np.zeros(n)
        for h in HEADINGS:
            _, avg = run(Ws, w0, bias, [(T_TRAIN, cue_vec(n, epg, ang, h, CUE_TRAIN))], record_from=T_TRAIN - T_AVG)
            r += avg / len(HEADINGS)
        target = np.array([r[types == t].mean() for t in types])
        s = s * np.clip((target / np.maximum(r, 1e-9)) ** ETA, 0.5, 2.0)
        history.append(float(np.std(r / np.maximum(target, 1e-9))))
    return np.where(exc, W * s[:, None], W), s, history


def analyse(W, epg, ang, kind):
    before = continuity(W, epg, ang)
    Wl, s, hist = learn(W, epg, ang, kind)
    after = continuity(Wl, epg, ang)
    return {"before": before, "after": after, "scale_summary": {"min": float(s.min()), "median": float(np.median(s)), "max": float(s.max())},
            "activity_cv_by_epoch": hist,
            "C1_retention_after": bool(after["retention"] >= 0.8), "C2_improves": bool(after["retention"] > before["retention"]),
            "C3_width_after": bool(after["median_fwhm"] is not None and 80 <= after["median_fwhm"] <= 120)}


def synthetic():
    N, rep = 16, 3
    angE = np.repeat(np.arange(N) * 2 * np.pi / N, rep)
    K = lambda a, b, s=0.0, k=3.0: np.exp(k * np.cos(a[:, None] - b[None, :] - s))
    n = 2 * N * rep + 1
    E, D, G_ = np.arange(N * rep), np.arange(N * rep, 2 * N * rep), np.array([n - 1])
    w = np.zeros((n, n))
    w[np.ix_(E, E)] = np.exp(6.0 * (np.cos(angE[:, None] - angE[None, :]) - 1))
    w[np.ix_(D, E)] = K(angE, angE, 0, 1); w[np.ix_(E, D)] = -0.3 * K(angE, angE, np.pi, 1)
    w[np.ix_(G_, E)] = 1.0; w[np.ix_(E, G_)] = -0.35 * np.exp(6.0 * (np.cos(angE[:, None] - angE[None, :]) - 1)).sum(1)[:, None] / (N * rep) * 8
    rng = np.random.default_rng(5)
    W = w * np.exp(0.3 * rng.normal(size=w.shape))
    kind = ["EPG"] * (N * rep) + ["Delta7"] * (N * rep) + ["G"]
    return analyse(W, E, angE, kind)


def main():
    if "--synthetic" in sys.argv:
        r = synthetic()
        for k in ("before", "after"):
            print(k, {x: r[k][x] for x in ("retention", "median_error_deg", "distinct_end_positions", "median_fwhm")})
        print("scale", r["scale_summary"], "cv", [round(v, 3) for v in r["activity_cv_by_epoch"]], "C", r["C1_retention_after"], r["C2_improves"], r["C3_width_after"])
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    nets = {}

    def kinds(A, ty, sd, nt):
        chosen, members = su.gi.select(A, ty, nt)
        base = [v for v in range(len(ty)) if ty[v] in su.gi.BASE]
        nodes = sorted(base + [v for t in chosen for v in members[t]])
        return [ty[v] for v in nodes]
    A, ty, sd, nt = su.gi.malecns(); nets["malecns"] = (su.raw_network(A, ty, su.s25.malecns()[2], sd, nt), kinds(A, ty, sd, nt))
    A, ty, sd, nt = su.gi.flywire(); nets["flywire"] = (su.raw_network(A, ty, None, sd, nt), kinds(A, ty, sd, nt))
    A, ty, inst, sd, nt = h22.hemibrain(); nets["hemibrain"] = (su.raw_network(A, ty, inst, sd, nt), kinds(A, ty, sd, nt))
    res = {k: analyse(net[0], net[1], net[2], kd) for k, (net, kd) in nets.items()}
    ok = all(r["C1_retention_after"] and r["C2_improves"] and r["C3_width_after"] for r in res.values())
    result = {"schema": "ce-a1-step34-homeostatic-flattening", "code_sha256": code_hash,
              "verdict": "HOMEOSTASIS_FLATTENS_RING" if ok else "HOMEOSTASIS_DOES_NOT_FLATTEN_RING", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"])
    for k, r in res.items():
        print("==", k, "C", r["C1_retention_after"], r["C2_improves"], r["C3_width_after"], "scale", r["scale_summary"])
        for p in ("before", "after"):
            print("   ", p, {x: r[p][x] for x in ("retention", "median_error_deg", "distinct_end_positions", "median_fwhm")})
        print("    cv by epoch", [round(v, 3) for v in r["activity_cv_by_epoch"]])


if __name__ == "__main__":
    main()
