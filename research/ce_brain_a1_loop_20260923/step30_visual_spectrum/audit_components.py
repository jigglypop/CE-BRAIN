"""Audit copy for step 30 (does NOT change the frozen verdict): restrict each eye to the largest component that is
connected in BOTH the lattice graph H and the coupling graph S, then recompute the frozen statistics.
Defect: isolated columns created extra zero eigenvalues, so the first 'non-trivial' mode was a component indicator."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("vs", HERE / "visual_spectrum.py")
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)


def common_component(C, xy):
    idx = np.arange(len(xy))
    for _ in range(10):
        S = (C[np.ix_(idx, idx)] + C[np.ix_(idx, idx)].T) / 2
        np.fill_diagonal(S, 0)
        H = vs.lattice_adjacency(xy[idx])
        keep = np.ones(len(idx), bool)
        for M in (H, S > 0):
            n, lab = connected_components(sparse.csr_array(M.astype(float)), directed=False)
            big = np.argmax(np.bincount(lab))
            keep &= lab == big
        if keep.all():
            return idx
        idx = idx[keep]
    return idx


def main():
    rng = np.random.default_rng(vs.SEED)
    out = {}
    for name, fn, sides in (("malecns", vs.malecns, ("R", "L")), ("flywire", vs.flywire, ("right", "left"))):
        for s in sides:
            C, xy = fn(s)
            idx = common_component(C, xy)
            r = vs.analyse(C[np.ix_(idx, idx)], xy[idx], rng)
            r["dropped_columns"] = int(len(xy) - len(idx))
            out[f"{name}_{s}"] = r
            print(name, s, "dropped", r["dropped_columns"], {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()
                                                            if not isinstance(v, (list, dict))}, "ratio",
                  {a: round(b, 3) for a, b in r["report_eigen_ratio_2_over_1"].items()},
                  "S eig", [round(x, 4) for x in r["S_low_eigenvalues"]], "H eig", [round(x, 4) for x in r["lattice_low_eigenvalues"]])
    ok = all(r["M1"] and r["M2"] and r["M3_null"] for r in out.values())
    (HERE / "results_component_audit.json").write_text(json.dumps({"note": "audit copy; frozen verdict unchanged", "all_pass": ok, "eyes": out}, indent=1, default=float), encoding="utf-8")
    print("audit all_pass", ok)


if __name__ == "__main__":
    main()
