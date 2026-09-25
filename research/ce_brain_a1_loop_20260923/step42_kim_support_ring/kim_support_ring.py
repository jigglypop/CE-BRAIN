"""A1 step 42: step 41 redone under Kim et al. 2017's own modelling condition -- bump support ~90 deg (16-direction
lattice: <= 5 active cells) -- at the few-neuron continuous-attractor optimum (Noorman et al. 2024). Stimulus strengths
are in units of each network's natural bump amplitude (Kim normalised input strength by bump amplitude). (CONTRACT.md)

Uses the frozen step 41 modules (tl_ring.py, few_neuron_ring.py) for the network, continuity, rotation and two-cue tests.

python kim_support_ring.py    refuses to run unless CONTRACT.md lists this code hash (and the step 41 hashes)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
S41 = HERE.parent / "step41_few_neuron_attractor"
sys.path.insert(0, str(S41))
import tl_ring as tl  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


f41 = load("few_neuron_ring", S41 / "few_neuron_ring.py")
NETS = {
    "local_opt": ("local", {"alpha": 2.500, "D": 1.5, "beta": 1.0}),
    "cosine_opt": ("cosine", {"JE": 1.444, "JI": 1.0}),
    "local_detuned": ("local", {"alpha": 2.500 * 0.95, "D": 1.5, "beta": 1.0}),
    "cosine_detuned": ("cosine", {"JE": 1.444 * 0.95, "JI": 1.0}),
}
A_FIRST, A_MAX, BISECT = 5.0, 10.0, 12            # x natural bump amplitude
A_REF, A2_SET = 1.0, (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.5)
SLOW = (1 / 16, 1 / 32)


def jumped(W, amp0, b, delta, a):
    C = f41.C
    r, _, _ = tl.run(W, C, [(f41.T_CUE, tl.cue(b), 0.0), (f41.T_FIRST, tl.wedge(b, A_FIRST * amp0), 0.0),
                            (f41.T_SECOND, tl.wedge(b + delta, a * amp0), 0.0), (f41.T_AFTER, 0.0, 0.0)])
    return bool(f41.bump_ok(r, amp0) and abs(tl.wrapd(tl.com(r) - (b + delta))) <= 22.5)


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
    thr = {str(int(d)): [threshold(W, amp0, b, d) for b in f41.BASES_S2] for d in (90.0, 180.0)}
    med = {k: (float(np.median(v)) if all(t is not None for t in v) else None) for k, v in thr.items()}
    ratio = med["180"] / med["90"] if med["90"] and med["180"] else None
    return {"thresholds_x_amp": thr, "median": med, "ratio_180_over_90": ratio, "S2": bool(ratio is not None and 0.8 <= ratio <= 1.25)}


def suppression(W, amp0):
    out = []
    for a2 in A2_SET:
        r, _, _ = tl.run(W, f41.C, [(f41.T_CUE, tl.cue(0.0), 0.0), (10.0, 0.0, 0.0),
                                    (f41.T_SECOND, tl.wedge(0.0, A_REF * amp0) + tl.wedge(180.0, a2 * amp0), 0.0)])
        out.append(float(r[0] - r.min()))
    return {"A2_x_amp": list(A2_SET), "ref_activity": out, "S3": bool(out[0] > 0 and min(out) < 0.5 * out[0])}


def analyse(kind, p):
    W, A = f41.build(kind, p)
    amp0, shp, n_act = f41.natural_amp(W)
    res = {"params": p, "dark_bump": {"amp": amp0, "fwhm": shp[0], "peaks": shp[1], "n_active": n_act}}
    res["continuity"] = f41.continuity(W, amp0)
    rot = f41.rotation(W, A, amp0)
    slow = {}
    for sgn in (1, -1):
        for fr in SLOW:
            s, r2, blow = f41.speed(W, A, sgn * fr * rot["v_fast"])
            slow["%+.5f" % (sgn * fr)] = {"speed_deg_per_tau": s, "gain": s / (sgn * fr * rot["v_fast"]), "r2": r2}
    rot["report_slower"] = slow
    res["rotation"] = rot
    res["two_cue"] = f41.two_cue(W, amp0)
    res["jump"] = jump_thresholds(W, amp0)
    res["suppression"] = suppression(W, amp0)
    return res


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), S41 / "tl_ring.py", S41 / "few_neuron_ring.py")}
    missing = [n for n, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    res = {}
    for name, (kind, p) in NETS.items():
        r = analyse(kind, p)
        r["criteria"] = {"C1": r["continuity"]["C1"], "R1": r["rotation"]["R1"], "S1": r["two_cue"]["S1"], "S2": r["jump"]["S2"],
                         "S3_secondary": r["suppression"]["S3"]}
        res[name] = r
        print("==", name, json.dumps({"dark": r["dark_bump"], "C1": [r["continuity"][k] for k in ("max_abs_err", "median_abs_err")],
                                      "R1": [r["rotation"]["gain_slow_over_fast"], {k: round(v["gain"], 4) for k, v in r["rotation"]["report_slower"].items()}],
                                      "S1": r["two_cue"]["n_ok"], "S2": [r["jump"]["thresholds_x_amp"], r["jump"]["ratio_180_over_90"]],
                                      "S3": [round(x, 3) for x in r["suppression"]["ref_activity"]], "criteria": r["criteria"]}, default=float), flush=True)
    L = res["local_opt"]["criteria"]
    ok = L["C1"] and L["R1"] and L["S1"] and L["S2"]
    pred_cos = res["cosine_opt"]["jump"]["ratio_180_over_90"]
    result = {"schema": "ce-a1-step42-kim-support-ring", "hashes": hashes,
              "verdict": "KIM_SUPPORT_LOCAL_RING_ROTATES_AND_SELECTS" if ok else "KIM_SUPPORT_LOCAL_RING_DOES_NOT_SATISFY_ALL",
              "report_cosine_ratio_above_1p25": bool(pred_cos is not None and pred_cos > 1.25), "networks": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], "cosine ratio > 1.25:", result["report_cosine_ratio_above_1p25"], {k: v["criteria"] for k, v in res.items()})


if __name__ == "__main__":
    main()
