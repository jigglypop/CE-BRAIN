"""A1 step 33: selection -- does the universal operating-point model reproduce the ring's winner-take-all rules? (CONTRACT.md)

Model: step 27 (sigmoid, homeostatic tonic level beta=-1, g=1.5, signed synapse counts, expanded network).
Literature (Kim et al. 2017 Science): a single bump; two simultaneous sites -> one wins; the input needed to make the
bump jump to a narrow (22.5 deg) site is not different for 90 vs 180 deg shifts (local-model signature).

python selection.py              full run; refuses unless CONTRACT.md lists this code hash
python selection.py --synthetic  pipeline on the synthetic ring (pre-freeze, writes nothing)
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
BETA, G = -1.0, 1.05  # near-critical: at g=1.5 the saturated bump cannot be out-competed (controls)
DT, T_EST, T_STIM, T_FREE = 0.1, 70.0, 20.0, 50.0
SHIFTS = (45.0, 90.0, 135.0, 180.0)
A_MAX, BISECT = 30.0, 12
WEDGE = 11.25


def wrapd(a):
    return (a + 180.0) % 360.0 - 180.0


def centre_deg(x, epg, ang):
    e = x[epg] - x[epg].min()
    return float(np.degrees(np.angle(np.sum(e * np.exp(1j * ang)))))


def simulate(W, epg, ang, w0, bias, phases):
    """phases: list of (duration, input vector or None)."""
    x = np.full(W.shape[0], su.sig(BETA))
    for dur, inp in phases:
        for _ in range(int(dur / DT)):
            drive = w0 * (W @ x) + bias + (0.0 if inp is None else inp)
            x = x + DT * (-x + su.sig(drive))
    return x


def wedge_input(n, epg, ang, centre, amp):
    v = np.zeros(n)
    sel = np.abs(wrapd(np.degrees(ang) - centre)) <= WEDGE
    v[epg[sel]] = amp
    return v


def setup(W, epg, ang):
    lam1 = su.lambda1(W, epg, ang)
    w0 = G / (lam1 * su.sig(BETA) * (1 - su.sig(BETA)))
    bias = BETA - w0 * (W @ np.full(W.shape[0], su.sig(BETA)))
    cue = np.zeros(W.shape[0])
    cue[epg] = 3.0 * np.maximum(np.cos(ang), 0)
    return w0, bias, cue


def jumped(W, epg, ang, w0, bias, cue, shift, amp):
    n = W.shape[0]
    x = simulate(W, epg, ang, w0, bias, [(20.0, cue), (T_EST - 20.0, None), (T_STIM, wedge_input(n, epg, ang, shift, amp)), (T_FREE, None)])
    width, peaks, contrast = su.width_of(x, epg, ang)
    c = centre_deg(x, epg, ang)
    return abs(wrapd(c - shift)) <= 22.5 and peaks == 1, c, width, peaks


def threshold(W, epg, ang, w0, bias, cue, shift):
    ok, *_ = jumped(W, epg, ang, w0, bias, cue, shift, A_MAX)
    if not ok:
        return None
    lo, hi = 0.0, A_MAX
    for _ in range(BISECT):
        mid = (lo + hi) / 2
        if jumped(W, epg, ang, w0, bias, cue, shift, mid)[0]:
            hi = mid
        else:
            lo = mid
    return hi


A_REF, A2_SET = 3.0, (0.0, 1.0, 2.0, 3.0, 5.0, 10.0)


def mutual_suppression(W, epg, ang, w0, bias, cue):
    """Kim 2017 Fig 2: reference site (0 deg) held at A_REF while a site at 180 deg receives A2; activity at the
    reference site at the end of 20 tau of simultaneous stimulation."""
    n = W.shape[0]
    ref_sel = np.abs(wrapd(np.degrees(ang))) <= WEDGE
    out = []
    for a2 in A2_SET:
        inp = wedge_input(n, epg, ang, 0.0, A_REF) + wedge_input(n, epg, ang, 180.0, a2)
        x = simulate(W, epg, ang, w0, bias, [(20.0, cue), (T_EST - 20.0, None), (T_STIM, inp)])
        out.append(float(x[epg][ref_sel].mean() - x[epg].min()))
    base = out[0]
    mono = all(b <= a + 1e-6 for a, b in zip(out, out[1:]))
    suppressed = base > 0 and min(out) < 0.5 * base
    return {"A2": list(A2_SET), "ref_activity_above_min": out, "monotone": bool(mono), "below_half": bool(suppressed)}


def analyse(W, epg, ang):
    w0, bias, cue = setup(W, epg, ang)
    n = W.shape[0]
    base = simulate(W, epg, ang, w0, bias, [(20.0, cue), (T_EST - 20.0, None)])
    bw, bp, bc = su.width_of(base, epg, ang)
    both = np.zeros(n)
    both[epg] = 3.0 * np.maximum(np.cos(ang), 0) + 2.7 * np.maximum(np.cos(ang - np.pi), 0)  # 10 % stronger cue at 0 deg
    xb = simulate(W, epg, ang, w0, bias, [(20.0, both), (T_EST, None)])
    uw, up, uc = su.width_of(xb, epg, ang)
    winner = centre_deg(xb, epg, ang)
    ms = mutual_suppression(W, epg, ang, w0, bias, cue)
    thr = {str(int(s)): threshold(W, epg, ang, w0, bias, cue, s) for s in SHIFTS}
    t90, t180 = thr["90"], thr["180"]
    ratio = (t180 / t90) if (t90 and t180) else None
    return {"base_bump": {"fwhm": bw, "peaks": bp, "centre_deg": centre_deg(base, epg, ang)},
            "two_cue_final": {"fwhm": uw, "peaks": up, "contrast": uc, "centre_deg": winner},
            "report_S4_mutual_suppression": ms, "jump_threshold": thr, "ratio_180_over_90": ratio,
            "S1_unique": bool(up == 1 and uc >= 0.3 and abs(wrapd(winner)) <= 22.5),
            "S2_local_signature": bool(ratio is not None and 0.8 <= ratio <= 1.25)}


def main():
    if "--synthetic" in sys.argv:
        syn = load("syn", LOOP / "step26_tonic_reduced/synthetic_net.py")
        W, epg, ang, gamma = syn.network()
        W = W * (1 + 1e-3 * np.random.default_rng(0).standard_normal(W.shape))  # break exact symmetry (synthetic only)
        print(json.dumps(analyse(W, epg, ang), indent=1, default=float))
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    nets = {}
    A, ty, sd, nt = su.gi.malecns(); nets["malecns"] = su.raw_network(A, ty, su.s25.malecns()[2], sd, nt)
    A, ty, sd, nt = su.gi.flywire(); nets["flywire"] = su.raw_network(A, ty, None, sd, nt)
    A, ty, inst, sd, nt = h22.hemibrain(); nets["hemibrain"] = su.raw_network(A, ty, inst, sd, nt)
    res = {k: analyse(W, epg, ang) for k, (W, epg, ang, basis, gamma) in nets.items()}
    ok = all(r["S1_unique"] and r["S2_local_signature"] for r in res.values())
    result = {"schema": "ce-a1-step33-selection", "code_sha256": code_hash, "beta": BETA, "g": G,
              "verdict": "SELECTION_RULES_REPRODUCED" if ok else "SELECTION_RULES_NOT_REPRODUCED", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"])
    for k, r in res.items():
        print("==", k, "S1", r["S1_unique"], "S2", r["S2_local_signature"], "ratio", None if r["ratio_180_over_90"] is None else round(r["ratio_180_over_90"], 3),
              "thr", r["jump_threshold"], "base", r["base_bump"], "two-cue", r["two_cue_final"],
              "S4 ref act (report)", [round(v, 3) for v in r["report_S4_mutual_suppression"]["ref_activity_above_min"]])


if __name__ == "__main__":
    main()
