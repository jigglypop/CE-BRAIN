"""A1 step 31: in the metric that lateral coupling encodes, are the T4/T5 shift operators cardinal isometries? (CONTRACT.md)

Metric: the three lattice edge types (1,0), (0,1), (1,1) carry mean lateral coupling w1, w2, w3. Read as cotangent
Laplace-Beltrami weights, w_t = s * cot(angle opposite edge t) in one lattice triangle (angles sum to pi, which fixes
s = 1 / sqrt(w1 w2 + w2 w3 + w3 w1)); the triangle shape defines a linear map M from lattice to metric coordinates.
T4 (Mi4 - Mi9) and T5 (Tm1+Tm2 - Tm9) centroid vectors are computed in lattice coordinates, mapped by M, and their
pair angles compared with physiology (Zhao et al. 2025: T4a-b and T4c-d approximately antiparallel, four cardinal axes).

python metric_isometry.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VIS = ROOT / "research/ce_brain_visual_sphere_20260923"
FW = ROOT / "data/external/flywire_783"
MALECNS = ROOT / "verify/MaleCNS"
PAIRS = {"T4": (("Mi4",), ("Mi9",)), "T5": (("Tm1", "Tm2"), ("Tm9",))}
MODULAR = ("L1", "L2", "L5", "Mi1", "Mi4", "Mi9", "Tm1", "Tm2", "Tm9", "Tm20", "T1", "C3")
EDGE_TYPES = ((1, 0), (0, 1), (1, 1))
HEX = np.array([[1.0, -0.5], [0.0, np.sqrt(3) / 2]])  # regular hexagon, 120-degree basis (columns = e1, e2)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def angle(u, v):
    return float(np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))


def edge_weights(C, keys):
    S = (C + C.T) / 2
    index = {k: i for i, k in enumerate(keys)}
    acc = defaultdict(list)
    for k, i in index.items():
        for t in EDGE_TYPES:
            for sgn in (1, -1):
                j = index.get((k[0] + sgn * t[0], k[1] + sgn * t[1]))
                if j is not None:
                    acc[t].append(S[i, j])
    return np.array([np.mean(acc[t]) for t in EDGE_TYPES])


def metric_map(w):
    s = 1.0 / np.sqrt(w[0] * w[1] + w[1] * w[2] + w[2] * w[0])
    a, b, c = np.arctan2(1.0, s * w)  # angles opposite (1,0), (0,1), (1,1)
    # triangle P0=0, P1=e1, P2=e1+e2: edge e1 opposite P2 (a), e2 opposite P0 (b), e1+e2 opposite P1 (c)
    P1 = np.array([np.sin(a), 0.0])
    P2 = np.sin(c) * np.array([np.cos(b), np.sin(b)])
    M = np.column_stack([P1, P2 - P1])
    return M / np.sqrt(abs(np.linalg.det(M))), np.degrees([a, b, c]), float(np.degrees(a + b + c))


def frame_tests(vectors, M):
    out = {}
    for family in PAIRS:
        med = {s: np.median(vectors[f"{family}{s}"] @ M.T, axis=0) for s in "abcd"}
        ab, cd = angle(med["a"], med["b"]), angle(med["c"], med["d"])
        ax = angle(med["a"] - med["b"], med["c"] - med["d"])
        out[family] = {"ab_deg": ab, "cd_deg": cd, "axes_deg": min(ax, 180 - ax),
                       "directions_deg": {s: float(np.degrees(np.arctan2(med[s][1], med[s][0]))) for s in "abcd"}}
    return out


def vectors_from(inputs, pos, ctype):
    """inputs: dict cell -> (pre ids array, weights array); pos: id -> lattice coords; returns centroid difference vectors."""
    vecs = defaultdict(list)
    for cell, t, (pre, w) in inputs:
        family = t[:2]
        plus, minus = PAIRS[family]

        def centre(types):
            m = np.array([ctype.get(p) in types for p in pre])
            if w[m].sum() == 0:
                return None
            return (w[m, None] * np.array([pos[p] for p in pre[m]])).sum(axis=0) / w[m].sum()
        a, b = centre(plus), centre(minus)
        if a is not None and b is not None and np.linalg.norm(a - b) > 1e-9:
            vecs[t].append(a - b)
    return {t: np.array(v) for t, v in vecs.items()}


def malecns_eye(side):
    import pyarrow as pa
    import pyarrow.ipc as ipc
    d = load("discover", VIS / "discover.py")
    gm = d.load_module("malecns_neuron_graph", MALECNS / "neuron_graph.py")
    graph = gm.load(MALECNS / "neuron_graph_result.json")
    n = len(graph["node_ids"])
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    h1 = t["assignedOlHex1"].to_numpy(zero_copy_only=False)
    h2 = t["assignedOlHex2"].to_numpy(zero_copy_only=False)
    ty, root, soma = t["type"].to_pylist(), t["rootSide"].to_pylist(), t["somaSide"].to_pylist()
    position, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    pos, ctype, nside = {}, {}, {}
    for i in np.flatnonzero(found):
        p = int(position[i])
        ctype[p], nside[p] = ty[i] or "", root[i] or soma[i] or ""
        if not np.isnan(h1[i]):
            pos[p] = np.array([h1[i], h2[i]], dtype=float)
    # coupling among modular columns of this eye
    cols = defaultdict(list)
    for p, xy in pos.items():
        if ctype[p] in MODULAR and nside[p] == side:
            cols[(int(xy[0]), int(xy[1]))].append(p)
    keys = sorted(k for k, v in cols.items() if len(v) >= 10)
    rows = [(v, g) for g, k in enumerate(keys) for v in cols[k]]
    G = sparse.csr_array((np.ones(len(rows)), ([r for r, _ in rows], [c for _, c in rows])), shape=(n, len(keys)))
    C = (G.T @ A @ G).toarray()
    # T4/T5 inputs (same side, >= 80 % same-side positioned inputs), as in the visual study
    incoming = A.tocsc()
    inputs = []
    for c, t_ in ctype.items():
        if t_[:2] in PAIRS and t_[2:] in ("a", "b", "c", "d") and len(t_) == 3:
            lo, hi = incoming.indptr[c], incoming.indptr[c + 1]
            src, w = incoming.indices[lo:hi], incoming.data[lo:hi].astype(float)
            has = np.array([s in pos for s in src])
            if has.sum() == 0:
                continue
            same = has & np.array([nside.get(s) == side for s in src])
            if same.sum() / has.sum() < 0.8:
                continue
            inputs.append((c, t_, (src[same], w[same])))
    return C, keys, vectors_from(inputs, pos, ctype)


def flywire_eye(side):
    import pandas as pd
    import pyarrow.feather as feather
    col = pd.read_csv(FW / "codex/column_assignment.csv.gz").drop_duplicates("root_id").set_index("root_id")
    pos = {r: np.array([p, q], dtype=float) for r, p, q in zip(col.index, col["p"], col["q"])}
    ctype, hemi = col["type"].to_dict(), col["hemisphere"].to_dict()
    e = feather.read_table(FW / "proofread_connections_783.feather", columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    e = e[e["pre_pt_root_id"].isin(pos.keys()) & e["post_pt_root_id"].isin(pos.keys())]
    e = e.groupby(["pre_pt_root_id", "post_pt_root_id"], as_index=False)["syn_count"].sum()
    mod = col[(col["hemisphere"] == side) & col["type"].isin(MODULAR)]
    counts = mod.groupby("column_id").size()
    cid = sorted(counts[counts >= 10].index)
    pq = mod.groupby("column_id")[["p", "q"]].first().loc[cid]
    keys = [(int(a), int(b)) for a, b in zip(pq["p"], pq["q"])]
    owner = {r: cid.index(c) for r, c in zip(mod.index, mod["column_id"]) if c in set(cid)}
    em = e[e["pre_pt_root_id"].isin(owner) & e["post_pt_root_id"].isin(owner)]
    C = np.zeros((len(cid), len(cid)))
    np.add.at(C, (em["pre_pt_root_id"].map(owner).to_numpy(), em["post_pt_root_id"].map(owner).to_numpy()), em["syn_count"].to_numpy(dtype=float))
    post = [r for r, t in ctype.items() if isinstance(t, str) and len(t) == 3 and t[:2] in PAIRS and t[2] in "abcd" and hemi[r] == side]
    ep = e[e["post_pt_root_id"].isin(post)]
    inputs = []
    for cell, g in ep.groupby("post_pt_root_id"):
        pre = g["pre_pt_root_id"].to_numpy()
        w = g["syn_count"].to_numpy(dtype=float)
        same = np.array([hemi[p] == side for p in pre])
        if same.mean() < 0.8:
            continue
        inputs.append((cell, ctype[cell], (pre[same], w[same])))
    return C, keys, vectors_from(inputs, pos, ctype)


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    res = {}
    for name, fn, sides in (("malecns", malecns_eye, ("R", "L")), ("flywire", flywire_eye, ("right", "left"))):
        for s in sides:
            C, keys, vecs = fn(s)
            w = edge_weights(C, keys)
            M, angs, total = metric_map(w)
            hexf, metf = frame_tests(vecs, HEX), frame_tests(vecs, M)
            r = {"edge_weights_10_01_11": w.tolist(), "triangle_angles_deg": angs.tolist(), "angle_sum": total,
                 "neurons": {t: int(len(v)) for t, v in vecs.items()}, "hex_frame": hexf, "metric_frame": metf}
            for f in PAIRS:
                m, hx = metf[f], hexf[f]
                r[f"G1_{f}"] = bool(m["ab_deg"] >= 170 and m["cd_deg"] >= 170)
                r[f"G2_{f}"] = bool(abs(m["axes_deg"] - 90) <= 10)
                r[f"G3_{f}"] = bool(m["cd_deg"] > hx["cd_deg"])
            res[f"{name}_{s}"] = r
    t4 = all(r["G1_T4"] and r["G2_T4"] and r["G3_T4"] for r in res.values())
    t5 = all(r["G1_T5"] and r["G2_T5"] and r["G3_T5"] for r in res.values())
    result = {"schema": "ce-a1-step31-visual-metric-isometry", "code_sha256": code_hash,
              "verdict_T4": "T4_CARDINAL_ISOMETRIES_IN_COUPLING_METRIC" if t4 else "T4_NOT_CARDINAL_IN_COUPLING_METRIC",
              "verdict_T5": "T5_CARDINAL_ISOMETRIES_IN_COUPLING_METRIC" if t5 else "T5_NOT_CARDINAL_IN_COUPLING_METRIC", "eyes": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print(result["verdict_T4"], "|", result["verdict_T5"])
    for k, r in res.items():
        print("==", k, "w", [round(x, 2) for x in r["edge_weights_10_01_11"]], "tri", [round(x, 1) for x in r["triangle_angles_deg"]],
              "G", {g: r[g] for g in r if g.startswith("G")})
        for f in PAIRS:
            h, m = r["hex_frame"][f], r["metric_frame"][f]
            print("   ", f, "hex ab/cd/axes %.1f/%.1f/%.1f" % (h["ab_deg"], h["cd_deg"], h["axes_deg"]),
                  "-> metric %.1f/%.1f/%.1f" % (m["ab_deg"], m["cd_deg"], m["axes_deg"]))


if __name__ == "__main__":
    main()
