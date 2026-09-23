"""A1 step 26: tonic-drive A1 + threshold on EPG -- width, width invariance and linear integration vs literature (CONTRACT.md).

tau x_E' = -x_E + [K(g, u) x_E + 1]_+ ; other populations linear around a tonic operating point (eliminated).
g is the only parameter, fixed per individual by the literature width (~100 deg); width invariance under PEN
drive and linear angular integration are then parameter-free checks.

python tonic_ring.py            full run; refuses unless CONTRACT.md lists this code hash
python tonic_ring.py --synthetic   same pipeline on the synthetic network (pre-freeze check, writes nothing)
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


tc = load("tonic_core", HERE / "tonic_core.py")
s25 = load("width_law", LOOP / "step25_width_law/width_law.py")
wc, gi, lf = s25.wc, s25.gi, s25.lf
I0 = 1.0
G_POINTS = 40
U_SET = (-0.1, -0.05, -0.02, 0.02, 0.05, 0.1)
LIT = (80.0, 120.0)


def build_with_side(A, ty, inst, sd, nt):
    W, epg, ang, basis, chosen = s25.build(A, ty, inst, nt)
    chosen_set, members = gi.select(A, ty, nt)
    base = [v for v in range(len(ty)) if ty[v] in gi.BASE]
    nodes = np.array(sorted(base + [v for t in chosen_set for v in members[t]]))
    kind = [ty[v] for v in nodes]
    gamma = np.array([(1.0 if sd[v] == "left" else -1.0 if sd[v] == "right" else 0.0) if ty[v].startswith("PEN") else 0.0 for v in nodes])
    return W, epg, ang, basis, gamma


def valid(r, ang):
    if r is None:
        return False, None, 0
    w, pk = tc.profile_fwhm(r["x"], ang, wc.fwhm_profile)
    ok = w is not None and pk == 1 and r["R_bump"] >= 0.3 and w < 300 and r["max"] > 1e-3
    return ok, w, pk


def analyse(W, epg, ang, gamma):
    rest = np.setdiff1d(np.arange(W.shape[0]), epg)
    rho = float(np.max(np.real(np.linalg.eigvals(W[np.ix_(rest, rest)]))))
    g_max = 0.99 / rho if rho > 0 else 10.0
    grid = np.linspace(g_max / G_POINTS, g_max, G_POINTS)
    scan = []
    for g in grid:
        K = tc.reduced_kernel(W, epg, g)
        r = None if K is None else tc.simulate(K, ang, I0)
        ok, w, pk = valid(r, ang)
        scan.append({"g": float(g), "valid": bool(ok), "fwhm": w, "peaks": pk, "R_bump": None if r is None else r["R_bump"]})
    cands = [s for s in scan if s["valid"] and LIT[0] <= s["fwhm"] <= LIT[1]]
    out = {"rest_spectral_abscissa": rho, "g_max": g_max, "scan": scan, "D1_width_reachable": bool(cands)}
    if not cands:
        out.update({"D2_width_invariant": False, "D3_linear_integration": False})
        return out
    best = min(cands, key=lambda s: abs(s["fwhm"] - 100.0))
    g = best["g"]
    runs = []
    for u in U_SET:
        K = tc.reduced_kernel(W, epg, g, gamma, u)
        r = None if K is None else tc.simulate(K, ang, I0)
        ok, w, pk = valid(r, ang)
        runs.append({"u": u, "valid": bool(ok), "fwhm": w, "velocity": None if r is None else r["velocity_rad_per_tau"]})
    good = [x for x in runs if x["valid"]]
    d2 = len(good) >= 4 and all(abs(x["fwhm"] - best["fwhm"]) <= 10 for x in good)
    d3 = False
    if len(good) >= 4:
        us = np.array([x["u"] for x in good])
        vs = np.array([x["velocity"] for x in good])
        k = float(us @ vs / (us @ us))
        r2 = float(1 - np.sum((vs - k * us) ** 2) / np.sum((vs - vs.mean()) ** 2)) if np.ptp(vs) > 0 else 0.0
        pairs = [(x["velocity"], y["velocity"]) for x in good for y in good if abs(x["u"] + y["u"]) < 1e-12 and x["u"] > 0]
        anti = bool(pairs) and all(abs(a + b) <= 0.25 * np.mean(np.abs(vs)) for a, b in pairs)
        d3 = bool(r2 >= 0.95 and anti and abs(k) > 0)
        out["integration"] = {"gain_rad_per_tau_per_u": k, "R2": r2, "antisymmetric": anti}
    out.update({"g_star": g, "fwhm_at_g_star": best["fwhm"], "drive_runs": runs,
                "D2_width_invariant": bool(d2), "D3_linear_integration": bool(d3)})
    return out


def synthetic():
    syn = load("syn", HERE / "synthetic_net.py")
    W, epg, ang, gamma = syn.network()
    return analyse(W, epg, ang, gamma)


def main():
    if "--synthetic" in sys.argv:
        res = synthetic()
        print(json.dumps({k: v for k, v in res.items() if k != "scan"}, indent=1, default=float))
        print("scan", [(round(s["g"], 3), s["fwhm"], s["valid"]) for s in res["scan"]])
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    res = {}
    A, ty, sd, nt = gi.malecns()
    inst = s25.malecns()[2]
    res["malecns"] = analyse(*build_with_side(A, ty, inst, sd, nt)[:3], build_with_side(A, ty, inst, sd, nt)[4])
    A, ty, sd, nt = gi.flywire()
    b = build_with_side(A, ty, None, sd, nt)
    res["flywire"] = analyse(b[0], b[1], b[2], b[4])
    A, ty, inst, sd, nt = h22.hemibrain()
    b = build_with_side(A, ty, inst, sd, nt)
    res["hemibrain"] = analyse(b[0], b[1], b[2], b[4])
    ok = all(d["D1_width_reachable"] and d["D2_width_invariant"] and d["D3_linear_integration"] for d in res.values())
    result = {"schema": "ce-a1-step26-tonic-reduced-ring", "code_sha256": code_hash, "I0": I0,
              "verdict": "TONIC_RING_MATCHES_LITERATURE_THREE_INDIVIDUALS" if ok else "TONIC_RING_NOT_MATCHED", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"])
    for n, d in res.items():
        print("==", n, "D1", d["D1_width_reachable"], "D2", d["D2_width_invariant"], "D3", d["D3_linear_integration"],
              "g*", d.get("g_star"), "fwhm", d.get("fwhm_at_g_star"), "integ", d.get("integration"))
        print("   scan", [(round(s["g"], 3), s["fwhm"], s["valid"]) for s in d["scan"]])
        if "drive_runs" in d:
            print("   drive", [(x["u"], x["fwhm"], None if x["velocity"] is None else round(x["velocity"], 4), x["valid"]) for x in d["drive_runs"]])


if __name__ == "__main__":
    main()
