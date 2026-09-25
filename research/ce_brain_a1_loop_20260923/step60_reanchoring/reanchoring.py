"""A1 step 60: after an NREM down state wipes the cortical head-direction bump (step 57: rho across silent gaps -0.03),
does the heading come back later in the up state (held upstream, e.g. by the brainstem generator, and re-imposed), or is
it lost (the bump stays at its new position)? (CONTRACT.md)

Data: DANDI 000939 extraction (31 mice). 100 ms bins; active >= 4 HD spikes with >= 2 per split half; silent <= 1.
Gaps: runs of 1-5 silent bins inside home-cage NREM, preceded by an active bin t0 and followed by a non-silent run.
Post-gap bins t_d = (first bin after the gap) + d - 1, d = 1..10 (0.1-1.0 s), counted only while no new silent bin
has occurred and t_d is active. Persistence rho(t0, t_d) with split halves (20 splits) and pair-specific
denominators (geometric mean of the same-bin half agreement at t0 and t_d; the step 59 post hoc correction).
Classes: early d = 1-2, late d = 5-10.
R1 re-anchoring:  rho_late > rho_early + 0.15 and rho_late > 0.2, in >= 70 % of sessions (>= 30 pairs per class).
R2 heading lost:  rho_late <= 0.1 and rho_early <= 0.1, in >= 70 % of sessions.
Verdict: R1 -> HEADING_REIMPOSED_FROM_UPSTREAM; R2 -> HEADING_LOST; else INTERMEDIATE.
Reference: the five step 58 model mice (cortical ring reset model; regenerated with the same seeds, sigma, gain).

python reanchoring.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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
GAP = (1, 5)
DMAX = 10
EARLY, LATE = (1, 2), (5, 10)
MIN_PAIRS = 30


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s57 = load("holding_gap", LOOP / "step57_sleep_holding/holding_gap.py")
s56 = s57.s56
se = load("sleep_equation", LOOP / "step58_sleep_equation/sleep_equation.py")


def rho_pairs(t, u, splits):
    """Split-half persistence with pair-specific denominators."""
    if t.size < MIN_PAIRS:
        return None
    num, den = [], []
    for pa, pb, va, vb in splits:
        ok = va[t] & vb[t] & va[u] & vb[u]
        if ok.sum() < MIN_PAIRS:
            continue
        tt, uu = t[ok], u[ok]
        num.append(np.mean((np.cos(pa[tt] - pb[uu]) + np.cos(pb[tt] - pa[uu])) / 2))
        a, b = np.mean(np.cos(pa[tt] - pb[tt])), np.mean(np.cos(pa[uu] - pb[uu]))
        den.append(np.sqrt(max(a, 1e-9) * max(b, 1e-9)))
    if not num or np.mean(den) <= 0.05:
        return None
    return float(np.mean(num) / np.mean(den))


def gap_pairs(nrem, active, silent):
    """(t0, t_d, d) for every NREM gap of 1-5 silent bins."""
    n = silent.size
    out_t, out_u, out_d = [], [], []
    i = 1
    while i < n - 1:
        if nrem[i] and silent[i] and not silent[i - 1]:
            j = i
            while j < n and silent[j] and nrem[j]:
                j += 1
            g = j - i
            t0 = i - 1
            if GAP[0] <= g <= GAP[1] and nrem[t0] and active[t0] and j < n and nrem[j]:
                for d in range(1, DMAX + 1):
                    k = j + d - 1
                    if k >= n or not nrem[k] or silent[k]:
                        break                                  # stop at the next silent bin or the end of NREM
                    if active[k]:
                        out_t.append(t0); out_u.append(k); out_d.append(d)
            i = j
        else:
            i += 1
    return np.array(out_t, int), np.array(out_u, int), np.array(out_d, int)


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
    nrem = (state == "nrem") & home
    if nrem.sum() * s57.BIN < s56.MIN_NREM or tracked < s56.MIN_TRACK:
        return {**info, "qualifies": False}
    splits = s57.halves_angles(N, th, rng)
    t, u, d = gap_pairs(nrem, active, silent)
    out = {**info, "qualifies": True, "n_gaps": int(np.unique(t).size)}
    out["rho_by_d"] = {str(k): rho_pairs(t[d == k], u[d == k], splits) for k in range(1, DMAX + 1)}
    out["n_by_d"] = {str(k): int((d == k).sum()) for k in range(1, DMAX + 1)}
    for name, (lo, hi) in (("early", EARLY), ("late", LATE)):
        m = (d >= lo) & (d <= hi)
        out[f"rho_{name}"], out[f"n_{name}"] = rho_pairs(t[m], u[m], splits), int(m.sum())
    e, l = out["rho_early"], out["rho_late"]
    out["R1"] = None if (e is None or l is None) else bool(l > e + 0.15 and l > 0.2)
    out["R2"] = None if (e is None or l is None) else bool(l <= 0.1 and e <= 0.1)
    return out


def verdict_of(rows):
    r1 = [r["R1"] for r in rows if r.get("R1") is not None]
    r2 = [r["R2"] for r in rows if r.get("R2") is not None]
    f1 = float(np.mean(r1)) if r1 else None
    f2 = float(np.mean(r2)) if r2 else None
    v = "HEADING_REIMPOSED_FROM_UPSTREAM" if (f1 is not None and f1 >= 0.7) else ("HEADING_LOST" if (f2 is not None and f2 >= 0.7) else "INTERMEDIATE")
    med = lambda k: float(np.median([r[k] for r in rows if r.get(k) is not None])) if any(r.get(k) is not None for r in rows) else None
    by_d = {str(k): (float(np.median([r["rho_by_d"][str(k)] for r in rows if r.get("rho_by_d", {}).get(str(k)) is not None]))
                     if any(r.get("rho_by_d", {}).get(str(k)) is not None for r in rows) else None) for k in range(1, DMAX + 1)}
    return {"R1_fraction": f1, "R1_n": len(r1), "R2_fraction": f2, "R2_n": len(r2), "verdict": v,
            "median_rho_early": med("rho_early"), "median_rho_late": med("rho_late"), "median_rho_by_d": by_d}


def model_rows():
    work = Path(tempfile.mkdtemp())
    s58 = json.loads((LOOP / "step58_sleep_equation/results.json").read_text(encoding="utf-8"))
    rows = []
    for seed in se.SEEDS:
        rng = np.random.default_rng(seed)
        sched = se.schedule(rng)
        rates = se.simulate(s58["sigma"], se.C_DOWN_PRIMARY, rng, sched)
        path = work / f"model_s{seed}.npz"
        se.spikes_and_save(rates, sched, rng, s58["gain"], path)
        rows.append(analyse(path, np.random.default_rng(seed + 1)))
        path.unlink()
        print("model", seed, rows[-1].get("rho_early"), rows[-1].get("rho_late"), flush=True)
    return rows


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step57_sleep_holding/holding_gap.py", LOOP / "step56_mouse_sleep_ring/mouse_sleep_ring.py",
            LOOP / "step58_sleep_equation/sleep_equation.py", LOOP / "step41_few_neuron_attractor/tl_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    rng = np.random.default_rng(60)
    mouse = []
    for p in sorted(s56.DATA.glob("*.npz")):
        r = analyse(p, rng)
        mouse.append(r)
        print(r["session"][:22], "gaps", r.get("n_gaps"), "early", r.get("rho_early"), "late", r.get("rho_late"), "R1", r.get("R1"), "R2", r.get("R2"), flush=True)
    mq = [r for r in mouse if r.get("qualifies")]
    model = model_rows()
    result = {"schema": "ce-a1-step60-reanchoring", "hashes": hashes, "mouse": verdict_of(mq), "model_reference": verdict_of(model),
              "sessions": mouse, "model_sessions": model}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("MOUSE", json.dumps(result["mouse"]), "\nMODEL", json.dumps(result["model_reference"]))


if __name__ == "__main__":
    main()
