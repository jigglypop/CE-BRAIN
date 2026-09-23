"""Post-hoc diagnostic for step 23 (does NOT change the frozen verdict).

Split each PEN route matrix Q^s_1 = dual^T (Gamma_s W) B by the presynaptic type feeding PEN (EPG, Delta7,
PEN, PEG): each source contributes a phasor kappa*e^{i psi}; the route angle is their vector sum.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("iso", HERE / "isometry.py")
iso = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iso)


def run(w, kind, side, ang):
    W = iso.lf.operator(w, kind)
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    lam, left, right = eig(W, left=True, right=True)
    out = {}
    for m in (1, 2):
        hp = iso.harmonic_pair(lam, left, right, epg, ang, m)
        if hp is None:
            continue
        _, B, dual = hp
        rows = {}
        for s in ("left", "right"):
            g = np.array([1.0 if k.startswith("PEN") and sd == s else 0.0 for k, sd in zip(kind, side)])
            total = iso.route(dual.T @ (g[:, None] * W) @ B)
            parts = {}
            for src in ("EPG", "Delta7", "PEN", "PEG"):
                cols = np.array([1.0 if (k.startswith(src) if src == "PEN" else k == src) else 0.0 for k in kind])
                Q = dual.T @ (g[:, None] * W * cols[None, :]) @ B
                r = iso.route(Q)
                parts[src] = (round(r["angle_deg"], 1), round(r["gain"], 4))
            share = {src: float((g[:, None] * w * np.array([1.0 if (k.startswith(src) if src == "PEN" else k == src) else 0.0 for k in kind])[None, :]).sum()
                                / (g[:, None] * w).sum()) for src in ("EPG", "Delta7", "PEN", "PEG")}
            rows[s] = {"total": (round(total["angle_deg"], 1), round(total["gain"], 4)), "by_source": parts,
                       "input_share": {k: round(v, 3) for k, v in share.items()}}
        out[m] = rows
    return out


def main():
    res = {}
    for name, w, kind, side, label in iso.datasets():
        epg = [i for i, k in enumerate(kind) if k == "EPG"]
        if all(label[i] for i in epg):
            ang = np.array([iso.lf.phi(*label[i]) for i in epg])
        else:
            ang = iso.lf.ring_pair(iso.lf.operator(w, kind), np.array(epg))[1]
        res[name] = run(w, kind, side, ang)
    (HERE / "diag_sources.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for n, d in res.items():
        for m, rows in d.items():
            for s, r in rows.items():
                print(n, "m", m, s, "total", r["total"], "by_source", r["by_source"], "input_share", r["input_share"])


if __name__ == "__main__":
    main()
