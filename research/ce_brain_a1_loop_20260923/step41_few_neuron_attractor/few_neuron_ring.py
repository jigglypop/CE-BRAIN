"""A1 step 41 (part A): on the fly lattice (16 directions), does a threshold-linear ring tuned to the few-neuron
continuous-attractor optimum (Noorman et al. 2024) rotate linearly down to slow speeds and obey Kim et al. 2017's
selection rules (one of two cues, narrow-input jump with a distance-independent threshold, mutual suppression)?
(CONTRACT.md)

Networks (tl_ring.py, c = 1): Kim 'local' W = (a - 2D) I + D (S + S^T) - b 11^T and Kim 'global' / Noorman cosine
W = J_E cos - J_I, each at its zero-drift optimum with FWHM ~90 deg (pre-freeze calibration, hold error only) and 5 %
detuned (control). Velocity: side-ring generator A = (W_+ - W_-)/2 with gain v.

python few_neuron_ring.py    refuses to run unless CONTRACT.md lists this code hash and tl_ring.py hash
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tl_ring as tl  # noqa: E402

NETS = {
    "local_opt": ("local", {"alpha": 2.463, "D": 2.5, "beta": 1.0}),
    "cosine_opt": ("cosine", {"JE": 0.4815, "JI": 0.5}),
    "local_detuned": ("local", {"alpha": 2.463 * 0.95, "D": 2.5, "beta": 1.0}),
    "cosine_detuned": ("cosine", {"JE": 0.4815 * 0.95, "JI": 0.5}),
}
C = 1.0
T_CUE, T_HOLD, T_FREE_S1 = 20.0, 100.0, 50.0
CUES_C = np.arange(0, 360, 5.625)
BASES_S1 = np.arange(0, 360, 45.0)
BASES_S2 = (0.0, 90.0, 180.0, 270.0)
T_FIRST, T_SECOND, T_AFTER = 20.0, 15.0, 30.0
A_FIRST, A_MAX, BISECT = 5.0, 10.0, 12
A_REF, A2_SET = 1.0, (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.5)
TARGET_FAST = 24.0            # deg per tau for the fastest test speed (~240 deg/s at tau = 0.1 s)
V_FRACTIONS = (1 / 8, 1 / 4, 1 / 2, 1.0)
T_ROT, FIT_FROM = 60.0, 10.0


def build(kind, p):
    W = tl.local_ring(p["alpha"], p["D"], p["beta"]) if kind == "local" else tl.cosine_ring(p["JE"], p["JI"])
    return W, tl.generator(W)


def natural_amp(W):
    r, _, _ = tl.run(W, C, [(T_CUE, tl.cue(0.0), 0.0), (T_HOLD, 0.0, 0.0)])
    return float(r.max()), tl.shape(r), int(np.sum(r > 1e-6))


def bump_ok(r, amp0):
    w, peaks, contrast, amp = tl.shape(r)
    return peaks == 1 and contrast >= 0.3 and amp >= 0.25 * amp0


def continuity(W, amp0):
    errs, ok = [], []
    for c in CUES_C:
        r, _, _ = tl.run(W, C, [(T_CUE, tl.cue(c), 0.0), (T_HOLD, 0.0, 0.0)])
        errs.append(float(tl.wrapd(tl.com(r) - c)))
        ok.append(bump_ok(r, amp0))
    e = np.abs(errs)
    return {"err": errs, "max_abs_err": float(e.max()), "median_abs_err": float(np.median(e)), "all_bumps": bool(all(ok)),
            "C1": bool(all(ok) and e.max() <= 5.625 and np.median(e) <= 2.0)}


def speed(W, A, v):
    every = int(0.5 / tl.DT)
    r, tr, blow = tl.run(W, C, [(T_CUE, tl.cue(0.0), 0.0), (T_ROT, 0.0, v)], A=A, every=every)
    ph = np.degrees(np.unwrap(np.radians(tr[int(T_CUE / 0.5):])))
    t = np.arange(ph.size) * 0.5
    m = t >= FIT_FROM
    if blow or m.sum() < 3:
        return float("nan"), float("nan"), True
    coef = np.polyfit(t[m], ph[m], 1)
    r2 = 1 - np.sum((ph[m] - np.polyval(coef, t[m])) ** 2) / max(np.sum((ph[m] - ph[m].mean()) ** 2), 1e-12)
    return float(coef[0]), float(r2), bool(blow)


def v_for_fast(W, A):
    """Velocity scale: smallest v (bisection) whose bump speed reaches TARGET_FAST deg/tau."""
    fast = lambda v: not (abs(speed(W, A, v)[0]) < TARGET_FAST)      # nan (blow-up) counts as fast
    lo, hi = 0.0, 0.05
    while not fast(hi) and hi < 2.0:
        hi *= 2
    for _ in range(14):
        mid = (lo + hi) / 2
        if fast(mid):
            hi = mid
        else:
            lo = mid
    return hi


def rotation(W, A, amp0):
    vf = v_for_fast(W, A)
    out = {}
    for sgn in (1, -1):
        for fr in V_FRACTIONS:
            v = sgn * fr * vf
            s, r2, blow = speed(W, A, v)
            out["%+.4f" % (sgn * fr)] = {"v": v, "speed_deg_per_tau": s, "gain": s / v, "r2": r2, "blow": blow}
    g_fast = np.mean([abs(out["%+.4f" % (sg * 1.0)]["gain"]) for sg in (1, -1)])
    g_slow = np.mean([abs(out["%+.4f" % (sg / 8)]["gain"]) for sg in (1, -1)])
    ok = all(o["r2"] >= 0.99 and not o["blow"] for o in out.values()) and bool(np.isfinite(g_slow / g_fast)) and abs(g_slow / g_fast - 1) <= 0.2
    return {"v_fast": vf, "speeds": out, "gain_slow_over_fast": float(g_slow / g_fast), "R1": bool(ok)}


def two_cue(W, amp0):
    out = []
    for c in BASES_S1:
        r, _, _ = tl.run(W, C, [(T_CUE, tl.cue(c, 1.0) + tl.cue(c + 180.0, 0.9), 0.0), (T_FREE_S1, 0.0, 0.0)])
        out.append({"strong": float(c), "final": tl.com(r), "ok": bool(bump_ok(r, amp0) and abs(tl.wrapd(tl.com(r) - c)) <= 22.5)})
    n_ok = sum(o["ok"] for o in out)
    return {"trials": out, "n_ok": n_ok, "S1": bool(n_ok >= 7)}


def jumped(W, amp0, b, delta, amp):
    r, _, _ = tl.run(W, C, [(T_CUE, tl.cue(b), 0.0), (T_FIRST, tl.wedge(b, A_FIRST), 0.0), (T_SECOND, tl.wedge(b + delta, amp), 0.0), (T_AFTER, 0.0, 0.0)])
    return bool(bump_ok(r, amp0) and abs(tl.wrapd(tl.com(r) - (b + delta))) <= 22.5)


def threshold(W, amp0, b, delta):
    if not jumped(W, amp0, b, delta, A_MAX):
        return None
    lo, hi = 0.0, A_MAX
    for _ in range(BISECT):
        mid = (lo + hi) / 2
        if jumped(W, amp0, b, delta, mid):
            hi = mid
        else:
            lo = mid
    return hi


def jump_thresholds(W, amp0):
    thr = {str(int(d)): [threshold(W, amp0, b, d) for b in BASES_S2] for d in (90.0, 180.0)}
    med = {k: (float(np.median(v)) if all(t is not None for t in v) else None) for k, v in thr.items()}
    ratio = med["180"] / med["90"] if med["90"] and med["180"] else None
    return {"thresholds": thr, "median": med, "ratio_180_over_90": ratio, "S2": bool(ratio is not None and 0.8 <= ratio <= 1.25)}


def suppression(W):
    out = []
    for a2 in A2_SET:
        r, _, _ = tl.run(W, C, [(T_CUE, tl.cue(0.0), 0.0), (10.0, 0.0, 0.0), (T_SECOND, tl.wedge(0.0, A_REF) + tl.wedge(180.0, a2), 0.0)])
        out.append(float(r[0] - r.min()))
    return {"A2": list(A2_SET), "ref_activity": out, "S3": bool(out[0] > 0 and min(out) < 0.5 * out[0])}


def analyse(kind, p):
    W, A = build(kind, p)
    amp0, shp, n_act = natural_amp(W)
    res = {"params": p, "dark_bump": {"amp": amp0, "fwhm": shp[0], "peaks": shp[1], "n_active": n_act}}
    res["continuity"] = continuity(W, amp0)
    res["rotation"] = rotation(W, A, amp0)
    res["two_cue"] = two_cue(W, amp0)
    res["jump"] = jump_thresholds(W, amp0)
    res["suppression"] = suppression(W)
    return res


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    h = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    th = hashlib.sha256((HERE / "tl_ring.py").read_bytes()).hexdigest()
    if h not in contract or th not in contract:
        raise SystemExit(f"CONTRACT.md does not list this code hash {h} and tl_ring.py hash {th}")
    res = {}
    for name, (kind, p) in NETS.items():
        r = analyse(kind, p)
        r["criteria"] = {"C1": r["continuity"]["C1"], "R1": r["rotation"]["R1"], "S1": r["two_cue"]["S1"], "S2": r["jump"]["S2"],
                         "S3_secondary": r["suppression"]["S3"]}
        res[name] = r
        print("==", name, json.dumps({"dark": r["dark_bump"], "C1": [r["continuity"][k] for k in ("max_abs_err", "median_abs_err")],
                                      "R1": [r["rotation"]["v_fast"], r["rotation"]["gain_slow_over_fast"]], "S1": r["two_cue"]["n_ok"],
                                      "S2": [r["jump"]["thresholds"], r["jump"]["ratio_180_over_90"]], "S3": [round(x, 3) for x in r["suppression"]["ref_activity"]],
                                      "criteria": r["criteria"]}, default=float), flush=True)
    L = res["local_opt"]["criteria"]
    ok = L["C1"] and L["R1"] and L["S1"] and L["S2"]
    result = {"schema": "ce-a1-step41-few-neuron-ring", "code_sha256": h, "tl_ring_sha256": th,
              "verdict": "FEW_NEURON_LOCAL_RING_ROTATES_AND_SELECTS" if ok else "FEW_NEURON_LOCAL_RING_DOES_NOT_SATISFY_ALL",
              "networks": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], {k: v["criteria"] for k, v in res.items()})


if __name__ == "__main__":
    main()
