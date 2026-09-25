"""A1 step 47: at the step 46 optimum, does the per-neuron connectome wiring keep the continuous attractor, or do
wells appear, and how much homogenisation removes them? (CONTRACT.md)

Networks (threshold-linear, tau dr/dt = -r + [W r + c + v A r + I]_+, c = 1, as in steps 41-46):
  N0  16-direction homogeneous ring (step 46 symmetric kernel, gain g*)
  N1  one unit per E-PG neuron, pair weights = step 46 kernel at the pair's angular offset (only cell-count heterogeneity)
  N2  one unit per E-PG neuron, actual flow-normalised weights (symmetric part), i.e. full synaptic heterogeneity
  Nh  (1 - h) N2 + h N1 for h in H_LEVELS
Gain: g1 = g* 16 / n_EPG (same total input as the 16-unit ring), then the best gain within +-20 % for each network
(minimal hold error, 16 positions). Velocity generator: connectome PEN pathway difference A = (F_PEN_left - F_PEN_right)/2.

python neuron_level_wells.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
S46 = LOOP / "step46_connectome_ring_class"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


c46 = load("connectome_ring_class", S46 / "connectome_ring_class.py")
su, h22, gi = c46.su, c46.h22, c46.gi
H_LEVELS = (0.0, 0.25, 0.5, 0.75, 0.9, 1.0)
CUES = np.arange(0, 360, 5.625)
CUES_CAL = np.arange(0, 360, 22.5) + 5.625
DT, T_CUE, T_HOLD = 0.02, 20.0, 100.0
G_REL = np.linspace(0.8, 1.2, 41)
TARGET_FAST, V_FRACTIONS, T_ROT, FIT_FROM = 24.0, (1 / 32, 1 / 8, 1.0), 60.0, 10.0


def matrices(A, ty, inst, sd, nt):
    chosen, members = gi.select(A, ty, nt)
    base = [v for v in range(len(ty)) if ty[v] in gi.BASE]
    nodes = np.array(sorted(base + [v for t in chosen for v in members[t]]))
    kind = np.array([ty[v] for v in nodes])
    Wraw, epg, ang, basis, gamma = su.raw_network(A, ty, inst, sd, nt)
    C = np.abs(Wraw)
    tot_in = np.asarray(A.sum(axis=0)).ravel()[nodes]
    E = epg
    def flow(mask):
        X = np.flatnonzero(mask)
        return C[np.ix_(E, X)] @ np.diag(1 / np.maximum(tot_in[X], 1)) @ C[np.ix_(X, E)]
    is_pen = np.char.startswith(kind.astype(str), "PEN")
    exc = C[np.ix_(E, E)] + flow(is_pen) + flow(kind == "PEG")
    inh = flow(kind == "Delta7") + flow(np.isin(kind, sorted(chosen)))
    penL, penR = flow(is_pen & (gamma > 0)), flow(is_pen & (gamma < 0))
    return {"K_full": exc - inh, "A_pen": (penL - penR) / 2, "ang": np.asarray(ang, float)}


def kernel16(M, ang):
    off = (np.degrees(ang)[:, None] - np.degrees(ang)[None, :]) % 360
    b = np.round(off / 22.5).astype(int) % 16
    return np.array([M[b == k].mean() for k in range(16)])


def at_offsets(k16, ang):
    """16-bin kernel evaluated at every pair's angular offset (circular linear interpolation)."""
    off = (np.degrees(ang)[:, None] - np.degrees(ang)[None, :]) % 360
    x = np.arange(17) * 22.5
    y = np.r_[k16, k16[0]]
    return np.interp(off, x, y)


def run(W, A, r0, phases, every=0):
    n = W.shape[0]
    r = np.zeros(n) if r0 is None else r0.copy()
    trace = []
    for dur, I, v in phases:
        M = W + v * A
        for s in range(int(round(dur / DT))):
            r = r + DT * (-r + np.maximum(M @ r + 1.0 + I, 0.0))
            if not np.all(np.isfinite(r)) or r.max() > 1e6:
                return None, None
            if every and s % every == 0:
                trace.append(r.copy())
    return r, trace


def com(r, ang):
    return float(np.degrees(np.angle(np.sum(r * np.exp(1j * ang)))) % 360)


def cue(ang, c_deg):
    return np.exp(4.0 * (np.cos(ang - np.radians(c_deg)) - 1))


def hold_errors(W, ang, cues):
    errs = []
    for c in cues:
        r, _ = run(W, np.zeros_like(W), None, [(T_CUE, cue(ang, c), 0.0), (T_HOLD, 0.0, 0.0)])
        if r is None:
            return None
        errs.append(float((com(r, ang) - c + 180) % 360 - 180))
    return np.array(errs)


def best_gain(Kn, ang, g1):
    best = None
    for f in G_REL:
        e = hold_errors(f * g1 * Kn, ang, CUES_CAL)
        if e is None:
            continue
        m = float(np.max(np.abs(e)))
        if best is None or m < best[1]:
            best = (float(f * g1), m)
    return best


