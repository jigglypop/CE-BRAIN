"""A1 step 63: in NREM does the whole head-direction system free-run? Upstream generator diffuses (random walk, D_NREM)
instead of holding the heading; the cortical ring follows it weakly (relay gain A_NREM) and loses its state at every
down state (step 58 drive on/off). Two parameters fitted on two mouse numbers; the rest are predictions, including the
level of the re-emergence curve (step 62 lesson). (CONTRACT.md)

Model = step 62 with one change: in NREM the generator heading is a random walk with diffusion D_NREM (rad^2/s) and the
relay carries it without extra jitter. Wake: generator random walk D_W = -ln(0.977)/0.3 and relay gain 1; exploration:
head direction. Step 58 ring, schedule, sigma, gain and spike generation unchanged.
Fit: A_NREM in {0.1, 0.2, 0.4, 0.8} x D_NREM in {1, 2, 4, 8} rad^2/s (seed 630), minimising
  (late re-emergence - mouse)^2 + (inside-up late holding - mouse)^2; mouse values from the step 62 results (same
  frozen estimators: pair-specific denominators).
Predictions (seeds 631-635, medians):
  P1 reset: re-emergence early <= 0.15.      P2 inside-up early in [0.3, 0.65].
  P3 NREM scatter: step 57 rho_all_3 NREM in [0.15, 0.5].
  P4 re-emergence curve level: mean |model - mouse| over d = 1..10 <= 0.05.
  P5 structure kept: ring index NREM/wake in [0.8, 1.2].      P6 wake holding: rho_all_3 wake >= 0.9.
Report: fitted D_NREM relative to D_W (Peyrache 2015: NREM packet much faster than wake).

python wandering_upstream.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


up = load("upstream_pull", LOOP / "step62_upstream_pull/upstream_pull.py")
se, ra, s57, s56 = up.se, up.ra, up.s57, up.s56

A_GRID = (0.1, 0.2, 0.4, 0.8)
D_GRID = (1.0, 2.0, 4.0, 8.0)
SEEDS = (631, 632, 633, 634, 635)


def simulate(sigma, rng, sched, a_nrem, d_nrem):
    c, head, states = sched
    n = c.size
    down = np.isnan(c)
    c = np.where(down, se.C_DOWN_PRIMARY, c)
    t = np.arange(n) * se.DT
    nrem = np.zeros(n, bool)
    for s, a0, b0 in states:
        if s == "nrem":
            nrem |= (t >= a0) & (t < b0)
    k = se.DT / se.TAU
    r = np.zeros(16)
    rates = np.empty((n, 16), dtype=np.float32)
    theta = 0.0
    sd_w, sd_n = np.sqrt(2 * up.D_W * se.DT), np.sqrt(2 * d_nrem * se.DT)
    CH = 10000
    for i0 in range(0, n, CH):
        m = min(CH, n - i0)
        noise = sigma * rng.standard_normal((m, 16))
        z = rng.standard_normal(m)
        for j in range(m):
            i = i0 + j
            if not np.isnan(head[i]):
                theta, a = head[i], 1.0
            elif nrem[i]:
                theta += sd_n * z[j]                              # NREM: the generator itself wanders
                a = 0.0 if down[i] else a_nrem
            else:
                theta += sd_w * z[j]
                a = 1.0
            inp = se.W @ r + c[i] + noise[j] + a * np.exp(4.0 * (np.cos(se.ANG - theta) - 1.0))
            r = r + k * (-r + np.maximum(inp, 0.0))
            rates[i] = r
    return rates


def run_model(a_nrem, d_nrem, seed, sigma, gain, work, full=False):
    rng = np.random.default_rng(seed)
    sched = se.schedule(rng)
    rates = simulate(sigma, rng, sched, a_nrem, d_nrem)
    path = work / f"wander_s{seed}_a{a_nrem}_d{d_nrem}.npz"
    se.spikes_and_save(rates, sched, rng, gain, path)
    out = {"a_nrem": a_nrem, "d_nrem": d_nrem, "seed": seed, **up.measures(path, np.random.default_rng(seed + 1))}
    if full:
        r57 = s57.analyse(path, np.random.default_rng(seed + 2))
        r56 = s56.analyse(path, np.random.default_rng(seed + 3))
        g = lambda dct, s, key: dct.get("states", {}).get(s, {}).get(key)
        out.update({"rho_all_3_nrem": g(r57, "nrem", "rho_all_3"), "rho_all_3_wake": g(r57, "wake_home", "rho_all_3"),
                    "rho_gap": g(r57, "nrem", "rho_gap"), "ring_wake": g(r56, "wake_home", "ring_index"), "ring_nrem": g(r56, "nrem", "ring_index")})
        out["ring_ratio"] = out["ring_nrem"] / out["ring_wake"] if out["ring_nrem"] is not None and out["ring_wake"] else None
    path.unlink()
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items() if k != "re_by_d"}), flush=True)
    return out


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step62_upstream_pull/upstream_pull.py", LOOP / "step58_sleep_equation/sleep_equation.py",
            LOOP / "step59_upstate_holding/upstate_holding.py", LOOP / "step60_reanchoring/reanchoring.py",
            LOOP / "step57_sleep_holding/holding_gap.py", LOOP / "step56_mouse_sleep_ring/mouse_sleep_ring.py",
            LOOP / "step41_few_neuron_attractor/tl_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s56.NPERM = 200
    s58 = json.loads((LOOP / "step58_sleep_equation/results.json").read_text(encoding="utf-8"))
    s62 = json.loads((LOOP / "step62_upstream_pull/results.json").read_text(encoding="utf-8"))
    sigma, gain = s58["sigma"], s58["gain"]
    target, mouse_prof = s62["mouse_targets"], s62["mouse_profile"]
    work = Path(tempfile.mkdtemp())
    grid = [run_model(a, d, 630, sigma, gain, work) for a in A_GRID for d in D_GRID]
    def loss(r):
        if r["re_late"] is None or r["up_late"] is None:
            return float("inf")
        return (r["re_late"] - target["re_late"]) ** 2 + (r["up_late"] - target["up_late"]) ** 2
    best = min(grid, key=loss)
    a_fit, d_fit = best["a_nrem"], best["d_nrem"]
    print("fitted A_NREM", a_fit, "D_NREM", d_fit, "loss", loss(best), flush=True)
    rows = [run_model(a_fit, d_fit, s, sigma, gain, work, full=True) for s in SEEDS]
    med = up.med
    m = {k: med(rows, k) for k in ("re_early", "re_late", "up_early", "up_mid", "up_late", "rho_all_3_nrem", "rho_all_3_wake", "rho_gap", "ring_ratio")}
    prof = [float(np.median([r["re_by_d"][i] for r in rows if r["re_by_d"][i] is not None])) if any(r["re_by_d"][i] is not None for r in rows) else np.nan
            for i in range(ra.DMAX)]
    diffs = [abs(prof[i] - mouse_prof[i]) for i in range(ra.DMAX) if np.isfinite(prof[i]) and np.isfinite(mouse_prof[i])]
    prof_mad = float(np.mean(diffs)) if len(diffs) >= 5 else None
    crit = {"P1_reset": m["re_early"] is not None and m["re_early"] <= 0.15,
            "P2_inside_up_early": m["up_early"] is not None and 0.3 <= m["up_early"] <= 0.65,
            "P3_nrem_scatter": m["rho_all_3_nrem"] is not None and 0.15 <= m["rho_all_3_nrem"] <= 0.5,
            "P4_curve_level": prof_mad is not None and prof_mad <= 0.05,
            "P5_structure_kept": m["ring_ratio"] is not None and 0.8 <= m["ring_ratio"] <= 1.2,
            "P6_wake_holding": m["rho_all_3_wake"] is not None and m["rho_all_3_wake"] >= 0.9}
    verdict = "FREE_RUNNING_UPSTREAM_EXPLAINS_NREM" if all(crit.values()) else "FREE_RUNNING_UPSTREAM_PARTIAL"
    result = {"schema": "ce-a1-step63-wandering-upstream", "hashes": hashes, "mouse_targets": target, "mouse_profile": mouse_prof,
              "grid": grid, "fit": {"A_NREM": a_fit, "D_NREM": d_fit, "D_NREM_over_D_W": d_fit / up.D_W}, "model_median": m,
              "model_profile": prof, "profile_mean_abs_diff": prof_mad, "criteria": crit, "verdict": verdict, "model_rows": rows}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", verdict, json.dumps(crit), "profile MAD", prof_mad, "D_NREM/D_W", round(d_fit / up.D_W, 1),
          "\nmodel", json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}),
          "\nmodel profile", [round(x, 3) for x in prof], "\nmouse profile", [round(x, 3) for x in mouse_prof])


if __name__ == "__main__":
    main()
