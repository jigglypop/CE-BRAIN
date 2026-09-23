"""A1 step 15: replicate MaleCNS findings in FlyWire 783 (CONTRACT.md).

python flywire_replication.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / "data/external/flywire_783"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lc = load("latent_confirm", HERE.parent / "step13_latent_confirm/latent_confirm.py")
sc11 = load("scan", HERE.parent / "step11_manifold_scan/scan.py")


def assess(M, rng):
    real, null = lc.measures(M), lc.measures(lc.edge_swap_null(M, rng))
    return {"real": real, "null_edge_swap": null, "ratio_rank90": real["rank90"] / null["rank90"],
            "ratio_PR": real["PR"] / null["PR"]}


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    import pandas as pd
    import pyarrow.feather as feather
    ann = pd.read_csv(DATA / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False)
    ann = ann.drop_duplicates("root_id")
    ids = np.sort(ann["root_id"].to_numpy(dtype=np.int64))
    ann = ann.set_index("root_id").loc[ids]
    edges = feather.read_table(DATA / "proofread_connections_783.feather",
                               columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    pre = np.searchsorted(ids, edges["pre_pt_root_id"].to_numpy(dtype=np.int64))
    post = np.searchsorted(ids, edges["post_pt_root_id"].to_numpy(dtype=np.int64))
    ok = (pre < len(ids)) & (post < len(ids))
    ok[ok] &= (ids[pre[ok]] == edges["pre_pt_root_id"].to_numpy()[ok]) & (ids[post[ok]] == edges["post_pt_root_id"].to_numpy()[ok])
    n = len(ids)
    A = sparse.csr_array((edges["syn_count"].to_numpy(dtype=float)[ok], (pre[ok], post[ok])), shape=(n, n))
    A.sum_duplicates()
    superc = ann["super_class"].fillna("").to_numpy()
    cellc = ann["cell_class"].fillna("").to_numpy()
    ctype = ann["cell_type"].fillna("").to_numpy()
    side = ann["side"].fillna("").to_numpy()
    rng = np.random.default_rng(lc.SEED)
    central, dn = np.flatnonzero(superc == "central"), np.flatnonzero(superc == "descending")
    F1 = assess(lc.trim(A[central, :][:, dn]), rng)
    u = F1["real"]["rank90"] / F1["real"]["shape"][1]
    f1 = 0.22 <= u <= 0.37 and F1["ratio_rank90"] <= 0.7 and F1["ratio_PR"] <= 0.5
    kc, mbon, alpn = np.flatnonzero(cellc == "Kenyon_Cell"), np.flatnonzero(cellc == "MBON"), np.flatnonzero(cellc == "ALPN")
    pk = assess(lc.trim(A[alpn, :][:, kc]), rng)
    km = assess(lc.trim(A[kc, :][:, mbon]), rng)
    f2 = 0.85 <= pk["ratio_rank90"] <= 1.15 and km["ratio_rank90"] < 0.7
    # F3/F4: same classifier as step 11
    AT = A.T.tocsr()
    groups = defaultdict(list)
    for v in range(n):
        if ctype[v]:
            groups[(ctype[v], side[v] or "M")].append(v)
    catalog = []
    for key, members in groups.items():
        if not 8 <= len(members) <= 2500:
            continue
        idx = np.array(sorted(members))
        prof = sparse.hstack([sc11.row_unit(A[idx, :]), sc11.row_unit(AT[idx, :])]).tocsr() / np.sqrt(2)
        S = (prof @ prof.T).toarray()
        D = np.arccos(np.clip(S, -1, 1))
        np.fill_diagonal(D, 0)
        entry, _ = sc11.classify(D)
        entry.update({"type": key[0], "side": key[1], "n": len(idx), "super_class": superc[idx[0]], "cell_class": cellc[idx[0]]})
        catalog.append(entry)
    r12 = lambda e: e.get("r1", 0) + e.get("r2", 0)
    kc_units = [r12(e) for e in catalog if e["cell_class"] == "Kenyon_Cell" and "r1" in e]
    by_super = defaultdict(list)
    for e in catalog:
        if "r1" in e and e["cell_class"] != "Kenyon_Cell":
            by_super[e["super_class"]].append(r12(e))
    super_medians = {k: float(np.median(v)) for k, v in by_super.items() if len(v) >= 20}
    f3 = bool(kc_units) and float(np.median(kc_units)) < 0.4 and all(m > 0.5 for m in super_medians.values())
    epg = {e["side"]: e for e in catalog if e["type"] == "EPG"}
    f4 = all(epg.get(s, {}).get("class") == "ring" for s in ("left", "right"))
    result = {"schema": "ce-a1-step15-flywire-replication", "code_sha256": code_hash, "neurons": int(n),
              "edges_used": int(ok.sum()), "dn": int(len(dn)),
              "F1_neck": {**F1, "rank90_per_dn": u, "pass": bool(f1)},
              "F2_mb": {"ALPN_KC": pk, "KC_MBON": km, "pass": bool(f2)},
              "F3_dichotomy": {"kc_units": len(kc_units), "kc_median_r12": float(np.median(kc_units)) if kc_units else None,
                               "super_class_medians": super_medians, "pass": f3},
              "F4_epg_ring": {s: {k: epg[s].get(k) for k in ("class", "radius_cv", "span_deg", "n")} for s in epg},
              "class_counts": {c: sum(e["class"] == c for e in catalog) for c in ("ring", "sheet", "line", "other", "fragmented")}}
    result["F4_epg_ring"]["pass"] = bool(f4)
    result["verdict"] = "FLYWIRE_REPLICATION_SUPPORTED" if f1 and f2 and f3 and f4 else "FLYWIRE_REPLICATION_PARTIAL_OR_FAILED"
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    (HERE / "catalog.json").write_text(json.dumps(catalog, indent=1, default=float), encoding="utf-8")
    brief = lambda d: (d["real"]["rank90"], round(d["real"]["PR"], 1), d["null_edge_swap"]["rank90"], round(d["null_edge_swap"]["PR"], 1),
                       round(d["ratio_rank90"], 3), round(d["ratio_PR"], 3), d["real"]["shape"])
    print(json.dumps({"neurons": n, "dn": int(len(dn)), "F1": (*brief(F1), round(u, 3), bool(f1)), "F2_ALPN_KC": brief(pk),
                      "F2_KC_MBON": brief(km), "F2": bool(f2), "F3": result["F3_dichotomy"], "F4": result["F4_epg_ring"],
                      "class_counts": result["class_counts"], "verdict": result["verdict"]}, indent=1, default=float))


if __name__ == "__main__":
    main()
