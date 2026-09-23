"""Post-hoc diagnostic for step 25b (does NOT change the frozen verdict): where is the activity at the
homogeneous-ReLU fixed point, and what sign structure do inhibitory populations have in the linear ring mode?"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("wfp", HERE / "width_fixed_point.py")
wfp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wfp)
s25 = wfp.s25


def main():
    out = {}
    for n, loader in (("malecns", s25.malecns), ("flywire", s25.flywire), ("hemibrain", s25.hemibrain)):
        A, ty, inst, nt = loader()
        W, epg, ang, basis, chosen = s25.build(A, ty, inst, nt)
        chosen_set, members = s25.gi.select(A, ty, nt)
        base = [v for v in range(len(ty)) if ty[v] in s25.gi.BASE]
        nodes = np.array(sorted(base + [v for t in chosen_set for v in members[t]]))
        kind = np.array([ty[v] for v in nodes])
        fp = wfp.fixed_point(W, epg, ang)
        x = np.zeros(W.shape[0]); x[epg] = np.maximum(np.cos(ang), 0); x /= np.linalg.norm(x)
        for _ in range(wfp.ITERS):
            new = x + wfp.ETA * np.maximum(W @ x, 0); new /= np.linalg.norm(new)
            if np.max(np.abs(new - x)) < wfp.TOL:
                x = new; break
            x = new
        share = {t: round(float(np.sum(x[kind == t] ** 2)), 4) for t in sorted(set(kind))}
        top = dict(sorted(share.items(), key=lambda kv: -kv[1])[:5])
        lam, left, right = eig(W, left=True, right=True)
        p1 = s25.iso.harmonic_pair(lam, left, right, epg, ang, 1)
        _, B, _ = p1
        v = B[:, 0]
        neg = {t: round(float(np.sum(np.minimum(v[kind == t], 0) ** 2) / max(np.sum(v[kind == t] ** 2), 1e-300)), 3)
               for t in ("EPG", "Delta7") if np.any(kind == t)}
        inhib_negfrac = float(np.sum(np.minimum(v[np.isin(kind, sorted(chosen_set))], 0) ** 2) / max(np.sum(v[np.isin(kind, sorted(chosen_set))] ** 2), 1e-300))
        out[n] = {"fixed_point_Lambda": fp["Lambda"], "activity_share_top": top, "ring_mode_negative_energy_fraction": neg,
                  "ring_mode_negative_energy_fraction_inhibitory_set": round(inhib_negfrac, 3)}
        print(n, json.dumps(out[n]))
    (HERE / "diag_populations.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
