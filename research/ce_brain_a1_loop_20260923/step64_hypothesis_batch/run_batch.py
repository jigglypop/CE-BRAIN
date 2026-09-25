"""A1 step 64: pre-registered batch of ten NREM extensions (H0-H9, hypotheses.py) of the A1 compass ring.

Every hypothesis gets the same treatment (CONTRACT.md):
  fit        its grid (16 points, H0 none) on seeds 640 and 641; loss = sum over the two targets of
             ((mean of the two seeds - mouse median) / mouse bootstrap SE)^2; targets: inside-up late holding
             (step 59/62 up_late, mouse 0.683) and NREM 0.3 s scatter (step 57 rho_all_3 NREM, mouse 0.319).
  validate   ten new simulated mice (seeds 650-659) at the best grid point.
  judge      each measure: model median over the ten mice vs mouse median over 31 mice; consistent if
             |difference| <= 2 sqrt(SE_model^2 + SE_mouse^2) (bootstrap SEs of the medians, 10000 resamples, seed 64).
             Fit check: both targets.  Held-out (never fitted): re-emergence early, late, rise (late - early per mouse),
             curve level (mean |model - mouse| over d = 1..10 <= 0.05, step 63), inside-up early and mid holding,
             gap reset rho, ring structure NREM / wake, wake holding.
  verdict    CONSISTENT = fit check and all nine held-out pass; leaderboard by held-out passes, then summed z^2.

env/py step64_hypothesis_batch/run_batch.py    refuses to run unless CONTRACT.md lists every code hash
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
for _p in (HERE, LOOP / "fastcore"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import analysis as an  # noqa: E402
import batch  # noqa: E402
import hypotheses as hy  # noqa: E402

up = hy._load("upstream_pull", LOOP / "step62_upstream_pull/upstream_pull.py")
s57, fm = up.s57, hy.fm

FIT_SEEDS = (640, 641)
VAL_SEEDS = tuple(range(650, 660))
GRID_A = (0.1, 0.2, 0.4, 0.8)
GRIDS = {
    "H0": [{}],
    "H1": [{"tau_f": a, "g_E": b} for a in (0.05, 0.1, 0.2, 0.4) for b in (0.3, 0.5, 0.7, 1.0)],
    "H2": [{"A": a, "S": b} for a in GRID_A for b in (30.0, 60.0, 90.0, 120.0)],
    "H3": [{"A": a, "D": b} for a in GRID_A for b in (1.0, 2.0, 4.0, 8.0)],
    "H4": [{"A": a, "S": b} for a in GRID_A for b in (30.0, 60.0, 90.0, 120.0)],
    "H5": [{"A": a, "D": b} for a in GRID_A for b in (1.0, 2.0, 4.0, 8.0)],
    "H6": [{"g_E": a, "g_I": b} for a in (0.7, 0.85, 1.0, 1.15) for b in (0.5, 0.75, 1.0, 1.5)],
    "H7": [{"m": a, "tau_n": b} for a in (2.0, 4.0, 8.0, 16.0) for b in (0.0, 0.01, 0.03, 0.1)],
    "H8": [{"g_a": a, "A": b} for a in (0.25, 0.5, 1.0, 2.0) for b in GRID_A],
    "H9": [{"A": a, "D": b} for a in GRID_A for b in (1.0, 2.0, 4.0, 8.0)],
}
TARGETS = ("up_late", "rho_all_3_nrem")
HELD = ("re_early", "re_late", "rise", "up_early", "up_mid", "rho_gap", "ring_ratio", "rho_all_3_wake")
N_BOOT, BOOT_SEED, MISSING_Z2 = 10000, 64, 100.0
DEPS = ("run_batch.py", "hypotheses.py", "../fastcore/models.py", "../fastcore/analysis.py", "../fastcore/ring_kernels.py",
        "../fastcore/batch.py", "../env/uv.lock", "../step62_upstream_pull/upstream_pull.py", "../step61_stp_trace/stp_trace.py",
        "../step58_sleep_equation/sleep_equation.py", "../step59_upstate_holding/upstate_holding.py",
        "../step60_reanchoring/reanchoring.py", "../step57_sleep_holding/holding_gap.py",
        "../step56_mouse_sleep_ring/mouse_sleep_ring.py", "../step41_few_neuron_attractor/tl_ring.py")


def run_session(spec):
    """One simulated mouse: schedule, hypothesis rates, step 58 spikes, step 62 / 57 / 56 measures."""
    t0 = time.time()
    rng = np.random.default_rng(spec["seed"])
    sched = fm.schedule(rng)
    rates = hy.simulate(spec["hyp"], spec["p"], rng, sched, spec["seed"], spec["ifb"])
    out = {"hyp": spec["hyp"], "p": spec["p"], "seed": spec["seed"], "valid": rates is not None}
    if rates is None:
        return out
    tag = "_".join(f"{k}{v}" for k, v in sorted(spec["p"].items()))
    path = Path(tempfile.gettempdir()) / f"h64_{os.getpid()}_{spec['hyp']}_{spec['seed']}_{tag}.npz"
    an.spikes_and_save(rates, sched, rng, hy.GAIN, path)
    m = up.measures(path, np.random.default_rng(spec["seed"] + 1))
    g = s57.analyse(path, np.random.default_rng(spec["seed"] + 2))
    s = an.structure(path)
    path.unlink()
    gs = lambda st, k: g.get("states", {}).get(st, {}).get(k)
    out.update({k: m[k] for k in ("re_by_d", "re_early", "re_late", "up_early", "up_mid", "up_late")})
    out.update({"rho_all_3_nrem": gs("nrem", "rho_all_3"), "rho_all_3_wake": gs("wake_home", "rho_all_3"),
                "rho_gap": gs("nrem", "rho_gap"), "ring_ratio": s.get("ring_ratio"),
                "rise": None if (out["re_late"] is None or out["re_early"] is None) else out["re_late"] - out["re_early"],
                "max_rate": float(rates.max()), "seconds": round(time.time() - t0, 1)})
    return out


def _median_se(vals, rng):
    x = np.asarray(vals, float)
    b = np.median(x[rng.integers(0, x.size, (N_BOOT, x.size))], axis=1)
    return float(np.median(x)), float(b.std())


def mouse_reference():
    """Mouse medians and bootstrap SEs from the sealed step 62 / 57 / 56 per-mouse results (same estimators)."""
    r62 = json.loads((LOOP / "step62_upstream_pull/results.json").read_text(encoding="utf-8"))
    r57 = json.loads((LOOP / "step57_sleep_holding/results.json").read_text(encoding="utf-8"))
    r56 = json.loads((LOOP / "step56_mouse_sleep_ring/results.json").read_text(encoding="utf-8"))
    rows = r62["mouse_rows"]
    g = lambda s, st, k: s.get("states", {}).get(st, {}).get(k)
    per = {k: [r[k] for r in rows] for k in ("re_early", "re_late", "up_early", "up_mid", "up_late")}
    per["rise"] = [None if (r["re_late"] is None or r["re_early"] is None) else r["re_late"] - r["re_early"] for r in rows]
    q57 = [s for s in r57["sessions"] if s.get("qualifies")]
    per["rho_all_3_nrem"] = [g(s, "nrem", "rho_all_3") for s in q57]
    per["rho_all_3_wake"] = [g(s, "wake_home", "rho_all_3") for s in q57]
    per["rho_gap"] = [g(s, "nrem", "rho_gap") for s in q57]
    per["ring_ratio"] = [None if (g(s, "nrem", "ring_index") is None or not g(s, "wake_home", "ring_index"))
                         else g(s, "nrem", "ring_index") / g(s, "wake_home", "ring_index")
                         for s in r56["sessions"] if s.get("qualifies")]
    rng = np.random.default_rng(BOOT_SEED)
    ref = {}
    for k, v in per.items():
        vals = [a for a in v if a is not None]
        med, se = _median_se(vals, rng)
        ref[k] = {"n": len(vals), "median": med, "se": se}
    ref["profile"] = r62["mouse_profile"]
    return ref


def fit_loss(rows, ref):
    tot = 0.0
    for k in TARGETS:
        v = [r[k] for r in rows if r.get("valid") and r.get(k) is not None]
        if len(v) < len(rows) or not v:
            return float("inf")
        tot += ((np.mean(v) - ref[k]["median"]) / ref[k]["se"]) ** 2
    return float(tot)


def judge(rows, ref):
    rng = np.random.default_rng(BOOT_SEED)
    res = {}
    for k in TARGETS + HELD:
        vals = [r[k] for r in rows if r.get("valid") and r.get(k) is not None]
        if len(vals) < 5:
            res[k] = {"model": None, "mouse": ref[k]["median"], "pass": False, "z": None}
            continue
        med, se = _median_se(vals, rng)
        z = (med - ref[k]["median"]) / np.sqrt(se ** 2 + ref[k]["se"] ** 2)
        res[k] = {"model": med, "model_se": se, "mouse": ref[k]["median"], "mouse_se": ref[k]["se"], "z": float(z),
                  "pass": bool(abs(z) <= 2.0), "n": len(vals)}
    prof = []
    for d in range(10):
        v = [r["re_by_d"][d] for r in rows if r.get("valid") and r.get("re_by_d") and r["re_by_d"][d] is not None]
        prof.append(float(np.median(v)) if len(v) >= 5 else float("nan"))
    diffs = [abs(prof[d] - ref["profile"][d]) for d in range(10) if np.isfinite(prof[d]) and np.isfinite(ref["profile"][d])]
    mad = float(np.mean(diffs)) if len(diffs) >= 5 else None
    held = {k: res[k]["pass"] for k in HELD}
    held["curve_level"] = mad is not None and mad <= 0.05
    z2 = float(sum((res[k]["z"] ** 2) if res[k]["z"] is not None else MISSING_Z2 for k in HELD))
    fit_ok = all(res[k]["pass"] for k in TARGETS)
    n_pass = int(sum(held.values()))
    verdict = "CONSISTENT" if (fit_ok and n_pass == len(held)) else ("PARTIAL" if n_pass > 0 else "FAILS")
    return {"measures": res, "profile": prof, "curve_mad": mad, "held_out": held, "n_held_pass": n_pass, "held_z2": z2,
            "fit_ok": fit_ok, "verdict": verdict, "n_valid": int(sum(bool(r.get("valid")) for r in rows))}


def _log(stream):
    def f(msg):
        if msg.endswith("elapsed"):
            done, total = msg.split()[1].split("/")
            if int(done) % 20 and done != total:
                return
        print(msg, flush=True)
        stream.write(msg + "\n")
        stream.flush()
    return f


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    hashes = {d: hashlib.sha256((HERE / d).read_bytes()).hexdigest() for d in DEPS}
    missing = [d for d, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    t_start = time.time()
    ref = mouse_reference()
    ifb = hy.calibrate_ifb()
    print("IFB calibration", json.dumps(ifb), flush=True)
    worker = f"{Path(__file__).resolve()}:run_session"
    with (HERE / "run.log").open("a", encoding="utf-8") as logf:
        log = _log(logf)
        order = ["H9"] + [h for h in GRIDS if h != "H9"]                 # longest sessions first (load balance)
        fit_specs = [{"hyp": h, "p": p, "seed": s, "ifb": ifb} for h in order for p in GRIDS[h] for s in FIT_SEEDS]
        log(f"fit: {len(fit_specs)} sessions")
        fit_rows = batch.run_specs(fit_specs, worker, workers=6, log=log)
        best, fit_table = {}, {}
        for h in GRIDS:
            table = []
            for p in GRIDS[h]:
                rows = [r for r in fit_rows if r.get("hyp") == h and r.get("p") == p]
                table.append({"p": p, "loss": fit_loss(rows, ref), **{k: (float(np.mean([r[k] for r in rows]))
                              if rows and all(r.get(k) is not None for r in rows) else None) for k in TARGETS}})
            fit_table[h] = table
            best[h] = min(table, key=lambda e: e["loss"])
            log(f"best {h}: {json.dumps(best[h])}")
        val_specs = [{"hyp": h, "p": best[h]["p"], "seed": s, "ifb": ifb} for h in order for s in VAL_SEEDS]
        log(f"validation: {len(val_specs)} sessions")
        val_rows = batch.run_specs(val_specs, worker, workers=6, log=log)
    judged = {h: judge([r for r in val_rows if r.get("hyp") == h], ref) for h in GRIDS}
    board = sorted(GRIDS, key=lambda h: (-judged[h]["n_held_pass"], judged[h]["held_z2"]))
    consistent = [h for h in board if judged[h]["verdict"] == "CONSISTENT"]
    verdict = ("CONSISTENT_EXTENSION_FOUND: " + ", ".join(consistent)) if consistent else "NO_EXTENSION_CONSISTENT"
    result = {"schema": "ce-a1-step64-hypothesis-batch", "hashes": hashes, "mouse_reference": ref, "ifb_calibration": ifb,
              "grids": GRIDS, "fit_seeds": FIT_SEEDS, "val_seeds": VAL_SEEDS, "fit_table": fit_table,
              "best": {h: best[h] for h in GRIDS}, "judged": judged, "leaderboard": board, "verdict": verdict,
              "errors": [r for r in fit_rows + val_rows if "_error" in r], "fit_rows": fit_rows, "val_rows": val_rows,
              "minutes": round((time.time() - t_start) / 60, 1)}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", verdict, flush=True)
    for h in board:
        j = judged[h]
        print(h, json.dumps(best[h]["p"]), j["verdict"], "fit_ok", j["fit_ok"], "held", j["n_held_pass"], "/ 9  z2",
              round(j["held_z2"], 1), {k: (round(v["model"], 3) if v["model"] is not None else None) for k, v in j["measures"].items()},
              "mad", None if j["curve_mad"] is None else round(j["curve_mad"], 3), flush=True)


if __name__ == "__main__":
    main()
