"""Post-hoc diagnostic for step 15 F4 (EPG ring). Does NOT change the frozen verdict.

Per-neuron MDS radius for EPG left/right in FlyWire, leave-one-out radius CV,
and the same numbers for MaleCNS EPG from the step-11 pipeline for comparison.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import dijkstra

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / "data/external/flywire_783"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc11 = load("scan", HERE.parent / "step11_manifold_scan/scan.py")


def radii(D):
    n = len(D)
    k = min(sc11.K, n - 1)
    order = np.argsort(D, axis=1)[:, 1:k + 1]
    rows = np.repeat(np.arange(n), k)
    g = sparse.csr_array((D[rows, order.ravel()], (rows, order.ravel())), shape=(n, n))
    G = dijkstra(g.maximum(g.T), directed=False)
    c = np.eye(n) - 1 / n
    w, v = np.linalg.eigh(-0.5 * c @ (G ** 2) @ c)
    w, v = w[::-1], v[:, ::-1]
    xy = v[:, :2] * np.sqrt(np.clip(w[:2], 0, None))
    xy -= xy.mean(axis=0)
    r = np.linalg.norm(xy, axis=1)
    return r, np.degrees(np.arctan2(xy[:, 1], xy[:, 0]))


def describe(D, ids):
    r, ang = radii(D)
    cv = r.std() / r.mean()
    loo = []
    for i in range(len(D)):
        keep = np.r_[0:i, i + 1:len(D)]
        e, _ = sc11.classify(D[np.ix_(keep, keep)])
        loo.append((e["radius_cv"], e["class"]))
    rel = r / np.median(r)
    return {"cv": float(cv), "radius_rel_sorted": np.round(np.sort(rel), 2).tolist(),
            "min_radius_neuron": str(ids[int(np.argmin(r))]), "loo_min_cv": float(min(x[0] for x in loo)),
            "loo_ring_count": sum(x[1] == "ring" for x in loo), "n": len(D)}


def profile_D(A, AT, idx):
    prof = sparse.hstack([sc11.row_unit(A[idx, :]), sc11.row_unit(AT[idx, :])]).tocsr() / np.sqrt(2)
    D = np.arccos(np.clip((prof @ prof.T).toarray(), -1, 1))
    np.fill_diagonal(D, 0)
    return D


def main():
    import pandas as pd
    import pyarrow.feather as feather
    ann = pd.read_csv(DATA / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False).drop_duplicates("root_id")
    ids = np.sort(ann["root_id"].to_numpy(dtype=np.int64))
    ann = ann.set_index("root_id").loc[ids]
    e = feather.read_table(DATA / "proofread_connections_783.feather",
                           columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    pre = np.searchsorted(ids, e["pre_pt_root_id"].to_numpy(dtype=np.int64))
    post = np.searchsorted(ids, e["post_pt_root_id"].to_numpy(dtype=np.int64))
    ok = (pre < len(ids)) & (post < len(ids))
    ok[ok] &= (ids[pre[ok]] == e["pre_pt_root_id"].to_numpy()[ok]) & (ids[post[ok]] == e["post_pt_root_id"].to_numpy()[ok])
    n = len(ids)
    A = sparse.csr_array((e["syn_count"].to_numpy(dtype=float)[ok], (pre[ok], post[ok])), shape=(n, n))
    A.sum_duplicates()
    AT = A.T.tocsr()
    ctype, side = ann["cell_type"].fillna("").to_numpy(), ann["side"].fillna("").to_numpy()
    out = {"note": "post-hoc diagnostic; frozen F4 verdict (FAIL) unchanged"}
    for s in ("left", "right"):
        idx = np.flatnonzero((ctype == "EPG") & (side == s))
        out[f"flywire_{s}"] = describe(profile_D(A, AT, idx), ids[idx])
        out[f"flywire_{s}"]["out_syn_per_neuron_median"] = float(np.median(A[idx, :].sum(axis=1)))
        out[f"flywire_{s}"]["in_syn_per_neuron_median"] = float(np.median(AT[idx, :].sum(axis=1)))
    (HERE / "diag_epg.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
