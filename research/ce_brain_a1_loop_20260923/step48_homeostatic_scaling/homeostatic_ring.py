"""A1 step 48: does homeostatic synaptic scaling (Renart, Song & Wang 2003 Neuron 38:473) remove the wells of the
per-neuron connectome ring (step 47 N2) at the few-neuron optimum, and keep the selection signature? (CONTRACT.md)

Network: step 47 N2 (one unit per E-PG, flow-normalised connectome weights, symmetric part), threshold-linear, c = 1:
  W = g (diag(s) E - I)       E: excitatory flows (direct + PEN + PEG), I: inhibitory flows (Delta7 + ring/ExR)
Homeostasis (Renart 2003: all excitatory synapses onto a neuron scaled by one factor so that its time-averaged rate
approaches a common target): the bump visits the 16 headings (cue 20 tau, hold 30 tau each); r_i = mean rate over the
holds; s_i <- s_i clip((target / r_i)^ETA, 0.5, 2), target = population mean of r; EPOCHS epochs.
Then the gain is re-optimised within +-20 % (minimal hold error, 16 positions) and the tests are run.

python homeostatic_ring.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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
S47 = LOOP / "step47_neuron_level_wells"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


nl = load("neuron_level_wells", S47 / "neuron_level_wells.py")
c46, su, gi = nl.c46, nl.su, nl.gi
EPOCHS, ETA = 30, 0.5
HEADINGS = np.arange(16) * 22.5
T_CUE, T_HOLD_H = 20.0, 30.0
A_FIRST, A_MAX, BISECT = 5.0, 10.0, 12
T_FIRST, T_SECOND, T_AFTER = 20.0, 15.0, 30.0


def matrices(A, ty, inst, sd, nt):
    """E and I separately (same flows as step 47), symmetric parts; PEN left/right difference as velocity generator."""
    chosen, members = gi.select(A, ty, nt)
    base = [v for v in range(len(ty)) if ty[v] in gi.BASE]
    nodes = np.array(sorted(base + [v for t in chosen for v in members[t]]))
    kind = np.array([ty[v] for v in nodes])
    Wraw, epg, ang, basis, gamma = su.raw_network(A, ty, inst, sd, nt)
    C = np.abs(Wraw)
    tot_in = np.asarray(A.sum(axis=0)).ravel()[nodes]
    Eix = epg

    def flow(mask):
        X = np.flatnonzero(mask)
        return C[np.ix_(Eix, X)] @ np.diag(1 / np.maximum(tot_in[X], 1)) @ C[np.ix_(X, Eix)]
    is_pen = np.char.startswith(kind.astype(str), "PEN")
    E = C[np.ix_(Eix, Eix)] + flow(is_pen) + flow(kind == "PEG")
    I = flow(kind == "Delta7") + flow(np.isin(kind, sorted(chosen)))
    A_pen = (flow(is_pen & (gamma > 0)) - flow(is_pen & (gamma < 0))) / 2
    return {"E": (E + E.T) / 2, "I": (I + I.T) / 2, "A_pen": A_pen, "ang": np.asarray(ang, float)}


def activity_profile(W, ang):
    """Mean rate of each neuron over holds at the 16 headings."""
    acc = np.zeros(ang.size)
    n = 0
    for h in HEADINGS:
        r, tr = nl.run(W, np.zeros_like(W), None, [(T_CUE, nl.cue(ang, h), 0.0), (T_HOLD_H, 0.0, 0.0)], every=int(1.0 / nl.DT))
        if r is None:
            return None
        hold = tr[int(T_CUE / 1.0):]
        acc += np.mean(hold, axis=0)
        n += 1
    return acc / n


def homeostasis(M, g):
    s = np.ones(M["ang"].size)
    hist = []
    for ep in range(EPOCHS):
        W = g * (s[:, None] * M["E"] - M["I"])
        r = activity_profile(W, M["ang"])
        if r is None:
            hist.append({"epoch": ep, "blow_up": True})
            s = s * 0.9
            continue
        target = r.mean()
        hist.append({"epoch": ep, "cv": float(r.std() / max(r.mean(), 1e-12)), "silent": int(np.sum(r < 1e-6))})
        s = np.clip(s * np.clip((target / np.maximum(r, 1e-9)) ** ETA, 0.5, 2.0), 0.1, 10.0)
    return s, hist


def dir_profile(r, ang):
    d = np.round(np.degrees(ang) / 22.5).astype(int) % 16
    return np.array([r[d == k].mean() if np.any(d == k) else 0.0 for k in range(16)])


def bump_ok(r, ang, amp0):
    p = dir_profile(r, ang)
    q = p - p.min()
    if q.max() <= 1e-9:
        return False
    peaks = int(np.sum((q > np.roll(q, 1)) & (q >= np.roll(q, -1)) & (q > 0.5 * q.max())))
    return peaks == 1 and q.max() / max(p.max(), 1e-12) >= 0.3 and r.max() >= 0.25 * amp0


def wedge(ang, c, amp):
    d = (np.degrees(ang) - c + 180) % 360 - 180
    return amp * (np.abs(d) <= 11.25).astype(float)


def jumped(W, ang, amp0, b, delta, a):
    r, _ = nl.run(W, np.zeros_like(W), None, [(T_CUE, nl.cue(ang, b), 0.0), (T_FIRST, wedge(ang, b, A_FIRST * amp0), 0.0),
                                                 (T_SECOND, wedge(ang, b + delta, a * amp0), 0.0), (T_AFTER, 0.0, 0.0)])
    if r is None:
        return False
    return bool(bump_ok(r, ang, amp0) and abs((nl.com(r, ang) - (b + delta) + 180) % 360 - 180) <= 22.5)


def threshold(W, ang, amp0, b, delta):
    if not jumped(W, ang, amp0, b, delta, A_MAX):
        return None
    lo, hi = 0.0, A_MAX
    for _ in range(BISECT):
        mid = (lo + hi) / 2
        if jumped(W, ang, amp0, b, delta, mid):
            hi = mid
        else:
            lo = mid
    return hi


def tests(W, A, ang):
    r0, _ = nl.run(W, np.zeros_like(W), None, [(T_CUE, nl.cue(ang, 0.0), 0.0), (100.0, 0.0, 0.0)])
    amp0 = float(r0.max()) if r0 is not None else float("nan")
    e = nl.hold_errors(W, ang, nl.CUES)
    out = {"amp0": amp0}
    if e is None:
        out["blow_up"] = True
        return out
    finals = (nl.CUES + e) % 360
    out.update({"max_abs_err": float(np.max(np.abs(e))), "median_abs_err": float(np.median(np.abs(e))),
                "retention_22p5": float(np.mean(np.abs(e) <= 22.5)), "distinct_end_positions": nl.wells(finals),
                "C1": bool(np.max(np.abs(e)) <= 5.625 and np.median(np.abs(e)) <= 2.0)})
    out["rotation"] = nl.rotation(W, A, ang)
    two = []
    for c in np.arange(0, 360, 45.0):
        r, _ = nl.run(W, np.zeros_like(W), None, [(T_CUE, nl.cue(ang, c) + 0.9 * nl.cue(ang, c + 180.0), 0.0), (50.0, 0.0, 0.0)])
        two.append(bool(r is not None and bump_ok(r, ang, amp0) and abs((nl.com(r, ang) - c + 180) % 360 - 180) <= 22.5))
    out["S1_n_ok"] = int(sum(two))
    thr = {str(int(d)): [threshold(W, ang, amp0, b, d) for b in (0.0, 90.0, 180.0, 270.0)] for d in (90.0, 180.0)}
    med = {k: (float(np.median(v)) if all(t is not None for t in v) else None) for k, v in thr.items()}
    out["S2"] = {"thresholds_x_amp": thr, "ratio_180_over_90": (med["180"] / med["90"]) if med["90"] and med["180"] else None}
    return out


def analyse(M, g_star):
    ang = M["ang"]
    n = ang.size
    g1 = g_star * 16 / n
    K = M["E"] - M["I"]
    res = {"n_epg": int(n)}
    s, hist = homeostasis(M, g1)
    res["homeostasis"] = {"history": hist, "s_min": float(s.min()), "s_median": float(np.median(s)), "s_max": float(s.max())}
    Kh = s[:, None] * M["E"] - M["I"]
    for label, KK, AA in (("before", K, M["A_pen"]), ("after", Kh, s[:, None] * M["A_pen"])):
        bg = nl.best_gain(KK, ang, g1)
        if bg is None:
            res[label] = {"exists": False}
            continue
        t = tests(bg[0] * KK, bg[0] * AA, ang)
        t["g"] = bg[0]
        res[label] = t
        print("   ", label, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in t.items() if k not in ("rotation", "S2")}),
              "rot", round(t.get("rotation", {}).get("slow_over_fast_gain", float("nan")), 3), "S2", t.get("S2", {}).get("ratio_180_over_90"), flush=True)
    a = res.get("after", {})
    res["H1_wells_removed"] = bool(a.get("retention_22p5", 0) >= 0.8 and a.get("distinct_end_positions", 0) >= 12)
    res["H2_strict_C1"] = bool(a.get("C1", False))
    r2 = a.get("S2", {}).get("ratio_180_over_90")
    res["H3_S2_local"] = bool(r2 is not None and 0.8 <= r2 <= 1.25)
    return res


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), S47 / "neuron_level_wells.py", LOOP / "step46_connectome_ring_class/connectome_ring_class.py",
            LOOP / "step41_few_neuron_attractor/tl_ring.py", LOOP / "step41_few_neuron_attractor/few_neuron_ring.py",
            LOOP / "step42_kim_support_ring/kim_support_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s46 = json.loads((LOOP / "step46_connectome_ring_class/results.json").read_text(encoding="utf-8"))
    res = {}
    for name, data in c46.datasets().items():
        print("==", name, flush=True)
        res[name] = analyse(matrices(*data), s46["datasets"][name]["variants"]["connectome"]["g_star"])
    h1 = {k: v["H1_wells_removed"] for k, v in res.items()}
    result = {"schema": "ce-a1-step48-homeostatic-scaling", "hashes": hashes, "H1_per_dataset": h1,
              "H2_per_dataset": {k: v["H2_strict_C1"] for k, v in res.items()}, "H3_per_dataset": {k: v["H3_S2_local"] for k, v in res.items()},
              "verdict": "HOMEOSTASIS_REMOVES_WELLS" if sum(h1.values()) >= 2 else "HOMEOSTASIS_DOES_NOT_REMOVE_WELLS", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], h1, result["H2_per_dataset"], result["H3_per_dataset"])


if __name__ == "__main__":
    main()
