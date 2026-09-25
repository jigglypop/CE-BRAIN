"""A1 step 36: is the connectome the end point of the predictive learning rule? (CONTRACT.md)

Learned solution: Vafidis et al. 2022 trained network (60 HD x [60 HR + 60 HD], learned from random initialisation with
dW = eta [f(V_a) - f(p V_d)] PSP_pre; author file on gin, reproduced dark PI gain 1.032 here).
Connectome: angle-offset profiles of PEN_L -> EPG, PEN_R -> EPG, EPG -> EPG and EPG -> Delta7 -> EPG using PB-glomerulus
angles (E1) in MaleCNS and hemibrain (FlyWire: label-free phases, report only).

python compare_learned.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
ROOT = HERE.parents[2]
LEARNED = ROOT / "data/external/vafidis_2022_learnpi/fly_rec2Enoughv02inh1rot15NoClipOUsigma225tau05NoBoundx1k1b25s015exc4N60InitNoAnneal05.npz"
BINS = np.arange(16) * 22.5  # common offset grid (deg)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lf = load("label_free_ring", LOOP / "step17_label_free_ring/label_free_ring.py")


def wrapd(a):
    return (np.asarray(a) + 180.0) % 360.0 - 180.0


def profile(W, ang_post, ang_pre):
    """Mean weight as a function of offset (post - pre), on 16 bins of 22.5 deg (circular linear interpolation)."""
    off = wrapd(np.degrees(ang_post)[:, None] - np.degrees(ang_pre)[None, :]).ravel()
    val = W.ravel()
    fine = np.arange(-180, 180, 1.0)
    acc = np.zeros(fine.size)
    cnt = np.zeros(fine.size)
    idx = np.round(off - fine[0]).astype(int) % fine.size
    np.add.at(acc, idx, val)
    np.add.at(cnt, idx, 1)
    ok = cnt > 0
    x, y = fine[ok], acc[ok] / cnt[ok]
    return np.interp(wrapd(BINS), np.r_[x - 360, x, x + 360], np.r_[y, y, y])


def shift_deg(p):
    q = np.maximum(p - np.median(p), 0)
    return float(np.degrees(np.angle(np.sum(q * np.exp(1j * np.radians(BINS))))))


def corr(a, b):
    a, b = a - a.mean(), b - b.mean()
    return float(a @ b / np.sqrt((a @ a) * (b @ b)))


def learned_profiles():
    d = np.load(LEARNED, allow_pickle=True)
    w = d["w"][:, :, -1] if d["w"].ndim == 3 else d["w"]
    n = w.shape[0]
    dirs = np.radians(np.repeat(360 * np.arange(n // 2) / (n // 2), 2))
    hr_dir = np.radians(np.r_[360 * np.arange(n // 2) / (n // 2), 360 * np.arange(n // 2) / (n // 2)])
    w_hr, w_hd = w[:, :n], w[:, n:]
    return {"HR_L": profile(w_hr[:, : n // 2], dirs, hr_dir[: n // 2]), "HR_R": profile(w_hr[:, n // 2:], dirs, hr_dir[n // 2:]),
            "HD_HD": profile(w_hd, dirs, dirs)}


def connectome_profiles(w, kind, side_pb, label):
    idx = lambda f: np.array([i for i, k in enumerate(kind) if f(k, i)])
    epg = idx(lambda k, i: k == "EPG" and label[i] is not None)
    penL = idx(lambda k, i: k.startswith("PEN") and label[i] is not None and label[i][0] == "L")
    penR = idx(lambda k, i: k.startswith("PEN") and label[i] is not None and label[i][0] == "R")
    d7 = idx(lambda k, i: k == "Delta7")
    phi = lambda ids: np.array([lf.phi(*label[i]) for i in ids])
    aE = phi(epg)
    out = {"PEN_L": profile(w[np.ix_(epg, penL)], aE, phi(penL)), "PEN_R": profile(w[np.ix_(epg, penR)], aE, phi(penR)),
           "EPG_EPG": profile(w[np.ix_(epg, epg)], aE, aE)}
    via = w[np.ix_(epg, d7)] @ w[np.ix_(d7, epg)]
    out["EPG_D7_EPG"] = -profile(via, aE, aE)
    return out, {"EPG": len(epg), "PEN_L": len(penL), "PEN_R": len(penR), "Delta7": len(d7)}


def compare(L, C):
    res = {}
    best = None
    for refl in (1, -1):
        idxr = (np.arange(16) * refl) % 16  # reflection of the offset axis
        cl = {k: v[idxr] for k, v in C.items()}
        for swap in (False, True):
            a, b = ("PEN_R", "PEN_L") if swap else ("PEN_L", "PEN_R")
            r = min(corr(L["HR_L"], cl[a]), corr(L["HR_R"], cl[b]))
            if best is None or r > best[0]:
                best = (r, refl, swap)
    r, refl, swap = best
    idxr = (np.arange(16) * refl) % 16
    cl = {k: v[idxr] for k, v in C.items()}
    a, b = ("PEN_R", "PEN_L") if swap else ("PEN_L", "PEN_R")
    sL, sR = shift_deg(cl[a]), shift_deg(cl[b])
    lL, lR = shift_deg(L["HR_L"]), shift_deg(L["HR_R"])
    X = np.column_stack([cl["EPG_EPG"], cl["EPG_D7_EPG"], np.ones(16)])
    coef, *_ = np.linalg.lstsq(X, L["HD_HD"], rcond=None)
    pred = X @ coef
    r2 = 1 - np.sum((L["HD_HD"] - pred) ** 2) / np.sum((L["HD_HD"] - L["HD_HD"].mean()) ** 2)
    res.update({"reflection": refl, "side_swap": swap, "corr_HR_PEN_min": r,
                "corr_HR_L": corr(L["HR_L"], cl[a]), "corr_HR_R": corr(L["HR_R"], cl[b]),
                "shift_learned_deg": [lL, lR], "shift_connectome_deg": [sL, sR],
                "V2_opposite": bool(np.sign(sL) != np.sign(sR)),
                "V2_magnitude_within_22_5": bool(abs(abs(sL) - abs(lL)) <= 22.5 and abs(abs(sR) - abs(lR)) <= 22.5),
                "V3_shape": bool(r >= 0.7),
                "report_HD_HD_fit": {"coef_direct_EPG_EPG": float(coef[0]), "coef_via_Delta7": float(coef[1]), "R2": float(r2),
                                     "corr_direct": corr(L["HD_HD"], cl["EPG_EPG"]), "corr_via_Delta7": corr(L["HD_HD"], cl["EPG_D7_EPG"])}})
    return res


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    L = learned_profiles()
    lL, lR = shift_deg(L["HR_L"]), shift_deg(L["HR_R"])
    V1 = bool(np.sign(lL) != np.sign(lR) and abs(abs(lL) - abs(lR)) <= 15)
    res = {"learned": {k: v.tolist() for k, v in L.items()}, "learned_shift_deg": [lL, lR], "V1_learned_opposite": V1, "datasets": {}}
    w, kind, side, label = lf.malecns()
    C, counts = connectome_profiles(w, kind, side, label)
    res["datasets"]["malecns"] = {"counts": counts, "profiles": {k: v.tolist() for k, v in C.items()}, **compare(L, C)}
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    A, ty, inst, sd, nt = h22.hemibrain()
    base = np.array([v for v in range(len(ty)) if ty[v] in lf.TYPES])
    lab = [(lambda m: (m.group(1), int(m.group(2))) if m else None)(h22.GLOM.search(inst[v])) for v in base]
    C, counts = connectome_profiles(h22.sub(A, base), [ty[v] for v in base], [sd[v] for v in base], lab)
    res["datasets"]["hemibrain"] = {"counts": counts, "profiles": {k: v.tolist() for k, v in C.items()}, **compare(L, C)}
    ok = V1 and all(r["V2_opposite"] and r["V2_magnitude_within_22_5"] and r["V3_shape"] for r in res["datasets"].values())
    res.update({"schema": "ce-a1-step36-connectome-vs-learned", "code_sha256": code_hash,
                "verdict": "CONNECTOME_MATCHES_LEARNED_SOLUTION" if ok else "CONNECTOME_DOES_NOT_MATCH_LEARNED_SOLUTION"})
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(res, stream, indent=1, default=float)
    print("verdict", res["verdict"], "| learned shifts", [round(x, 1) for x in (lL, lR)], "V1", V1)
    for k, r in res["datasets"].items():
        print("==", k, r["counts"], "refl", r["reflection"], "swap", r["side_swap"],
              "corr HR-PEN L/R %.2f/%.2f" % (r["corr_HR_L"], r["corr_HR_R"]),
              "shift conn", [round(x, 1) for x in r["shift_connectome_deg"]], "learned", [round(x, 1) for x in r["shift_learned_deg"]],
              "V2", r["V2_opposite"], r["V2_magnitude_within_22_5"], "V3", r["V3_shape"], "HD-HD fit", {a: round(b, 3) for a, b in r["report_HD_HD_fit"].items()})


if __name__ == "__main__":
    main()
