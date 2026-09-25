"""A1 step 53: fly-like walking -> standing protocol (Noorman et al. 2024 Nat Neurosci 27:2207) on the neuron-level
connectome ring. Removes the cue-release confound of step 52: the bump position is set by velocity integration, as in
the fly walking in darkness. Tests holding (standing-bout U2) and smooth integration (slow/fast gain, coverage,
residual velocity vs position). (CONTRACT.md)

Behaviour (one fixed seed, identical for every network): alternating walking U(1, 4) s and standing U(0.3, 2) s,
3600 s; angular velocity during walking = Ornstein-Uhlenbeck, sd 80 deg/s, correlation time 0.3 s, reset to 0 at
each walking onset; 0 while standing. tau = 0.1 s (paper), dt = 0.02 tau, PVA sampled at 10 Hz (every tau).
Networks per dataset (threshold-linear, c = 1):
  literal       step 47 N2 at the step 47 gain; velocity generator A1 (angle-averaged PEN kernel, as step 47 N1)
  homeostasis   step 51 scaling (s, gain); generator diag(s) A1
  direction     step 46 16-direction ring at g*; generator = derivative of W (as step 46)
Velocity: v(t) = omega(t) tau / G, G = bump speed per unit v at the fast calibration (nl.rotation, 24 deg/tau).
Analyses (paper Methods / plotDriftAnalysisFigs.m): standing bouts start = PVA at the last walking frame, end = PVA at
the last standing frame; Watson U2, 500 permutations. Bump velocity (10 Hz) vs omega on walking frames:
slope through origin for 5 <= |omega| < 30 (slow) and |omega| > 90 deg/s (fast); coverage = 16 bins with >= 1 % of
walking frames; residuals of left/right OLS fits binned by position (64 bins), sinusoid R2 (1, 2, 3, 8, 16).

python walk_stand.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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


sb = load("standing_bouts", LOOP / "step52_standing_bout_test/standing_bouts.py")
hr, nl, c46 = sb.hr, sb.nl, sb.c46
tl = c46.tl
TAU_S, SESSION_S, SEED = 0.1, 3600.0, 53
WALK_S, STAND_S = (1.0, 4.0), (0.3, 2.0)
OU_SD, OU_TC = 80.0, 0.3
FRAME = int(round(1.0 / nl.DT))            # 10 Hz = every tau
SLOW, FAST = (5.0, 30.0), 90.0


def behaviour(rng):
    dt_s = nl.DT * TAU_S
    n = int(round(SESSION_S / dt_s))
    omega = np.zeros(n)
    walking = np.zeros(n, bool)
    t, w = 0, True
    a = np.exp(-dt_s / OU_TC)
    b = OU_SD * np.sqrt(1 - a * a)
    while t < n:
        k = int(round(rng.uniform(*(WALK_S if w else STAND_S)) / dt_s))
        k = min(k, n - t)
        if w:
            x, z = 0.0, rng.standard_normal(k)
            seg = np.empty(k)
            for i in range(k):
                x = a * x + b * z[i]
                seg[i] = x
            omega[t:t + k] = seg
            walking[t:t + k] = True
        t += k
        w = not w
    return omega, walking


def calibrate(W, A, ang):
    rot = nl.rotation(W, A, ang)
    sp = rot["speeds"]["1.0"]["speed"]
    ok = bool(np.isfinite(sp) and abs(sp) >= 1.0)
    return (sp / rot["v_fast"] if ok else 24.0 / rot["v_fast"]), ok, rot


def session(W, A, ang, G, omega):
    r, _ = nl.run(W, np.zeros_like(W), None, [(20.0, nl.cue(ang, 0.0), 0.0)])
    v = omega * TAU_S / G
    phase = np.empty(omega.size // FRAME)
    for f in range(phase.size):
        for k in range(f * FRAME, (f + 1) * FRAME):
            r = r + nl.DT * (-r + np.maximum(W @ r + v[k] * (A @ r) + 1.0, 0.0))
        if not np.all(np.isfinite(r)) or r.max() > 1e6:
            return None
        phase[f] = nl.com(r, ang)
    return phase


def analyse(phase, omega, walking, rng):
    nf = phase.size
    om = omega[:nf * FRAME].reshape(nf, FRAME).mean(1)
    wk = walking[:nf * FRAME].reshape(nf, FRAME)[:, -1]
    starts, ends = [], []
    f = 1
    while f < nf:
        if wk[f - 1] and not wk[f]:
            g = f
            while g + 1 < nf and not wk[g + 1]:
                g += 1
            if g + 1 < nf:
                starts.append(phase[f - 1])
                ends.append(phase[g])
            f = g + 1
        else:
            f += 1
    starts, ends = np.array(starts), np.array(ends)
    drift = (ends - starts + 180) % 360 - 180
    out = {"n_bouts": int(starts.size), **sb.u2_perm_test(np.radians(starts), np.radians(ends), rng),
           "median_abs_drift_deg": float(np.median(np.abs(drift))), "p90_abs_drift_deg": float(np.percentile(np.abs(drift), 90))}
    bv = ((np.diff(phase) + 180) % 360 - 180) / TAU_S          # motion from the end of frame f to the end of frame f + 1
    both = wk[:-1] & wk[1:]
    x, y, ph = om[1:][both], bv[both], phase[:-1][both]        # driven by the angular velocity during frame f + 1
    def slope(m):
        return float(np.sum(x[m] * y[m]) / np.sum(x[m] ** 2)) if m.sum() > 10 else float("nan")
    gs = slope((np.abs(x) >= SLOW[0]) & (np.abs(x) < SLOW[1]))
    gf = slope(np.abs(x) > FAST)
    occ = np.histogram(phase[wk], bins=16, range=(0, 360))[0] / max(wk.sum(), 1)
    res = np.empty_like(y)
    for m in (x < 0, x >= 0):
        X = np.c_[x[m], np.ones(m.sum())]
        res[m] = y[m] - X @ np.linalg.lstsq(X, y[m], rcond=None)[0]
    edges = np.linspace(0, 360, 65)
    idx = np.clip(np.digitize(ph, edges) - 1, 0, 63)
    binned = np.array([res[idx == i].mean() if np.any(idx == i) else np.nan for i in range(64)])
    ok = np.isfinite(binned)
    centres = np.radians((edges[:-1] + edges[1:]) / 2)
    out.update({"gain_slow": gs, "gain_fast": gf, "slow_over_fast": gs / gf if np.isfinite(gs) and np.isfinite(gf) and gf != 0 else float("nan"),
                "coverage_bins_ge_1pct": int(np.sum(occ >= 0.01)),
                "residual_R2_by_frequency": {str(w): sb.sinus_r2(centres[ok], binned[ok], w) for w in (1, 2, 3, 8, 16)} if ok.sum() > 8 else None})
    return out


def networks(name, data, M, s46, s47, s51):
    ang = M["ang"]
    a16 = nl.kernel16(M["A_pen"], ang)
    a16 = (a16 - a16[(-np.arange(16)) % 16]) / 2
    A1 = nl.at_offsets(a16, ang)
    A1 = (A1 - A1.T) / 2
    g47 = s47["datasets"][name]["networks"]["0.0"]["g"]
    d51 = s51["datasets"][name]
    s, g51 = np.array(d51["s"]), d51["after"]["g"]
    P, _ = c46.kernels(*data)
    W16 = c46.ring(c46.symmetrise(P["exc"] - P["inh_all"]), s46["datasets"][name]["variants"]["connectome"]["g_star"])
    return {"literal": (g47 * (M["E"] - M["I"]), g47 * A1, ang),
            "homeostasis": (g51 * (s[:, None] * M["E"] - M["I"]), g51 * s[:, None] * A1, ang),
            "direction": (W16, tl.generator(W16), np.radians(np.arange(16) * 22.5))}


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step52_standing_bout_test/standing_bouts.py", LOOP / "step48_homeostatic_scaling/homeostatic_ring.py",
            LOOP / "step47_neuron_level_wells/neuron_level_wells.py", LOOP / "step46_connectome_ring_class/connectome_ring_class.py",
            LOOP / "step41_few_neuron_attractor/tl_ring.py", LOOP / "step41_few_neuron_attractor/few_neuron_ring.py",
            LOOP / "step42_kim_support_ring/kim_support_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s46 = json.loads((LOOP / "step46_connectome_ring_class/results.json").read_text(encoding="utf-8"))
    s47 = json.loads((LOOP / "step47_neuron_level_wells/results.json").read_text(encoding="utf-8"))
    s51 = json.loads((LOOP / "step51_homeostasis_fixed_target/results.json").read_text(encoding="utf-8"))
    omega, walking = behaviour(np.random.default_rng(SEED))
    rng = np.random.default_rng(SEED + 1)
    res = {}
    for name, data in c46.datasets().items():
        M = hr.matrices(*data)
        res[name] = {}
        for label, (W, A, ang) in networks(name, data, M, s46, s47, s51).items():
            G, rot_ok, rot = calibrate(W, A, ang)
            phase = session(W, A, ang, G, omega)
            entry = {"G_deg_per_tau_per_v": G, "calibration_reached_fast": rot_ok, "calibration": rot}
            entry.update({"blow_up": True} if phase is None else analyse(phase, omega, walking, rng))
            res[name][label] = entry
            print(name, label, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in entry.items() if k != "calibration"}), flush=True)
    def hold_ok(e):
        return bool(e.get("p", 0.0) >= 0.05)
    def rot_ok(e):
        r = e.get("slow_over_fast", float("nan"))
        return bool(np.isfinite(r) and 0.8 <= r <= 1.25 and e.get("coverage_bins_ge_1pct", 0) == 16)
    summary = {lab: {"hold_consistent": {k: hold_ok(v[lab]) for k, v in res.items()}, "smooth_rotation": {k: rot_ok(v[lab]) for k, v in res.items()}}
               for lab in ("literal", "homeostasis", "direction")}
    verdict = {"literal_holding": "INCONSISTENT" if sum(not x for x in summary["literal"]["hold_consistent"].values()) >= 2 else "CONSISTENT",
               "homeostasis_holding": "CONSISTENT" if sum(summary["homeostasis"]["hold_consistent"].values()) >= 2 else "INCONSISTENT",
               "homeostasis_smooth_rotation": "PASS" if sum(summary["homeostasis"]["smooth_rotation"].values()) >= 2 else "FAIL",
               "literal_smooth_rotation": "PASS" if sum(summary["literal"]["smooth_rotation"].values()) >= 2 else "FAIL",
               "protocol_valid": bool(sum(summary["direction"]["hold_consistent"][k] and summary["direction"]["smooth_rotation"][k] for k in res) >= 2)}
    result = {"schema": "ce-a1-step53-walk-stand", "hashes": hashes, "fly_p_values": sb.FLY_P, "summary": summary, "verdict": verdict,
              "behaviour": {"n_steps": int(omega.size), "walking_fraction": float(walking.mean()), "omega_sd_walking": float(omega[walking].std())},
              "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", json.dumps(verdict), json.dumps(summary))


if __name__ == "__main__":
    main()
