"""A1 step 62: can ONE extension -- a weak, jittery upstream heading input during NREM (brainstem generator holds the
heading; the NREM relay passes it weakly and noisily, e.g. thalamic burst mode) -- added to the step 58 sleep equation
reproduce the mouse NREM facts of steps 57, 59 and 60 together? Two parameters are fitted on two mouse numbers; four
other mouse numbers are predictions. (CONTRACT.md)

Model (step 58 ring and schedule unchanged: Kim local ring, 16 units, tau 20 ms, dt 1 ms, sigma 0.2, drive on/off):
  generator heading theta_g: exploration = head direction; home-cage wake = random walk with D_W = -ln(0.977)/0.3
  rad^2/s (the mouse wake rho(0.3 s)); NREM = held (D = 0).
  relayed heading psi = theta_g + eta, eta = Ornstein-Uhlenbeck (tau 0.1 s, sd S): wake S = 0, NREM S = S_NREM.
  relay input to unit k = a exp(4 (cos(psi - phi_k) - 1)): wake a = 1 (the exploration cue amplitude), NREM up state
  a = A_NREM, NREM down state a = 0.
Fit: A_NREM in {0.05, 0.1, 0.2, 0.4} x S_NREM in {30, 60, 90} deg, one simulated session (seed 620) each, minimising
  (late re-emergence - mouse)^2 + (inside-up late holding - mouse)^2, both from the frozen estimators below.
Estimators (pair-specific denominators, step 60): re-emergence = step 60 rho(t0, t_d) by d, early d 1-2, late d 5-10;
  inside-up holding = continuous 0.2 s pairs classed by time since the last silent bin (step 59 classes: early 1-3,
  mid 4-6, late >= 7 bins). Mouse values are recomputed here with the same code (31 mice).
Predictions (5 simulated mice, seeds 621-625, medians):
  P1 reset: re-emergence early <= 0.15.       P2 inside-up early in [0.3, 0.65] (mouse ~0.48).
  P3 NREM scatter: step 57 rho_all_3 NREM in [0.15, 0.5] (mouse 0.319).
  P4 time course: Pearson r of the d = 1..10 re-emergence profiles, model vs mouse, >= 0.7.
  P5 structure kept: ring index NREM/wake in [0.8, 1.2].   P6 wake holding: step 57 rho_all_3 wake >= 0.9.

python upstream_pull.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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


se = load("sleep_equation", LOOP / "step58_sleep_equation/sleep_equation.py")
uh = load("upstate_holding", LOOP / "step59_upstate_holding/upstate_holding.py")
ra = load("reanchoring", LOOP / "step60_reanchoring/reanchoring.py")
s57, s56 = ra.s57, ra.s56

D_W = -np.log(0.977) / 0.3
TAU_ETA = 0.1
A_GRID = (0.05, 0.1, 0.2, 0.4)
S_GRID = (30.0, 60.0, 90.0)
SEEDS = (621, 622, 623, 624, 625)


def simulate(sigma, rng, sched, a_nrem, s_nrem):
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
    ea = np.exp(-se.DT / TAU_ETA)
    r = np.zeros(16)
    rates = np.empty((n, 16), dtype=np.float32)
    theta, eta = 0.0, 0.0
    sd_w = np.sqrt(2 * D_W * se.DT)
    s_rad = np.radians(s_nrem)
    CH = 10000
    for i0 in range(0, n, CH):
        m = min(CH, n - i0)
        noise = sigma * rng.standard_normal((m, 16))
        z1, z2 = rng.standard_normal(m), rng.standard_normal(m)
        for j in range(m):
            i = i0 + j
            if not np.isnan(head[i]):
                theta = head[i]                                   # exploration: generator = head direction
            elif not nrem[i]:
                theta += sd_w * z1[j]                             # home-cage wake: head moves
            if nrem[i]:
                eta = ea * eta + s_rad * np.sqrt(1 - ea * ea) * z2[j]
                a = 0.0 if down[i] else a_nrem
            else:
                eta, a = 0.0, 1.0
            inp = se.W @ r + c[i] + noise[j] + a * np.exp(4.0 * (np.cos(se.ANG - (theta + eta)) - 1.0))
            r = r + k * (-r + np.maximum(inp, 0.0))
            rates[i] = r
    return rates


def measures(path, rng):
    """Re-emergence (step 60) and inside-up holding classes (step 59) with pair-specific denominators."""
    S = s56.load(path)
    hd_idx = np.flatnonzero(S["hd_flag"])
    th, tracked = s56.preferred(S, [S["spikes"][i] for i in hd_idx])
    T = max(float(np.max(np.concatenate([s for s in S["spikes"] if s.size]))), float(S["ss"][1].max()))
    edges = np.arange(0, T + s57.BIN, s57.BIN)
    centres = (edges[:-1] + edges[1:]) / 2
    N = np.array([np.histogram(S["spikes"][i], edges)[0] for i in hd_idx], dtype=float)
    state, home, opto = s56.labels(centres, S)
    tot = N.sum(0)
    active, silent = tot >= s57.ACTIVE, tot <= s57.SILENT
    nrem = (state == "nrem") & home
    splits = s57.halves_angles(N, th, rng)
    out = {}
    t, u, d = ra.gap_pairs(nrem, active, silent)
    out["re_by_d"] = [ra.rho_pairs(t[d == k], u[d == k], splits) for k in range(1, ra.DMAX + 1)]
    for name, (lo, hi) in (("re_early", ra.EARLY), ("re_late", ra.LATE)):
        m = (d >= lo) & (d <= hi)
        out[name] = ra.rho_pairs(t[m], u[m], splits)
    seg = np.cumsum(np.r_[1, np.diff(nrem.astype(int)) != 0])
    tc, uc = s57.pair_sets(nrem, active, silent, seg)["cont_2"]
    since = uh.since_silent(silent, seg)[tc]
    for name, (lo, hi) in uh.CLASSES.items():
        m = (since >= lo) & (since <= hi)
        out[f"up_{name}"] = ra.rho_pairs(tc[m], uc[m], splits)
    return out


def run_model(a_nrem, s_nrem, seed, sigma, gain, work, full=False):
    rng = np.random.default_rng(seed)
    sched = se.schedule(rng)
    rates = simulate(sigma, rng, sched, a_nrem, s_nrem)
    path = work / f"pull_s{seed}_a{a_nrem}_s{s_nrem}.npz"
    se.spikes_and_save(rates, sched, rng, gain, path)
    out = {"a_nrem": a_nrem, "s_nrem": s_nrem, "seed": seed, **measures(path, np.random.default_rng(seed + 1))}
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


def med(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return float(np.median(v)) if v else None


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step58_sleep_equation/sleep_equation.py", LOOP / "step59_upstate_holding/upstate_holding.py",
            LOOP / "step60_reanchoring/reanchoring.py", LOOP / "step57_sleep_holding/holding_gap.py",
            LOOP / "step56_mouse_sleep_ring/mouse_sleep_ring.py", LOOP / "step41_few_neuron_attractor/tl_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s56.NPERM = 200
    s58 = json.loads((LOOP / "step58_sleep_equation/results.json").read_text(encoding="utf-8"))
    sigma, gain = s58["sigma"], s58["gain"]
    mouse = [measures(p, np.random.default_rng(62)) for p in sorted(s56.DATA.glob("*.npz"))]
    target = {"re_late": med(mouse, "re_late"), "up_late": med(mouse, "up_late")}
    mouse_med = {k: med(mouse, k) for k in ("re_early", "re_late", "up_early", "up_mid", "up_late")}
    mouse_prof = [float(np.median([m["re_by_d"][i] for m in mouse if m["re_by_d"][i] is not None])) for i in range(ra.DMAX)]
    print("mouse targets", json.dumps(target), "mouse medians", json.dumps(mouse_med), flush=True)
    work = Path(tempfile.mkdtemp())
    grid = [run_model(a, s, 620, sigma, gain, work) for a in A_GRID for s in S_GRID]
    def loss(r):
        if r["re_late"] is None or r["up_late"] is None:
            return float("inf")
        return (r["re_late"] - target["re_late"]) ** 2 + (r["up_late"] - target["up_late"]) ** 2
    best = min(grid, key=loss)
    a_fit, s_fit = best["a_nrem"], best["s_nrem"]
    print("fitted A_NREM", a_fit, "S_NREM", s_fit, "loss", loss(best), flush=True)
    rows = [run_model(a_fit, s_fit, s, sigma, gain, work, full=True) for s in SEEDS]
    m = {k: med(rows, k) for k in ("re_early", "re_late", "up_early", "up_mid", "up_late", "rho_all_3_nrem", "rho_all_3_wake", "rho_gap", "ring_ratio")}
    prof = [float(np.median([r["re_by_d"][i] for r in rows if r["re_by_d"][i] is not None])) if any(r["re_by_d"][i] is not None for r in rows) else np.nan
            for i in range(ra.DMAX)]
    ok_idx = [i for i in range(ra.DMAX) if np.isfinite(prof[i]) and np.isfinite(mouse_prof[i])]
    prof_r = float(np.corrcoef([prof[i] for i in ok_idx], [mouse_prof[i] for i in ok_idx])[0, 1]) if len(ok_idx) >= 5 else None
    crit = {"P1_reset": m["re_early"] is not None and m["re_early"] <= 0.15,
            "P2_inside_up_early": m["up_early"] is not None and 0.3 <= m["up_early"] <= 0.65,
            "P3_nrem_scatter": m["rho_all_3_nrem"] is not None and 0.15 <= m["rho_all_3_nrem"] <= 0.5,
            "P4_time_course": prof_r is not None and prof_r >= 0.7,
            "P5_structure_kept": m["ring_ratio"] is not None and 0.8 <= m["ring_ratio"] <= 1.2,
            "P6_wake_holding": m["rho_all_3_wake"] is not None and m["rho_all_3_wake"] >= 0.9}
    verdict = "ONE_UPSTREAM_PULL_EXPLAINS_NREM" if all(crit.values()) else "UPSTREAM_PULL_PARTIAL"
    result = {"schema": "ce-a1-step62-upstream-pull", "hashes": hashes, "mouse_targets": target, "mouse_medians": mouse_med,
              "mouse_profile": mouse_prof, "grid": grid, "fit": {"A_NREM": a_fit, "S_NREM": s_fit}, "model_median": m, "model_profile": prof,
              "profile_r": prof_r, "criteria": crit, "verdict": verdict, "model_rows": rows, "mouse_rows": mouse}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", verdict, json.dumps(crit), "profile r", prof_r, "\nmodel", json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}),
          "\nmodel profile", [round(x, 3) for x in prof], "\nmouse profile", [round(x, 3) for x in mouse_prof])


if __name__ == "__main__":
    main()
