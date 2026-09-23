"""A1 step 28: is bump pinning caused by neuron-level weight heterogeneity? (CONTRACT.md)

Step-27 model at the common operating point (beta=-1, g=1.5). W_h = (1-h) W_raw + h W_avg, where W_avg averages
weights over neuron pairs within the same (group, group) block; groups = instance (type + PB glomerulus + side) for
the five head-direction types and type + side for the inhibitory set. If heterogeneity causes pinning, linear
integration must appear at h = 1 while the literature width is kept.
Drive is multiplicative PEN gain modulation, W(u) = W + u * Gamma * W (the A1 generator S = u Gamma W of steps
23-24); step 27 used an additive drive, which cannot rotate a bump in the near-linear sigmoid regime.

python pinning.py              full run; refuses unless CONTRACT.md lists this code hash
python pinning.py --synthetic  noisy synthetic ring (pre-freeze check, writes nothing)
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


su = load("sigmoid_universal", LOOP / "step27_sigmoid_universal/sigmoid_universal.py")
BETA, G = -1.0, 1.5
H_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
U_SET = (-0.5, -0.3, -0.2, -0.1, 0.1, 0.2, 0.3, 0.5)
R2_MIN = 0.9
LIT = su.LIT


def group_average(W, groups):
    keys = sorted(set(groups))
    idx = np.array([keys.index(g) for g in groups])
    P = np.zeros((len(groups), len(keys)))
    P[np.arange(len(groups)), idx] = 1.0
    sizes = P.sum(axis=0)
    block = (P.T @ W @ P) / np.outer(sizes, sizes)
    return P @ block @ P.T


def run_mult(W, epg, ang, b, w0, gamma=None, u=0.0):
    """Step-27 run with multiplicative PEN gain drive: input = w0 (W + u Gamma W) x + bias."""
    n = W.shape[0]
    x = np.full(n, su.sig(b))
    bias = b - w0 * (W @ x)
    Wu = W if gamma is None or u == 0 else W + u * gamma[:, None] * W
    cue = np.zeros(n)
    cue[epg] = 3.0 * np.maximum(np.cos(ang), 0)
    phases = []
    steps_c, steps_f = int(su.T_CUE / su.DT), int(su.T_FREE / su.DT)
    for s in range(steps_c + steps_f):
        x = x + su.DT * (-x + su.sig(w0 * (Wu @ x) + bias + (cue if s < steps_c else 0.0)))
        if s >= steps_c and (s - steps_c) % int(5 / su.DT) == 0:
            e = x[epg] - x[epg].min()
            phases.append(np.angle(np.sum(e * np.exp(1j * ang))))
    width, peaks, contrast = su.width_of(x, epg, ang)
    ph = np.unwrap(phases)
    t = np.arange(len(ph)) * 5.0
    late = t >= 50.0
    vel = float(np.polyfit(t[late], ph[late], 1)[0]) if late.sum() > 2 else 0.0
    persistent = width is not None and peaks == 1 and contrast >= 0.3 and width < 300
    return {"fwhm": width, "velocity": vel, "persistent": bool(persistent)}


def integration(W, epg, ang, gamma):
    lam1 = su.lambda1(W, epg, ang)
    if lam1 is None or lam1 <= 0:
        return {"lambda1": lam1, "ok": False}
    w0 = G / (lam1 * su.sig(BETA) * (1 - su.sig(BETA)))
    base = run_mult(W, epg, ang, BETA, w0)
    runs = [dict(run_mult(W, epg, ang, BETA, w0, gamma, u), u=u) for u in U_SET]
    good = [r for r in runs if r["persistent"]]
    inv = base["persistent"] and len(good) == len(U_SET) and all(abs(r["fwhm"] - base["fwhm"]) <= 10 for r in good)
    lin = False
    if len(good) == len(U_SET):
        us, vs = np.array([r["u"] for r in good]), np.array([r["velocity"] for r in good])
        k = float(us @ vs / (us @ us))
        r2 = float(1 - np.sum((vs - k * us) ** 2) / np.sum((vs - vs.mean()) ** 2)) if np.ptp(vs) > 0 else 0.0
        anti = all(abs(a["velocity"] + c["velocity"]) <= 0.25 * np.mean(np.abs(vs)) for a in good for c in good
                   if abs(a["u"] + c["u"]) < 1e-12 and a["u"] > 0)
        moves = abs(k) * max(abs(u) for u in U_SET) >= np.radians(su.MIN_MOVE_DEG_PER_100TAU) / 100.0
        lin = bool(r2 >= R2_MIN and anti and moves)
    return {"lambda1": lam1, "width": base["fwhm"], "width_ok": bool(base["persistent"] and base["fwhm"] is not None
                                                                     and LIT[0] <= base["fwhm"] <= LIT[1]),
            "width_invariant": bool(inv), "linear_integration": lin,
            "velocities_deg_per_100tau": {str(r["u"]): float(np.degrees(r["velocity"]) * 100) for r in runs},
            "pinning_threshold_u": next((abs(r["u"]) for r in sorted(runs, key=lambda r: abs(r["u"])) if r["u"] > 0 and
                                         all(abs(np.degrees(q["velocity"]) * 100) >= su.MIN_MOVE_DEG_PER_100TAU and q["persistent"]
                                             for q in runs if abs(abs(q["u"]) - r["u"]) < 1e-12)
                                         and np.prod([q["velocity"] for q in runs if abs(abs(q["u"]) - r["u"]) < 1e-12]) < 0), None),
            "ok": True}


def labelled_groups(kind, inst, chosen):
    out = []
    for k, s in zip(kind, inst):
        if k in chosen:
            side = "L" if s.endswith("_L") else "R" if s.endswith("_R") else ""
            out.append(f"{k}|{side}")
        else:
            out.append(s or k)
    return out


def network_with_groups(A, ty, inst, sd, nt, theta_groups=False):
    W, epg, ang, basis, gamma = su.raw_network(A, ty, inst, sd, nt)
    chosen, members = su.gi.select(A, ty, nt)
    base = [v for v in range(len(ty)) if ty[v] in su.gi.BASE]
    nodes = np.array(sorted(base + [v for t in chosen for v in members[t]]))
    kind = [ty[v] for v in nodes]
    if not theta_groups:
        groups = labelled_groups(kind, [inst[v] for v in nodes], set(chosen))
    else:
        # FlyWire: label-free groups -- EPG by theta bin, other base types by input-phase bin, + side
        bnodes = np.array(sorted(base))
        kb = [ty[v] for v in bnodes]
        Wb = su.lf.operator(A[bnodes, :][:, bnodes].toarray().T, kb)
        eb = np.array([i for i, k in enumerate(kb) if k == "EPG"])
        _, theta, B, _ = su.lf.ring_pair(Wb, eb)
        z = B[:, 0] + 1j * B[:, 1]
        phase = {int(bnodes[i]): float(np.angle(z[i])) for i in range(len(bnodes))}
        groups = []
        for v in nodes:
            if ty[v] in chosen:
                groups.append(f"{ty[v]}|{sd[v]}")
            else:
                groups.append(f"{ty[v]}|{sd[v]}|{int(np.mod(np.round(phase[int(v)] / np.radians(22.5)), 16))}")
    return W, epg, ang, basis, gamma, groups


def analyse(W, epg, ang, gamma, groups):
    Wavg = group_average(W, groups)
    rows = []
    for h in H_GRID:
        r = integration((1 - h) * W + h * Wavg, epg, ang, gamma)
        r["h"] = h
        rows.append(r)
    full = rows[-1]
    return {"n_groups": len(set(groups)), "rows": rows,
            "P1_linear_at_h1": bool(full.get("linear_integration")), "P3_width_at_h1": bool(full.get("width_ok"))}


def synthetic():
    """Synthetic ring with 3 neurons per angle per population and multiplicative log-normal weight noise."""
    N, rep = 16, 3
    ang16 = np.arange(N) * 2 * np.pi / N
    angE = np.repeat(ang16, rep)
    K = lambda a, b, s=0.0, k=3.0: np.exp(k * np.cos(a[:, None] - b[None, :] - s))
    pops = {"E": angE, "L": angE, "R": angE, "D": angE}
    order = ["E", "L", "R", "D"]
    n = 4 * N * rep + 1
    sl = {p: np.arange(i * N * rep, (i + 1) * N * rep) for i, p in enumerate(order)}
    G = np.array([n - 1])
    w = np.zeros((n, n))
    w[np.ix_(sl["E"], sl["E"])] = K(angE, angE)
    w[np.ix_(sl["L"], sl["E"])] = K(angE, angE, 0, 4); w[np.ix_(sl["R"], sl["E"])] = K(angE, angE, 0, 4)
    w[np.ix_(sl["E"], sl["L"])] = 0.5 * K(angE, angE, np.radians(55), 4)
    w[np.ix_(sl["E"], sl["R"])] = 0.5 * K(angE, angE, -np.radians(55), 4)
    w[np.ix_(sl["D"], sl["E"])] = K(angE, angE, 0, 1); w[np.ix_(sl["E"], sl["D"])] = -0.3 * K(angE, angE, np.pi, 1)
    w[np.ix_(G, sl["E"])] = 1.0; w[np.ix_(sl["E"], G)] = -2.0 * K(angE, angE).sum(1)[:, None]
    W = w / np.abs(w).sum(1, keepdims=True).clip(1e-12) * 100.0
    rng = np.random.default_rng(3)
    Wn = W * np.exp(0.4 * rng.normal(size=W.shape))
    gamma = np.zeros(n); gamma[sl["L"]] = 1; gamma[sl["R"]] = -1
    groups = [f"{p}|{i % (N * rep) // rep}" for p in order for i in range(N * rep)] + ["G"]
    return {"noise_free": analyse(W, sl["E"], angE, gamma, groups), "noisy": analyse(Wn, sl["E"], angE, gamma, groups)}


def main():
    if "--synthetic" in sys.argv:
        for key, res in synthetic().items():
            print("==", key)
            for r in res["rows"]:
                print("  h", r["h"], "width", r.get("width"), "lin", r.get("linear_integration"), "inv", r.get("width_invariant"), "thr", r.get("pinning_threshold_u"),
                      {k: round(v, 2) for k, v in r.get("velocities_deg_per_100tau", {}).items()})
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    res = {}
    A, ty, sd, nt = su.gi.malecns()
    res["malecns"] = analyse(*network_with_groups(A, ty, su.s25.malecns()[2], sd, nt)[0:3], network_with_groups(A, ty, su.s25.malecns()[2], sd, nt)[4],
                             network_with_groups(A, ty, su.s25.malecns()[2], sd, nt)[5])
    A, ty, inst, sd, nt = h22.hemibrain()
    net = network_with_groups(A, ty, inst, sd, nt)
    res["hemibrain"] = analyse(net[0], net[1], net[2], net[4], net[5])
    A, ty, sd, nt = su.gi.flywire()
    net = network_with_groups(A, ty, None, sd, nt, theta_groups=True)
    res["flywire_report"] = analyse(net[0], net[1], net[2], net[4], net[5])
    primary = ("malecns", "hemibrain")
    ok = all(res[k]["P1_linear_at_h1"] and res[k]["P3_width_at_h1"] for k in primary)
    result = {"schema": "ce-a1-step28-pinning-origin", "code_sha256": code_hash, "beta": BETA, "g": G,
              "verdict": "HETEROGENEITY_CAUSES_PINNING" if ok else "HETEROGENEITY_NOT_SUFFICIENT", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"])
    for n, d in res.items():
        print("==", n, "groups", d["n_groups"], "P1", d["P1_linear_at_h1"], "P3", d["P3_width_at_h1"])
        for r in d["rows"]:
            print("   h", r["h"], "width", r.get("width"), "lin", r.get("linear_integration"), "inv", r.get("width_invariant"), "thr", r.get("pinning_threshold_u"),
                  {k: round(v, 1) for k, v in r.get("velocities_deg_per_100tau", {}).items()})


if __name__ == "__main__":
    main()
