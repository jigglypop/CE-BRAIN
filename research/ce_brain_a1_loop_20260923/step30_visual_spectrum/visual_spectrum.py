"""A1 step 30: is the visual lateral coupling a function of the fixed column lattice's Laplacian? (CONTRACT.md)

Column coupling C = synapses between modular columnar neurons of different columns (one eye). S = (C + C^T)/2.
Low random-walk eigenfunctions of S are compared with those of the hex-lattice graph Laplacian (nearest
neighbours = planar distance 1) by the mean squared cosine of principal angles (k = 2 and k = 6).

python visual_spectrum.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.linalg import eigh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VIS = ROOT / "research/ce_brain_visual_sphere_20260923"
FW = ROOT / "data/external/flywire_783"
MIN_MEMBERS, K_SMALL, K_LARGE, N_NULL, SEED = 10, 2, 6, 200, 20260923
M1_MIN, M2_MIN = 0.9, 0.7


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def low_modes(S, k):
    d = S.sum(axis=1)
    keep = d > 0
    L = np.diag(d) - S
    w, v = eigh(L, np.diag(np.where(keep, d, 1.0)))  # random-walk (generalised) eigenfunctions
    return w[1:k + 1], v[:, 1:k + 1]


def subspace_similarity(U, V):
    qa, _ = np.linalg.qr(U - U.mean(axis=0))
    qb, _ = np.linalg.qr(V - V.mean(axis=0))
    s = np.linalg.svd(qa.T @ qb, compute_uv=False)
    return float(np.mean(s ** 2))


def lattice_adjacency(xy):
    d = np.linalg.norm(xy[:, None] - xy[None], axis=2)
    return ((d > 0.9) & (d < 1.1)).astype(float)


def analyse(C, xy, rng):
    S = (C + C.T) / 2
    np.fill_diagonal(S, 0)
    H = lattice_adjacency(xy)
    out = {"columns": int(len(xy)), "lattice_edges": int(H.sum() / 2),
           "lateral_asymmetry": float(np.linalg.norm(C - C.T) / np.linalg.norm(C + C.T))}
    wS, fS = low_modes(S, K_LARGE)
    wH, fH = low_modes(H, K_LARGE)
    sim2 = subspace_similarity(fS[:, :K_SMALL], fH[:, :K_SMALL])
    sim6 = subspace_similarity(fS, fH)
    null2, null6 = [], []
    for _ in range(N_NULL):
        p = rng.permutation(len(xy))
        Sp = S[np.ix_(p, p)]
        _, fp = low_modes(Sp, K_LARGE)
        null2.append(subspace_similarity(fp[:, :K_SMALL], fH[:, :K_SMALL]))
        null6.append(subspace_similarity(fp, fH))
    X = xy - xy.mean(axis=0)
    coef, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(xy)), fS[:, :2]]), X, rcond=None)
    pred = np.column_stack([np.ones(len(xy)), fS[:, :2]]) @ coef
    r2 = 1 - np.sum((X - pred) ** 2) / np.sum(X ** 2)
    out.update({"S_low_eigenvalues": wS.tolist(), "lattice_low_eigenvalues": wH.tolist(),
                "sim_k2": sim2, "sim_k6": sim6, "null_k2_q99": float(np.quantile(null2, 0.99)), "null_k6_q99": float(np.quantile(null6, 0.99)),
                "report_xy_R2_from_two_modes": float(r2),
                "report_eigen_ratio_2_over_1": {"S": float(wS[1] / wS[0]), "lattice": float(wH[1] / wH[0])},
                "M1": bool(sim2 >= M1_MIN), "M2": bool(sim6 >= M2_MIN),
                "M3_null": bool(sim2 > np.quantile(null2, 0.99) and sim6 > np.quantile(null6, 0.99))})
    return out


def malecns(side):
    d = load("discover", VIS / "discover.py")
    graph, cols = d.columns(side)
    keys = sorted(k for k, v in cols.items() if len(v) >= MIN_MEMBERS)
    n = len(graph["node_ids"])
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    rows = [(v, g) for g, k in enumerate(keys) for v in cols[k]]
    G = sparse.csr_array((np.ones(len(rows)), ([r for r, _ in rows], [c for _, c in rows])), shape=(n, len(keys)))
    C = (G.T @ A @ G).toarray()
    E1, E2 = np.array([1.0, 0.0]), np.array([-0.5, np.sqrt(3) / 2])
    xy = np.array([k[0] * E1 + k[1] * E2 for k in keys])
    return C, xy


def flywire(side):
    import pandas as pd
    import pyarrow.feather as feather
    d = load("discover", VIS / "discover.py")
    col = pd.read_csv(FW / "codex/column_assignment.csv.gz").drop_duplicates("root_id")
    col = col[(col["hemisphere"] == side) & col["type"].isin(d.MODULAR)]
    counts = col.groupby("column_id").size()
    keep = counts[counts >= MIN_MEMBERS].index
    col = col[col["column_id"].isin(keep)]
    cid = sorted(keep)
    index = {c: i for i, c in enumerate(cid)}
    pq = col.groupby("column_id")[["p", "q"]].first().loc[cid]
    xy = np.column_stack([(pq["q"] - pq["p"]) / 2.0, (pq["p"] + pq["q"]) * np.sqrt(3) / 2.0])
    owner = dict(zip(col["root_id"], col["column_id"].map(index)))
    e = feather.read_table(FW / "proofread_connections_783.feather", columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    e = e[e["pre_pt_root_id"].isin(owner) & e["post_pt_root_id"].isin(owner)]
    C = np.zeros((len(cid), len(cid)))
    np.add.at(C, (e["pre_pt_root_id"].map(owner).to_numpy(), e["post_pt_root_id"].map(owner).to_numpy()), e["syn_count"].to_numpy(dtype=float))
    return C, xy


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    rng = np.random.default_rng(SEED)
    res = {}
    for name, fn, sides in (("malecns", malecns, ("R", "L")), ("flywire", flywire, ("right", "left"))):
        for s in sides:
            res[f"{name}_{s}"] = analyse(*fn(s), rng)
    ok = all(r["M1"] and r["M2"] and r["M3_null"] for r in res.values())
    result = {"schema": "ce-a1-step30-visual-spectrum", "code_sha256": code_hash,
              "verdict": "LATERAL_COUPLING_IS_LATTICE_LAPLACIAN_FUNCTION" if ok else "LATERAL_COUPLING_NOT_LATTICE_LAPLACIAN_FUNCTION",
              "eyes": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"])
    for k, r in res.items():
        print(k, {x: (round(v, 3) if isinstance(v, float) else v) for x, v in r.items() if not isinstance(v, (list, dict))},
              "ratio", {a: round(b, 3) for a, b in r["report_eigen_ratio_2_over_1"].items()})


if __name__ == "__main__":
    main()