def wells(finals):
    ends = []
    for f in sorted(np.mod(finals, 360)):
        if not ends or min(abs((f - e + 180) % 360 - 180) for e in ends) > 11.25:
            ends.append(f)
    return len(ends)


def rotation(W, A, ang):
    """Bump speed per unit v at the fast end (calibrated to TARGET_FAST deg/tau) and gains at slower speeds."""
    def speed(v):
        r, tr = run(W, A, None, [(T_CUE, cue(ang, 0.0), 0.0), (T_ROT, 0.0, v)], every=int(0.5 / DT))
        if r is None:
            return float("nan")
        ph = np.degrees(np.unwrap([np.angle(np.sum(x * np.exp(1j * ang))) for x in tr[int(T_CUE / 0.5):]]))
        t = np.arange(ph.size) * 0.5
        m = t >= FIT_FROM
        return float(np.polyfit(t[m], ph[m], 1)[0]) if m.sum() > 3 else float("nan")
    lo, hi = 0.0, 0.05
    while abs(speed(hi)) < TARGET_FAST and hi < 50:
        hi *= 2
    for _ in range(12):
        mid = (lo + hi) / 2
        if abs(speed(mid)) >= TARGET_FAST:
            hi = mid
        else:
            lo = mid
    out = {}
    for fr in V_FRACTIONS:
        s = speed(fr * hi)
        out[str(fr)] = {"speed": s, "gain": s / (fr * hi)}
    return {"v_fast": hi, "speeds": out, "slow_over_fast_gain": out[str(1 / 32)]["gain"] / out["1.0"]["gain"]}


def analyse(M, g_star):
    ang = M["ang"]
    n = ang.size
    Kfull = (M["K_full"] + M["K_full"].T) / 2
    k16 = c46.symmetrise(kernel16(M["K_full"], ang))
    K1 = at_offsets(k16, ang)
    K1 = (K1 + K1.T) / 2
    a16 = kernel16(M["A_pen"], ang)
    a16 = (a16 - a16[(-np.arange(16)) % 16]) / 2
    A1 = at_offsets(a16, ang)
    A1 = (A1 - A1.T) / 2
    g1 = g_star * 16 / n
    out = {"n_epg": int(n), "g1_mapped": g1, "networks": {}}
    for h in H_LEVELS:
        Kh = (1 - h) * Kfull + h * K1
        bg = best_gain(Kh, ang, g1)
        if bg is None:
            out["networks"][str(h)] = {"exists": False}
            continue
        g = bg[0]
        e = hold_errors(g * Kh, ang, CUES)
        if e is None:                      # blow-up at one of the 64 positions: record as failure
            out["networks"][str(h)] = {"g": g, "g_over_mapped": g / g1, "blow_up_in_C1": True, "C1": False}
            print("   h", h, "blow-up in C1 at g", g, flush=True)
            continue
        finals = (CUES + e) % 360
        entry = {"g": g, "g_over_mapped": g / g1, "max_abs_err": float(np.max(np.abs(e))), "median_abs_err": float(np.median(np.abs(e))),
                 "retention_22p5": float(np.mean(np.abs(e) <= 22.5)), "distinct_end_positions": wells(finals),
                 "C1": bool(np.max(np.abs(e)) <= 5.625 and np.median(np.abs(e)) <= 2.0)}
        if h in (0.0, 1.0):
            entry["rotation"] = rotation(g * Kh, g * (M["A_pen"] if h == 0.0 else A1), ang)
        out["networks"][str(h)] = entry
        print("   h", h, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in entry.items() if k != "rotation"}),
              "rot" if "rotation" in entry else "", json.dumps(entry.get("rotation", {}).get("slow_over_fast_gain")), flush=True)
    ok = [h for h in H_LEVELS if out["networks"].get(str(h), {}).get("C1")]
    out["min_h_for_C1"] = min(ok) if ok else None
    return out


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), S46 / "connectome_ring_class.py", LOOP / "step41_few_neuron_attractor/tl_ring.py",
            LOOP / "step41_few_neuron_attractor/few_neuron_ring.py", LOOP / "step42_kim_support_ring/kim_support_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [n for n, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s46 = json.loads((S46 / "results.json").read_text(encoding="utf-8"))
    res = {}
    for name, data in c46.datasets().items():
        g_star = s46["datasets"][name]["variants"]["connectome"]["g_star"]
        print("==", name, "g*", g_star, flush=True)
        res[name] = analyse(matrices(*data), g_star)
    wells_full = {n: bool(not d["networks"]["0.0"].get("C1", False)) for n, d in res.items()}
    result = {"schema": "ce-a1-step47-neuron-level-wells", "hashes": hashes, "per_dataset_full_wiring_has_wells": wells_full,
              "verdict": "NEURON_LEVEL_WIRING_HAS_WELLS" if sum(wells_full.values()) >= 2 else "NEURON_LEVEL_WIRING_CONTINUOUS",
              "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], wells_full, {n: d["min_h_for_C1"] for n, d in res.items()})


if __name__ == "__main__":
    main()
