"""A1 step 24: psi law -- PEN rotation angle = phasor sum of PB (shifted) and EB (unshifted) input routes (CONTRACT.md).

The step-23 route matrix Q^s_1 = dual^T (Gamma_s W) B is split by the ROI where the synapses onto PEN sit
(W_r = W * w_r / w, r in PB, EB, other). Three individuals; E1 angles for MaleCNS/hemibrain, label-free
theta for FlyWire.

python psi_law.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
ROOT = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


iso = load("isometry", LOOP / "step23_isometry_generator/isometry.py")
lf = iso.lf
ROIS = ("PB", "EB")
PB_RANGE, EB_MAX, OPP_MAX = (35.0, 75.0), 15.0, 20.0


def malecns():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    gm = load("g", lf.MALECNS / "neuron_graph.py")
    rm = load("r", lf.MALECNS / "neuron_roi.py")
    graph = gm.load(lf.MALECNS / "neuron_graph_result.json")
    roi = rm.load(lf.MALECNS / "neuron_roi_result.json")
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    ty, soma, inst = t["type"].to_pylist(), t["somaSide"].to_pylist(), t["instance"].to_pylist()
    rows = sorted((int(pos[i]), ty[i], soma[i], lf.GLOM.search(inst[i] or "")) for i in np.flatnonzero(found) if ty[i] in lf.TYPES)
    nodes = np.array([r[0] for r in rows])
    kind = [r[1] for r in rows]
    side = [{"L": "left", "R": "right"}.get(r[2], "") for r in rows]
    label = [(r[3].group(1), int(r[3].group(2))) if r[3] else None for r in rows]
    n, width = roi["node_count"], len(roi["roi_names"])
    local = np.full(n, -1, dtype=np.int64)
    local[nodes] = np.arange(len(nodes))
    dyad = roi["key"] // width
    pre, post = local[dyad // n], local[dyad % n]
    keep = (pre >= 0) & (post >= 0)
    r_idx = (roi["key"][keep] % width).astype(np.int64)
    names = np.array(roi["roi_names"])
    w = np.zeros((len(nodes), len(nodes)))
    np.add.at(w, (post[keep], pre[keep]), roi["count"][keep].astype(float))
    split = {}
    for r in ROIS:
        sel = names[r_idx] == r
        m = np.zeros_like(w)
        np.add.at(m, (post[keep][sel], pre[keep][sel]), roi["count"][keep][sel].astype(float))
        split[r] = m
    w_ref, *_ = lf.malecns()
    if not np.array_equal(w, w_ref):
        raise ValueError("ROI-summed MaleCNS matrix differs from the step-17 matrix")
    return w, split, kind, side, label


def flywire():
    import pandas as pd
    import pyarrow.feather as feather
    ann = pd.read_csv(lf.FLYWIRE / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False).drop_duplicates("root_id")
    ann = ann[ann["cell_type"].isin(lf.TYPES)].sort_values("root_id")
    ids = ann["root_id"].to_numpy(dtype=np.int64)
    e = feather.read_table(lf.FLYWIRE / "proofread_connections_783.feather",
                           columns=["pre_pt_root_id", "post_pt_root_id", "neuropil", "syn_count"]).to_pandas()
    e = e[e["pre_pt_root_id"].isin(ids) & e["post_pt_root_id"].isin(ids)]
    post = np.searchsorted(ids, e["post_pt_root_id"].to_numpy(dtype=np.int64))
    pre = np.searchsorted(ids, e["pre_pt_root_id"].to_numpy(dtype=np.int64))
    c = e["syn_count"].to_numpy(dtype=float)
    w = np.zeros((len(ids), len(ids)))
    np.add.at(w, (post, pre), c)
    split = {}
    for r in ROIS:
        sel = (e["neuropil"] == r).to_numpy()
        m = np.zeros_like(w)
        np.add.at(m, (post[sel], pre[sel]), c[sel])
        split[r] = m
    w_ref, kind, side, label = lf.flywire()
    if not np.array_equal(w, w_ref):
        raise ValueError("neuropil-summed FlyWire matrix differs from the step-17 matrix")
    return w, split, kind, side, label


def hemibrain():
    import pandas as pd
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    A, ty, inst, sd, nt = h22.hemibrain()
    base = np.array([v for v in range(len(ty)) if ty[v] in lf.TYPES])
    w = h22.sub(A, base)
    neu = pd.read_csv(h22.HB / "exported-traced-adjacencies-v1.2/traced-neurons.csv").drop_duplicates("bodyId").sort_values("bodyId")
    ids = neu["bodyId"].to_numpy(dtype=np.int64)[base]
    rc = pd.read_csv(h22.HB / "exported-traced-adjacencies-v1.2/traced-roi-connections.csv")
    rc = rc[rc["bodyId_pre"].isin(ids) & rc["bodyId_post"].isin(ids)]
    split = {}
    for r in ROIS:
        s = rc[rc["roi"] == r]
        m = np.zeros_like(w)
        np.add.at(m, (np.searchsorted(ids, s["bodyId_post"].to_numpy()), np.searchsorted(ids, s["bodyId_pre"].to_numpy())),
                  s["weight"].to_numpy(dtype=float))
        split[r] = m
    if np.any(split["PB"] + split["EB"] > w + 1e-9):
        raise ValueError("hemibrain ROI counts exceed total counts")
    label = [(lambda m: (m.group(1), int(m.group(2))) if m else None)(h22.GLOM.search(inst[v])) for v in base]
    return w, split, [ty[v] for v in base], [sd[v] for v in base], label


def analyse(w, split, kind, side, label):
    W = lf.operator(w, kind)
    frac = {r: np.divide(split[r], w, out=np.zeros_like(w), where=w > 0) for r in ROIS}
    frac["other"] = np.where(w > 0, 1 - frac["PB"] - frac["EB"], 0.0)
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    if all(label[i] for i in epg):
        ang, basis = np.array([lf.phi(*label[i]) for i in epg]), "E1_labels"
    else:
        ang, basis = lf.ring_pair(W, epg)[1], "label_free"
    lam, left, right = eig(W, left=True, right=True)
    info, B, dual = iso.harmonic_pair(lam, left, right, epg, ang, 1)
    out = {"basis": basis, "pair": info, "sides": {}}
    for s in ("left", "right"):
        g = np.array([1.0 if k.startswith("PEN") and sd == s else 0.0 for k, sd in zip(kind, side)])
        total = iso.route(dual.T @ (g[:, None] * W) @ B)
        parts = {r: iso.route(dual.T @ (g[:, None] * W * frac[r]) @ B) for r in ("PB", "EB", "other")}
        pen_rows = g > 0
        share = {r: float((w[pen_rows] * frac[r][pen_rows]).sum() / w[pen_rows].sum()) for r in ("PB", "EB", "other")}
        out["sides"][s] = {"total": total, "by_roi": parts, "input_synapse_share": share}
    L, R = out["sides"]["left"]["by_roi"], out["sides"]["right"]["by_roi"]
    p1 = (all(PB_RANGE[0] <= abs(x["PB"]["angle_deg"]) <= PB_RANGE[1] for x in (L, R))
          and abs(iso.wrapd(L["PB"]["angle_deg"] + R["PB"]["angle_deg"])) <= OPP_MAX)
    p2 = all(abs(x["EB"]["angle_deg"]) <= EB_MAX for x in (L, R))
    out.update({"P1_PB_shifted": bool(p1), "P2_EB_unshifted": bool(p2)})
    return out


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    res = {name: analyse(*loader()) for name, loader in (("malecns", malecns), ("flywire", flywire), ("hemibrain", hemibrain))}
    ok = all(d["P1_PB_shifted"] and d["P2_EB_unshifted"] for d in res.values())
    result = {"schema": "ce-a1-step24-psi-law", "code_sha256": code_hash,
              "verdict": "PSI_LAW_SUPPORTED_THREE_INDIVIDUALS" if ok else "PSI_LAW_NOT_SUPPORTED", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"])
    for n, d in res.items():
        print("==", n, d["basis"], "P1", d["P1_PB_shifted"], "P2", d["P2_EB_unshifted"])
        for s, x in d["sides"].items():
            print("  ", s, "total", round(x["total"]["angle_deg"], 1), round(x["total"]["gain"], 4),
                  {r: (round(v["angle_deg"], 1), round(v["gain"], 4), round(v["conformal_fraction"], 3)) for r, v in x["by_roi"].items()},
                  "syn share", {r: round(v, 3) for r, v in x["input_synapse_share"].items()})


if __name__ == "__main__":
    main()
