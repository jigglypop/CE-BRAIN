"""Discovery (post hoc, allowed): the metric that optic-lobe wiring puts on the fixed medulla columns.

Columns = hex-assigned modular columnar neurons of one side. Local edge length between lattice
neighbours = angle between the columns' unit input/output connectivity profiles. Geodesic distances
come from Dijkstra on the lattice with those lengths; the curvature fit compares a flat chart with
spherical caps of radius R (chord Gram rank-3 residual).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import dijkstra

ROOT = Path(__file__).resolve().parents[2]
MALECNS = ROOT / "verify/MaleCNS"
MODULAR = ("L1", "L2", "L5", "Mi1", "Mi4", "Mi9", "Tm1", "Tm2", "Tm9", "Tm20", "T1", "C3")
OFFSETS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def columns(side, types=MODULAR):
    import pyarrow as pa
    import pyarrow.ipc as ipc
    graph_module = load_module("malecns_neuron_graph", MALECNS / "neuron_graph.py")
    graph = graph_module.load(MALECNS / "neuron_graph_result.json", verify_hash=False)
    with pa.memory_map(str(graph_module.SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    h1 = table["assignedOlHex1"].to_numpy(zero_copy_only=False)
    h2 = table["assignedOlHex2"].to_numpy(zero_copy_only=False)
    ty, root, soma = table["type"].to_pylist(), table["rootSide"].to_pylist(), table["somaSide"].to_pylist()
    position, found = graph_module.locate(table["bodyId"].to_numpy(), graph["node_ids"])
    cols = {}
    for i in np.flatnonzero(~np.isnan(h1) & found):
        if ty[i] in types and (root[i] or soma[i]) == side:
            cols.setdefault((int(h1[i]), int(h2[i])), []).append(int(position[i]))
    return graph, cols


def profile_distance(graph, cols, keys):
    n = len(graph["node_ids"])
    a = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    rows = [(v, g) for g, k in enumerate(keys) for v in cols[k]]
    g = sparse.csr_array((np.ones(len(rows)), ([r for r, _ in rows], [c for _, c in rows])), shape=(n, len(keys)))

    def unit(m):
        norms = np.sqrt(np.asarray(m.multiply(m).sum(axis=1)).ravel())
        return sparse.diags(1 / np.where(norms > 0, norms, 1)) @ m
    prof = sparse.hstack([unit(sparse.csr_array(g.T @ a)), unit(sparse.csr_array((a @ g).T))]).tocsr() / np.sqrt(2)
    sim = (prof @ prof.T).toarray()
    return np.arccos(np.clip(sim, -1, 1))


def lattice_geodesic(keys, distance):
    index = {k: i for i, k in enumerate(keys)}
    rows, cols_, vals = [], [], []
    for k, i in index.items():
        for dx, dy in OFFSETS:
            j = index.get((k[0] + dx, k[1] + dy))
            if j is not None:
                rows.append(i), cols_.append(j), vals.append(distance[i, j])
    edges = sparse.csr_array((vals, (rows, cols_)), shape=(len(keys),) * 2)
    return dijkstra(edges, directed=False), np.array(vals), edges


def curvature_fit(geo, scale):
    """Rank residual of flat (centred Gram, rank 2) vs spherical caps (chord Gram, rank 3) over R."""
    d = geo / scale
    n = len(d)
    centre = np.eye(n) - 1 / n
    flat = -0.5 * centre @ (d ** 2) @ centre
    w = np.linalg.eigvalsh(flat)[::-1]
    out = {"flat_rank2_residual": float(np.sqrt(np.sum(w[2:] ** 2) / np.sum(w ** 2)))}
    scan = []
    for radius in np.geomspace(3, 300, 61):
        if d.max() / radius > np.pi:
            continue
        chord = 2 * radius * np.sin(d / (2 * radius))
        gram = radius ** 2 - chord ** 2 / 2
        w = np.linalg.eigvalsh(gram)[::-1]
        scan.append((float(radius), float(np.sqrt(np.sum(w[3:] ** 2) / np.sum(w ** 2)))))
    best = min(scan, key=lambda s: s[1])
    out.update({"sphere_best_radius_in_mean_edges": best[0], "sphere_best_rank3_residual": best[1], "scan": scan})
    return out


def main(side="R"):
    graph, cols = columns(side)
    keys = sorted(k for k, v in cols.items() if len(v) >= 10)
    distance = profile_distance(graph, cols, keys)
    geo, edge_len, _ = lattice_geodesic(keys, distance)
    finite = np.isfinite(geo).all(axis=1)
    keys = [k for k, f in zip(keys, finite) if f]
    geo, distance = geo[np.ix_(finite, finite)], distance[np.ix_(finite, finite)]
    hexd = np.array([[max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs((a[0] - a[1]) - (b[0] - b[1]))) for b in keys] for a in keys])
    iu = np.triu_indices(len(keys), 1)
    from scipy.stats import spearmanr
    fit = curvature_fit(geo, edge_len.mean())
    report = {"side": side, "columns": len(keys), "edge_length_mean": float(edge_len.mean()),
              "edge_length_cv": float(edge_len.std() / edge_len.mean()),
              "spearman_profile_vs_hex": float(spearmanr(distance[iu], hexd[iu]).statistic),
              "neighbour_profile_distance_by_hex": {int(h): float(np.median(distance[iu][hexd[iu] == h])) for h in range(1, 6)},
              **{k: v for k, v in fit.items() if k != "scan"},
              "scan_head": fit["scan"][::6]}
    r = report["sphere_best_radius_in_mean_edges"]
    report["implied_step_deg"] = float(np.degrees(1 / r))
    report["implied_solid_angle_sr"] = float(len(keys) * np.sqrt(3) / 2 / r ** 2)
    print(json.dumps(report, indent=1))
    np.savez(Path(__file__).with_name(f"discovery_{side}.npz"), keys=np.array(keys), geo=geo, distance=distance)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "R")
