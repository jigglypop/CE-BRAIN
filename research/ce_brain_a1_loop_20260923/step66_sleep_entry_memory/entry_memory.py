"""A1 step 66: does the mouse head-direction bump keep a weak alignment with the heading it had when NREM began, for the
whole NREM episode (heading held upstream and leaked at low fidelity, step 65), or does that alignment vanish within
seconds (heading wanders)? (CONTRACT.md)

Data: DANDI 000939 extraction (31 sessions). 100 ms bins; active >= 4 HD spikes with >= 2 per split half (step 57).
Entries: NREM intervals in the home cage (opto excluded) that follow a wake interval of >= 10 s within 1 s and last
>= 30 s. Reference = active wake bins in the last 5 s before NREM onset (>= 5 bins); targets = active NREM bins of the
episode (>= 50 bins), grouped by time since onset: 0-10, 10-30, 30-60, 60-120, 120-300, >= 300 s; late = >= 60 s.
Alignment rho(reference, target) = split-half noise-free persistence with pair-specific denominators (step 60
rho_pairs, 20 splits, >= 30 pairs). Matched: an episode's reference with its own targets. Mismatched: the reference
with the targets of the neighbouring episodes (i - 1, i + 1, cyclic) at the same times since their onsets. At most
20000 pairs per episode, window and set (seeded subsample).
M1 heading held through NREM: per session late matched - late mismatched; median and 95 % bootstrap CI (10000, seed 66)
   over sessions (>= 10); HEADING_HELD if the lower bound > 0, HEADING_NOT_HELD if the upper bound < 0.05, else
   UNRESOLVED.
Estimator check (model references, 10 simulated mice each, seeds 670-679, step 64 code): held generator + relay
jitter (H2, A 0.4, S 120 deg) must give HEADING_HELD; wandering generator (H3, A 0.4, D 4) must give
HEADING_NOT_HELD. If either fails the mouse verdict is not interpreted.

env/py step66_sleep_entry_memory/entry_memory.py    refuses to run unless CONTRACT.md lists every code hash
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
S64 = LOOP / "step64_hypothesis_batch"
for _p in (HERE, S64, LOOP / "fastcore"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import analysis as an  # noqa: E402
import batch  # noqa: E402
import hypotheses as hy  # noqa: E402
import run_batch as rb  # noqa: E402

up, fm = rb.up, hy.fm
ra, s57, s56 = up.ra, up.s57, up.s56
WINDOWS = ((0.0, 10.0), (10.0, 30.0), (30.0, 60.0), (60.0, 120.0), (120.0, 300.0), (300.0, 1e9))
LATE = (60.0, 1e9)
REF_S, MIN_WAKE_S, MIN_NREM_S, MAX_GAP_S, MIN_REF, MIN_TGT, CAP = 5.0, 10.0, 30.0, 1.0, 5, 50, 20000
MODELS = {"H2_held": ("H2", {"A": 0.4, "S": 120.0}), "H3_wandering": ("H3", {"A": 0.4, "D": 4.0})}
MODEL_SEEDS = tuple(range(670, 680))
N_BOOT = 10000
DEPS = ("entry_memory.py", "../step64_hypothesis_batch/run_batch.py", "../step64_hypothesis_batch/hypotheses.py",
        "../fastcore/models.py", "../fastcore/analysis.py", "../fastcore/ring_kernels.py", "../fastcore/batch.py",
        "../env/uv.lock", "../step62_upstream_pull/upstream_pull.py", "../step61_stp_trace/stp_trace.py",
        "../step58_sleep_equation/sleep_equation.py", "../step59_upstate_holding/upstate_holding.py",
        "../step60_reanchoring/reanchoring.py", "../step57_sleep_holding/holding_gap.py",
        "../step56_mouse_sleep_ring/mouse_sleep_ring.py", "../step41_few_neuron_attractor/tl_ring.py")


def _wname(lo, hi):
    return f"{int(lo)}-{int(hi) if hi < 1e8 else 'end'}"


def _pairs(ref, tgt, since, lo, hi, rng):
    u = tgt[(since >= lo) & (since < hi)]
    if u.size == 0 or ref.size == 0:
        return np.empty(0, np.int64), np.empty(0, np.int64)
    t, v = np.repeat(ref, u.size), np.tile(u, ref.size)
    if t.size > CAP:
        k = np.sort(rng.choice(t.size, CAP, replace=False))
        t, v = t[k], v[k]
    return t, v


def entry_alignment(path, seed):
    """Alignment of NREM bumps with the pre-sleep heading, by time since NREM onset (matched and mismatched)."""
    rng_split, rng_cap = np.random.default_rng(seed), np.random.default_rng(seed + 1)
    S = s56.load(path)
    hd_idx = np.flatnonzero(S["hd_flag"])
    if hd_idx.size < s56.MIN_HD:
        return {"qualifies": False}
    th, tracked = s56.preferred(S, [S["spikes"][i] for i in hd_idx])
    T = max(float(np.max(np.concatenate([s for s in S["spikes"] if s.size]))), float(S["ss"][1].max()))
    edges = np.arange(0, T + s57.BIN, s57.BIN)
    centres = (edges[:-1] + edges[1:]) / 2
    N = np.array([np.histogram(S["spikes"][i], edges)[0] for i in hd_idx], dtype=float)
    state, home, opto = s56.labels(centres, S)
    active = N.sum(0) >= s57.ACTIVE
    if ((state == "nrem") & home).sum() * s57.BIN < s56.MIN_NREM or tracked < s56.MIN_TRACK:
        return {"qualifies": False}
    splits = s57.halves_angles(N, th, rng_split)
    ss, se_, sl = S["ss"]
    o = np.argsort(ss)
    ss, se_, sl = ss[o], se_[o], sl[o]
    eps = []
    for k in range(1, len(sl)):
        if not (sl[k] == "nrem" and sl[k - 1] == "wake" and abs(ss[k] - se_[k - 1]) <= MAX_GAP_S
                and se_[k - 1] - ss[k - 1] >= MIN_WAKE_S and se_[k] - ss[k] >= MIN_NREM_S):
            continue
        a, b = ss[k], se_[k]
        ref = np.flatnonzero((centres >= a - REF_S) & (centres < a) & (state == "wake") & home & active)
        tgt = np.flatnonzero((centres >= a) & (centres < b) & (state == "nrem") & home & active)
        if ref.size >= MIN_REF and tgt.size >= MIN_TGT:
            eps.append((a, ref, tgt, centres[tgt] - a))
    out = {"qualifies": len(eps) >= 3, "n_episodes": len(eps)}
    if not out["qualifies"]:
        return out
    n = len(eps)
    for name, (lo, hi) in [(_wname(*w), w) for w in WINDOWS] + [("late", LATE)]:
        mt, mv, xt, xv = [], [], [], []
        for i, (a, ref, tgt, since) in enumerate(eps):
            t, v = _pairs(ref, tgt, since, lo, hi, rng_cap)
            mt.append(t), mv.append(v)
            for j in sorted({(i - 1) % n, (i + 1) % n} - {i}):
                t, v = _pairs(ref, eps[j][2], eps[j][3], lo, hi, rng_cap)
                xt.append(t), xv.append(v)
        mt, mv, xt, xv = (np.concatenate(z) for z in (mt, mv, xt, xv))
        out[name] = {"matched": ra.rho_pairs(mt, mv, splits), "mismatched": ra.rho_pairs(xt, xv, splits),
                     "n_matched": int(mt.size), "n_mismatched": int(xt.size)}
    L = out["late"]
    out["late_diff"] = None if (L["matched"] is None or L["mismatched"] is None) else L["matched"] - L["mismatched"]
    return out


def mouse_session(spec):
    return {"session": Path(spec["path"]).stem, **entry_alignment(Path(spec["path"]), 66)}


def model_session(spec):
    t0 = time.time()
    rng = np.random.default_rng(spec["seed"])
    sched = fm.schedule(rng)
    rates = hy.simulate(spec["hyp"], spec["p"], rng, sched, spec["seed"], spec["ifb"])
    path = Path(tempfile.gettempdir()) / f"h66_{os.getpid()}_{spec['model']}_{spec['seed']}.npz"
    an.spikes_and_save(rates, sched, rng, hy.GAIN, path)
    out = entry_alignment(path, spec["seed"] + 66)
    path.unlink()
    return {"model": spec["model"], "seed": spec["seed"], **out, "seconds": round(time.time() - t0, 1)}


def summarise(rows):
    q = [r for r in rows if r.get("qualifies")]
    d = np.array([r["late_diff"] for r in q if r.get("late_diff") is not None], float)
    res = {"n_sessions": len(q), "n_with_late": int(d.size)}
    if d.size >= 10:
        b = np.median(d[np.random.default_rng(66).integers(0, d.size, (N_BOOT, d.size))], axis=1)
        lo, hi = np.percentile(b, [2.5, 97.5])
        res.update({"late_diff_median": float(np.median(d)), "ci95": [float(lo), float(hi)],
                    "verdict": "HEADING_HELD" if lo > 0 else ("HEADING_NOT_HELD" if hi < 0.05 else "UNRESOLVED")})
    else:
        res["verdict"] = "UNRESOLVED"
    names = [_wname(*w) for w in WINDOWS] + ["late"]
    med = lambda k, s: (float(np.median([r[k][s] for r in q if r.get(k, {}).get(s) is not None]))
                        if any(r.get(k, {}).get(s) is not None for r in q) else None)
    res["by_window"] = {k: {"matched": med(k, "matched"), "mismatched": med(k, "mismatched"),
                            "n_sessions": sum(1 for r in q if r.get(k, {}).get("matched") is not None)} for k in names}
    return res


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    hashes = {dep: hashlib.sha256((HERE / dep).read_bytes()).hexdigest() for dep in DEPS}
    missing = [dep for dep, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    t_start = time.time()
    ifb = hy.calibrate_ifb()
    with (HERE / "run.log").open("a", encoding="utf-8") as logf:
        log = rb._log(logf)
        specs = [{"model": m, "hyp": h, "p": p, "seed": s, "ifb": ifb} for m, (h, p) in MODELS.items() for s in MODEL_SEEDS]
        model_rows = batch.run_specs(specs, f"{Path(__file__).resolve()}:model_session", workers=6, log=log)
        mouse_specs = [{"path": str(p)} for p in sorted(s56.DATA.glob("*.npz"))]
        mouse_rows = batch.run_specs(mouse_specs, f"{Path(__file__).resolve()}:mouse_session", workers=6, log=log)
    models = {m: summarise([r for r in model_rows if r.get("model") == m]) for m in MODELS}
    check = models["H2_held"]["verdict"] == "HEADING_HELD" and models["H3_wandering"]["verdict"] == "HEADING_NOT_HELD"
    mouse = summarise(mouse_rows)
    verdict = mouse["verdict"] if check else f"ESTIMATOR_CHECK_FAILED (mouse {mouse['verdict']})"
    result = {"schema": "ce-a1-step66-sleep-entry-memory", "hashes": hashes, "models": models, "estimator_check": check,
              "mouse": mouse, "verdict": verdict, "model_rows": model_rows, "mouse_rows": mouse_rows,
              "errors": [r for r in model_rows + mouse_rows if "_error" in r], "minutes": round((time.time() - t_start) / 60, 1)}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", verdict, "estimator check", check, flush=True)
    for m, s in list(models.items()) + [("mouse", mouse)]:
        print(m, s["verdict"], "late diff", s.get("late_diff_median"), s.get("ci95"), "n", s["n_with_late"], flush=True)
        for k, v in s["by_window"].items():
            print("   ", k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()}, flush=True)


if __name__ == "__main__":
    main()
