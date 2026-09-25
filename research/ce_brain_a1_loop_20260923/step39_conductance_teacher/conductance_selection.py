"""A1 step 39: with the teacher of Urbanczik & Senn 2014 (conductance nudging toward a target bump shaped like the
fly's: FWHM ~90 deg, unsaturated), does the same predictive learning rule (Vafidis et al. 2022) give a ring that obeys
Kim et al. 2017 -- narrow-input jump with a distance-independent threshold, mutual suppression -- while keeping one of
two cues, holding its bump without wells and integrating at fly turning speeds? (CONTRACT.md)

Training: from the authors' random initialisation N(0, 1/N), 8e4 s (the authors' training length), authors' rule,
OU heading generator and parameters, exact somatic step; a fresh seed not used in screening. Two networks share the
seed and trajectory: the conductance teacher fixed in CONTRACT.md, and the authors' current teacher (paired control).
Tests: step 37 logic and constants, light = each network's own teacher, optogenetic wedge = somatic current as in
step 37; rotation criterion at fly turning speeds (Seelig & Jayaraman 2015), 30 deg/s reported.

python conductance_selection.py train <conductance|current>   writes trained_<kind>.npz (refuses unless CONTRACT.md lists the hashes)
python conductance_selection.py test                           writes results.json
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
sys.path.insert(0, str(HERE))
import us_network as us  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s37 = load("learned_selection", LOOP / "step37_learned_ring_selection/learned_selection.py")
TEACHER = {"g0": None, "EE": None, "sigma": None}       # fixed by the screening rule in CONTRACT.md
T_TRAIN, SEED = 80000.0, 51
SPEEDS_R1, SPEEDS_SLOW = (-180.0, -90.0, -60.0, 60.0, 90.0, 180.0), (-30.0, 30.0)
us.SOMA["mode"] = "exp"


def teacher(kind="conductance"):
    if kind == "current":
        return us.Teacher("current", M=us.P["M"], sigma=us.P["sigma"])
    return us.Teacher("conductance", sigma=TEACHER["sigma"], g0=TEACHER["g0"], EE=TEACHER["EE"], EI=-1.0)


def wedge(c, amp):
    return {"r": s37.wedge_r(c, amp), "exc": 0.0, "g0": 0.0, "Ustar": 0.0}


def bump_ok(f):
    width, peaks, contrast, amp = us.shape(f)
    return peaks == 1 and contrast >= 0.3 and amp >= s37.MIN_AMP


def dark_bump(w, T):
    f, _ = us.run(w, [(s37.T_LIGHT, T.light(0.0), 0.0), (3.0, us.DARK, 0.0)])
    width, peaks, contrast, amp = us.shape(f)
    return {"fwhm": width, "peaks": peaks, "contrast": contrast, "amp_hz": 1e3 * amp, "centre": us.com(f),
            "peak_over_fmax": float(f.max() / us.P["fmax"]), "n_hd_above_0p9_fmax": int(np.sum(f >= 0.9 * us.P["fmax"]))}


def continuity(w, T):
    every = int(0.1 / us.P["dt"])
    out = []
    for c in s37.CUES_C:
        f, tr = us.run(w, [(s37.T_LIGHT, T.light(c), 0.0), (s37.T_DARK_C, us.DARK, 0.0)], every)
        dark = np.unwrap(np.radians(tr[int(s37.T_LIGHT / 0.1):]))
        late = np.arange(dark.size) * 0.1 >= s37.T_DARK_C - 5.0
        slope = float(np.degrees(np.polyfit(np.arange(dark.size)[late] * 0.1, dark[late], 1)[0]))
        out.append({"cue": float(c), "final": us.com(f), "err": float(s37.wrapd(us.com(f) - c)), "bump": bool(bump_ok(f)), "late_drift_deg_s": slope})
    err = np.array([abs(o["err"]) for o in out])
    kept = np.array([o["bump"] for o in out]) & (err <= 22.5)
    return {"trials": out, "retention": float(kept.mean()), "median_abs_err": float(np.median(err)), "max_abs_err": float(err.max()),
            "median_abs_late_drift_deg_s": float(np.median([abs(o["late_drift_deg_s"]) for o in out])), "C1": bool(kept.mean() >= 0.8)}


def two_cue(w, T):
    out = []
    for c in s37.BASES_S1:
        f, _ = us.run(w, [(s37.T_LIGHT, T.light(c, 1.0, c + 180.0, 0.9), 0.0), (s37.T_DARK_S1, us.DARK, 0.0)])
        width, peaks, contrast, amp = us.shape(f)
        out.append({"strong": float(c), "final": us.com(f), "peaks": peaks, "amp_hz": 1e3 * amp,
                    "ok": bool(bump_ok(f) and abs(s37.wrapd(us.com(f) - c)) <= 22.5)})
    n_ok = sum(o["ok"] for o in out)
    return {"trials": out, "n_ok": n_ok, "S1": bool(n_ok >= 7)}


def jumped(w, T, b, delta, amp):
    f, _ = us.run(w, [(s37.T_LIGHT, T.light(b), 0.0), (s37.T_FIRST, wedge(b, s37.A_FIRST), 0.0),
                      (s37.T_SECOND, wedge(b + delta, amp), 0.0), (s37.T_AFTER, us.DARK, 0.0)])
    return bool(bump_ok(f) and abs(s37.wrapd(us.com(f) - (b + delta))) <= 22.5)


def threshold(w, T, b, delta):
    if not jumped(w, T, b, delta, s37.A_MAX):
        return None
    lo, hi = 0.0, s37.A_MAX
    for _ in range(s37.BISECT):
        mid = (lo + hi) / 2
        if jumped(w, T, b, delta, mid):
            hi = mid
        else:
            lo = mid
    return hi


def jump_thresholds(w, T):
    thr = {str(int(d)): [threshold(w, T, b, d) for b in s37.BASES_S2] for d in (90.0, 180.0)}
    med = {k: (float(np.median(v)) if all(t is not None for t in v) else None) for k, v in thr.items()}
    ratio = med["180"] / med["90"] if med["90"] and med["180"] else None
    return {"thresholds": thr, "median": med, "ratio_180_over_90": ratio, "S2": bool(ratio is not None and 0.8 <= ratio <= 1.25)}


def suppression(w, T, b=0.0):
    sel = np.abs(s37.wrapd(us.DIR - b)) <= 11.25
    out = []
    for a2 in s37.A2_SET:
        inp = {"r": s37.wedge_r(b, s37.A_REF) + s37.wedge_r(b + 180.0, a2), "exc": 0.0, "g0": 0.0, "Ustar": 0.0}
        f, _ = us.run(w, [(s37.T_LIGHT, T.light(b), 0.0), (1.0, us.DARK, 0.0), (s37.T_SECOND, inp, 0.0)])
        out.append(float(f[sel].mean() - f.min()))
    return {"A2": list(s37.A2_SET), "ref_activity": out, "S3": bool(out[0] > 0 and min(out) < 0.5 * out[0])}


def rotation(w, T, speeds):
    every = int(0.05 / us.P["dt"])
    out = {}
    for om in speeds:
        f, tr = us.run(w, [(s37.T_LIGHT, T.light(0.0), 0.0), (s37.T_ROT, us.DARK, om)], every)
        ph = np.degrees(np.unwrap(np.radians(tr[int(s37.T_LIGHT / 0.05):])))
        t = np.arange(ph.size) * 0.05
        m = t >= s37.FIT_FROM
        coef = np.polyfit(t[m], ph[m], 1)
        r2 = 1 - np.sum((ph[m] - np.polyval(coef, t[m])) ** 2) / max(np.sum((ph[m] - ph[m].mean()) ** 2), 1e-12)
        out[str(int(om))] = {"gain": float(coef[0] / om), "r2": float(r2), "bump_end": bool(bump_ok(f))}
    return out


def analyse(w, T):
    rot, slow = rotation(w, T, SPEEDS_R1), rotation(w, T, SPEEDS_SLOW)
    return {"dark_bump": dark_bump(w, T), "continuity": continuity(w, T), "two_cue": two_cue(w, T), "jump": jump_thresholds(w, T),
            "suppression": suppression(w, T),
            "rotation": {"speeds": rot, "report_slow": slow,
                         "R1": bool(all(0.8 <= o["gain"] <= 1.2 and o["r2"] >= 0.99 and o["bump_end"] for o in rot.values()))}}


def summary(r):
    return {"dark_bump": r["dark_bump"], "C1": [r["continuity"][k] for k in ("retention", "median_abs_err", "max_abs_err", "C1")],
            "S1": [r["two_cue"]["n_ok"], r["two_cue"]["S1"]], "S2": [r["jump"]["thresholds"], r["jump"]["ratio_180_over_90"], r["jump"]["S2"]],
            "S3": [[round(1e3 * v, 1) for v in r["suppression"]["ref_activity"]], r["suppression"]["S3"]],
            "R1": [{k: (round(o["gain"], 3), round(o["r2"], 4)) for k, o in {**r["rotation"]["speeds"], **r["rotation"]["report_slow"]}.items()}, r["rotation"]["R1"]]}


def code_hash():
    h = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    if h not in contract:
        raise SystemExit(f"CONTRACT.md does not list this code hash {h}")
    for dep in ("us_network.py", "us_fast.py", "train_long.py"):
        dh = hashlib.sha256((HERE / dep).read_bytes()).hexdigest()
        if dh not in contract:
            raise SystemExit(f"CONTRACT.md does not list {dep} hash {dh}")
    return h


def main_train(kind):
    import train_long as tl
    import us_fast as uf
    h = code_hash()
    T = teacher(kind)
    rng = np.random.default_rng(SEED)
    n, m = us.N, us.N
    w = rng.normal(0, np.sqrt(1 / (n + m)), (n, n + m))
    steps, chunks = int(round(T_TRAIN / us.P["dt"])), 100
    K = steps // chunks
    th_last, v_last = 180.0, 0.0
    st = tl.authors_init_state(n, m, th_last)
    snaps, errs = [], []
    for c in range(chunks):
        th, v_last = tl.ou_chunk(th_last, v_last, rng.standard_normal(K), us.P["dt"], 225.0, 0.5)
        th_last = th[-1]
        w, sn, er = uf.train_fast(w, th, T, us.P, us.DIR, us.W_ROT, us.SIGN, soma="exp", n_snap=1, state=st)
        snaps.append(w.copy())
        errs.append(float(er[0]))
    out = HERE / f"trained_{kind}.npz"
    with out.open("xb") as stream:
        np.savez(stream, w=w, snaps=np.array(snaps), err_hz=np.array(errs), code_sha256=h)
    print("trained", kind, T_TRAIN, "s; error first/last %.3f/%.3f Hz" % (errs[0], np.mean(errs[-5:])), "sha256", hashlib.sha256(out.read_bytes()).hexdigest())


def main_test():
    h = code_hash()
    res, sha, curves = {}, {}, {}
    for kind in ("conductance", "current"):
        path = HERE / f"trained_{kind}.npz"
        z = np.load(path)
        if str(z["code_sha256"]) != h:
            raise SystemExit(f"{path.name} was not made by this code")
        sha[kind], curves[kind] = hashlib.sha256(path.read_bytes()).hexdigest(), z["err_hz"].tolist()
        T = teacher(kind)
        nets = (("trained", z["w"]), ("control_homogeneous", s37.homogeneous(z["w"]))) if kind == "conductance" else (("paired_current_teacher", z["w"]),)
        for k, wk in nets:
            res[f"{kind}:{k}"] = analyse(wk, T)
            print("==", kind, k, json.dumps(summary(res[f"{kind}:{k}"]), default=float), flush=True)
    L = res["conductance:trained"]
    crit = {"C1": L["continuity"]["C1"], "S1": L["two_cue"]["S1"], "S2": L["jump"]["S2"], "R1": L["rotation"]["R1"],
            "S3_secondary": L["suppression"]["S3"]}
    ok = crit["C1"] and crit["S1"] and crit["S2"] and crit["R1"]
    result = {"schema": "ce-a1-step39-conductance-teacher-selection", "code_sha256": h, "teacher": TEACHER, "T_train_s": T_TRAIN, "seed": SEED,
              "network_sha256": sha, "error_curve_hz": curves,
              "verdict": "CONDUCTANCE_TEACHER_RING_SELECTS_PERSISTS_ROTATES" if ok else "CONDUCTANCE_TEACHER_RING_DOES_NOT_SATISFY_ALL",
              "criteria": crit, "networks": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], crit)


if __name__ == "__main__":
    if sys.argv[1] == "train":
        main_train(sys.argv[2])
    else:
        main_test()
