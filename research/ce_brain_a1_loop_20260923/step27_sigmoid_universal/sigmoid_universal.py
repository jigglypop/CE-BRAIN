"""A1 step 27: does ONE operating point (b, g) give the literature bump width in all three individuals? (CONTRACT.md)

Literature model class (connectome-constrained HD models): tau x' = -x + sigma(w0 * W_raw x + b + u), sigma logistic,
W_raw = signed synapse counts (Delta7 and rule-chosen inhibitory types negative). Homeostatic bias: every neuron sits
at the same tonic level sigma(beta) (b_i = beta - w0 (W_raw x*)_i, x* = sigma(beta)); the linearisation is then
w0 sigma'(beta) W_raw and the gain is set relative to the memory mode: w0 = g / (lambda1_raw * sigma'(beta)).

python sigmoid_universal.py              full run; refuses unless CONTRACT.md lists this code hash
python sigmoid_universal.py --synthetic  pipeline on the synthetic network (pre-freeze, writes nothing)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s25 = load("width_law", LOOP / "step25_width_law/width_law.py")
wc, gi, lf, iso = s25.wc, s25.gi, s25.lf, s25.iso
B_GRID = (-3.0, -2.0, -1.0, 0.0)
G_GRID = (1.05, 1.2, 1.5, 2.0, 3.0, 4.0)
DT, T_CUE, T_FREE = 0.1, 20.0, 150.0
LIT = (80.0, 120.0)
U_SET = (-0.1, -0.05, 0.05, 0.1)
MIN_MOVE_DEG_PER_100TAU = 5.0


def sig(z):
    return 1.0 / (1.0 + np.exp(-z))


def raw_network(A, ty, inst, sd, nt):
    chosen, members = gi.select(A, ty, nt)
    base = [v for v in range(len(ty)) if ty[v] in gi.BASE]
    nodes = np.array(sorted(base + [v for t in chosen for v in members[t]]))
    kind = [ty[v] for v in nodes]
    w = A[nodes, :][:, nodes].toarray().T
    sign = np.array([-1.0 if (k == "Delta7" or k in chosen) else 1.0 for k in kind])
    Wraw = w * sign[None, :]
    _, epg, ang, basis, _ = s25.build(A, ty, inst, nt)
    gamma = np.array([(1.0 if sd[v] == "left" else -1.0 if sd[v] == "right" else 0.0) if ty[v].startswith("PEN") else 0.0 for v in nodes])
    return Wraw, epg, ang, basis, gamma


def lambda1(W, epg, ang):
    lam, left, right = eig(W, left=True, right=True)
    p = iso.harmonic_pair(lam, left, right, epg, ang, 1)
    return None if p is None else float(np.mean(p[0]["lambda"]))


def width_of(x, epg, ang):
    bins = np.mod(np.round(ang / np.radians(22.5)).astype(int), 16)
    prof = np.array([x[epg][bins == b].mean() if np.any(bins == b) else np.nan for b in range(16)])
    ok = ~np.isnan(prof)
    p = prof[ok] - np.nanmin(prof)
    if p.max() <= 1e-9:
        return None, 0, 0.0
    peaks = int(np.sum((p > np.roll(p, 1)) & (p >= np.roll(p, -1)) & (p > 0.5 * p.max())))
    contrast = float(p.max() / max(np.nanmax(prof), 1e-12))
    return wc.fwhm_profile(p, np.radians(22.5) * np.arange(16)[ok]), peaks, contrast


def run_one(W, epg, ang, b, w0, gamma=None, u=0.0, cue_deg=0.0):
    n = W.shape[0]
    x = np.full(n, sig(b))
    bias = b - w0 * (W @ x)
    cue = np.zeros(n)
    cue[epg] = 3.0 * np.maximum(np.cos(ang - np.radians(cue_deg)), 0)
    drive = np.zeros(n) if gamma is None else u * gamma
    phases = []
    steps_c, steps_f = int(T_CUE / DT), int(T_FREE / DT)
    for s in range(steps_c + steps_f):
        inp = w0 * (W @ x) + bias + drive + (cue if s < steps_c else 0.0)
        x = x + DT * (-x + sig(inp))
        if s >= steps_c and (s - steps_c) % int(5 / DT) == 0:
            e = x[epg] - x[epg].min()
            phases.append(np.angle(np.sum(e * np.exp(1j * ang))))
    width, peaks, contrast = width_of(x, epg, ang)
    ph = np.unwrap(phases)
    t = np.arange(len(ph)) * 5.0
    late = t >= 50.0
    vel = float(np.polyfit(t[late], ph[late], 1)[0]) if late.sum() > 2 else 0.0
    drift = float(np.degrees(abs(ph[-1] - ph[np.argmax(late)]))) if late.any() else 0.0
    persistent = width is not None and peaks == 1 and contrast >= 0.3 and width < 300
    return {"fwhm": width, "peaks": peaks, "contrast": contrast, "drift_deg": drift, "velocity": vel, "persistent": bool(persistent)}


def scan(W, epg, ang, gamma):
    lam1 = lambda1(W, epg, ang)
    table = []
    for b in B_GRID:
        slope = sig(b) * (1 - sig(b))
        for g in G_GRID:
            w0 = g / (lam1 * slope)
            r = run_one(W, epg, ang, b, w0)
            r.update({"b": b, "g": g, "in_literature": bool(r["persistent"] and r["drift_deg"] <= 45 and LIT[0] <= r["fwhm"] <= LIT[1])})
            table.append(r)
    return lam1, table


def drive_test(W, epg, ang, gamma, lam1, b, g):
    w0 = g / (lam1 * sig(b) * (1 - sig(b)))
    base = run_one(W, epg, ang, b, w0)
    runs = [dict(run_one(W, epg, ang, b, w0, gamma, u), u=u) for u in U_SET]
    good = [r for r in runs if r["persistent"]]
    inv = len(good) == len(U_SET) and all(abs(r["fwhm"] - base["fwhm"]) <= 10 for r in good)
    lin = False
    if len(good) == len(U_SET):
        us, vs = np.array([r["u"] for r in good]), np.array([r["velocity"] for r in good])
        k = float(us @ vs / (us @ us))
        r2 = float(1 - np.sum((vs - k * us) ** 2) / np.sum((vs - vs.mean()) ** 2)) if np.ptp(vs) > 0 else 0.0
        anti = all(abs(a["velocity"] + c["velocity"]) <= 0.25 * np.mean(np.abs(vs)) for a in good for c in good if abs(a["u"] + c["u"]) < 1e-12 and a["u"] > 0)
        moves = abs(k) * max(abs(u) for u in U_SET) >= np.radians(MIN_MOVE_DEG_PER_100TAU) / 100.0
        lin = bool(r2 >= 0.95 and anti and moves)
    return {"base": base, "runs": runs, "width_invariant": bool(inv), "linear_integration": bool(lin)}


def main():
    if "--synthetic" in sys.argv:
        syn = load("syn", LOOP / "step26_tonic_reduced/synthetic_net.py")
        W, epg, ang, gamma = syn.network()
        lam1, table = scan(W, epg, ang, gamma)
        print("lambda1", lam1)
        for r in table:
            print(r["b"], r["g"], r["fwhm"], r["peaks"], round(r["contrast"], 2), round(r["drift_deg"], 1), r["persistent"], r["in_literature"])
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    nets = {}
    A, ty, sd, nt = gi.malecns()
    nets["malecns"] = raw_network(A, ty, s25.malecns()[2], sd, nt)
    A, ty, sd, nt = gi.flywire()
    nets["flywire"] = raw_network(A, ty, None, sd, nt)
    A, ty, inst, sd, nt = h22.hemibrain()
    nets["hemibrain"] = raw_network(A, ty, inst, sd, nt)
    res = {}
    for name, (W, epg, ang, basis, gamma) in nets.items():
        lam1, table = scan(W, epg, ang, gamma)
        res[name] = {"basis": basis, "lambda1_raw": lam1, "table": table}
    ok_sets = {name: {(r["b"], r["g"]) for r in d["table"] if r["in_literature"]} for name, d in res.items()}
    common = sorted(set.intersection(*ok_sets.values()))
    U1 = bool(common)
    drive = {}
    if common:
        b, g = common[len(common) // 2]
        for name, (W, epg, ang, basis, gamma) in nets.items():
            drive[name] = drive_test(W, epg, ang, gamma, res[name]["lambda1_raw"], b, g)
    U2 = bool(drive) and all(d["width_invariant"] for d in drive.values())
    U3 = bool(drive) and all(d["linear_integration"] for d in drive.values())
    result = {"schema": "ce-a1-step27-sigmoid-universal", "code_sha256": code_hash,
              "U1_common_operating_point": U1, "common_points": common, "U2_width_invariant": U2, "U3_linear_integration": U3,
              "verdict": "UNIVERSAL_OPERATING_POINT_SUPPORTED" if U1 and U2 and U3 else
                         ("UNIVERSAL_WIDTH_ONLY" if U1 else "NO_UNIVERSAL_OPERATING_POINT"),
              "per_dataset_literature_points": {k: sorted(v) for k, v in ok_sets.items()}, "datasets": res, "drive": drive}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], "common", common)
    for k, v in ok_sets.items():
        print(k, "lambda1_raw %.1f" % res[k]["lambda1_raw"], "lit points", sorted(v))
        print("   ", [(r["b"], r["g"], r["fwhm"], r["persistent"]) for r in res[k]["table"]])
    for k, d in drive.items():
        print("drive", k, "inv", d["width_invariant"], "lin", d["linear_integration"],
              [(r["u"], r["fwhm"], round(r["velocity"], 4), r["persistent"]) for r in d["runs"]], "base", d["base"]["fwhm"])


if __name__ == "__main__":
    main()
