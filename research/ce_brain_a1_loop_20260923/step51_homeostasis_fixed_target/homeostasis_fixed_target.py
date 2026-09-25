"""A1 step 51: homeostatic synaptic scaling (Renart, Song & Wang 2003 Neuron 38:473) with a fixed common target and
slow multiplicative updates (the proportional form of van Rossum, Bi & Turrigiano 2000 J Neurosci 20:8812), on the
per-neuron connectome ring (step 47 N2). Does it remove the idiosyncratic wells found in step 50? (CONTRACT.md)

Network (step 48 E, I, A_pen; threshold-linear, c = 1):   W = g (diag(s) E - I),   velocity  g diag(s) A_pen
  s_i scales every excitatory input onto E-PG i (Renart: "scales the excitatory synapses to each cell").
Epoch: 16 trials, cue centres (k + u) 22.5 deg, u ~ U(0, 1) per epoch; each trial from rest: cue T_CUE, delay T_DELAY;
  rbar_i = mean rate over the whole trial (sampled every tau), averaged over the 16 trials.
Update: s_i <- clip(s_i * clip(1 + BETA (r_T - rbar_i) / r_T, 1 - STEP_MAX, 1 + STEP_MAX), S_MIN, S_MAX)
  r_T = population mean of rbar in the first epoch without blow-up, then fixed; g = step 47 best gain of N2.
  An epoch with a blow-up: s <- 0.95 s (recorded).
After EPOCHS: gain re-optimised within +-20 % (minimal hold error, 16 positions); step 48 test battery.
Control: the learned s permuted across neurons (seeded), gain re-optimised, hold test only.

python homeostasis_fixed_target.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hr = load("homeostatic_ring", LOOP / "step48_homeostatic_scaling/homeostatic_ring.py")
nl, c46 = hr.nl, hr.c46
EPOCHS, BETA, STEP_MAX, S_MIN, S_MAX = 200, 0.05, 0.05, 0.2, 5.0
T_CUE, T_DELAY = 20.0, 30.0
SEED = 51


def trial_average(W, ang, cues):
    acc = np.zeros(ang.size)
    for c in cues:
        r, tr = nl.run(W, np.zeros_like(W), None, [(T_CUE, nl.cue(ang, c), 0.0), (T_DELAY, 0.0, 0.0)], every=int(1.0 / nl.DT))
        if r is None:
            return None
        acc += np.mean(tr, axis=0)
    return acc / len(cues)


def homeostasis(M, g, rng):
    s = np.ones(M["ang"].size)
    r_T, hist = None, []
    for ep in range(EPOCHS):
        cues = (np.arange(16) + rng.random()) * 22.5
        rbar = trial_average(g * (s[:, None] * M["E"] - M["I"]), M["ang"], cues)
        if rbar is None:
            s = s * 0.95
            hist.append({"epoch": ep, "blow_up": True})
            continue
        if r_T is None:
            r_T = float(rbar.mean())
        hist.append({"epoch": ep, "cv": float(rbar.std() / max(rbar.mean(), 1e-12)), "mean_over_target": float(rbar.mean() / r_T)})
        s = np.clip(s * np.clip(1 + BETA * (r_T - rbar) / r_T, 1 - STEP_MAX, 1 + STEP_MAX), S_MIN, S_MAX)
        if ep % 20 == 0 or ep == EPOCHS - 1:
            print("    epoch", ep, json.dumps(hist[-1]), "s range", round(float(s.min()), 3), round(float(s.max()), 3), flush=True)
    return s, r_T, hist


def hold_summary(W, ang):
    e = nl.hold_errors(W, ang, nl.CUES)
    if e is None:
        return {"blow_up": True, "retention_22p5": 0.0}
    return {"retention_22p5": float(np.mean(np.abs(e) <= 22.5)), "distinct_end_positions": nl.wells((nl.CUES + e) % 360),
            "max_abs_err": float(np.max(np.abs(e))), "median_abs_err": float(np.median(np.abs(e))), "errors": e.tolist()}


def analyse(M, g, rng):
    ang = M["ang"]
    s, r_T, hist = homeostasis(M, g, rng)
    res = {"n_epg": int(ang.size), "g_homeostasis": g, "r_target": r_T, "history": hist,
           "s": s.tolist(), "s_min": float(s.min()), "s_median": float(np.median(s)), "s_max": float(s.max())}
    Kh = s[:, None] * M["E"] - M["I"]
    bg = nl.best_gain(Kh, ang, g)
    if bg is None:
        res["after"] = {"exists": False}
    else:
        t = hr.tests(bg[0] * Kh, bg[0] * s[:, None] * M["A_pen"], ang)
        t["g"], t["g_over_homeostasis"] = bg[0], bg[0] / g
        t["drift_field"] = hold_summary(bg[0] * Kh, ang).get("errors")
        res["after"] = t
        print("    after", json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in t.items() if k not in ("rotation", "S2", "drift_field")}),
              "rot", round(t.get("rotation", {}).get("slow_over_fast_gain", float("nan")), 3), "S2", t.get("S2", {}).get("ratio_180_over_90"), flush=True)
    sp = rng.permutation(s)
    Kc = sp[:, None] * M["E"] - M["I"]
    bgc = nl.best_gain(Kc, ang, g)
    res["control_permuted_s"] = {"exists": False} if bgc is None else {"g": bgc[0], **{k: v for k, v in hold_summary(bgc[0] * Kc, ang).items() if k != "errors"}}
    print("    control", json.dumps(res["control_permuted_s"]), flush=True)
    a = res["after"]
    res["H1_wells_removed"] = bool(a.get("retention_22p5", 0) >= 0.8 and a.get("distinct_end_positions", 0) >= 12)
    res["H2_strict_C1"] = bool(a.get("C1", False))
    r2 = a.get("S2", {}).get("ratio_180_over_90")
    res["H3_S2_local"] = bool(r2 is not None and 0.8 <= r2 <= 1.25)
    res["control_below_0p8"] = bool(res["control_permuted_s"].get("retention_22p5", 0) < 0.8)
    return res


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step48_homeostatic_scaling/homeostatic_ring.py", LOOP / "step47_neuron_level_wells/neuron_level_wells.py",
            LOOP / "step46_connectome_ring_class/connectome_ring_class.py", LOOP / "step41_few_neuron_attractor/tl_ring.py",
            LOOP / "step41_few_neuron_attractor/few_neuron_ring.py", LOOP / "step42_kim_support_ring/kim_support_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s47 = json.loads((LOOP / "step47_neuron_level_wells/results.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(SEED)
    res = {}
    for name, data in c46.datasets().items():
        print("==", name, flush=True)
        res[name] = analyse(hr.matrices(*data), s47["datasets"][name]["networks"]["0.0"]["g"], rng)
    h1 = {k: v["H1_wells_removed"] for k, v in res.items()}
    result = {"schema": "ce-a1-step51-homeostasis-fixed-target", "hashes": hashes, "H1_per_dataset": h1,
              "H2_per_dataset": {k: v["H2_strict_C1"] for k, v in res.items()}, "H3_per_dataset": {k: v["H3_S2_local"] for k, v in res.items()},
              "control_below_0p8": {k: v["control_below_0p8"] for k, v in res.items()},
              "verdict": "HOMEOSTASIS_REMOVES_WELLS" if sum(h1.values()) >= 2 else "HOMEOSTASIS_DOES_NOT_REMOVE_WELLS", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], h1, result["H2_per_dataset"], result["H3_per_dataset"], result["control_below_0p8"])


if __name__ == "__main__":
    main()
