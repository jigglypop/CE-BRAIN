"""Post-hoc diagnostic for step 22 H2 (does NOT change the frozen verdict).

Expanded hemibrain operator: top modes with EPG share, P0 and E1-labelled harmonic powers; where does the
E1 heading pair sit relative to the uniform mode? Also report the same with only ER*/ExR* inhibitory
types (literature ring-neuron set, chosen post hoc).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("h", HERE / "hemibrain_third.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def table(A, ty, inst, chosen_types, members):
    base = [v for v in range(len(ty)) if ty[v] in h.gi.BASE]
    nodes = np.array(sorted(base + [v for t in chosen_types for v in members[t]]))
    kind = [ty[v] for v in nodes]
    w = h.sub(A, nodes)
    sign = np.array([-1.0 if (k == "Delta7" or k in chosen_types) else 1.0 for k in kind])
    W = (w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :]
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    phi = np.array([h.lf.phi(m.group(1), int(m.group(2))) for m in (h.GLOM.search(inst[nodes[i]]) for i in epg)])
    lam, right = eig(W)
    rows = []
    for k in np.argsort(-lam.real)[:12]:
        v = right[epg, k]
        tot = np.sum(np.abs(v) ** 2)
        P = [abs(np.sum(v)) ** 2 / (len(v) * tot)] + [(abs(np.sum(v * np.exp(-1j * m * phi))) ** 2 + abs(np.sum(v * np.exp(1j * m * phi))) ** 2) / (len(v) * tot) for m in (1, 2)]
        grp = {}
        for t in sorted(set(kind)):
            idx = [i for i, kk in enumerate(kind) if kk == t]
            grp[t] = float(np.sum(np.abs(right[idx, k]) ** 2) / np.sum(np.abs(right[:, k]) ** 2))
        top = sorted(grp.items(), key=lambda kv: -kv[1])[:3]
        rows.append({"re": round(float(lam[k].real), 4), "im": round(float(lam[k].imag), 4), "P0_P1_P2_E1": [round(float(x), 3) for x in P],
                     "epg_share": round(grp.get("EPG", 0.0), 3), "top_types": [(t, round(s, 2)) for t, s in top]})
    return rows


def main():
    A, ty, inst, sd, nt = h.hemibrain()
    chosen, members = h.gi.select(A, ty, nt)
    ring_only = [t for t in chosen if t.startswith(("ER", "ExR"))]
    out = {"note": "post-hoc diagnostic; frozen H2 verdict (FAIL) unchanged",
           "rule_chosen": table(A, ty, inst, list(chosen), members),
           "ER_ExR_only_posthoc": {"types": ring_only, "modes": table(A, ty, inst, ring_only, members)}}
    (HERE / "diag_h2.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for key in ("rule_chosen",):
        print(key)
        for r in out[key]:
            print("  ", r)
    print("ER_ExR_only_posthoc", ring_only)
    for r in out["ER_ExR_only_posthoc"]["modes"]:
        print("  ", r)


if __name__ == "__main__":
    main()
