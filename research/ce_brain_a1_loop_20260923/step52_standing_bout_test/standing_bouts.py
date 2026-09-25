"""A1 step 52: would the wells of the per-neuron connectome ring be visible in the fly data of Noorman et al. 2024
(Nat Neurosci 27:2207)? Their standing-bout analysis applied to the models. (CONTRACT.md)

Fly analysis (paper Methods and plotDriftAnalysisFigs.m, Zenodo 10.5281/zenodo.12789923): standing bouts of the fly
in darkness; bump position (PVA) at the start and at the end of each bout; Watson's U2 two-sample test (Zar 1999
eq. 27.17, ties accommodated) between start and end positions, permutation test with 500 permutations,
p = mean(U2_H0 >= U2_obs). Flies 1-10: p = 0.556, 1, 1, 0.992, 0.998, 1, 0.958, 1, 0.986, 0.118 (bouts 0.3-2 s:
312-1005 per fly). Model time constant tau = 0.1 s (paper).

Model bouts: N_BOUTS per network; start position uniform; bump formed by the cue (T_CUE) and released; bout duration
uniform in [0.3, 2] s = [3, 20] tau; start = PVA at release, end = PVA after the bout.
Networks per dataset:
  literal       step 47 N2 (flow-normalised per-neuron wiring, symmetric part) at the step 47 gain
  homeostasis   step 51 after scaling (s, gain from step 51)
  direction     step 46 16-direction ring at g* (continuous reference)
Sensitivity (report): tau = 0.05 s (Kim et al. 2019), bouts [6, 40] tau.

python standing_bouts.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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
N_BOUTS, N_PERM, T_CUE = 700, 500, 20.0
BOUT_S = (0.3, 2.0)
TAU_PRIMARY, TAU_SENS = 0.1, 0.05
FLY_P = (0.5560, 1.0, 1.0, 0.9920, 0.9980, 1.0, 0.9580, 1.0, 0.9860, 0.1180)
SEED = 52


def watsons_u2(a1, a2):
    """Zar (1999) eq. 27.17 with ties, as watsons_U2.m (Megevand)."""
    a1, a2 = np.sort(np.asarray(a1, float)), np.sort(np.asarray(a2, float))
    n1, n2 = a1.size, a2.size
    n = n1 + n2
    v, t = np.unique(np.r_[a1, a2], return_counts=True)
    d = np.searchsorted(a1, v, side="right") / n1 - np.searchsorted(a2, v, side="right") / n2
    return float(n1 * n2 / n ** 2 * (np.sum(t * d ** 2) - np.sum(t * d) ** 2 / n))


def u2_perm_test(a1, a2, rng):
    obs = watsons_u2(a1, a2)
    pool = np.r_[a1, a2]
    h0 = np.empty(N_PERM)
    for i in range(N_PERM):
        p = rng.permutation(pool)
        h0[i] = watsons_u2(p[:a1.size], p[a1.size:])
    return {"U2": obs, "p": float(np.mean(h0 >= obs)), "p_plus1": float((1 + np.sum(h0 >= obs)) / (1 + N_PERM))}


def bouts(W, ang, tau_s, rng):
    starts, ends, durs = [], [], []
    for _ in range(N_BOUTS):
        c = rng.uniform(0, 360)
        d = rng.uniform(*BOUT_S)
        r, _ = nl.run(W, np.zeros_like(W), None, [(T_CUE, nl.cue(ang, c), 0.0)])
        if r is None:
            return None
        s0 = nl.com(r, ang)
        r, _ = nl.run(W, np.zeros_like(W), r, [(d / tau_s, 0.0, 0.0)])
        if r is None:
            return None
        starts.append(s0)
        ends.append(nl.com(r, ang))
        durs.append(d)
    return np.array(starts), np.array(ends), np.array(durs)


def sinus_r2(psi, y, w):
    """R2 of y = A sin(w psi + theta) + C (the paper fits w in {8, 16}; w in {1, 2, 3} probes a few idiosyncratic wells)."""
    X = np.c_[np.sin(w * psi), np.cos(w * psi), np.ones_like(psi)]
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return float(1 - np.sum((y - X @ beta) ** 2) / np.sum((y - y.mean()) ** 2))


def analyse_bouts(W, ang, tau_s, rng):
    b = bouts(W, ang, tau_s, rng)
    if b is None:
        return {"blow_up": True}
    s, e, d = b
    drift = (e - s + 180) % 360 - 180
    test = u2_perm_test(np.radians(s), np.radians(e), rng)
    return {**test, "median_abs_drift_deg": float(np.median(np.abs(drift))), "p90_abs_drift_deg": float(np.percentile(np.abs(drift), 90)),
            "frac_abs_drift_le_5deg": float(np.mean(np.abs(drift) <= 5.0)), "mean_duration_s": float(d.mean()),
            "drift_R2_by_frequency": {str(w): sinus_r2(np.radians(s), np.radians(drift), w) for w in (1, 2, 3, 8, 16)}}


def networks(name, data, M, s46, s47, s51):
    ang = M["ang"]
    out = {"literal": (s47["datasets"][name]["networks"]["0.0"]["g"] * (M["E"] - M["I"]), ang)}
    d51 = s51["datasets"][name]
    s = np.array(d51["s"])
    out["homeostasis"] = (d51["after"]["g"] * (s[:, None] * M["E"] - M["I"]), ang)
    P, _ = c46.kernels(*data)
    k = c46.symmetrise(P["exc"] - P["inh_all"])
    out["direction"] = (c46.ring(k, s46["datasets"][name]["variants"]["connectome"]["g_star"]), np.radians(np.arange(16) * 22.5))
    return out


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step48_homeostatic_scaling/homeostatic_ring.py", LOOP / "step47_neuron_level_wells/neuron_level_wells.py",
            LOOP / "step46_connectome_ring_class/connectome_ring_class.py", LOOP / "step41_few_neuron_attractor/tl_ring.py",
            LOOP / "step41_few_neuron_attractor/few_neuron_ring.py", LOOP / "step42_kim_support_ring/kim_support_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s46 = json.loads((LOOP / "step46_connectome_ring_class/results.json").read_text(encoding="utf-8"))
    s47 = json.loads((LOOP / "step47_neuron_level_wells/results.json").read_text(encoding="utf-8"))
    s51 = json.loads((LOOP / "step51_homeostasis_fixed_target/results.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(SEED)
    res = {}
    for name, data in c46.datasets().items():
        M = hr.matrices(*data)
        res[name] = {}
        for label, (W, ang) in networks(name, data, M, s46, s47, s51).items():
            entry = {"primary_tau_0p1": analyse_bouts(W, ang, TAU_PRIMARY, rng), "sensitivity_tau_0p05": analyse_bouts(W, ang, TAU_SENS, rng)}
            res[name][label] = entry
            print(name, label, json.dumps(entry), flush=True)
    lit = {k: v["literal"]["primary_tau_0p1"].get("p", 0.0) < 0.05 for k, v in res.items()}
    ctrl = {k: v["direction"]["primary_tau_0p1"].get("p", 0.0) >= 0.05 for k, v in res.items()}
    result = {"schema": "ce-a1-step52-standing-bouts", "hashes": hashes, "fly_p_values": FLY_P,
              "literal_detectable": lit, "control_not_detectable": ctrl,
              "verdict": "LITERAL_WIRING_INCONSISTENT_WITH_FLY" if sum(lit.values()) >= 2 else "LITERAL_WIRING_CONSISTENT_WITH_FLY",
              "protocol_valid": bool(sum(ctrl.values()) >= 2), "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], lit, "control ok", ctrl)


if __name__ == "__main__":
    main()
