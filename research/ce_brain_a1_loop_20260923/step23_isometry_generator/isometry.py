"""A1 step 23: is the head-direction operator "rotation-invariant metric + isometry shift"? (CONTRACT.md)

Candidate fundamental form:  x' = -F(-Laplacian_S1) x + u (T_{+D} - T_{-D}) x.
In the harmonic-m pair basis (EPG components fitted to cos m*phi, sin m*phi) the left-PEN route must act as
kappa_m * R(m*D) and the right-PEN route as kappa_m * R(-m*D): the rotation angle doubles from m=1 to m=2.
MaleCNS and hemibrain use E1 glomerulus angles; FlyWire uses the label-free step-17 angle.

python isometry.py            full run; refuses unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lf = load("label_free_ring", LOOP / "step17_label_free_ring/label_free_ring.py")
GAP_MAX, PURITY_MIN, CONFORMAL_MIN, ANGLE_TOL = 0.10, 0.8, 0.8, 20.0
DELTA_RANGE = (35.0, 65.0)


def wrapd(a):
    return (a + 180.0) % 360.0 - 180.0


def powers(v, ang):
    tot = np.sum(np.abs(v) ** 2)
    out = [abs(np.sum(v)) ** 2 / (len(v) * tot)]
    for m in (1, 2, 3):
        out.append((abs(np.sum(v * np.exp(-1j * m * ang))) ** 2 + abs(np.sum(v * np.exp(1j * m * ang))) ** 2) / (len(v) * tot))
    return [float(x) for x in out]


def harmonic_pair(lam, left, right, epg, ang, m):
    order = np.argsort(-lam.real)
    cand = []
    for k in order:
        P = powers(right[epg, k], ang)
        if int(np.argmax(P)) == m and P[m] >= PURITY_MIN:
            cand.append((k, P[m]))
    if not cand:
        return None
    k1 = cand[0][0]
    if abs(lam[k1].imag) > 1e-9 * max(1.0, abs(lam[k1].real)):
        span = np.column_stack([right[:, k1].real, right[:, k1].imag])
        dual_src = np.column_stack([left[:, k1].real, left[:, k1].imag])
        lam_pair, purity = [lam[k1], np.conj(lam[k1])], [cand[0][1], cand[0][1]]
    else:
        if len(cand) < 2:
            return None
        k2 = cand[1][0]
        span = np.column_stack([right[:, k1].real, right[:, k2].real])
        dual_src = np.column_stack([left[:, k1].real, left[:, k2].real])
        lam_pair, purity = [lam[k1], lam[k2]], [cand[0][1], cand[1][1]]
    template = np.column_stack([np.cos(m * ang), np.sin(m * ang)])
    coef, *_ = np.linalg.lstsq(span[epg], template, rcond=None)
    B = span @ coef
    r2 = float(1 - np.linalg.norm(B[epg] - template) ** 2 / np.linalg.norm(template) ** 2)
    dual = dual_src @ np.linalg.inv(B.T @ dual_src)
    gap = float((lam_pair[0].real - lam_pair[1].real) / abs(lam_pair[0].real))
    return {"lambda": [float(l.real) for l in lam_pair], "lambda_imag": [float(l.imag) for l in lam_pair],
            "purity": [float(p) for p in purity], "gap": gap, "template_R2": r2}, B, dual


def route(Q):
    a, b = (Q[0, 0] + Q[1, 1]) / 2, (Q[1, 0] - Q[0, 1]) / 2
    conf = np.array([[a, -b], [b, a]])
    return {"angle_deg": float(np.degrees(np.arctan2(b, a))), "gain": float(np.hypot(a, b)),
            "conformal_fraction": float(1 - np.linalg.norm(Q - conf) ** 2 / np.linalg.norm(Q) ** 2) if np.linalg.norm(Q) > 0 else 0.0}


def analyse(w, kind, side, ang_epg):
    W = lf.operator(w, kind)
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    lam, left, right = eig(W, left=True, right=True)
    gL = np.array([1.0 if k.startswith("PEN") and s == "left" else 0.0 for k, s in zip(kind, side)])
    gR = np.array([1.0 if k.startswith("PEN") and s == "right" else 0.0 for k, s in zip(kind, side)])
    out = {"pairs": {}, "routes": {}}
    for m in (1, 2, 3):
        hp = harmonic_pair(lam, left, right, epg, ang_epg, m)
        if hp is None:
            out["pairs"][m] = None
            continue
        info, B, dual = hp
        out["pairs"][m] = info
        out["routes"][m] = {s: route(dual.T @ (g[:, None] * W) @ B) for s, g in (("left", gL), ("right", gR))}
    uni = [lam[k].real for k in np.argsort(-lam.real) if powers(right[epg, k], ang_epg)[0] >= 0.5]
    out["lambda_uniform"] = float(uni[0]) if uni else None
    ok12 = out["pairs"].get(1) and out["pairs"].get(2)
    real_pos = lambda p: min(p["lambda"]) > 0 and max(abs(i) for i in p["lambda_imag"]) <= 0.1 * abs(p["lambda"][0])
    K1 = bool(ok12 and all(out["pairs"][m]["gap"] <= GAP_MAX and min(out["pairs"][m]["purity"]) >= PURITY_MIN
                           and real_pos(out["pairs"][m]) for m in (1, 2)))
    K2, K3, detail = False, False, {}
    if ok12:
        r = out["routes"]
        conformal = all(r[m][s]["conformal_fraction"] >= CONFORMAL_MIN for m in (1, 2) for s in ("left", "right"))
        dbl = {s: float(wrapd(r[2][s]["angle_deg"] - 2 * r[1][s]["angle_deg"])) for s in ("left", "right")}
        opp = float(wrapd(r[1]["left"]["angle_deg"] + r[1]["right"]["angle_deg"]))
        delta = float(abs(wrapd(r[1]["left"]["angle_deg"] - r[1]["right"]["angle_deg"])) / 2)
        K2 = bool(conformal and all(abs(v) <= ANGLE_TOL for v in dbl.values()) and abs(opp) <= ANGLE_TOL)
        K3 = bool(DELTA_RANGE[0] <= delta <= DELTA_RANGE[1])
        detail = {"conformal_all": bool(conformal), "psi2_minus_2psi1_deg": dbl, "psi1_left_plus_right_deg": opp, "Delta_deg": delta}
        if out["pairs"].get(3):
            detail["report_psi3_minus_3psi1_deg"] = {s: float(wrapd(r[3][s]["angle_deg"] - 3 * r[1][s]["angle_deg"])) for s in ("left", "right")}
    out.update({"K1_invariance": K1, "K2_isometry": K2, "K3_literature_shift": K3, "detail": detail})
    lm = [np.mean(out["pairs"][m]["lambda"]) if out["pairs"].get(m) else None for m in (1, 2, 3)]
    out["report_spectrum"] = {"lambda_0": out["lambda_uniform"], "lambda_m": lm}
    return out


def datasets():
    yield "malecns", *lf.malecns()
    w, kind, side, label = lf.flywire()
    yield "flywire", w, kind, side, label
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    A, ty, inst, sd, nt = h22.hemibrain()
    base = np.array([v for v in range(len(ty)) if ty[v] in lf.TYPES])
    lab = [(lambda m: (m.group(1), int(m.group(2))) if m else None)(h22.GLOM.search(inst[v])) for v in base]
    yield "hemibrain", h22.sub(A, base), [ty[v] for v in base], [sd[v] for v in base], lab


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    result = {"schema": "ce-a1-step23-isometry-generator", "code_sha256": code_hash, "datasets": {}}
    for name, w, kind, side, label in datasets():
        epg = [i for i, k in enumerate(kind) if k == "EPG"]
        _, theta, _, _ = lf.ring_pair(lf.operator(w, kind), np.array(epg))
        res = {}
        if all(label[i] for i in epg):
            res["E1_labels"] = analyse(w, kind, side, np.array([lf.phi(*label[i]) for i in epg]))
        res["label_free"] = analyse(w, kind, side, theta)
        primary = res.get("E1_labels", res["label_free"])
        res["primary"] = "E1_labels" if "E1_labels" in res else "label_free"
        res["pass"] = bool(primary["K1_invariance"] and primary["K2_isometry"] and primary["K3_literature_shift"])
        result["datasets"][name] = res
    result["verdict"] = ("ISOMETRY_GENERATOR_SUPPORTED_THREE_INDIVIDUALS" if all(d["pass"] for d in result["datasets"].values())
                         else "ISOMETRY_GENERATOR_NOT_SUPPORTED")
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
