"""A1 step 59: where inside the NREM up state is the mouse head-direction bump weakly held (step 57: rho 0.645 inside
continuous activity; step 58 model: 0.973)? Onset only (bump re-forming / rebound after the down state) or sustained
through the up state (an upstream source keeps shaking it, e.g. thalamic burst mode)? (CONTRACT.md)

Data: DANDI 000939 extraction (31 mice), step 57 estimator unchanged (split-half noise-free persistence rho, 100 ms
bins, active >= 4 HD spikes with >= 2 per half, silent <= 1). NREM continuous-activity pairs at 0.2 s (t, t+2, all
three bins active) are classified by the time since the last silent bin at t, inside the same NREM run:
early 0.1-0.3 s (1-3 bins), mid 0.4-0.6 s (4-6 bins), late >= 0.7 s (>= 7 bins, including runs without a silent bin).
Q1 onset effect:        rho_early < rho_late in >= 70 % of sessions (>= 30 pairs in each class).
Q2 sustained weakness:  rho_late < 0.9 x rho_wake (wake continuous pairs at 0.2 s) in >= 70 % of sessions.
Verdict: Q2 -> SUSTAINED_WEAK_HOLDING; else Q1 -> ONSET_ONLY; else UNRESOLVED.
Reference: the same analysis on the five step 58 model mice (regenerated with the same seeds, sigma and gain).

python upstate_holding.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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
CLASSES = {"early": (1, 3), "mid": (4, 6), "late": (7, 10 ** 9)}
MIN_PAIRS = 30


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s57 = load("holding_gap", LOOP / "step57_sleep_holding/holding_gap.py")
s56 = s57.s56
se = load("sleep_equation", LOOP / "step58_sleep_equation/sleep_equation.py")


def since_silent(silent, seg):
    out = np.empty(silent.size, dtype=np.int64)
    last, cur = -10 ** 9, None
    for i in range(silent.size):
        if seg[i] != cur:
            cur, last = seg[i], -10 ** 9
        if silent[i]:
            last = i
        out[i] = i - last
    return out


def analyse(path, rng):
    S = s56.load(path)
    hd_idx = np.flatnonzero(S["hd_flag"])
    info = {"session": path.stem}
    if hd_idx.size < s56.MIN_HD:
        return {**info, "qualifies": False}
    th, tracked = s56.preferred(S, [S["spikes"][i] for i in hd_idx])
    T = max(float(np.max(np.concatenate([s for s in S["spikes"] if s.size]))), float(S["ss"][1].max()))
    edges = np.arange(0, T + s57.BIN, s57.BIN)
    centres = (edges[:-1] + edges[1:]) / 2
    N = np.array([np.histogram(S["spikes"][i], edges)[0] for i in hd_idx], dtype=float)
    state, home, opto = s56.labels(centres, S)
    tot = N.sum(0)
    active, silent = tot >= s57.ACTIVE, tot <= s57.SILENT
    nrem, wake = (state == "nrem") & home, (state == "wake") & home
    if nrem.sum() * s57.BIN < s56.MIN_NREM or tracked < s56.MIN_TRACK:
        return {**info, "qualifies": False}
    splits = s57.halves_angles(N, th, rng)
    out = {**info, "qualifies": True}
    segw = np.cumsum(np.r_[1, np.diff(wake.astype(int)) != 0])
    tw, uw = s57.pair_sets(wake, active, silent, segw)["cont_2"]
    out["rho_wake"] = s57.rho(tw, uw, splits, wake & active)
    seg = np.cumsum(np.r_[1, np.diff(nrem.astype(int)) != 0])
    t, u = s57.pair_sets(nrem, active, silent, seg)["cont_2"]
    since = since_silent(silent, seg)[t]
    for name, (lo, hi) in CLASSES.items():
        m = (since >= lo) & (since <= hi)
        out[f"n_{name}"] = int(m.sum())
        out[f"rho_{name}"] = s57.rho(t[m], u[m], splits, nrem & active) if m.sum() >= MIN_PAIRS else None
    e, l, w = out["rho_early"], out["rho_late"], out["rho_wake"]
    out["Q1"] = None if (e is None or l is None) else bool(e < l)
    out["Q2"] = None if (l is None or w is None) else bool(l < 0.9 * w)
    return out


def verdict_of(rows):
    q1 = [r["Q1"] for r in rows if r.get("Q1") is not None]
    q2 = [r["Q2"] for r in rows if r.get("Q2") is not None]
    f1 = float(np.mean(q1)) if q1 else None
    f2 = float(np.mean(q2)) if q2 else None
    v = "SUSTAINED_WEAK_HOLDING" if (f2 is not None and f2 >= 0.7) else ("ONSET_ONLY" if (f1 is not None and f1 >= 0.7) else "UNRESOLVED")
    med = {k: (float(np.median([r[k] for r in rows if r.get(k) is not None])) if any(r.get(k) is not None for r in rows) else None)
           for k in ("rho_wake", "rho_early", "rho_mid", "rho_late", "n_early", "n_mid", "n_late")}
    return {"Q1_fraction": f1, "Q1_n": len(q1), "Q2_fraction": f2, "Q2_n": len(q2), "verdict": v, "median": med}


def model_rows(rng_seed_offset=0):
    work = Path(tempfile.mkdtemp())
    s58 = json.loads((LOOP / "step58_sleep_equation/results.json").read_text(encoding="utf-8"))
    sigma, gain = s58["sigma"], s58["gain"]
    rows = []
    for seed in se.SEEDS:
        rng = np.random.default_rng(seed)                        # same call order as step 58 run_one
        sched = se.schedule(rng)
        rates = se.simulate(sigma, se.C_DOWN_PRIMARY, rng, sched)
        path = work / f"model_s{seed}.npz"
        se.spikes_and_save(rates, sched, rng, gain, path)
        rows.append(analyse(path, np.random.default_rng(seed + 1)))
        path.unlink()
        print("model", seed, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items() if k != "session"}), flush=True)
    return rows


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step57_sleep_holding/holding_gap.py", LOOP / "step56_mouse_sleep_ring/mouse_sleep_ring.py",
            LOOP / "step58_sleep_equation/sleep_equation.py", LOOP / "step41_few_neuron_attractor/tl_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    rng = np.random.default_rng(59)
    mouse = []
    for p in sorted(s56.DATA.glob("*.npz")):
        r = analyse(p, rng)
        mouse.append(r)
        print(r["session"][:22], json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != "session"}), flush=True)
    mq = [r for r in mouse if r.get("qualifies")]
    model = model_rows()
    result = {"schema": "ce-a1-step59-upstate-holding", "hashes": hashes, "mouse": verdict_of(mq), "model_reference": verdict_of(model),
              "sessions": mouse, "model_sessions": model}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("MOUSE", json.dumps(result["mouse"]), "\nMODEL", json.dumps(result["model_reference"]))


if __name__ == "__main__":
    main()
