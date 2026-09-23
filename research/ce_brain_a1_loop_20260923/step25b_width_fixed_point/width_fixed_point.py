"""A1 step 25b: parameter-free bump width of A1 + ReLU on the connectome, three individuals (CONTRACT.md).

tau x' = -x + [g W x]_+ is homogeneous: the persistent bump is the nonlinear eigenvector x = [W x]_+ / Lambda,
found by shifted power iteration x <- norm(x + eta [W x]_+) (fixes the step-25 period-2 defect).

python width_fixed_point.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s25 = load("width_law", LOOP / "step25_width_law/width_law.py")
wc = s25.wc
ETA, ITERS, TOL = 0.2, 40000, 1e-11
LIT = (80.0, 120.0)
C_SCAN = tuple(np.round(np.arange(0, 3.01, 0.25), 2))


def fixed_point(W, epg, ang):
    x = np.zeros(W.shape[0])
    x[epg] = np.maximum(np.cos(ang), 0)
    x /= np.linalg.norm(x)
    it = 0
    for it in range(ITERS):
        new = x + ETA * np.maximum(W @ x, 0)
        new /= np.linalg.norm(new)
        done = np.max(np.abs(new - x)) < TOL
        x = new
        if done:
            break
    h = np.maximum(W @ x, 0)
    lam = float(x @ h)
    resid = float(np.linalg.norm(h - lam * x) / max(np.linalg.norm(lam * x), 1e-300))
    bins = np.mod(np.round(ang / np.radians(22.5)).astype(int), 16)
    prof = np.array([x[epg][bins == b].mean() if np.any(bins == b) else np.nan for b in range(16)])
    ok = ~np.isnan(prof)
    p = prof[ok]
    width = wc.fwhm_profile(p, np.radians(22.5) * np.arange(16)[ok]) if p.max() > 0 else None
    peaks = int(np.sum((p > np.roll(p, 1)) & (p >= np.roll(p, -1)) & (p > 0.5 * p.max()))) if p.max() > 0 else 0
    return {"Lambda": lam, "resid": resid, "iters": int(it + 1), "fwhm": width, "peaks": peaks,
            "epg_activity_share": float(np.sum(x[epg] ** 2)), "profile16": [None if np.isnan(v) else float(v) for v in prof]}


def valid(fp, lam1):
    return fp["Lambda"] >= 0.05 * lam1 and fp["resid"] <= 1e-6 and fp["peaks"] == 1 and fp["fwhm"] is not None


def run(A, ty, inst, nt):
    W, epg, ang, basis, chosen = s25.build(A, ty, inst, nt)
    sp = s25.spectrum(W, epg, ang)
    fp = fixed_point(W, epg, ang)
    ok = valid(fp, sp["lambda1"])
    scan = []
    for c in C_SCAN:
        Wc = W.copy()
        Wc[:, epg] -= c * sp["lambda1"] / len(epg)
        f = fixed_point(Wc, epg, ang)
        scan.append({"c": float(c), "fwhm": f["fwhm"], "valid": bool(valid(f, sp["lambda1"])), "Lambda": f["Lambda"], "peaks": f["peaks"]})
    vals = [(s["c"], s["fwhm"]) for s in scan if s["valid"]]
    c_star = None
    for (c0, f0), (c1, f1) in zip(vals, vals[1:]):
        if (f0 - 100.0) * (f1 - 100.0) <= 0 and f0 != f1:
            c_star = c0 + (100.0 - f0) * (c1 - c0) / (f1 - f0)
            break
    return {"basis": basis, "inhibitory_types": chosen, "spectrum": sp,
            "rho_uniform_over_memory": sp["lambda0"] / sp["lambda1"], "fixed_point": fp, "valid": bool(ok),
            "W2_literature": bool(ok and LIT[0] <= fp["fwhm"] <= LIT[1]), "report_scan": scan, "report_c_for_100deg": c_star}


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    res = {n: run(*loader()) for n, loader in (("malecns", s25.malecns), ("flywire", s25.flywire), ("hemibrain", s25.hemibrain))}
    ok = all(d["W2_literature"] for d in res.values())
    result = {"schema": "ce-a1-step25b-width-fixed-point", "code_sha256": code_hash,
              "verdict": "PARAMETER_FREE_BUMP_WIDTH_MATCHES_LITERATURE" if ok else "PARAMETER_FREE_BUMP_WIDTH_NOT_MATCHED", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"])
    for n, d in res.items():
        fp = d["fixed_point"]
        print("==", n, d["basis"], "rho %.3f" % d["rho_uniform_over_memory"], "Lambda %.4f resid %.1e iters %d" % (fp["Lambda"], fp["resid"], fp["iters"]),
              "fwhm", fp["fwhm"], "peaks", fp["peaks"], "valid", d["valid"], "W2", d["W2_literature"], "c*", d["report_c_for_100deg"])
        print("   profile16", [None if v is None else round(v, 3) for v in fp["profile16"]])
        print("   scan", [(s["c"], s["fwhm"], s["valid"]) for s in d["report_scan"]])


if __name__ == "__main__":
    main()
