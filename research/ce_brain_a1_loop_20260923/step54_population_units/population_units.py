"""A1 step 54: candidate 1 of the neuron-level gap. If E-PGs of one direction act as one computational unit
("sets of neurons with the same HD tuning", Noorman et al. 2024), the circuit is the population (mean-field) reduction
of the actual wiring: tau dr_a/dt = -r_a + [sum_b Kd[a, b] r_b + c]_+,
Kd[a, b] = mean over E-PGs i of direction a of sum over E-PGs j of direction b of K_ij  (K = E - I, step 48 flows).
It keeps the conserved structure found in step 50 (identical E-PG counts per direction, reproducible direction
deviations) and averages out the idiosyncratic within-direction part. Is it a continuous attractor that holds like the
fly? (CONTRACT.md)

Networks (16 units, directions from PB labels; FlyWire: label-free angles binned to 16):
  population        g Kd,  velocity g Ad (Ad = population reduction of the PEN left-right flow difference)
  population_eqcnt  report: columns rescaled to equal counts (Kd[:, b] * mean(n) / n_b), same velocity rescaling
Gain: best within +-20 % of g1 = g* 16 / n_EPG (minimal hold error, 16 positions), as in steps 47-51.
Tests: step 48 battery (64-position hold, rotation, S1, S2), drift field MaleCNS vs hemibrain (63 circular shifts),
step 53 walking -> standing protocol (same behaviour seed).

python population_units.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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


ws = load("walk_stand", LOOP / "step53_walk_stand_protocol/walk_stand.py")
ho = load("heterogeneity_origin", LOOP / "step50_heterogeneity_origin/heterogeneity_origin.py")
sb, hr, nl, c46 = ws.sb, ws.hr, ws.nl, ws.c46
ANG16 = np.radians(np.arange(16) * 22.5)


def population(M):
    n = np.bincount(ho.dirs_of(M["ang"]), minlength=16).astype(float)
    Kd = ho.direction_kernel(M["E"] - M["I"], M["ang"])
    Ad = ho.direction_kernel(M["A_pen"], M["ang"])
    eq = n.mean() / np.where(n > 0, n, 1.0)
    return {"population": (Kd, Ad), "population_eqcnt": (Kd * eq[None, :], Ad * eq[None, :])}, n


def evaluate(K, A, g1, omega, walking, rng, label):
    bg = nl.best_gain(K, ANG16, g1)
    if bg is None:
        print("   ", label, "no usable gain", flush=True)
        return {"exists": False}
    W, Av = bg[0] * K, bg[0] * A
    t = hr.tests(W, Av, ANG16)
    t["g"], t["g_over_mapped"] = bg[0], bg[0] / g1
    e = nl.hold_errors(W, ANG16, nl.CUES)
    t["drift_field"] = None if e is None else e.tolist()
    G, ok, _ = ws.calibrate(W, Av, ANG16)
    phase = ws.session(W, Av, ANG16, G, omega)
    t["walk_stand"] = {"blow_up": True} if phase is None else ws.analyse(phase, omega, walking, rng)
    t["walk_stand"]["calibration_reached_fast"] = ok
    ss = {k: v for k, v in t["walk_stand"].items() if k in ("U2", "p", "median_abs_drift_deg", "slow_over_fast", "coverage_bins_ge_1pct")}
    print("   ", label, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in t.items() if k not in ("rotation", "S2", "drift_field", "walk_stand")}),
          "rot", round(t.get("rotation", {}).get("slow_over_fast_gain", float("nan")), 3), "S2", t.get("S2", {}).get("ratio_180_over_90"), "walk", json.dumps(ss), flush=True)
    return t


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step53_walk_stand_protocol/walk_stand.py", LOOP / "step52_standing_bout_test/standing_bouts.py",
            LOOP / "step50_heterogeneity_origin/heterogeneity_origin.py", LOOP / "step48_homeostatic_scaling/homeostatic_ring.py",
            LOOP / "step47_neuron_level_wells/neuron_level_wells.py", LOOP / "step46_connectome_ring_class/connectome_ring_class.py",
            LOOP / "step41_few_neuron_attractor/tl_ring.py", LOOP / "step41_few_neuron_attractor/few_neuron_ring.py",
            LOOP / "step42_kim_support_ring/kim_support_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s46 = json.loads((LOOP / "step46_connectome_ring_class/results.json").read_text(encoding="utf-8"))
    omega, walking = ws.behaviour(np.random.default_rng(ws.SEED))
    rng = np.random.default_rng(54)
    res = {}
    for name, data in c46.datasets().items():
        print("==", name, flush=True)
        M = hr.matrices(*data)
        nets, counts = population(M)
        g1 = s46["datasets"][name]["variants"]["connectome"]["g_star"] * 16 / M["ang"].size
        res[name] = {"counts": counts.tolist()}
        for label, (K, A) in nets.items():
            res[name][label] = evaluate(K, A, g1, omega, walking, rng, label)
    pop = {k: v["population"] for k, v in res.items()}
    c1 = {k: bool(v.get("C1", False)) for k, v in pop.items()}
    near = {k: bool(v.get("retention_22p5", 0) >= 0.8 and v.get("distinct_end_positions", 0) >= 12) for k, v in pop.items()}
    hold = {k: bool(v.get("walk_stand", {}).get("p", 0.0) >= 0.05) for k, v in pop.items()}
    f1, f2 = pop["malecns"].get("drift_field"), pop["hemibrain"].get("drift_field")
    shared = None
    if f1 is not None and f2 is not None and np.std(f1) > 0 and np.std(f2) > 0:
        a, b = np.array(f1), np.array(f2)
        r = float(np.corrcoef(a, b)[0, 1])
        null = np.array([np.corrcoef(a, np.roll(b, s))[0, 1] for s in range(1, a.size)])
        shared = {"r": r, "p": float((1 + np.sum(null >= r)) / a.size)}
    verdict = ("CONSERVED_POPULATION_STRUCTURE_CONTINUOUS" if sum(c1.values()) >= 2 else
               "CONSERVED_POPULATION_STRUCTURE_NEARLY_CONTINUOUS" if sum(near.values()) >= 2 else "CONSERVED_POPULATION_STRUCTURE_HAS_WELLS")
    result = {"schema": "ce-a1-step54-population-units", "hashes": hashes, "verdict": verdict, "C1": c1, "retention_and_ends": near,
              "fly_holding_consistent": hold, "fly_holding_verdict": "CONSISTENT" if sum(hold.values()) >= 2 else "INCONSISTENT",
              "drift_field_malecns_vs_hemibrain": shared, "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", verdict, "C1", c1, "near", near, "hold", hold, "shared drift", shared)


if __name__ == "__main__":
    main()
