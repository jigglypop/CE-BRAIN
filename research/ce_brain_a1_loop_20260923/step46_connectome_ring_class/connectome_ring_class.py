"""A1 step 46: is the fly's EPG recurrent structure a Kim 'local' ring? (CONTRACT.md)

Kernel from the connectome (MaleCNS, hemibrain, FlyWire; same node set as steps 27/33): flow-normalised synapse
counts over 16 angular-offset bins, excitation = EPG->EPG + EPG->PEN_a/PEN_b/PEG->EPG, inhibition = EPG->Delta7->EPG +
EPG->(step 2c ring/ExR types)->EPG; two-step flow via X = C(X->EPG) diag(1/whole-brain input of X) C(EPG->X).
Ring (step 41/42 form, 16 units, threshold-linear, c = 1): W_ij = g K((i-j) 22.5 deg); the single free gain g is set
by the step 42 calibration rule (few-neuron optimum: hold error <= 2 deg, <= 5 active, smallest hold error).
Tests: the step 42 battery (C1, R1, S1, S2 in bump-amplitude units, S3). Controls: inhibition replaced by the Delta7
pathway only or by the ring/ExR pathway only (same total).

python connectome_ring_class.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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
S41, S42 = LOOP / "step41_few_neuron_attractor", LOOP / "step42_kim_support_ring"
sys.path.insert(0, str(S41))
import tl_ring as tl  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


f41 = load("few_neuron_ring", S41 / "few_neuron_ring.py")
k42 = load("kim_support_ring", S42 / "kim_support_ring.py")
su = load("sigmoid_universal", LOOP / "step27_sigmoid_universal/sigmoid_universal.py")
h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
gi = su.gi
N = 16
G_GRID = np.round(np.geomspace(0.002, 0.2, 121), 6)
HOLD_POS = (0.0, 2.8125, 5.625, 8.4375, 11.25, 14.0625, 16.875, 19.6875)


def profile(M, ang):
    off = (np.degrees(ang)[:, None] - np.degrees(ang)[None, :]) % 360
    b = np.round(off / 22.5).astype(int) % N
    return np.array([M[b == k].mean() for k in range(N)])


def kernels(A, ty, inst, sd, nt):
    chosen, members = gi.select(A, ty, nt)
    base = [v for v in range(len(ty)) if ty[v] in gi.BASE]
    nodes = np.array(sorted(base + [v for t in chosen for v in members[t]]))
    kind = np.array([ty[v] for v in nodes])
    Wraw, epg, ang, basis, gamma = su.raw_network(A, ty, inst, sd, nt)
    C = np.abs(Wraw)
    tot_in = np.asarray(A.sum(axis=0)).ravel()[nodes]
    E = epg
    flow = lambda types: (lambda X: C[np.ix_(E, X)] @ np.diag(1 / np.maximum(tot_in[X], 1)) @ C[np.ix_(X, E)])(np.flatnonzero(np.isin(kind, types)))
    exc = C[np.ix_(E, E)] + flow(["PEN_a(PEN1)"]) + flow(["PEN_b(PEN2)"]) + flow(["PEG"])
    d7, flat = flow(["Delta7"]), flow(sorted(chosen))
    P = {"exc": profile(exc, ang), "inh_d7": profile(d7, ang), "inh_flat": profile(flat, ang)}
    P["inh_all"] = P["inh_d7"] + P["inh_flat"]
    info = {"n_epg": int(len(E)), "angle_basis": basis, "chosen_types": sorted(chosen),
            "rowsum": {"exc": float(exc.sum(1).mean()), "inh_d7": float(d7.sum(1).mean()), "inh_flat": float(flat.sum(1).mean())}}
    return P, info


def harm(p):
    F = np.fft.rfft(p)
    return float(2 * np.abs(F[1]) / abs(F[0].real))


def symmetrise(kernel):
    """A1: the symmetric coupling L_g is the attractor part; the antisymmetric part belongs to the shift operators S_k."""
    return (kernel + kernel[(-np.arange(N)) % N]) / 2


def ring(kernel, g):
    idx = (np.arange(N)[:, None] - np.arange(N)[None, :]) % N
    return g * kernel[idx]


def hold(W, positions=HOLD_POS):
    errs, nacts = [], []
    for p in positions:
        r, _, blow = tl.run(W, 1.0, [(20.0, tl.cue(p), 0.0), (100.0, 0.0, 0.0)])
        if blow:
            return None
        errs.append(float(tl.wrapd(tl.com(r) - p)))
        nacts.append(int(np.sum(r > 1e-6)))
    return errs, nacts


FWHM_TARGET = (82.3 + 90.9) / 2        # Seelig & Jayaraman 2015 calcium bump FWHM (single stripe / darkness)


def calibrate(kernel):
    """Coarse scan of g, then bisection of every sign change of the drift from a quarter-lattice start (5.625 deg)
    inside bump regimes (2..12 active); keep optima with max hold error <= 2 deg; choose the one whose natural bump
    FWHM is closest to the literature calcium FWHM."""
    rows = []
    for g in G_GRID:
        h = hold(ring(kernel, g), (5.625,))
        if h is None:
            break
        rows.append((float(g), h[0][0], h[1][0]))
    optima = []
    for (g0, d0, n0), (g1, d1, n1) in zip(rows, rows[1:]):
        if not (2 <= n0 <= 12 and 2 <= n1 <= 12) or np.sign(d0) == np.sign(d1) or abs(d0) > 11.3 or abs(d1) > 11.3:
            continue
        lo, hi, dlo = g0, g1, d0
        for _ in range(40):
            mid = (lo + hi) / 2
            h = hold(ring(kernel, mid), (5.625,))
            if h is None:
                hi = mid
                continue
            if np.sign(h[0][0]) == np.sign(dlo):
                lo, dlo = mid, h[0][0]
            else:
                hi = mid
        g = (lo + hi) / 2
        h = hold(ring(kernel, g))
        if h is not None:
            amp0, shp, n_act = f41.natural_amp(ring(kernel, g))
            optima.append({"g": g, "max_hold_err": max(abs(e) for e in h[0]), "n_act_max": max(h[1]), "n_act_min": min(h[1]),
                           "fwhm": shp[0], "amp": amp0})
    ok = [o for o in optima if o["max_hold_err"] <= 2.0 and o["fwhm"] is not None]
    best = min(ok, key=lambda o: abs(o["fwhm"] - FWHM_TARGET)) if ok else None
    return best, {"coarse": rows, "optima": optima}


def battery(W):
    A = tl.generator(W)
    amp0, shp, n_act = f41.natural_amp(W)
    res = {"dark_bump": {"amp": amp0, "fwhm": shp[0], "peaks": shp[1], "n_active": n_act},
           "continuity": f41.continuity(W, amp0), "rotation": f41.rotation(W, A, amp0), "two_cue": f41.two_cue(W, amp0),
           "jump": k42.jump_thresholds(W, amp0), "suppression": k42.suppression(W, amp0)}
    res["criteria"] = {"C1": res["continuity"]["C1"], "R1": res["rotation"]["R1"], "S1": res["two_cue"]["S1"], "S2": res["jump"]["S2"],
                       "S3_secondary": res["suppression"]["S3"]}
    return res


def datasets():
    out = {}
    A, ty, sd, nt = gi.malecns()
    out["malecns"] = (A, ty, su.s25.malecns()[2], sd, nt)
    A, ty, inst, sd, nt = h22.hemibrain()
    out["hemibrain"] = (A, ty, inst, sd, nt)
    A, ty, sd, nt = gi.flywire()
    out["flywire"] = (A, ty, None, sd, nt)
    return out


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), S41 / "tl_ring.py", S41 / "few_neuron_ring.py", S42 / "kim_support_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [n for n, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    res = {}
    for name, data in datasets().items():
        P, info = kernels(*data)
        tot = P["inh_all"].sum()
        raw = P["exc"] - P["inh_all"]
        anti = (raw - raw[(-np.arange(N)) % N]) / 2
        variants = {"connectome": symmetrise(raw),
                    "control_delta7_only": symmetrise(P["exc"] - P["inh_d7"] * tot / P["inh_d7"].sum()),
                    "control_flat_only": symmetrise(P["exc"] - P["inh_flat"] * tot / P["inh_flat"].sum())}
        d = {"info": info, "profiles": {k: v.tolist() for k, v in P.items()},
             "report_antisymmetric_fraction": float(np.linalg.norm(anti) / np.linalg.norm(raw)),
             "inhibition_H1_over_H0": {k: harm(P[k]) for k in ("inh_all", "inh_d7", "inh_flat")}, "variants": {}}
        for vname, K in variants.items():
            best, cal = calibrate(K)
            entry = {"calibration": cal, "g_star": None if best is None else best["g"]}
            if best is not None:
                entry["optimum"] = best
                entry.update(battery(ring(K, best["g"])))
            d["variants"][vname] = entry
            print("==", name, vname, "g*", entry["g_star"], json.dumps(entry.get("criteria"), default=float),
                  "S2", json.dumps(entry.get("jump", {}).get("thresholds_x_amp"), default=float), entry.get("jump", {}).get("ratio_180_over_90"),
                  "bump", json.dumps(entry.get("dark_bump"), default=float), flush=True)
        res[name] = d
    def passes(d):
        v = d["variants"]["connectome"]
        return bool(d["inhibition_H1_over_H0"]["inh_all"] < 0.5 and v.get("criteria") is not None
                    and all(v["criteria"][k] for k in ("C1", "R1", "S1")))
    main_ok = {n: passes(d) for n, d in res.items()}
    s2_pred = {n: (d["variants"]["connectome"].get("jump", {}).get("ratio_180_over_90")) for n, d in res.items()}
    result = {"schema": "ce-a1-step46-connectome-ring-class", "hashes": hashes, "per_dataset_pass": main_ok,
              "report_S2_ratio_predicted_above_1p25": {n: (None if r is None else bool(r > 1.25)) for n, r in s2_pred.items()},
              "verdict": "CONNECTOME_RING_LOCAL_CLASS_CONTINUOUS" if all(main_ok.values()) else "CONNECTOME_RING_NOT_SHOWN_LOCAL_CONTINUOUS",
              "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], main_ok)


if __name__ == "__main__":
    main()
