"""A1 step 65: (A) reverse proof of the step 64 post hoc finding and (B) is the rise of inside-up holding a time course
inside each up state or a mixing of short and long runs? (CONTRACT.md)

A  Post hoc (sealed step 64 grid, 2 seeds): the held generator relayed with a strong OU jitter, A 0.4 and S 120 deg
   (H2, and H4 = H2 + T-channel rebound), gave the mouse re-emergence curve (mean |model - mouse| 0.029-0.032). Here the
   exact point runs on ten new simulated mice per model (seeds 660-669, step 64 code unchanged) and is judged with the
   step 64 rule (model median vs mouse median, |z| <= 2 with bootstrap SEs):
     T1 re-emergence early, T2 late, T3 rise (late - early), T4 curve level (mean |model - mouse| over d 1-10 <= 0.05),
     T5 gap reset rho.  All five -> TRACE_REPRODUCED for that model.
   Report: inside-up holding, NREM scatter, ring ratio, wake; relay fidelity f = mean cos(psi - theta) over NREM up
   steps (theory exp(-S^2 / 2) = 0.111 for S 120 deg), ring alignment m = mean cos(bump angle - theta) over NREM up
   bins (by time since up onset), and m_late^2 next to the late re-emergence.
B  Mouse data (31 sessions, DANDI 000939 extraction) and the model sessions: NREM continuous pairs (t, t+2, all active;
   step 57 / 59) split by bins since the last silent bin (early 1-3, mid 4-6, late 7-10) and by the length of the
   non-silent run that contains t (both ends silent): short <= 12 bins (1.2 s), long >= 20 bins (2 s). Persistence with
   pair-specific denominators (step 60 rho_pairs, >= 30 pairs).
     B1 within-run time course: per session short-late - short-early; median and 95 % bootstrap CI (10000, seed 65);
        supported if the CI lower bound > 0 (>= 10 sessions).
     B2 run-length effect: per session long-late - short-late; supported if the CI lower bound > 0.
   Verdict: B1 and B2 -> BOTH, B1 only -> WITHIN_UP_TIME_COURSE, B2 only -> RUN_LENGTH_EFFECT, else NEITHER.

env/py step65_trace_confirmation/trace_confirm.py    refuses to run unless CONTRACT.md lists every code hash
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
from numba import njit

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

up, fm, rk = rb.up, hy.fm, hy.rk
ra, uh, s57, s56 = up.ra, up.uh, up.s57, up.s56
MODELS = {"H2": {"A": 0.4, "S": 120.0}, "H4": {"A": 0.4, "S": 120.0}}
SEEDS = tuple(range(660, 670))
TRACE = ("re_early", "re_late", "rise", "rho_gap")
REPORT = ("up_early", "up_mid", "up_late", "rho_all_3_nrem", "ring_ratio", "rho_all_3_wake")
SHORT_MAX, LONG_MIN = 12, 20
TIME_CLASSES = {"early": (1, 3), "mid": (4, 6), "late": (7, 10)}
N_BOOT = 10000
DEPS = ("trace_confirm.py", "../step64_hypothesis_batch/run_batch.py", "../step64_hypothesis_batch/hypotheses.py",
        "../fastcore/models.py", "../fastcore/analysis.py", "../fastcore/ring_kernels.py", "../fastcore/batch.py",
        "../env/uv.lock", "../step62_upstream_pull/upstream_pull.py", "../step61_stp_trace/stp_trace.py",
        "../step58_sleep_equation/sleep_equation.py", "../step59_upstate_holding/upstate_holding.py",
        "../step60_reanchoring/reanchoring.py", "../step57_sleep_holding/holding_gap.py",
        "../step56_mouse_sleep_ring/mouse_sleep_ring.py", "../step41_few_neuron_attractor/tl_ring.py")


# ------------------------------------------------------------------------ A: simulation that also keeps the heading
@njit(cache=True)
def _pull_chunk_theta(theta, eta, head, nrem, down, z1, z2, sd_w, s_rad, ea, a_nrem, psi_out, a_out, th_out):
    """fastcore models._pull_chunk with the same arithmetic, also returning the generator heading theta per step."""
    for j in range(z1.size):
        if not np.isnan(head[j]):
            theta = head[j]
        elif not nrem[j]:
            theta += sd_w * z1[j]
        if nrem[j]:
            eta = ea * eta + s_rad * np.sqrt(1 - ea * ea) * z2[j]
            a = 0.0 if down[j] else a_nrem
        else:
            eta = 0.0
            a = 1.0
        psi_out[j] = theta + eta
        a_out[j] = a
        th_out[j] = theta
    return theta, eta


def simulate_capture(hyp, p, rng, sched, ifb):
    """Step 64 hypotheses.simulate for H2 / H4 (same draws and operations), returning (rates, theta, psi)."""
    c, head, down, nrem = hy._masks(sched)
    n = c.size
    rates = np.empty((n, 16), dtype=np.float32, order="F")
    zb, eb = np.empty((hy.CH, 16)), np.empty((hy.CH, 16))
    th_all, psi_all = np.empty(n), np.empty(n)
    sd_w = np.sqrt(2 * hy.D_W * hy.DT)
    theta, eta, r = 0.0, 0.0, np.zeros(16)
    if hyp == "H4":
        h, e_plus, e_minus = 0.0, np.exp(-1.0 / hy.TAU_H_PLUS), np.exp(-1.0 / hy.TAU_H_MINUS)
        hb = np.empty(hy.CH)
    for i0 in range(0, n, hy.CH):
        m = min(hy.CH, n - i0)
        sl = slice(i0, i0 + m)
        noise = fm._noise(rng, hy.SIGMA, zb, m)
        z1, z2 = rng.standard_normal(m), rng.standard_normal(m)
        psi, a = np.empty(m), np.empty(m)
        theta, eta = _pull_chunk_theta(theta, eta, head[sl], nrem[sl], down[sl], z1, z2, sd_w, np.radians(p["S"]),
                                       np.exp(-hy.DT / hy.TAU_ETA), p["A"], psi, a, th_all[sl])
        psi_all[sl] = psi
        if hyp == "H2":
            ext = rk.von_mises_input(hy.ANG, psi, a, eb[:m])
        else:
            h = hy.rebound_h(h, nrem[sl], down[sl], e_plus, e_minus, hb[:m])
            up_n = nrem[sl] & ~down[sl]
            ext = rk.von_mises_input(hy.ANG, psi, a * np.where(up_n, 1.0 - hb[:m], 1.0), eb[:m])
            ext += np.where(up_n, p["A"] * ifb["B"] * hb[:m] / ifb["h_ref"], 0.0)[:, None]
        r = rk.ring_chunk(hy.se.W, r, c[sl], noise, ext, hy.K, rates[sl])
    return rates, th_all, psi_all


def alignment(rates, theta, psi, sched, S_deg):
    """Relay fidelity and ring alignment with the held heading in NREM up states (100 ms bins, by time since onset)."""
    c, head, down, nrem = hy._masks(sched)
    upn = nrem & ~down
    fid = float(np.mean(np.cos(psi[upn] - theta[upn])))
    n_bins = rates.shape[0] // 100
    B = slice(0, n_bins * 100)
    z = (rates[B].astype(float) @ np.exp(1j * hy.ANG)).reshape(n_bins, 100).mean(1)
    tot = rates[B].astype(float).sum(1).reshape(n_bins, 100).mean(1)
    thb = np.angle(np.exp(1j * theta[B]).reshape(n_bins, 100).mean(1))
    upb = upn[B].reshape(n_bins, 100).all(1)
    onset = np.flatnonzero(upn[1:] & ~upn[:-1]) + 1                 # up-state onsets (steps)
    since = np.full(n_bins, -1)
    for k, o in enumerate(onset):
        end = onset[k + 1] if k + 1 < onset.size else rates.shape[0]
        b0, b1 = int(np.ceil(o / 100)), min(end // 100, n_bins)
        since[b0:b1] = np.arange(b1 - b0)
    ok = upb & (tot > 0.05 * np.median(tot[upb]))
    cosd = np.cos(np.angle(z) - thb)
    by_t = [float(np.mean(cosd[ok & (since == k)])) if np.any(ok & (since == k)) else None for k in range(10)]
    late = ok & (since >= 5)
    m_late = float(np.mean(cosd[late])) if late.any() else None
    return {"relay_fidelity": fid, "theory_fidelity": float(np.exp(-np.radians(S_deg) ** 2 / 2)),
            "alignment_all": float(np.mean(cosd[ok])), "alignment_by_100ms_since_onset": by_t, "alignment_late": m_late,
            "alignment_late_sq": None if m_late is None else m_late ** 2}


# ------------------------------------------------------------------------------- B: holding split by run length
def _until_silent(silent, seg):
    out = np.empty(silent.size, dtype=np.int64)
    nxt, cur = 10 ** 9, None
    for i in range(silent.size - 1, -1, -1):
        if seg[i] != cur:
            cur, nxt = seg[i], 10 ** 9
        if silent[i]:
            nxt = i
        out[i] = nxt - i
    return out


def run_split(path, rng):
    """Inside-up holding (0.2 s, continuous) by time since silent and by the length of the containing run."""
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
    tot = N.sum(0)
    active, silent = tot >= s57.ACTIVE, tot <= s57.SILENT
    nrem = (state == "nrem") & home
    if nrem.sum() * s57.BIN < s56.MIN_NREM or tracked < s56.MIN_TRACK:
        return {"qualifies": False}
    splits = s57.halves_angles(N, th, rng)
    seg = np.cumsum(np.r_[1, np.diff(nrem.astype(int)) != 0])
    t, u = s57.pair_sets(nrem, active, silent, seg)["cont_2"]
    since = uh.since_silent(silent, seg)[t]
    until = _until_silent(silent, seg)[t]
    closed = (since < 10 ** 8) & (until < 10 ** 8)
    run = since + until - 1
    out = {"qualifies": True, "n_pairs": int(t.size), "run_len_median_bins": float(np.median(run[closed])) if closed.any() else None}
    for rn, rmask in (("short", closed & (run <= SHORT_MAX)), ("long", closed & (run >= LONG_MIN))):
        for tn, (lo, hi) in TIME_CLASSES.items():
            msk = rmask & (since >= lo) & (since <= hi)
            out[f"n_{rn}_{tn}"] = int(msk.sum())
            out[f"rho_{rn}_{tn}"] = ra.rho_pairs(t[msk], u[msk], splits)
    return out


# ------------------------------------------------------------------------------------------------------ workers
def model_session(spec):
    """One simulated mouse: step 64 run_session measures + alignment + run split, on the same session."""
    t0 = time.time()
    rng = np.random.default_rng(spec["seed"])
    sched = fm.schedule(rng)
    rates, theta, psi = simulate_capture(spec["hyp"], spec["p"], rng, sched, spec["ifb"])
    path = Path(tempfile.gettempdir()) / f"h65_{os.getpid()}_{spec['hyp']}_{spec['seed']}.npz"
    an.spikes_and_save(rates, sched, rng, hy.GAIN, path)
    m = up.measures(path, np.random.default_rng(spec["seed"] + 1))
    g = s57.analyse(path, np.random.default_rng(spec["seed"] + 2))
    s = an.structure(path)
    split = run_split(path, np.random.default_rng(spec["seed"] + 3))
    path.unlink()
    gs = lambda st, k: g.get("states", {}).get(st, {}).get(k)
    out = {"hyp": spec["hyp"], "seed": spec["seed"], "valid": True, **{k: m[k] for k in ("re_by_d", "re_early", "re_late", "up_early", "up_mid", "up_late")}}
    out.update({"rho_all_3_nrem": gs("nrem", "rho_all_3"), "rho_all_3_wake": gs("wake_home", "rho_all_3"), "rho_gap": gs("nrem", "rho_gap"),
                "ring_ratio": s.get("ring_ratio"), "rise": None if (out["re_late"] is None or out["re_early"] is None) else out["re_late"] - out["re_early"],
                "alignment": alignment(rates, theta, psi, sched, spec["p"]["S"]), "split": split, "seconds": round(time.time() - t0, 1)})
    return out


def mouse_session(spec):
    return {"session": Path(spec["path"]).stem, **run_split(Path(spec["path"]), np.random.default_rng(65))}


def _ci(vals):
    x = np.asarray([v for v in vals if v is not None], float)
    if x.size < 10:
        return {"n": int(x.size), "median": None, "ci95": None, "supported": False}
    b = np.median(x[np.random.default_rng(65).integers(0, x.size, (N_BOOT, x.size))], axis=1)
    lo, hi = np.percentile(b, [2.5, 97.5])
    return {"n": int(x.size), "median": float(np.median(x)), "ci95": [float(lo), float(hi)], "supported": bool(lo > 0)}


def split_summary(rows):
    d = lambda r, a, b: None if (r.get(a) is None or r.get(b) is None) else r[a] - r[b]
    q = [r for r in rows if r.get("qualifies")]
    b1 = _ci([d(r, "rho_short_late", "rho_short_early") for r in q])
    b2 = _ci([d(r, "rho_long_late", "rho_short_late") for r in q])
    cls = {k: (float(np.median([r[k] for r in q if r.get(k) is not None])) if any(r.get(k) is not None for r in q) else None)
           for k in [f"rho_{a}_{b}" for a in ("short", "long") for b in TIME_CLASSES]}
    verdict = {(True, True): "BOTH", (True, False): "WITHIN_UP_TIME_COURSE", (False, True): "RUN_LENGTH_EFFECT",
               (False, False): "NEITHER"}[(b1["supported"], b2["supported"])]
    return {"B1_within_run": b1, "B2_run_length": b2, "class_medians": cls, "verdict": verdict, "n_sessions": len(q)}


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    hashes = {d: hashlib.sha256((HERE / d).read_bytes()).hexdigest() for d in DEPS}
    missing = [d for d, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    t_start = time.time()
    ref = rb.mouse_reference()
    ifb = hy.calibrate_ifb()
    with (HERE / "run.log").open("a", encoding="utf-8") as logf:
        log = rb._log(logf)
        specs = [{"hyp": h, "p": p, "seed": s, "ifb": ifb} for h, p in MODELS.items() for s in SEEDS]
        model_rows = batch.run_specs(specs, f"{Path(__file__).resolve()}:model_session", workers=6, log=log)
        mouse_specs = [{"path": str(p)} for p in sorted(s56.DATA.glob("*.npz"))]
        mouse_rows = batch.run_specs(mouse_specs, f"{Path(__file__).resolve()}:mouse_session", workers=6, log=log)
    A = {}
    for h in MODELS:
        rows = [r for r in model_rows if r.get("hyp") == h]
        j = rb.judge(rows, ref)
        trace = {k: j["measures"][k]["pass"] for k in TRACE}
        trace["curve_level"] = j["curve_mad"] is not None and j["curve_mad"] <= 0.05
        al = [r["alignment"] for r in rows if "alignment" in r]
        A[h] = {"trace_criteria": trace, "verdict": "TRACE_REPRODUCED" if all(trace.values()) else "TRACE_NOT_REPRODUCED",
                "measures": {k: j["measures"][k] for k in TRACE + REPORT + ("up_late",) if k in j["measures"]},
                "curve_mad": j["curve_mad"], "profile": j["profile"],
                "alignment_median": {k: float(np.median([a[k] for a in al if a[k] is not None])) for k in
                                     ("relay_fidelity", "theory_fidelity", "alignment_all", "alignment_late", "alignment_late_sq")},
                "alignment_by_100ms_since_onset": [float(np.median([a["alignment_by_100ms_since_onset"][k] for a in al
                                                                    if a["alignment_by_100ms_since_onset"][k] is not None]))
                                                   for k in range(10)],
                "split": split_summary([r["split"] for r in rows])}
    B = split_summary(mouse_rows)
    result = {"schema": "ce-a1-step65-trace-confirmation", "hashes": hashes, "mouse_reference": ref, "ifb_calibration": ifb,
              "models": MODELS, "seeds": SEEDS, "A": A, "B_mouse": B, "model_rows": model_rows, "mouse_rows": mouse_rows,
              "errors": [r for r in model_rows + mouse_rows if "_error" in r], "minutes": round((time.time() - t_start) / 60, 1)}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    for h in MODELS:
        a = A[h]
        print(h, a["verdict"], json.dumps(a["trace_criteria"]), "mad", round(a["curve_mad"], 3) if a["curve_mad"] is not None else None,
              {k: round(v["model"], 3) for k, v in a["measures"].items() if v.get("model") is not None},
              "\n  profile", [round(x, 3) for x in a["profile"]], "\n  alignment", json.dumps(a["alignment_median"]),
              "\n  by onset", [round(x, 3) for x in a["alignment_by_100ms_since_onset"]],
              "\n  model split", a["split"]["verdict"], json.dumps(a["split"]["class_medians"]), flush=True)
    print("mouse split", B["verdict"], json.dumps(B["B1_within_run"]), json.dumps(B["B2_run_length"]),
          "\n  class medians", json.dumps(B["class_medians"]), flush=True)


if __name__ == "__main__":
    main()
