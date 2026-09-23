"""A1 step 13: confirm the neck latent channel and the MB expand-compress profile (CONTRACT.md).

python latent_confirm.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MALECNS = ROOT / "verify/MaleCNS"
SEED = 20260923


def normalize_cols(M):
    M = sparse.csc_array(M, dtype=float)
    col = np.asarray(M.sum(axis=0)).ravel()
    return M @ sparse.diags(1 / np.where(col > 0, col, 1))


def measures(M):
    s = np.linalg.svd(normalize_cols(M).toarray(), compute_uv=False)
    s = s[s > 1e-12]
    e2 = s ** 2
    rank90 = int(np.searchsorted(np.cumsum(e2) / e2.sum(), 0.9) + 1)
    p = s / s.sum()
    return {"rank90": rank90, "erank": float(np.exp(-np.sum(p * np.log(p)))), "PR": float(e2.sum() ** 2 / np.sum(e2 ** 2)),
            "shape": list(M.shape)}


def trim(M):
    M = sparse.csr_array(M)
    M = M[np.asarray(M.sum(axis=1)).ravel() > 0, :]
    return M[:, np.asarray(M.sum(axis=0)).ravel() > 0]


def edge_swap_null(M, rng, rounds=10):
    coo = sparse.coo_array(M)
    r, c, w = coo.row.astype(np.int64), coo.col.astype(np.int64), coo.data.copy()
    C = M.shape[1]
    for _ in range(rounds):
        keys = np.sort(r * C + c)
        perm = rng.permutation(len(r))
        a, b = perm[0::2][: len(perm) // 2], perm[1::2][: len(perm) // 2]
        k1, k2 = r[a] * C + c[b], r[b] * C + c[a]
        exists = lambda k: keys[np.clip(np.searchsorted(keys, k), 0, len(keys) - 1)] == k
        ok = (r[a] != r[b]) & (c[a] != c[b]) & ~exists(k1) & ~exists(k2)
        allk = np.r_[k1[ok], k2[ok]]
        uniq, cnt = np.unique(allk, return_counts=True)
        dup = set(uniq[cnt > 1].tolist())
        if dup:
            bad = np.array([x in dup or y in dup for x, y in zip(k1[ok], k2[ok])])
            idx = np.flatnonzero(ok)
            ok[idx[bad]] = False
        ca = c[a[ok]].copy()
        c[a[ok]] = c[b[ok]]
        c[b[ok]] = ca
    return sparse.csr_array((w, (r, c)), shape=M.shape)


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    spec = importlib.util.spec_from_file_location("g", MALECNS / "neuron_graph.py")
    gm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gm)
    graph = gm.load(MALECNS / "neuron_graph_result.json")
    n = len(graph["node_ids"])
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    labels = graph["superclass_labels"]
    sc = np.array([labels[c] if c >= 0 else "" for c in graph["superclass"]])
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    cls, typ, side = np.full(n, "", object), np.full(n, "", object), np.full(n, "", object)
    for p, f, c, ty, s in zip(pos, found, t["class"].to_pylist(), t["type"].to_pylist(), t["somaSide"].to_pylist()):
        if f:
            cls[p], typ[p], side[p] = c or "", ty or "", s or ""
    sets = {"central": np.flatnonzero(sc == "cb_intrinsic"), "DN": np.flatnonzero(sc == "descending_neuron"),
            "VNC": np.flatnonzero(sc == "vnc_intrinsic"), "MN": np.flatnonzero(np.isin(sc, ["vnc_motor", "cb_motor"])),
            "KC": np.flatnonzero(np.char.startswith(typ.astype(str), "KC")), "MBON": np.flatnonzero(cls == "MBON"),
            "ALPN": np.flatnonzero(cls == "ALPN")}
    mats = {"M1": ("central", "DN"), "M2": ("DN", "VNC"), "M3": ("VNC", "MN"), "M4": ("KC", "MBON"), "M5": ("ALPN", "KC")}
    rng = np.random.default_rng(SEED)
    res = {}
    for name, (a, b) in mats.items():
        M = trim(A[sets[a], :][:, sets[b]])
        real, null = measures(M), measures(edge_swap_null(M, rng))
        res[name] = {"real": real, "null_edge_swap": null, "ratio_rank90": real["rank90"] / null["rank90"]}
        print(name, json.dumps(res[name]), flush=True)
    c1 = all(res[m]["ratio_rank90"] < 0.6 and res[m]["real"]["rank90"] < 0.5 * min(res[m]["real"]["shape"]) for m in ("M1", "M2"))
    # C2 hemisphere replication
    hemi = {}
    for s in ("L", "R"):
        dn = sets["DN"][side[sets["DN"]] == s]
        M = trim(A[sets["central"], :][:, dn])
        m = measures(M)
        hemi[s] = {**m, "rank90_per_column": m["rank90"] / M.shape[1]}
    c2 = abs(hemi["L"]["rank90_per_column"] - hemi["R"]["rank90_per_column"]) / max(hemi["L"]["rank90_per_column"], hemi["R"]["rank90_per_column"]) <= 0.2
    # C3 robustness
    robust = {}
    for m in ("M1", "M2"):
        a, b = mats[m]
        M = trim(A[sets[a], :][:, sets[b]])
        Mt = M.copy()
        Mt.data[Mt.data < 5] = 0
        Mt.eliminate_zeros()
        thr = measures(trim(Mt))["rank90"]
        pois = []
        for _ in range(5):
            Mp = M.copy()
            Mp.data = rng.poisson(Mp.data).astype(float)
            Mp.eliminate_zeros()
            pois.append(measures(trim(Mp))["rank90"])
        base = res[m]["real"]["rank90"]
        robust[m] = {"threshold5_rank90": thr, "threshold5_change": abs(thr - base) / base, "poisson_rank90": pois,
                     "poisson_cv": float(np.std(pois) / np.mean(pois))}
    c3 = all(robust[m]["threshold5_change"] < 0.2 and robust[m]["poisson_cv"] < 0.05 for m in robust)
    c4 = res["M4"]["ratio_rank90"] < 0.7 and abs(res["M5"]["ratio_rank90"] - 1) <= 0.1
    # type-level report
    dn = sets["DN"]
    types = sorted(set(typ[dn]) - {""})
    col_type = np.array([types.index(typ[v]) if typ[v] in types else -1 for v in dn])
    keep = col_type >= 0
    M1 = A[sets["central"], :][:, dn[keep]]
    agg = sparse.csr_array((np.ones(keep.sum()), (np.arange(keep.sum()), col_type[keep])), shape=(keep.sum(), len(types)))
    type_rank = measures(trim(M1 @ agg))["rank90"]
    result = {"schema": "ce-a1-step13-latent-confirm", "code_sha256": code_hash, "matrices": res, "hemisphere": hemi,
              "robustness": robust, "C1": c1, "C2": bool(c2), "C3": bool(c3), "C4": bool(c4),
              "report": {"dn_neurons": int(len(dn)), "dn_types": len(types), "type_level_rank90": type_rank,
                         "neuron_level_rank90": res["M1"]["real"]["rank90"]},
              "verdict": "LATENT_CHANNEL_CONFIRMED" if c1 and c2 and c3 and c4 else "LATENT_CHANNEL_NOT_CONFIRMED"}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps({k: v for k, v in result.items() if k not in ("matrices",)}, indent=1, default=float))


if __name__ == "__main__":
    main()
