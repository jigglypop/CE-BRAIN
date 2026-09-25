"""A1 step 61: does short-term synaptic plasticity (Mongillo, Barak & Tsodyks 2008 Science 319:1543; activity-silent
memory) added to the step 58 sleep equation reproduce the faint heading trace that re-emerges after NREM down states
(step 60: rho 0.03 right after the gap -> 0.09 at 0.5-1 s; mismatched control 0.003)? (CONTRACT.md)

Model: step 58 ring (Kim local ring, 16 units, tau 20 ms, dt 1 ms, drive on/off in NREM, same schedule and spike
generation) with facilitation/depression on the neighbour excitation only:
  W_eff = g_E * E * diag(u_j x_j / U0) + R,   E = D (S + S^T),   R = (alpha - 2D) I - beta 11^T   (alpha 2.5, D 1.5, beta 1)
  dx_j/dt = (1 - x_j)/tau_d - u_j x_j R_j,   du_j/dt = (U0 - u_j)/tau_f + U0 (1 - u_j) R_j,   R_j = GAIN r_j (Hz)
  U0 0.2, tau_d 0.2 s, tau_f 1.5 s (Mongillo 2008, as restated by Taher, Torcini & Olmi 2020); GAIN = step 58 gain.
Calibration on wake only: (1) g_E from G_GRID = the value with the smallest maximum noise-free hold error (16 cue
positions, cue 0.5 s then 3 s free, drive 1) among values with a surviving, bounded bump; (2) sigma from SIGMAS closest
to the mouse wake rho(0.3 s) = 0.977 on a full simulated session (seed 610).
Evaluation: 5 simulated mice (seeds 611-615); step 60 re-emergence (rho_by_d, early d 1-2, late d 5-10, pair-specific
denominators), step 57 (NREM scatter, inside-up holding, gap reset), step 56 (ring index).
S1 reset right after the gap: rho_early <= 0.15 (mouse 0.031).
S2 faint re-emergence: rho_late - rho_early >= 0.04 and rho_late <= 0.35 (mouse +0.056, late 0.087).
S3 structure kept: ring index NREM / wake in [0.8, 1.2].      S4 wake holding: wake rho(0.3 s) >= 0.9.
Report (model and mouse): late re-emergence after long (>= 8 non-silent bins) vs short (< 6) preceding up states.

python stp_trace.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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
ra = load("reanchoring", LOOP / "step60_reanchoring/reanchoring.py")
s57, s56, tl = ra.s57, ra.s56, se.tl

ALPHA, DD, BETA = 2.5, 1.5, 1.0
S_ = np.roll(np.eye(16), 1, axis=1)
E = DD * (S_ + S_.T)
R = (ALPHA - 2 * DD) * np.eye(16) - BETA * np.ones((16, 16))
U0, TAU_D, TAU_F = 0.2, 0.2, 1.5
G_GRID = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
SIGMAS = (0.05, 0.1, 0.2, 0.4)
SEEDS = (611, 612, 613, 614, 615)
MOUSE = {"rho_early": 0.031, "rho_late": 0.087, "rho_all_3_wake": 0.977}
LONG_UP, SHORT_UP = 8, 6


def step_stp(r, u, x, c, noise, cue, gE, gain, k):
    Rj = gain * r
    u = u + se.DT * ((U0 - u) / TAU_F + U0 * (1 - u) * Rj)
    x = x + se.DT * ((1 - x) / TAU_D - u * x * Rj)
    x = np.clip(x, 0.0, 1.0)
    W = gE * E * (u * x / U0)[None, :] + R
    inp = W @ r + c + noise + cue
    return r + k * (-r + np.maximum(inp, 0.0)), u, x


def hold_error(gE, gain):
    """Noise-free maximum hold error (deg) of the STP ring with drive 1; None if the bump dies or blows up."""
    k = se.DT / se.TAU
    errs = []
    for c0 in np.arange(16) * 22.5 + 5.625:
        r, u, x = np.zeros(16), np.full(16, U0), np.ones(16)
        cue = np.exp(4.0 * (np.cos(se.ANG - np.radians(c0)) - 1.0))
        for i in range(int(3.5 / se.DT)):
            r, u, x = step_stp(r, u, x, 1.0, 0.0, cue if i < int(0.5 / se.DT) else 0.0, gE, gain, k)
            if not np.all(np.isfinite(r)) or r.max() > 1e4:
                return None
        if r.max() - r.min() < 0.05:
            return None
        pos = np.degrees(np.angle(np.sum(r * np.exp(1j * se.ANG)))) % 360
        errs.append(abs((pos - c0 + 180) % 360 - 180))
    return float(max(errs))


def simulate(sigma, rng, sched, gE, gain):
    c, head, states = sched
    c = np.where(np.isnan(c), se.C_DOWN_PRIMARY, c)
    n = c.size
    r, u, x = np.zeros(16), np.full(16, U0), np.ones(16)
    rates = np.empty((n, 16), dtype=np.float32)
    k = se.DT / se.TAU
    CH = 10000
    for i0 in range(0, n, CH):
        noise = sigma * rng.standard_normal((min(CH, n - i0), 16))
        for j in range(noise.shape[0]):
            i = i0 + j
            cue = np.exp(4.0 * (np.cos(se.ANG - head[i]) - 1.0)) if not np.isnan(head[i]) else 0.0
            r, u, x = step_stp(r, u, x, c[i], noise[j], cue, gE, gain, k)
            rates[i] = r
    return rates


def preceding_up(active, silent, t0):
    """Number of consecutive non-silent bins ending at t0 (the up state before the gap)."""
    k = 0
    while t0 - k >= 0 and not silent[t0 - k]:
        k += 1
    return k


def reemergence_by_up(path, rng):
    """Step 60 analysis split by the preceding up-state length (report)."""
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
    t, u, d = ra.gap_pairs(nrem, active, silent)
    up = np.array([preceding_up(active, silent, a) for a in t]) if t.size else np.array([], int)
    late = (d >= ra.LATE[0]) & (d <= ra.LATE[1])
    return {"late_after_long_up": ra.rho_pairs(t[late & (up >= LONG_UP)], u[late & (up >= LONG_UP)], splits),
            "late_after_short_up": ra.rho_pairs(t[late & (up < SHORT_UP)], u[late & (up < SHORT_UP)], splits),
            "n_long": int((late & (up >= LONG_UP)).sum()), "n_short": int((late & (up < SHORT_UP)).sum())}


def run_model(sigma, seed, gE, gain, work):
    rng = np.random.default_rng(seed)
    sched = se.schedule(rng)
    rates = simulate(sigma, rng, sched, gE, gain)
    path = work / f"stp_s{seed}_sig{sigma}.npz"
    se.spikes_and_save(rates, sched, rng, gain, path)
    r60 = ra.analyse(path, np.random.default_rng(seed + 1))
    r57 = s57.analyse(path, np.random.default_rng(seed + 2))
    r56 = s56.analyse(path, np.random.default_rng(seed + 3))
    rep = reemergence_by_up(path, np.random.default_rng(seed + 4))
    g = lambda dct, s, key: dct.get("states", {}).get(s, {}).get(key)
    out = {"seed": seed, "sigma": sigma, "rho_early": r60.get("rho_early"), "rho_late": r60.get("rho_late"), "rho_by_d": r60.get("rho_by_d"),
           "rho_all_3_wake": g(r57, "wake_home", "rho_all_3"), "rho_all_3_nrem": g(r57, "nrem", "rho_all_3"),
           "rho_cont_2_nrem": g(r57, "nrem", "rho_cont_2"), "rho_gap": g(r57, "nrem", "rho_gap"),
           "ring_wake": g(r56, "wake_home", "ring_index"), "ring_nrem": g(r56, "nrem", "ring_index"), **rep}
    out["ring_ratio"] = out["ring_nrem"] / out["ring_wake"] if out["ring_nrem"] is not None and out["ring_wake"] else None
    path.unlink()
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items() if k != "rho_by_d"}), flush=True)
    return out


def med(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return float(np.median(v)) if v else None


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step58_sleep_equation/sleep_equation.py", LOOP / "step60_reanchoring/reanchoring.py",
            LOOP / "step57_sleep_holding/holding_gap.py", LOOP / "step56_mouse_sleep_ring/mouse_sleep_ring.py",
            LOOP / "step41_few_neuron_attractor/tl_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s56.NPERM = 200
    gain = json.loads((LOOP / "step58_sleep_equation/results.json").read_text(encoding="utf-8"))["gain"]
    herr = {str(g): hold_error(g, gain) for g in G_GRID}
    print("hold error by g_E:", herr, flush=True)
    ok = {g: e for g, e in herr.items() if e is not None}
    if not ok:
        raise SystemExit("no g_E keeps a bounded bump")
    gE = float(min(ok, key=ok.get))
    work = Path(tempfile.mkdtemp())
    cal = [run_model(s, 610, gE, gain, work) for s in SIGMAS]
    good = [r for r in cal if r["rho_all_3_wake"] is not None]
    sigma = min(good, key=lambda r: abs(r["rho_all_3_wake"] - MOUSE["rho_all_3_wake"]))["sigma"]
    print("calibrated g_E", gE, "sigma", sigma, flush=True)
    rows = [run_model(sigma, s, gE, gain, work) for s in SEEDS]
    m = {k: med(rows, k) for k in ("rho_early", "rho_late", "rho_all_3_wake", "rho_all_3_nrem", "rho_cont_2_nrem", "rho_gap", "ring_ratio",
                                   "late_after_long_up", "late_after_short_up")}
    crit = {"S1_reset": m["rho_early"] is not None and m["rho_early"] <= 0.15,
            "S2_faint_reemergence": m["rho_late"] is not None and m["rho_early"] is not None and m["rho_late"] - m["rho_early"] >= 0.04 and m["rho_late"] <= 0.35,
            "S3_structure_kept": m["ring_ratio"] is not None and 0.8 <= m["ring_ratio"] <= 1.2,
            "S4_wake_holding": m["rho_all_3_wake"] is not None and m["rho_all_3_wake"] >= 0.9}
    verdict = "STF_REPRODUCES_FAINT_TRACE" if all(crit.values()) else "STF_DOES_NOT_REPRODUCE"
    mouse = []
    for p in sorted(s56.DATA.glob("*.npz")):
        mouse.append(reemergence_by_up(p, np.random.default_rng(61)))
    mm = {k: med(mouse, k) for k in ("late_after_long_up", "late_after_short_up", "n_long", "n_short")}
    diff = [r["late_after_long_up"] - r["late_after_short_up"] for r in mouse if r["late_after_long_up"] is not None and r["late_after_short_up"] is not None]
    mm["long_minus_short_median"] = float(np.median(diff)) if diff else None
    mm["long_gt_short_fraction"] = float(np.mean(np.array(diff) > 0)) if diff else None
    mm["n_sessions"] = len(diff)
    result = {"schema": "ce-a1-step61-stp-trace", "hashes": hashes, "hold_error_by_gE": herr, "g_E": gE, "sigma": sigma, "gain": gain,
              "calibration": cal, "mouse_targets": MOUSE, "criteria": crit, "verdict": verdict, "model_median": m, "model_rows": rows,
              "mouse_report_preceding_up": mm, "mouse_rows": mouse}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", verdict, json.dumps(crit), "\nmodel", json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}),
          "\nmouse preceding-up report", json.dumps(mm))


if __name__ == "__main__":
    main()
