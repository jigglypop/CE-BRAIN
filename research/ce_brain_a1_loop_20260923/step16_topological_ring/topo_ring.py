"""A1 step 16: is the EPG wiring manifold topologically a ring (one persistent H1 cycle)? (CONTRACT.md)

Distance: chord distance between unit connectivity profiles (monotone in the step-11 angle distance,
so the Vietoris-Rips filtration is the same). Null: Gaussian cloud with the same PCA spectrum (same
second moments, no hole). Pass: longest H1 lifetime > null q95 of the longest lifetime and >= 2x the
second-longest.

python topo_ring.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from ripser import ripser
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MALECNS = ROOT / "verify/MaleCNS"
FLYWIRE = ROOT / "data/external/flywire_783"
SEED = 20260923
N_NULL_EPG, N_NULL_SCAN = 500, 100
SCAN_N = (15, 40)
REPORT_TYPES = ("EPG", "PEN_a(PEN1)", "PEN_b(PEN2)", "PEG", "Delta7", "ER4d")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc11 = load("scan", HERE.parent / "step11_manifold_scan/scan.py")


def pca_coords(A, AT, idx):
    """Unit profiles -> PCA coordinates via the centred Gram matrix (no densifying)."""
    prof = sparse.hstack([sc11.row_unit(A[idx, :]), sc11.row_unit(AT[idx, :])]).tocsr() / np.sqrt(2)
    norms = np.sqrt(np.asarray(prof.multiply(prof).sum(axis=1)).ravel())
    if np.any(norms < 0.5):
        return None
    K = (prof @ prof.T).toarray()
    n = len(idx)
    c = np.eye(n) - 1 / n
    w, v = np.linalg.eigh(c @ K @ c)
    keep = w > 1e-12
    return v[:, keep] * np.sqrt(w[keep])


def top2_lifetimes(Y):
    D = np.linalg.norm(Y[:, None] - Y[None], axis=2)
    dg = ripser(D, distance_matrix=True, maxdim=1)["dgms"][1]
    life = np.sort(dg[:, 1] - dg[:, 0])[::-1] if len(dg) else np.zeros(0)
    return np.r_[life, 0.0, 0.0][:2]


def h1_test(Y, rng, n_null):
    l1, l2 = top2_lifetimes(Y)
    scale = np.sqrt((Y ** 2).sum(axis=0) / (len(Y) - 1))
    null = np.array([top2_lifetimes(rng.normal(size=Y.shape) * scale)[0] for _ in range(n_null)])
    q95 = float(np.quantile(null, 0.95))
    return {"l1": float(l1), "l2": float(l2), "null_q95": q95, "l1_over_q95": float(l1 / q95) if q95 > 0 else None,
            "null_p": float((1 + np.sum(null >= l1)) / (1 + n_null)), "dims": int(Y.shape[1]),
            "pass": bool(l1 > q95 and l1 >= 2 * l2)}


def malecns():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    gm = load("g", MALECNS / "neuron_graph.py")
    graph = gm.load(MALECNS / "neuron_graph_result.json")
    n = len(graph["node_ids"])
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    groups, sup = defaultdict(list), {}
    for p, f, ty, side, sc in zip(pos, found, t["type"].to_pylist(), t["somaSide"].to_pylist(), t["superclass"].to_pylist()):
        if f and ty:
            key = (ty, {"L": "left", "R": "right"}.get(side, "M"))
            groups[key].append(int(p))
            sup[key] = sc or ""
    return A, groups, sup


def flywire():
    import pandas as pd
    import pyarrow.feather as feather
    ann = pd.read_csv(FLYWIRE / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False).drop_duplicates("root_id")
    ids = np.sort(ann["root_id"].to_numpy(dtype=np.int64))
    ann = ann.set_index("root_id").loc[ids]
    e = feather.read_table(FLYWIRE / "proofread_connections_783.feather",
                           columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    pre = np.searchsorted(ids, e["pre_pt_root_id"].to_numpy(dtype=np.int64))
    post = np.searchsorted(ids, e["post_pt_root_id"].to_numpy(dtype=np.int64))
    ok = (pre < len(ids)) & (post < len(ids))
    ok[ok] &= (ids[pre[ok]] == e["pre_pt_root_id"].to_numpy()[ok]) & (ids[post[ok]] == e["post_pt_root_id"].to_numpy()[ok])
    n = len(ids)
    A = sparse.csr_array((e["syn_count"].to_numpy(dtype=float)[ok], (pre[ok], post[ok])), shape=(n, n))
    A.sum_duplicates()
    groups, sup = defaultdict(list), {}
    for v, (ty, side, sc) in enumerate(zip(ann["cell_type"].fillna(""), ann["side"].fillna(""), ann["super_class"].fillna(""))):
        if ty:
            key = (ty, side if side in ("left", "right") else "M")
            groups[key].append(v)
            sup[key] = sc
    return A, groups, sup


def run(name, A, groups, sup, rng):
    AT = A.T.tocsr()
    out = {"report_types": {}, "scan": []}
    for ty in REPORT_TYPES:
        for side in ("left", "right"):
            members = groups.get((ty, side))
            if not members or len(members) < 8:
                continue
            Y = pca_coords(A, AT, np.array(sorted(members)))
            if Y is not None:
                out["report_types"][f"{ty}|{side}"] = {"n": len(members), **h1_test(Y, rng, N_NULL_EPG)}
    skipped = 0
    for key in sorted(groups):
        members = groups[key]
        if key[0] == "EPG" or not SCAN_N[0] <= len(members) <= SCAN_N[1]:
            continue
        Y = pca_coords(A, AT, np.array(sorted(members)))
        if Y is None:
            skipped += 1
            continue
        out["scan"].append({"type": key[0], "side": key[1], "n": len(members), "super_class": sup[key],
                            **h1_test(Y, rng, N_NULL_SCAN)})
    out["scan_skipped_zero_profile"] = skipped
    rate = np.mean([s["pass"] for s in out["scan"]]) if out["scan"] else float("nan")
    by_sup = defaultdict(list)
    for s in out["scan"]:
        by_sup[s["super_class"]].append(s["pass"])
    out["scan_pass_rate"] = float(rate)
    out["scan_pass_rate_by_super_class"] = {k: [float(np.mean(v)), len(v)] for k, v in sorted(by_sup.items())}
    print(name, json.dumps({k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                            for k, v in out["report_types"].items()}, indent=1), flush=True)
    print(name, "scan", len(out["scan"]), "pass rate", round(rate, 3), out["scan_pass_rate_by_super_class"], flush=True)
    return out


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    rng = np.random.default_rng(SEED)
    M = run("malecns", *malecns(), rng)
    F = run("flywire", *flywire(), rng)
    epg = lambda d: [d["report_types"].get(f"EPG|{s}", {}).get("pass", False) for s in ("left", "right")]
    t0, t1 = all(epg(M)), all(epg(F))
    t2 = M["scan_pass_rate"] <= 0.2 and F["scan_pass_rate"] <= 0.2
    verdict = ("EPG_TOPOLOGICAL_RING_REPLICATED" if t0 and t1 and t2 else
               "METHOD_CONTROL_FAILED" if not t0 else
               "EPG_TOPOLOGICAL_RING_NOT_REPLICATED" if not t1 else "EPG_RING_NONSPECIFIC")
    result = {"schema": "ce-a1-step16-topological-ring", "code_sha256": code_hash, "seed": SEED,
              "T0_malecns_epg": bool(t0), "T1_flywire_epg": bool(t1), "T2_specificity": bool(t2),
              "verdict": verdict, "malecns": M, "flywire": F}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print(json.dumps({k: result[k] for k in ("T0_malecns_epg", "T1_flywire_epg", "T2_specificity", "verdict")}, indent=1))


if __name__ == "__main__":
    main()
