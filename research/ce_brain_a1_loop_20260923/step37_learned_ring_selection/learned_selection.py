"""A1 step 37: does the learned ring (end point of the Vafidis et al. 2022 predictive learning rule) keep one bump,
hold it without wells in darkness and rotate smoothly? (CONTRACT.md)

Equations: the authors' fly_rec.network (two-compartment HD cells, HR cells, fixed HD->HR, learned w), the authors'
parameters, no noise, no training. Inputs are written in HD-direction coordinates: light = the authors' visual input
(vis_in with global excitation), darkness = no visual input and no global excitation, optogenetic wedge = 22.5 deg sector
of somatic input (Kim et al. 2017 Science), angular velocity = the authors' vestibular input to HR cells.

python learned_selection.py              full run; refuses unless CONTRACT.md lists this code hash
python learned_selection.py --synthetic  hand-made local / global rings in the same model family (pre-freeze, writes nothing)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VAF = ROOT / "data/external/vafidis_2022_learnpi"
LEARNED = VAF / "fly_rec2Enoughv02inh1rot15NoClipOUsigma225tau05NoBoundx1k1b25s015exc4N60InitNoAnneal05.npz"
sys.path.insert(0, str(VAF))
import fly_rec as rec  # noqa: E402

P = {"dt": 5e-4, "n_neu": 60, "v0": 2, "v_max": 720, "M": 4, "sigma": .15, "inh": -1, "inh_rot": -1.5, "n_sigma": 0,
     "exc": 4, "tau_s": 65, "filt": True, "tau_d": 100, "x0": 1, "beta": 2.5, "gD": 2, "gL": 1, "fmax": .15, "eta": 5e-2}
N, NDIR, DPHI = 60, 30, 12.0
DIR = np.repeat(np.arange(NDIR) * DPHI, 2)            # HD neuron directions (deg); pairs share a direction
W_ROT = np.diag(np.full(N, 2 / P["fmax"]))            # authors' default 1-1 HD -> HR
SIGN = np.r_[np.ones(N // 2), -np.ones(N // 2)]
K_VEST = P["v0"] / P["v_max"]
DARK = (0.0, 0.0)

T_LIGHT, T_DARK_C, T_DARK_S1 = 2.0, 10.0, 5.0         # s
T_FIRST, T_SECOND, T_AFTER = 2.5, 1.842, 3.0          # Kim 2017 protocol 1: first profile ~2-3 s, second 100 frames
A_FIRST, A_MAX, BISECT = 16.0, 32.0, 12               # authors' stimulation magnitude (stability.py M=16)
A_REF, A2_SET = 8.0, (0.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 36.0)  # Kim 2017: fixed reference, second up to 4.5x
CUES_C = np.arange(0, 360, 6.0)
BASES_S1 = np.arange(0, 360, 45.0)
BASES_S2 = (0.0, 90.0, 180.0, 270.0)
SPEEDS, T_ROT, FIT_FROM = (-60.0, -30.0, 30.0, 60.0), 12.0, 2.0
MIN_AMP = 0.25 * P["fmax"]


def wrapd(a):
    return (np.asarray(a) + 180.0) % 360.0 - 180.0


def light(c, m=1.0, c2=None, m2=0.0):
    th = np.radians(DIR)
    g = lambda cc: np.exp(-np.sin((th - np.radians(cc)) / 2) ** 2 / (2 * P["sigma"] ** 2))
    r = P["M"] * m * g(c) + (0.0 if c2 is None else P["M"] * m2 * g(c2)) - P["exc"] - 1
    return r, P["exc"]


def wedge_r(c, amp):
    d = wrapd(DIR - c)
    return amp * np.clip(np.minimum(d + DPHI / 2, 11.25) - np.maximum(d - DPHI / 2, -11.25), 0, None) / DPHI


def com(f):
    return float(np.degrees(np.angle(np.sum(f * np.exp(1j * np.radians(DIR))))) % 360)


def shape(f):
    p = f.reshape(NDIR, 2).mean(1)
    q = p - p.min()
    if q.max() <= 1e-9:
        return None, 0, 0.0, 0.0
    peaks = int(np.sum((q > np.roll(q, 1)) & (q >= np.roll(q, -1)) & (q > 0.5 * q.max())))
    a = np.arange(NDIR) * DPHI
    grid = np.arange(0, 360, 0.25)
    fine = np.interp(grid, np.r_[a - 360, a, a + 360], np.r_[q, q, q])
    return float(np.sum(fine >= fine.max() / 2) * 0.25), peaks, float(q.max() / max(p.max(), 1e-12)), float(q.max())


def run(w, phases, every=0):
    """phases: list of (seconds, (r, exc), omega deg/s). Returns final HD rates and the bump-centre trace."""
    w = w.copy()
    f, f_rot, u, V, Iden, x = (np.zeros(N) for _ in range(6))
    Delta, PSP, I_PSP = np.zeros((N, 2 * N)), np.zeros(2 * N), np.zeros(2 * N)
    dt_ms, trace = P["dt"] * 1e3, []
    for sec, (r, exc), omega in phases:
        v = SIGN * K_VEST * omega
        for s in range(int(round(sec / P["dt"]))):
            f, f_rot, u, Iden, V, Delta, w, PSP, I_PSP, x, _ = rec.network(
                f, f_rot, u, w, W_ROT, v, r, Iden, V, Delta, PSP, I_PSP, x, False, P["eta"], P["x0"], P["beta"], P["fmax"],
                dt_ms, P["inh"], P["inh_rot"], exc, P["n_sigma"], P["filt"], P["tau_s"], P["tau_d"], P["gD"], P["gL"])
            if every and s % every == 0:
                trace.append(com(f))
    return f, np.array(trace)


def bump_ok(f):
    width, peaks, contrast, amp = shape(f)
    return peaks == 1 and contrast >= 0.3 and amp >= MIN_AMP


def continuity(w):
    every = int(0.1 / P["dt"])
    out = []
    for c in CUES_C:
        f, tr = run(w, [(T_LIGHT, light(c), 0.0), (T_DARK_C, DARK, 0.0)], every)
        dark = np.unwrap(np.radians(tr[int(T_LIGHT / 0.1):]))
        late = np.arange(dark.size) * 0.1 >= T_DARK_C - 5.0
        slope = float(np.degrees(np.polyfit(np.arange(dark.size)[late] * 0.1, dark[late], 1)[0]))
        width, peaks, contrast, amp = shape(f)
        out.append({"cue": float(c), "final": com(f), "err": float(wrapd(com(f) - c)), "bump": bool(bump_ok(f)),
                    "fwhm": width, "amp_hz": 1e3 * amp, "late_drift_deg_s": slope})
    err = np.array([abs(o["err"]) for o in out])
    kept = np.array([o["bump"] for o in out]) & (err <= 22.5)
    widths = [o["fwhm"] for o in out if o["fwhm"] is not None]
    return {"trials": out, "retention": float(kept.mean()), "median_abs_err": float(np.median(err)), "max_abs_err": float(err.max()),
            "median_fwhm": float(np.median(widths)) if widths else None,
            "median_abs_late_drift_deg_s": float(np.median([abs(o["late_drift_deg_s"]) for o in out])), "C1": bool(kept.mean() >= 0.8)}


def two_cue(w):
    out = []
    for c in BASES_S1:
        f, _ = run(w, [(T_LIGHT, light(c, 1.0, c + 180.0, 0.9), 0.0), (T_DARK_S1, DARK, 0.0)])
        width, peaks, contrast, amp = shape(f)
        ok = bool(bump_ok(f) and abs(wrapd(com(f) - c)) <= 22.5)
        out.append({"strong": float(c), "final": com(f), "peaks": peaks, "contrast": contrast, "amp_hz": 1e3 * amp, "fwhm": width, "ok": ok})
    n_ok = sum(o["ok"] for o in out)
    return {"trials": out, "n_ok": n_ok, "S1": bool(n_ok >= 7)}


def jumped(w, b, delta, amp):
    f, _ = run(w, [(T_LIGHT, light(b), 0.0), (T_FIRST, (wedge_r(b, A_FIRST), 0.0), 0.0),
                   (T_SECOND, (wedge_r(b + delta, amp), 0.0), 0.0), (T_AFTER, DARK, 0.0)])
    return bool(bump_ok(f) and abs(wrapd(com(f) - (b + delta))) <= 22.5)


def threshold(w, b, delta):
    if not jumped(w, b, delta, A_MAX):
        return None
    lo, hi = 0.0, A_MAX
    for _ in range(BISECT):
        mid = (lo + hi) / 2
        if jumped(w, b, delta, mid):
            hi = mid
        else:
            lo = mid
    return hi


def jump_thresholds(w):
    thr = {str(int(d)): [threshold(w, b, d) for b in BASES_S2] for d in (90.0, 180.0)}
    med = {k: (float(np.median(v)) if all(t is not None for t in v) else None) for k, v in thr.items()}
    ratio = med["180"] / med["90"] if med["90"] and med["180"] else None
    return {"thresholds": thr, "median": med, "ratio_180_over_90": ratio, "S2": bool(ratio is not None and 0.8 <= ratio <= 1.25)}


def suppression(w, b=0.0):
    sel = np.abs(wrapd(DIR - b)) <= 11.25
    out = []
    for a2 in A2_SET:
        f, _ = run(w, [(T_LIGHT, light(b), 0.0), (1.0, DARK, 0.0), (T_SECOND, (wedge_r(b, A_REF) + wedge_r(b + 180.0, a2), 0.0), 0.0)])
        out.append(float(f[sel].mean() - f.min()))
    return {"A2": list(A2_SET), "ref_activity": out, "S3": bool(out[0] > 0 and min(out) < 0.5 * out[0])}


def rotation(w):
    every = int(0.05 / P["dt"])
    out = {}
    for om in SPEEDS:
        f, tr = run(w, [(T_LIGHT, light(0.0), 0.0), (T_ROT, DARK, om)], every)
        ph = np.degrees(np.unwrap(np.radians(tr[int(T_LIGHT / 0.05):])))
        t = np.arange(ph.size) * 0.05
        m = t >= FIT_FROM
        coef = np.polyfit(t[m], ph[m], 1)
        pred = np.polyval(coef, t[m])
        r2 = 1 - np.sum((ph[m] - pred) ** 2) / np.sum((ph[m] - ph[m].mean()) ** 2)
        inst = np.diff(ph[m]) / 0.05
        out[str(int(om))] = {"gain": float(coef[0] / om), "r2": float(r2), "speed_cv": float(np.std(inst) / max(abs(np.mean(inst)), 1e-9)),
                             "bump_end": bool(bump_ok(f))}
    ok = all(0.8 <= o["gain"] <= 1.2 and o["r2"] >= 0.99 and o["bump_end"] for o in out.values())
    return {"speeds": out, "R1": bool(ok)}


def analyse(w, parts=("C", "S1", "S2", "S3", "R1")):
    res = {}
    f, _ = run(w, [(T_LIGHT, light(0.0), 0.0), (3.0, DARK, 0.0)])
    width, peaks, contrast, amp = shape(f)
    res["dark_bump"] = {"fwhm": width, "peaks": peaks, "contrast": contrast, "amp_hz": 1e3 * amp, "centre": com(f),
                        "peak_over_fmax": float(f.max() / P["fmax"]), "n_hd_above_0p9_fmax": int(np.sum(f >= 0.9 * P["fmax"]))}
    if "C" in parts:
        res["continuity"] = continuity(w)
    if "S1" in parts:
        res["two_cue"] = two_cue(w)
    if "S2" in parts:
        res["jump"] = jump_thresholds(w)
    if "S3" in parts:
        res["suppression"] = suppression(w)
    if "R1" in parts:
        res["rotation"] = rotation(w)
    return res


def learned():
    d = np.load(LEARNED, allow_pickle=True)
    return d["w"][:, :, -1] if d["w"].ndim == 3 else d["w"]


def blocks():
    """Block and direction-offset labels for w (60 HD x [60 HR + 60 HD])."""
    post_par = np.arange(N) % 2
    pre_dir = np.r_[np.arange(N) % NDIR, np.arange(N) // 2]
    pre_blk = np.r_[np.arange(N) // NDIR, 2 + np.arange(N) % 2]      # 0 HR_L, 1 HR_R, 2 HD even, 3 HD odd
    off = (np.arange(N)[:, None] // 2 - pre_dir[None, :]) % NDIR
    return post_par[:, None] * 4 + pre_blk[None, :], off


def homogeneous(w, harmonics=None):
    """Rotation average of w inside each (post parity, pre block) and direction offset; harmonics keeps only those
    circular harmonics of the offset profile."""
    blk, off = blocks()
    out = np.zeros_like(w)
    for b in np.unique(blk):
        prof = np.array([w[(blk == b) & (off == k)].mean() for k in range(NDIR)])
        if harmonics is not None:
            F = np.fft.rfft(prof)
            F[[k for k in range(F.size) if k not in harmonics]] = 0
            prof = np.fft.irfft(F, NDIR)
        m = blk == b
        out[m] = prof[off[m]]
    return out


SYN_GLOBAL = (4.0, -1.0)


def synthetic(kind):
    d = np.radians(DIR)
    off = d[:, None] - d[None, :]
    hd = 14.5 * np.exp(13 * (np.cos(off) - 1)) - 2.0 if kind == "local" else SYN_GLOBAL[0] * np.cos(off) + SYN_GLOBAL[1]
    hr_dir = np.radians(np.r_[np.arange(NDIR), np.arange(NDIR)] * DPHI)
    shift = np.radians(np.r_[np.full(NDIR, 60.0), np.full(NDIR, -60.0)])
    hr = 8.0 * np.exp(4 * (np.cos(d[:, None] - hr_dir[None, :] - shift[None, :]) - 1)) - 2.0
    return np.hstack([hr, hd])


def summary(r):
    s = {"dark_bump": r["dark_bump"]}
    if "continuity" in r:
        s["C"] = {k: r["continuity"][k] for k in ("retention", "median_abs_err", "max_abs_err", "median_fwhm", "median_abs_late_drift_deg_s", "C1")}
    if "two_cue" in r:
        s["S1"] = {"n_ok": r["two_cue"]["n_ok"], "S1": r["two_cue"]["S1"], "finals": [round(o["final"], 1) for o in r["two_cue"]["trials"]]}
    if "jump" in r:
        s["S2"] = r["jump"]
    if "suppression" in r:
        s["S3"] = r["suppression"]
    if "rotation" in r:
        s["R1"] = r["rotation"]
    return s


def main():
    if "--synthetic" in sys.argv:
        for kind in ("local", "global"):
            print("==", kind, json.dumps(summary(analyse(synthetic(kind))), default=float), flush=True)
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    W = learned()
    nets = {"learned": W, "control_homogeneous": homogeneous(W), "control_cosine": homogeneous(W, harmonics=(0, 1)),
            "control_untrained": np.random.default_rng(0).normal(0, np.sqrt(1 / (2 * N)), (N, 2 * N))}
    res = {}
    for k, w in nets.items():
        res[k] = analyse(w)
        print("==", k, json.dumps(summary(res[k]), default=float), flush=True)
    L = res["learned"]
    ok = L["continuity"]["C1"] and L["two_cue"]["S1"] and L["jump"]["S2"] and L["rotation"]["R1"]
    result = {"schema": "ce-a1-step37-learned-ring-selection", "code_sha256": code_hash,
              "verdict": "LEARNED_RING_SELECTS_PERSISTS_ROTATES" if ok else "LEARNED_RING_DOES_NOT_SATISFY_ALL",
              "criteria": {"C1": L["continuity"]["C1"], "S1": L["two_cue"]["S1"], "S2": L["jump"]["S2"], "R1": L["rotation"]["R1"],
                           "S3_secondary": L["suppression"]["S3"]}, "networks": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], result["criteria"])


if __name__ == "__main__":
    main()
