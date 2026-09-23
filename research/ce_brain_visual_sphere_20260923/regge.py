"""Discovery: Regge (deficit-angle) curvature of the wiring metric on the fixed hex column lattice.

Edge length rulers (all from synapse counts between the neurons of two neighbouring columns):
  profile : angle between unit input/output connectivity profiles (saturating)
  inv_sqrt: 1 / sqrt(direct synapses between the two columns, both directions)
  neglog  : -log(direct synapses / max direct synapses) + 1
Deficit at an interior vertex = 2*pi - sum of its six triangle angles (law of cosines); the sum of
deficits over interior vertices is the integrated Gaussian curvature (scale-free).
"""
from __future__ import annotations

import json
import sys

import numpy as np
from scipy import sparse

import discover as d

TRIANGLES = (((1, 0), (1, 1)), ((1, 1), (0, 1)), ((0, 1), (-1, 0)), ((-1, 0), (-1, -1)), ((-1, -1), (0, -1)), ((0, -1), (1, 0)))


def direct_coupling(graph, cols, keys):
    n = len(graph["node_ids"])
    a = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    rows = [(v, g) for g, k in enumerate(keys) for v in cols[k]]
    g = sparse.csr_array((np.ones(len(rows)), ([r for r, _ in rows], [c for _, c in rows])), shape=(n, len(keys)))
    w = (g.T @ a @ g).toarray()
    return w + w.T


def angle(a, b, c):
    """Angle opposite side c in a triangle with sides a, b, c."""
    return np.arccos(np.clip((a * a + b * b - c * c) / (2 * a * b), -1, 1))


def regge(keys, length):
    index = {k: i for i, k in enumerate(keys)}
    deficits, triangles_ok = {}, 0
    for k, i in index.items():
        total, complete = 0.0, True
        for (ax, ay), (bx, by) in TRIANGLES:
            j, m = index.get((k[0] + ax, k[1] + ay)), index.get((k[0] + bx, k[1] + by))
            if j is None or m is None:
                complete = False
                break
            lij, lim, ljm = length(i, j), length(i, m), length(j, m)
            if not (lij > 0 and lim > 0 and ljm > 0) or lij + lim <= ljm or lij + ljm <= lim or lim + ljm <= lij:
                complete = False
                break
            total += angle(lij, lim, ljm)
        if complete:
            deficits[k] = 2 * np.pi - total
            triangles_ok += 1
    return deficits


def main(side="R"):
    graph, cols = d.columns(side)
    keys = sorted(k for k, v in cols.items() if len(v) >= 10)
    prof = d.profile_distance(graph, cols, keys)
    w = direct_coupling(graph, cols, keys)
    wmax = max(w[i, j] for i in range(len(keys)) for j in range(len(keys)) if i != j)
    rulers = {"profile": lambda i, j: prof[i, j],
              "inv_sqrt": lambda i, j: 1 / np.sqrt(w[i, j]) if w[i, j] > 0 else np.inf,
              "neglog": lambda i, j: 1 - np.log(w[i, j] / wmax) if w[i, j] > 0 else np.inf}
    index = {k: i for i, k in enumerate(keys)}
    by_dir = {}
    for (dx, dy) in ((1, 0), (0, 1), (1, 1)):
        vals = [w[index[k], index[(k[0] + dx, k[1] + dy)]] for k in keys if (k[0] + dx, k[1] + dy) in index]
        by_dir[f"{dx},{dy}"] = {"median_direct_synapses": float(np.median(vals)), "n": len(vals)}
    nonneighbour = [w[index[a], index[b]] for a in keys[:200] for b in keys
                    if max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[0] - a[1] - b[0] + b[1])) == 2]
    report = {"side": side, "columns": len(keys), "direct_synapses_by_lattice_direction": by_dir,
              "median_direct_synapses_hex_distance_2": float(np.median(nonneighbour)), "rulers": {}}
    for name, length in rulers.items():
        deficits = regge(keys, length)
        dv = np.array(list(deficits.values()))
        report["rulers"][name] = {"interior_vertices": len(dv), "integrated_curvature_sr": float(dv.sum()),
                                  "mean_deficit_deg": float(np.degrees(dv.mean())),
                                  "deficit_sd_deg": float(np.degrees(dv.std())),
                                  "fraction_positive": float(np.mean(dv > 0))}
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "R")
