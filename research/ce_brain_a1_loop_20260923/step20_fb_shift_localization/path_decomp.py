"""A1 step 20: where does FlyWire's right-side 22.5 deg FB phasor shift arise? (CONTRACT.md)

PFN heading phase split by PB input path (EPG only, Delta7 only, PEN+PEG only); for each path the four
FB offsets are refitted with the step-19 hDeltaB-relative method, and FlyWire is compared with MaleCNS by
rotation (+ reflection) + one common shift delta of the right-side groups.

python path_decomp.py            full run; refuses unless CONTRACT.md lists this code hash
python path_decomp.py --control  MaleCNS only (pre-freeze calibration, writes nothing)
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
spec = importlib.util.spec_from_file_location("fb_label_free", LOOP / "step19_fb_phasor_replication/fb_label_free.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)
lf, GROUPS, wrap = fb.lf, fb.GROUPS, fb.wrap
PATHS = {"all": set(lf.TYPES), "EPG": {"EPG"}, "Delta7": {"Delta7"}, "PEN_PEG": {"PEN_a(PEN1)", "PEN_b(PEN2)", "PEG"}}
TOL, FIT_MAX = 8.0, 15.0


def decompose(w, kind, side):
    base = np.array([i for i, k in enumerate(kind) if k in lf.TYPES])
    pfn = np.array([i for i, k in enumerate(kind) if k in fb.PFN_TYPES and side[i]])
    hdb = np.array([i for i, k in enumerate(kind) if k == fb.HDB])
    kb = [kind[i] for i in base]
    W = lf.operator(w[np.ix_(base, base)], kb)
    epg = np.array([i for i, k in enumerate(kb) if k == "EPG"])
    _, _, B, _ = lf.ring_pair(W, epg)
    z = (B[:, 0] + 1j * B[:, 1]) * np.array([-1.0 if k == "Delta7" else 1.0 for k in kb])
    w_in = w[np.ix_(pfn, base)]
    gidx = np.array([GROUPS.index(kind[i][-1] + side[i][0].upper()) for i in pfn])
    Wph = w[np.ix_(hdb, pfn)]
    out, alphas = {}, {}
    for name, types in PATHS.items():
        cols = np.array([j for j, k in enumerate(kb) if k in types])
        S = w_in[:, cols] @ z[cols]
        a = np.angle(S)
        alphas[name] = a
        V = np.stack([Wph[:, gidx == k] @ np.exp(1j * a[gidx == k]) for k in range(len(GROUPS))], axis=1)
        O, cons = fb.offsets(np.angle(V), np.abs(V), gidx)
        out[name] = {"input_share": float(w_in[:, cols].sum() / w_in.sum()),
                     "input_share_by_group": {g: float(w_in[gidx == k][:, cols].sum() / w_in[gidx == k].sum())
                                              for k, g in enumerate(GROUPS)},
                     "coherence_median": float(np.median(np.abs(S) / np.maximum(np.abs(w_in[:, cols]) @ np.abs(z[cols]), 1e-12))),
                     "geometry": fb.geometry(O), "consistency": {g: float(c) for g, c in zip(GROUPS, cons)}}
    d = wrap(alphas["Delta7"] - alphas["EPG"])
    out["report_delta7_minus_epg_input_phase_deg"] = {
        g: float(np.degrees(np.angle(np.mean(np.exp(1j * d[gidx == k]))))) for k, g in enumerate(GROUPS)}
    return out


def compare(m_off, f_off):
    """FlyWire vs MaleCNS offsets: rotation (+reflection) with and without a common right-side shift."""
    m = np.array([m_off[g] for g in GROUPS])
    f = np.array([f_off[g] for g in GROUPS])
    wd = lambda a: (a + 180) % 360 - 180
    right = np.array([0, 1, 0, 1])
    best, best_rot = None, None
    for s in (1, -1):
        for rot in np.arange(-180, 180, 0.5):
            e0 = float(np.max(np.abs(wd(f - s * m - rot))))
            if best_rot is None or e0 < best_rot[0]:
                best_rot = (e0, s, float(rot))
            for delta in np.arange(-60, 60.5, 0.5):
                e = float(np.max(np.abs(wd(f - s * m - rot - delta * right))))
                if best is None or e < best[0]:
                    best = (e, s, float(rot), float(delta))
    return {"rotation_only_max_resid": best_rot[0], "shift_fit_max_resid": best[0], "orientation": best[1],
            "rotation": best[2], "right_shift_delta": best[3]}


def classify(c):
    if c["shift_fit_max_resid"] > FIT_MAX:
        return "unresolved"
    if abs(abs(c["right_shift_delta"]) - 22.5) <= TOL:
        return "carries_shift"
    if abs(c["right_shift_delta"]) <= TOL:
        return "clean"
    return "other"


def main():
    if "--control" in sys.argv:
        print(json.dumps(decompose(*fb.malecns()[:3]), indent=1, default=float))
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    M = decompose(*fb.malecns()[:3])
    F = decompose(*fb.flywire()[:3])
    comp = {p: compare(M[p]["geometry"]["offsets_deg"], F[p]["geometry"]["offsets_deg"]) for p in PATHS}
    cls = {p: classify(c) for p, c in comp.items()}
    e, d = cls["EPG"], cls["Delta7"]
    locus = ("PFN_to_FB_projection (both input paths carry the shift)" if e == d == "carries_shift" else
             "Delta7_input" if e == "clean" and d == "carries_shift" else
             "EPG_input" if e == "carries_shift" and d == "clean" else
             "unresolved")
    result = {"schema": "ce-a1-step20-fb-shift-localization", "code_sha256": code_hash, "locus": locus,
              "path_class": cls, "comparison": comp, "malecns": M, "flywire": F}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print(json.dumps({"locus": locus, "path_class": cls, "comparison": comp,
                      "share": {p: (round(M[p]["input_share"], 3), round(F[p]["input_share"], 3)) for p in PATHS},
                      "coherence": {p: (round(M[p]["coherence_median"], 3), round(F[p]["coherence_median"], 3)) for p in PATHS},
                      "offsets": {p: (M[p]["geometry"]["offsets_deg"], F[p]["geometry"]["offsets_deg"]) for p in PATHS},
                      "d7_minus_epg": (M["report_delta7_minus_epg_input_phase_deg"], F["report_delta7_minus_epg_input_phase_deg"])},
                     indent=1, default=float))


if __name__ == "__main__":
    main()
