"""A1 step 11 (discovery, post hoc allowed): whole-brain scan of the manifolds that fixed neurons' wiring forms.

For every (cell type, side) with at least MIN_N neurons: connectivity-profile angle distance ->
k-NN geodesic distance -> classical MDS -> class {ring, line, sheet, fragmented, other}, plus the
rank correlation between wiring geodesic distance and soma distance (low = folded relative to anatomy).
Positive controls known from earlier steps: EPG (ring), modular medulla columns (sheet).
"""
from __future__ import annotations

from collections import defaultdict
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MALECNS = ROOT / "verify/MaleCNS"
MIN_N, MAX_N, K = 8, 2500, 6


def row_unit(m):
    norms = np.sqrt(np.asarray(m.multiply(m).sum(axis=1)).ravel())
    return sparse.diags(1 / np.where(norms > 0, norms, 1)) @ m


def classify(D):
    n = len(D)
    k = min(K, n - 1)
    order = np.argsort(D, axis=1)[:, 1:k + 1]
    rows = np.repeat(np.arange(n), k)
    graph = sparse.csr_array((D[rows, order.ravel()], (rows, order.ravel())), shape=(n, n))
    graph = graph.maximum(graph.T)
    ncomp, _ = connected_components(graph, directed=False)
    if ncomp > 1:
        return {"class": "fragmented", "components": int(ncomp)}, None
    G = dijkstra(graph, directed=False)
    centre = np.eye(n) - 1 / n
    B = -0.5 * centre @ (G ** 2) @ centre
    w, v = np.linalg.eigh(B)
    w, v = w[::-1], v[:, ::-1]
    pos = np.clip(w, 0, None)
    total = pos.sum()
    r1, r2 = pos[0] / total, pos[1] / total
    xy = v[:, :2] * np.sqrt(pos[:2])
    xy -= xy.mean(axis=0)
    radius = np.linalg.norm(xy, axis=1)
    cv = float(radius.std() / radius.mean())
    theta = np.sort(np.mod(np.arctan2(xy[:, 1], xy[:, 0]), 2 * np.pi))
    span = float(np.degrees(2 * np.pi - np.max(np.diff(np.r_[theta, theta[0] + 2 * np.pi]))))
    ratio21 = pos[1] / pos[0] if pos[0] > 0 else 0.0
    two = r1 + r2
    if two >= 0.6 and ratio21 >= 0.5 and cv <= 0.25 and span >= 300:
        cls = "ring"
    elif r1 >= 0.6 and ratio21 < 0.3:
        cls = "line"
    elif two >= 0.6 and ratio21 >= 0.5:
        cls = "sheet"
    else:
        cls = "other"
    return {"class": cls, "r1": float(r1), "r2": float(r2), "ratio21": float(ratio21), "radius_cv": cv,
            "span_deg": span}, G


def main():
    started = time.perf_counter()
    import pyarrow as pa
    import pyarrow.ipc as ipc
    spec = importlib.util.spec_from_file_location("g", MALECNS / "neuron_graph.py")
    gm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gm)
    graph = gm.load(MALECNS / "neuron_graph_result.json")
    n = len(graph["node_ids"])
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    AT = A.T.tocsr()
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    groups, soma, meta = defaultdict(list), {}, {}
    for p, f, ty, side, sc, cl, loc in zip(pos, found, t["type"].to_pylist(), t["somaSide"].to_pylist(),
                                           t["superclass"].to_pylist(), t["class"].to_pylist(), t["somaLocation"].to_pylist()):
        if f and ty:
            key = (ty, side if side in ("L", "R") else "M")
            groups[key].append(int(p))
            meta[key] = (sc, cl)
            if loc is not None:
                soma[int(p)] = np.array(loc, dtype=float)
    catalog = []
    keys = [k for k, v in groups.items() if MIN_N <= len(v) <= MAX_N]
    for i, key in enumerate(sorted(keys)):
        idx = np.array(sorted(groups[key]))
        prof = sparse.hstack([row_unit(A[idx, :]), row_unit(AT[idx, :])]).tocsr() / np.sqrt(2)
        S = (prof @ prof.T).toarray()
        D = np.arccos(np.clip(S, -1, 1))
        np.fill_diagonal(D, 0)
        entry, G = classify(D)
        entry.update({"type": key[0], "side": key[1], "n": int(len(idx)), "superclass": meta[key][0], "class_annot": meta[key][1]})
        if G is not None:
            have = [j for j, v in enumerate(idx) if int(v) in soma]
            if len(have) >= MIN_N:
                xyz = np.array([soma[int(idx[j])] for j in have])
                P = np.linalg.norm(xyz[:, None] - xyz[None, :], axis=2)
                iu = np.triu_indices(len(have), 1)
                entry["rho_wiring_vs_soma"] = float(spearmanr(G[np.ix_(have, have)][iu], P[iu]).statistic)
        catalog.append(entry)
        if (i + 1) % 250 == 0:
            print(f"{i + 1}/{len(keys)} type-sides, {time.perf_counter() - started:.0f}s", flush=True)
    counts = defaultdict(int)
    for e in catalog:
        counts[e["class"]] += 1
    out = {"schema": "ce-a1-step11-manifold-scan", "type_sides": len(catalog), "class_counts": dict(counts),
           "params": {"MIN_N": MIN_N, "MAX_N": MAX_N, "K": K}, "elapsed_seconds": round(time.perf_counter() - started, 1),
           "catalog": catalog}
    (HERE / "catalog.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "catalog"}, indent=1))


if __name__ == "__main__":
    main()
