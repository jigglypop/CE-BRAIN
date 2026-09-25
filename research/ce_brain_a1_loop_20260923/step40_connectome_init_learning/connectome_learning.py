"""A1 step 40: started from the real EPG/PEN wiring, does the predictive learning rule reach a working ring sooner than
from shuffled or random wiring, and does the trained connectome ring hold its bump, rotate at fly turning speeds and
select? (CONTRACT.md)

Network: the authors' fly_rec.network equations (step 39 port, exact somatic step, checked against the authors) with
HD = EPG (E1 PB-glomerulus angles) and HR = PEN_a + PEN_b. Teacher: the authors' current-based visual input with
M = 3, sigma = 0.26, chosen by the step 38 width law 4 asin(sigma sqrt(2 ln M)) = 91 deg (fly: 82-91 deg).
Fixed HD->HR = EPG->PEN synapse counts, each PEN row normalised to the authors' 2/fmax. Velocity sign of each PB side =
sign of that side's PEN->EPG angular shift. Plastic init w = [a C(PEN->EPG) | b C(EPG->EPG) - c C(Delta7->EPG)
C(EPG->Delta7)], with a, b, c matching the mean row sums of the positive / negative parts of a trained 60-cell network
with a ~90 deg bump (step 38 calibration M = 3, sigma = 0.25; magnitude only). Controls: the same entries shuffled
inside each block; the authors' random init N(0, 1/N). One OU trajectory per dataset shared by the three conditions.

python connectome_learning.py train <malecns|hemibrain> <connectome|shuffled|random>
python connectome_learning.py evaluate
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
S39 = LOOP / "step39_conductance_teacher"
sys.path.insert(0, str(S39))
import us_network as us  # noqa: E402
import us_fast as uf  # noqa: E402
import train_long as tl  # noqa: E402

us.SOMA["mode"] = "exp"
TEACHER = {"kind": "current", "M": 3.0, "sigma": 0.26}
MAGNITUDE_SOURCE = HERE / "magnitude_source.npz"       # step 38 calibration network M=3, sigma=0.25 (row-sum magnitudes only)
T_TRAIN, SEEDS = 80000.0, {"malecns": 61, "hemibrain": 62}
SHUFFLE_SEED, RANDOM_SEED = 1, 2
DATASETS, CONDITIONS = ("malecns", "hemibrain"), ("connectome", "shuffled", "random")
CHECK = (5, 10, 25, 50, 100)                            # percent of training at which snapshots are evaluated
SPEEDS_R1, SPEEDS_SLOW = (-180.0, -90.0, -60.0, 60.0, 90.0, 180.0), (-30.0, 30.0)
CUES_C = np.arange(0, 360, 6.0)
BASES_S1 = np.arange(0, 360, 45.0)
BASES_S2 = (0.0, 90.0, 180.0, 270.0)
T_LIGHT, T_DARK_C, T_DARK_S1, T_ROT, FIT_FROM = 2.0, 10.0, 5.0, 12.0, 2.0
T_FIRST, T_SECOND, T_AFTER = 2.5, 1.842, 3.0
A_FIRST, A_MAX, BISECT = 16.0, 32.0, 12
MIN_AMP = 0.25 * us.P["fmax"]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def wrapd(a):
    return (np.asarray(a) + 180.0) % 360.0 - 180.0


class Net:
    def __init__(self, ang_hd, w_rot_true, sign):
        self.ang = np.asarray(ang_hd, float) % 360
        self.n, self.m = len(self.ang), len(sign)
        perm = np.r_[np.arange(0, self.n, 2), np.arange(1, self.n, 2)]   # network() feeds HR with x[::2] ++ x[1::2]
        self.w_rot = np.ascontiguousarray(np.asarray(w_rot_true, float)[:, perm])
        self.sign = np.asarray(sign, float)
        self.grid = np.unique(np.round(self.ang, 6))
        self.spacing = 360.0 / len(self.grid)


def teacher():
    return us.Teacher("current", M=TEACHER["M"], sigma=TEACHER["sigma"])


def light(net, T, c, m=1.0, c2=None, m2=0.0):
    return T.light(c, m, c2, m2, ang=net.ang)


def wedge(net, c, amp):
    d = wrapd(net.ang - c)
    h = net.spacing / 2
    r = amp * np.clip(np.minimum(d + h, 11.25) - np.maximum(d - h, -11.25), 0, None) / net.spacing
    return {"r": r, "exc": 0.0, "g0": 0.0, "Ustar": 0.0}


def com(net, f):
    return float(np.degrees(np.angle(np.sum(f * np.exp(1j * np.radians(net.ang))))) % 360)


def shape(net, f):
    p = np.array([f[np.isclose(net.ang, a)].mean() for a in net.grid])
    q = p - p.min()
    if q.max() <= 1e-9:
        return None, 0, 0.0, 0.0
    peaks = int(np.sum((q > np.roll(q, 1)) & (q >= np.roll(q, -1)) & (q > 0.5 * q.max())))
    grid = np.arange(0, 360, 0.25)
    fine = np.interp(grid, np.r_[net.grid - 360, net.grid, net.grid + 360], np.r_[q, q, q])
    return float(np.sum(fine >= fine.max() / 2) * 0.25), peaks, float(q.max() / max(p.max(), 1e-12)), float(q.max())


def bump_ok(net, f):
    width, peaks, contrast, amp = shape(net, f)
    return peaks == 1 and contrast >= 0.3 and amp >= MIN_AMP


def run(net, w, phases, every=0):
    w, st, trace = w.copy(), us.zero_state(net.n, net.m), []
    k = us.P["v0"] / us.P["v_max"]
    for sec, inp, omega in phases:
        v = net.sign * k * omega
        for s in range(int(round(sec / us.P["dt"]))):
            w, _ = us.step(st, w, v, inp, False, w_rot=net.w_rot)
            if every and s % every == 0:
                trace.append(com(net, st["f"]))
    return st["f"], np.array(trace)


def rotation(net, w, T, speeds):
    every = int(0.05 / us.P["dt"])
    out = {}
    for om in speeds:
        f, tr = run(net, w, [(T_LIGHT, light(net, T, 0.0), 0.0), (T_ROT, us.DARK, om)], every)
        ph = np.degrees(np.unwrap(np.radians(tr[int(T_LIGHT / 0.05):])))
        t = np.arange(ph.size) * 0.05
        msk = t >= FIT_FROM
        coef = np.polyfit(t[msk], ph[msk], 1)
        r2 = 1 - np.sum((ph[msk] - np.polyval(coef, t[msk])) ** 2) / max(np.sum((ph[msk] - ph[msk].mean()) ** 2), 1e-12)
        out[str(int(om))] = {"gain": float(coef[0] / om), "r2": float(r2), "bump_end": bool(bump_ok(net, f))}
    return out


def r1_pass(rot):
    return bool(all(0.8 <= o["gain"] <= 1.2 and o["r2"] >= 0.99 and o["bump_end"] for o in rot.values()))


def continuity(net, w, T):
    every = int(0.1 / us.P["dt"])
    out = []
    for c in CUES_C:
        f, tr = run(net, w, [(T_LIGHT, light(net, T, c), 0.0), (T_DARK_C, us.DARK, 0.0)], every)
        out.append({"cue": float(c), "err": float(wrapd(com(net, f) - c)), "bump": bool(bump_ok(net, f))})
    err = np.array([abs(o["err"]) for o in out])
    kept = np.array([o["bump"] for o in out]) & (err <= 22.5)
    return {"trials": out, "retention": float(kept.mean()), "median_abs_err": float(np.median(err)), "C1": bool(kept.mean() >= 0.8)}


def two_cue(net, w, T):
    out = []
    for c in BASES_S1:
        f, _ = run(net, w, [(T_LIGHT, light(net, T, c, 1.0, c + 180.0, 0.9), 0.0), (T_DARK_S1, us.DARK, 0.0)])
        out.append({"strong": float(c), "final": com(net, f), "ok": bool(bump_ok(net, f) and abs(wrapd(com(net, f) - c)) <= 22.5)})
    n_ok = sum(o["ok"] for o in out)
    return {"trials": out, "n_ok": n_ok, "S1": bool(n_ok >= 7)}


def jumped(net, w, T, b, delta, amp):
    f, _ = run(net, w, [(T_LIGHT, light(net, T, b), 0.0), (T_FIRST, wedge(net, b, A_FIRST), 0.0),
                        (T_SECOND, wedge(net, b + delta, amp), 0.0), (T_AFTER, us.DARK, 0.0)])
    return bool(bump_ok(net, f) and abs(wrapd(com(net, f) - (b + delta))) <= 22.5)


def threshold(net, w, T, b, delta):
    if not jumped(net, w, T, b, delta, A_MAX):
        return None
    lo, hi = 0.0, A_MAX
    for _ in range(BISECT):
        mid = (lo + hi) / 2
        if jumped(net, w, T, b, delta, mid):
            hi = mid
        else:
            lo = mid
    return hi


def jump_thresholds(net, w, T):
    thr = {str(int(d)): [threshold(net, w, T, b, d) for b in BASES_S2] for d in (90.0, 180.0)}
    med = {k: (float(np.median(v)) if all(t is not None for t in v) else None) for k, v in thr.items()}
    ratio = med["180"] / med["90"] if med["90"] and med["180"] else None
    return {"thresholds": thr, "median": med, "ratio_180_over_90": ratio, "S2": bool(ratio is not None and 0.8 <= ratio <= 1.25)}


def dark_bump(net, w, T):
    f, _ = run(net, w, [(T_LIGHT, light(net, T, 0.0), 0.0), (3.0, us.DARK, 0.0)])
    width, peaks, contrast, amp = shape(net, f)
    return {"fwhm": width, "peaks": peaks, "amp_hz": 1e3 * amp, "peak_over_fmax": float(f.max() / us.P["fmax"])}


# ---------------------------------------------------------------- connectome network

def connectome(dataset):
    lf = load("label_free_ring", LOOP / "step17_label_free_ring/label_free_ring.py")
    if dataset == "malecns":
        w, kind, side, label = lf.malecns()
    else:
        h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
        A, ty, inst, sd, nt = h22.hemibrain()
        base = np.array([v for v in range(len(ty)) if ty[v] in lf.TYPES])
        label = [(lambda mm: (mm.group(1), int(mm.group(2))) if mm else None)(h22.GLOM.search(inst[v])) for v in base]
        w, kind = h22.sub(A, base), [ty[v] for v in base]
    idx = lambda f: np.array([i for i, k in enumerate(kind) if f(k, i)])
    epg = idx(lambda k, i: k == "EPG" and label[i] is not None)
    pen = idx(lambda k, i: k.startswith("PEN") and label[i] is not None)
    d7 = idx(lambda k, i: k == "Delta7")
    B = lambda post, pre: w[np.ix_(post, pre)]
    ang_e = np.degrees([lf.phi(*label[i]) for i in epg])
    ang_p = np.degrees([lf.phi(*label[i]) for i in pen])
    side_p = np.array([label[i][0] for i in pen])
    C_pe = B(epg, pen)
    shift = {}
    for s in ("L", "R"):
        cols = side_p == s
        off = np.radians(wrapd(ang_e[:, None] - ang_p[None, cols]))
        shift[s] = float(np.degrees(np.angle(np.sum(C_pe[:, cols] * np.exp(1j * off)))))
    sign = np.array([np.sign(shift[s]) for s in side_p])
    C_ep = B(pen, epg)
    w_rot = C_ep / np.maximum(C_ep.sum(1, keepdims=True), 1e-12) * (2 / us.P["fmax"])
    return {"net": Net(ang_e, w_rot, sign), "C_pe": C_pe, "C_ee": B(epg, epg), "C_ede": B(epg, d7) @ B(d7, epg),
            "shift_deg": shift, "counts": {"EPG": len(epg), "PEN": len(pen), "Delta7": len(d7)}}


def magnitudes():
    W = np.load(MAGNITUDE_SOURCE)["w"]
    hr, hd = W[:, :60], W[:, 60:]
    return {"hr_pos": float(np.maximum(hr, 0).sum(1).mean()), "hd_pos": float(np.maximum(hd, 0).sum(1).mean()),
            "hd_neg": float(np.maximum(-hd, 0).sum(1).mean())}


def initial_w(c, condition):
    mag = magnitudes()
    a = mag["hr_pos"] / c["C_pe"].sum(1).mean()
    b = mag["hd_pos"] / c["C_ee"].sum(1).mean()
    cc = mag["hd_neg"] / c["C_ede"].sum(1).mean()
    hr, hd = a * c["C_pe"], b * c["C_ee"] - cc * c["C_ede"]
    if condition == "shuffled":
        rng = np.random.default_rng(SHUFFLE_SEED)
        hr = rng.permutation(hr.ravel()).reshape(hr.shape)
        hd = rng.permutation(hd.ravel()).reshape(hd.shape)
    w = np.hstack([hr, hd])
    if condition == "random":
        w = np.random.default_rng(RANDOM_SEED).normal(0, np.sqrt(1 / w.shape[1]), w.shape)
    return w, {"a": a, "b": b, "c": cc, **mag}


def checked_hash():
    h = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    if h not in contract:
        raise SystemExit(f"CONTRACT.md does not list this code hash {h}")
    for dep in (S39 / "us_network.py", S39 / "us_fast.py", S39 / "train_long.py", MAGNITUDE_SOURCE):
        dh = hashlib.sha256(dep.read_bytes()).hexdigest()
        if dh not in contract:
            raise SystemExit(f"CONTRACT.md does not list {dep.name} hash {dh}")
    return h


def main_train(dataset, condition):
    h = checked_hash()
    c = connectome(dataset)
    net = c["net"]
    w, scales = initial_w(c, condition)
    w0 = w.copy()
    rng = np.random.default_rng(SEEDS[dataset])                 # same trajectory for the three conditions
    steps, chunks = int(round(T_TRAIN / us.P["dt"])), 100
    K = steps // chunks
    th_last, v_last = 180.0, 0.0
    st = us.zero_state(net.n, net.m)
    snaps, errs = [], []
    for k in range(chunks):
        th, v_last = tl.ou_chunk(th_last, v_last, rng.standard_normal(K), us.P["dt"], 225.0, 0.5)
        th_last = th[-1]
        w, sn, er = uf.train_fast(w, th, teacher(), us.P, net.ang, net.w_rot, net.sign, soma="exp", n_snap=1, state=st)
        snaps.append(w.copy())
        errs.append(float(er[0]))
    out = HERE / f"train_{dataset}_{condition}.npz"
    with out.open("xb") as stream:
        np.savez(stream, w0=w0, w=w, snaps=np.array(snaps), err_hz=np.array(errs), code_sha256=h)
    print(dataset, condition, "err first/last %.3f/%.3f" % (errs[0], np.mean(errs[-5:])), scales, c["shift_deg"], flush=True)


def corr(a, b):
    a, b = a.ravel() - a.mean(), b.ravel() - b.mean()
    return float(a @ b / np.sqrt((a @ a) * (b @ b)))


def main_evaluate():
    h = checked_hash()
    T = teacher()
    res = {"schema": "ce-a1-step40-connectome-init-learning", "code_sha256": h, "teacher": TEACHER, "T_train_s": T_TRAIN, "datasets": {}}
    for ds in DATASETS:
        c = connectome(ds)
        net = c["net"]
        d = {"counts": c["counts"], "pen_shift_deg": c["shift_deg"], "runs": {}}
        for cond in CONDITIONS:
            z = np.load(HERE / f"train_{ds}_{cond}.npz")
            if str(z["code_sha256"]) != h:
                raise SystemExit(f"train_{ds}_{cond}.npz was not made by this code")
            snaps, err = z["snaps"], z["err_hz"]
            curve = {str(p): {"gain90": rotation(net, snaps[p - 1], T, (90.0,))["90"]} for p in CHECK}
            wf = z["w"]
            rot, slow = rotation(net, wf, T, SPEEDS_R1), rotation(net, wf, T, SPEEDS_SLOW)
            run_res = {"err_hz_first10pct": float(err[:10].mean()), "err_hz_last5pct": float(err[-5:].mean()), "err_curve_hz": err.tolist(),
                       "gain90_at_percent": curve, "dark_bump": dark_bump(net, wf, T), "rotation": rot, "rotation_slow": slow, "R1": r1_pass(rot),
                       "corr_final_init_hr": corr(wf[:, :net.m], z["w0"][:, :net.m]), "corr_final_init_hd": corr(wf[:, net.m:], z["w0"][:, net.m:])}
            if cond == "connectome":
                run_res["before_training"] = {"dark_bump": dark_bump(net, z["w0"], T), "rotation": rotation(net, z["w0"], T, (90.0,)),
                                              "continuity": continuity(net, z["w0"], T)}
                run_res["continuity"] = continuity(net, wf, T)
                run_res["two_cue"] = two_cue(net, wf, T)
                run_res["jump"] = jump_thresholds(net, wf, T)
            d["runs"][cond] = run_res
            print("==", ds, cond, json.dumps({k: run_res[k] for k in ("err_hz_first10pct", "err_hz_last5pct", "gain90_at_percent", "R1", "dark_bump")}, default=float), flush=True)
        r = d["runs"]
        d["H1_head_start"] = bool(r["connectome"]["err_hz_first10pct"] < min(r["shuffled"]["err_hz_first10pct"], r["random"]["err_hz_first10pct"]))
        d["H2_function"] = bool(r["connectome"]["R1"] and r["connectome"]["continuity"]["C1"])
        d["H3_selection"] = bool(r["connectome"]["two_cue"]["S1"])          # narrow-input jump (S2) reported only
        res["datasets"][ds] = d
    ok = all(d["H1_head_start"] and d["H2_function"] and d["H3_selection"] for d in res["datasets"].values())
    res["verdict"] = "CONNECTOME_INIT_LEARNS_WORKING_RING" if ok else "CONNECTOME_INIT_DOES_NOT_SATISFY_ALL"
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(res, stream, indent=1, default=float)
    print("verdict", res["verdict"], {ds: (d["H1_head_start"], d["H2_function"], d["H3_selection"]) for ds, d in res["datasets"].items()})


if __name__ == "__main__":
    if sys.argv[1] == "train":
        main_train(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "evaluate":
        main_evaluate()
