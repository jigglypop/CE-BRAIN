"""A1 step 58: the sleep equation. Does the existing compass ring (Kim 2017 local ring at the Noorman 2024 optimum,
threshold-linear, step 42 'local_opt') plus ONE change -- the drive c(t) alternating on/off (NREM up/down states)
instead of staying on (wake/REM) -- reproduce the mouse sleep facts of steps 56-57 when simulated spikes are put
through the SAME analysis code? (CONTRACT.md)

Model: tau dr/dt = -r + [W r + c(t) + I(t) + sigma xi(t)]_+, W = local_ring(2.5, 1.5, 1), 16 units, tau = 20 ms,
dt = 1 ms, xi white per step. Wake/REM: c = 1. NREM: up c = C_UP for U(0.5, 1.0) s, down c = C_DOWN for
U(0.1, 0.3) s. C_UP = 1 / up duty (mean rate kept equal to wake, the step 56 rate result). C_DOWN = -1 (primary),
0 (report). Exploration (tuning): cue 1.0 x von Mises (kappa 4) at a random-walk head direction.
Spikes: 3 cells per unit (48 HD cells), Poisson, rate = GAIN r + 0.1 Hz, GAIN such that the mean wake HD rate is 2 Hz;
4 non-HD cells at 5 Hz. Session: 10 min exploration, then 50 min home cage alternating wake and NREM blocks U(3, 6) min.
Calibration (wake only): sigma from a grid so that wake rho(0.3 s) of the step 57 estimator is closest to the mouse
median 0.977. Evaluation: 5 simulated mice (seeds), step 56 and step 57 analysis functions unchanged.
Mouse targets (steps 56-57 medians): ring index NREM/wake 0.98; rho(0.3 s) wake 0.977, NREM 0.319; rho across
silent gaps -0.027; rho inside continuous activity (0.2 s) NREM 0.645.
M1 reset: rho_gap <= 0.2.  M2 NREM scatters: rho_all_3 NREM in [0.1, 0.55] and wake >= 0.9.
M3 structure kept: ring index NREM/wake in [0.8, 1.2].  M4 weak holding inside up states: rho_cont_2 NREM in [0.4, 0.85].
(medians over the 5 simulated mice)

python sleep_equation.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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


tl = load("tl_ring", LOOP / "step41_few_neuron_attractor/tl_ring.py")
s56 = load("mouse_sleep_ring", LOOP / "step56_mouse_sleep_ring/mouse_sleep_ring.py")
s57 = load("holding_gap", LOOP / "step57_sleep_holding/holding_gap.py")

TAU, DT = 0.020, 0.001
W = tl.local_ring(2.5, 1.5, 1.0)
ANG = np.radians(np.arange(16) * 22.5)
UP, DOWN = (0.5, 1.0), (0.1, 0.3)
C_UP = 1.0 / (np.mean(UP) / (np.mean(UP) + np.mean(DOWN)))
C_DOWN_PRIMARY, C_DOWN_REPORT = -1.0, 0.0
EXPLORE_S, HOME_S, BLOCK = 600.0, 3000.0, (180.0, 360.0)
CELLS_PER_UNIT, BASE_HZ, TARGET_HZ, N_OTHER, OTHER_HZ = 3, 0.1, 2.0, 4, 5.0
SIGMAS = (0.02, 0.05, 0.1, 0.2, 0.4)
MOUSE = {"ring_ratio": 0.98, "rho_all_3_wake": 0.977, "rho_all_3_nrem": 0.319, "rho_gap": -0.027, "rho_cont_2_nrem": 0.645}
SEEDS = (581, 582, 583, 584, 585)


def schedule(rng):
    """Per-step drive c, cue input angle (nan = none), state labels and epoch boundaries."""
    n_ex, n_home = int(EXPLORE_S / DT), int(HOME_S / DT)
    n = n_ex + n_home
    c = np.ones(n)
    head = np.full(n, np.nan)
    om, th = 0.0, 0.0                                              # head direction random walk (OU angular velocity)
    a = np.exp(-DT / 0.5)
    for i in range(n_ex):
        om = a * om + np.radians(90.0) * np.sqrt(1 - a * a) * rng.standard_normal()
        th += om * DT
        head[i] = th
    states, t, wake = [("wake", 0.0, EXPLORE_S)], EXPLORE_S, True
    while t < EXPLORE_S + HOME_S:
        d = min(rng.uniform(*BLOCK), EXPLORE_S + HOME_S - t)
        states.append(("wake" if wake else "nrem", t, t + d))
        if not wake:
            i, j = int(round(t / DT)), int(round((t + d) / DT))
            while i < j:
                u, dn = int(rng.uniform(*UP) / DT), int(rng.uniform(*DOWN) / DT)
                c[i:min(i + u, j)] = C_UP
                c[min(i + u, j):min(i + u + dn, j)] = np.nan               # marks down; value set per variant
                i += u + dn
        t += d
        wake = not wake
    return c, head, states


def simulate(sigma, c_down, rng, sched):
    c, head, states = sched
    c = np.where(np.isnan(c), c_down, c)
    n = c.size
    r = np.zeros(16)
    rates = np.empty((n, 16), dtype=np.float32)
    k = DT / TAU
    CH = 10000
    for i0 in range(0, n, CH):                                   # noise drawn per chunk (memory)
        noise = sigma * rng.standard_normal((min(CH, n - i0), 16))
        for j in range(noise.shape[0]):
            i = i0 + j
            inp = W @ r + c[i] + noise[j]
            if not np.isnan(head[i]):
                inp = inp + np.exp(4.0 * (np.cos(ANG - head[i]) - 1.0))
            r = r + k * (-r + np.maximum(inp, 0.0))
            rates[i] = r
    return rates


def spikes_and_save(rates, sched, rng, gain, path):
    c, head, states = sched
    n = rates.shape[0]
    t = np.arange(n) * DT
    unit = np.repeat(np.arange(16), CELLS_PER_UNIT)
    trains = []
    for u in unit:
        lam = (gain * rates[:, u] + BASE_HZ) * DT
        trains.append(t[rng.random(n) < lam])
    for _ in range(N_OTHER):
        trains.append(t[rng.random(n) < OTHER_HZ * DT])
    idx = np.cumsum([s.size for s in trains])
    ex = ~np.isnan(head)
    ht = t[ex][::10]
    hd = np.degrees(np.mod(head[ex][::10], 2 * np.pi))
    np.savez_compressed(path, spike_times=np.concatenate(trains), spike_times_index=idx,
                        unit_id=np.arange(len(trains)), is_head_direction=np.r_[np.ones(unit.size, bool), np.zeros(N_OTHER, bool)],
                        is_excitatory=np.r_[np.ones(unit.size, bool), np.zeros(N_OTHER, bool)],
                        is_fast_spiking=np.r_[np.zeros(unit.size, bool), np.ones(N_OTHER, bool)],
                        ss_start=np.array([s[1] for s in states]), ss_stop=np.array([s[2] for s in states]),
                        ss_state=np.array([s[0] for s in states]),
                        ep_start=np.array([0.0, EXPLORE_S]), ep_stop=np.array([EXPLORE_S, EXPLORE_S + HOME_S]),
                        ep_tag=np.array(["wake_square", "home_cage"]), hd_t=ht, hd=hd)


def mean_wake_rate(rates, sched):
    c, head, states = sched
    t = np.arange(rates.shape[0]) * DT
    m = np.zeros(t.size, bool)
    for s, a, b in states:
        if s == "wake" and a >= EXPLORE_S:
            m |= (t >= a) & (t < b)
    return float(rates[m].mean())


def run_one(sigma, c_down, seed, gain, workdir):
    rng = np.random.default_rng(seed)
    sched = schedule(rng)
    rates = simulate(sigma, c_down, rng, sched)
    if gain is None:
        gain = TARGET_HZ / mean_wake_rate(rates, sched)
    path = workdir / f"sim_s{seed}_sig{sigma}_cd{c_down}.npz"
    spikes_and_save(rates, sched, rng, gain, path)
    r57 = s57.analyse(path, np.random.default_rng(seed + 1))
    r56 = s56.analyse(path, np.random.default_rng(seed + 2))
    st57, st56 = r57.get("states", {}), r56.get("states", {})
    g = lambda d, s, k: d.get(s, {}).get(k)
    out = {"sigma": sigma, "c_down": c_down, "seed": seed, "gain": gain,
           "rho_all_3_wake": g(st57, "wake_home", "rho_all_3"), "rho_all_3_nrem": g(st57, "nrem", "rho_all_3"),
           "rho_gap": g(st57, "nrem", "rho_gap"), "rho_gap_matched_cont": g(st57, "nrem", "rho_gap_matched_cont"),
           "rho_cont_2_nrem": g(st57, "nrem", "rho_cont_2"), "rho_cont_2_wake": g(st57, "wake_home", "rho_cont_2"),
           "silent_nrem": g(st57, "nrem", "silent_fraction"), "silent_wake": g(st57, "wake_home", "silent_fraction"),
           "ring_wake": g(st56, "wake_home", "ring_index"), "ring_nrem": g(st56, "nrem", "ring_index"),
           "C_wake": g(st56, "wake_home", "C"), "C_nrem": g(st56, "nrem", "C")}
    out["ring_ratio"] = (out["ring_nrem"] / out["ring_wake"]) if out["ring_nrem"] is not None and out["ring_wake"] else None
    tr = r56.get("transition", {})
    out["rate_change_index_at_waking"] = tr.get("hd_rate", {}).get("change_index")
    path.unlink()
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items()}), flush=True)
    return out


def med(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return float(np.median(v)) if v else None


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step41_few_neuron_attractor/tl_ring.py", LOOP / "step56_mouse_sleep_ring/mouse_sleep_ring.py",
            LOOP / "step57_sleep_holding/holding_gap.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s56.NPERM = 200                                               # permutation count for the simulated sessions
    work = Path(tempfile.mkdtemp())
    print("== calibration (wake rho(0.3 s) only)", flush=True)
    cal = [run_one(s, C_DOWN_PRIMARY, 580, None, work) for s in SIGMAS]
    ok = [r for r in cal if r["rho_all_3_wake"] is not None]
    best = min(ok, key=lambda r: abs(r["rho_all_3_wake"] - MOUSE["rho_all_3_wake"]))
    sigma, gain = best["sigma"], best["gain"]
    print("== calibrated sigma", sigma, "gain", gain, flush=True)
    res = {}
    for cd in (C_DOWN_PRIMARY, C_DOWN_REPORT):
        rows = [run_one(sigma, cd, s, gain, work) for s in SEEDS]
        res[str(cd)] = {"rows": rows, "median": {k: med(rows, k) for k in rows[0] if k not in ("seed", "sigma", "c_down")}}
    m = res[str(C_DOWN_PRIMARY)]["median"]
    crit = {"M1_reset": m["rho_gap"] is not None and m["rho_gap"] <= 0.2,
            "M2_nrem_scatters": m["rho_all_3_nrem"] is not None and 0.1 <= m["rho_all_3_nrem"] <= 0.55 and (m["rho_all_3_wake"] or 0) >= 0.9,
            "M3_structure_kept": m["ring_ratio"] is not None and 0.8 <= m["ring_ratio"] <= 1.2,
            "M4_weak_holding_inside_up": m["rho_cont_2_nrem"] is not None and 0.4 <= m["rho_cont_2_nrem"] <= 0.85}
    verdict = "SLEEP_EQUATION_REPRODUCES_MOUSE" if all(crit.values()) else "SLEEP_EQUATION_PARTIAL"
    result = {"schema": "ce-a1-step58-sleep-equation", "hashes": hashes, "calibration": cal, "sigma": sigma, "gain": gain,
              "c_up": C_UP, "mouse_targets": MOUSE, "criteria": crit, "verdict": verdict, "variants": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", verdict, json.dumps(crit), "primary medians", json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()}))


if __name__ == "__main__":
    main()
