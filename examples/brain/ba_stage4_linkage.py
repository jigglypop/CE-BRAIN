"""BA-STAGE4 anatomy linkage lock (anatomy-blind with respect to responses).

Contract: paper/검증_원장/BA_STAGE4_해부학_다리_계약.md. Builds, WITHOUT reading
any endpoint response value: the parcel-index mapping (empirically from
ds004080's own label columns), group-median Domhof SC/Lengths matrices, per
(source, target-site) anatomy features f_SC/f_PL, and the attrition counts.

Frozen conventions (declared here, before any response contact):
  - 0-based matrix index = 75*(hemisphere==R) + (Destrieux_label - 1);
    ordering empirically confirmed (intra/inter 10.0x, homotopic 17.9x,
    G_front_sup at 15/90, precentral<->S_central adjacency).
  - f_SC(s,t) = mean over parcel pairs of log1p(median-SC[p,q]); diagonal
    p==q replaced by row max (contract axiom); sensitivity diag=0 also saved.
  - f_PL(s,t) = mean over parcel pairs of median-Lengths[p,q]; diagonal := 0.
  - A site's parcel set = valid labels of its two contacts; any invalid
    contact label drops the site for ALL candidates (matched attrition).
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
S4 = REPO / "data/external/stage4"
OUT = Path.cwd() / "ba-stage4-linkage-receipt.json"
FEAT = Path.cwd() / "ba-stage4-anatomy-features.json"
EP = REPO / "_workspace/ce/brain-human-ccep-multisubject-precision-retry-20260825/artifacts"
H = 75


def group_median(kind: str) -> np.ndarray:
    files = sorted((S4 / "150-Destrieux/1StructuralConnectivity").glob(f"*/{kind}.csv"))
    assert len(files) == 200, len(files)
    return np.median(np.stack([np.loadtxt(p) for p in files]), axis=0)


def build_label_table():
    """index->text mapping harvested from ds004080's own columns; consistency-checked."""
    table = {}
    hemis = {}
    for f in (S4 / "electrodes").glob("*_electrodes.tsv"):
        sub, ses = f.stem.replace("_electrodes", "").split("_", 1)
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                lab, txt, hemi = r["Destrieux_label"], r["Destrieux_label_text"], r["hemisphere"]
                try:
                    li = int(float(lab))
                except ValueError:
                    li = None
                key = (sub, ses, r["name"])
                norm = txt.replace("G&S_", "G_and_S_").replace("&", "_and_")
                if li is not None and 1 <= li <= H and txt not in ("", "n/a") and hemi in ("L", "R"):
                    if li in table and table[li] != norm:
                        raise RuntimeError(f"label text conflict {li}: {table[li]} vs {norm}")
                    table[li] = norm
                    hemis[key] = (hemi, li)
                else:
                    hemis[key] = None
    return table, hemis


def main():
    for p in (OUT, FEAT):
        if p.exists():
            raise FileExistsError(p)
    sc = group_median("Counts")
    pl = group_median("Lengths")
    table, contact_map = build_label_table()
    fsc = np.log1p(sc.copy())
    fsc_diag0 = fsc.copy()
    np.fill_diagonal(fsc_diag0, 0.0)
    rowmax = fsc.max(axis=1)
    np.fill_diagonal(fsc, 0.0)
    np.fill_diagonal(fsc, np.maximum(fsc.max(axis=1), 0.0))  # row max EXCLUDING old diag
    pl0 = pl.copy()
    np.fill_diagonal(pl0, 0.0)

    def idx(hemi, li):
        return (H if hemi == "R" else 0) + (li - 1)

    features = {}
    stats = {"sites_total": 0, "sites_dropped": 0, "sources_total": 0,
             "sources_dropped_anchor": 0, "targets_total": 0}
    for stage in ("d0", "d1", "d2", "d3"):
        d = json.loads((EP / f"{stage}-endpoints.json").read_text(encoding="utf-8"))
        for s in d["sources"]:
            sub = s["subject"]
            ses = s["source_id"].split("|")[0]

            def parcels(contacts):
                out = []
                for c in contacts:
                    v = contact_map.get((sub, ses, c))
                    if v is None:
                        return None
                    out.append(idx(*v))
                return out

            sp = parcels(s["source_contacts"])
            stats["sources_total"] += 1
            rec = {}
            anchor_ok = 0
            for t in s["targets"]:
                stats["targets_total"] += 1
                stats["sites_total"] += 1
                tp = parcels(t["contacts"])
                if sp is None or tp is None:
                    stats["sites_dropped"] += 1
                    continue
                pairs = [(p, q) for p in sp for q in tp]
                rec[t["site_id"]] = {
                    "f_sc": float(np.mean([fsc[p, q] for p, q in pairs])),
                    "f_sc_diag0": float(np.mean([fsc_diag0[p, q] for p, q in pairs])),
                    "f_pl": float(np.mean([pl0[p, q] for p, q in pairs])),
                }
                if t["role"] == "anchor":
                    anchor_ok += 1
            if anchor_ok < 4:
                stats["sources_dropped_anchor"] += 1
                rec["__source_dropped__"] = True
            features[f"{sub}|{s['source_id']}|{stage}"] = rec

    FEAT.write_text(json.dumps(features, sort_keys=True), encoding="utf-8")
    receipt = {
        "schema": "ba-stage4-linkage-v1",
        "contract": "paper/검증_원장/BA_STAGE4_해부학_다리_계약.md",
        "zip_sha256": "fcd4f122ad26e897f65b4537012b851b00f832c8ea0c778e19f7d574b022e812",
        "zip_bytes": 132605861,
        "license": "CC BY 4.0 + HCP Open Access terms (EBRAINS descriptor p.1)",
        "ordering_convention": "0-based = 75*(hemi==R) + (a2009s per-hemisphere index - 1)",
        "ordering_evidence": {"intra_inter_ratio": 10.0, "homotopic_ratio": 17.9,
                              "gfrontsup_rows": [15, 90],
                              "precentral_top_partner_scentral": True},
        "label_table_size": len(table),
        "conventions": __doc__,
        "attrition": stats,
        "sc_group_median_sha256": hashlib.sha256(sc.tobytes()).hexdigest(),
        "pl_group_median_sha256": hashlib.sha256(pl.tobytes()).hexdigest(),
        "features_sha256": hashlib.sha256(FEAT.read_bytes()).hexdigest(),
        "responses_read": False,
    }
    OUT.write_text(json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"event": "LINKAGE_COMPLETE", "attrition": stats,
                      "features_sha256": receipt["features_sha256"][:16]}))
    np.save(Path.cwd() / "ba-stage4-fsc.npy", fsc)
    np.save(Path.cwd() / "ba-stage4-pl.npy", pl0)


if __name__ == "__main__":
    main()
