"""A1 step 18: replicate the step-2c global-inhibition result in FlyWire, label-free (CONTRACT.md).

Same selection rule as 2c (EPG loop >= 100 synapses both ways, modal NT gaba/glutamate) applied to
MaleCNS (consensus_nt) and FlyWire (top_nt); the expanded operator is judged with the step-17
label-free definitions (isolated degenerate pair, circle, soma-side Gamma).

python gi_replication.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
ROOT = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lf = load("label_free_ring", LOOP / "step17_label_free_ring/label_free_ring.py")
BASE = set(lf.TYPES)


def malecns():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    gm = load("g", lf.MALECNS / "neuron_graph.py")
    graph = gm.load(lf.MALECNS / "neuron_graph_result.json")
    n = len(graph["node_ids"])
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        ann = ipc.open_file(source).read_all()
    with pa.memory_map(str(gm.SOURCE_DIR / "neurotransmitters.feather"), "r") as source:
        nt = ipc.open_file(source).read_all()
    node_type, node_side, node_nt = (np.full(n, "", dtype=object) for _ in range(3))
    pos, found = gm.locate(ann["bodyId"].to_numpy(), graph["node_ids"])
    for p, f, t, s in zip(pos, found, ann["type"].to_pylist(), ann["somaSide"].to_pylist()):
        if f:
            node_type[p], node_side[p] = t or "", {"L": "left", "R": "right"}.get(s, "")
    pos, found = gm.locate(nt["body"].to_numpy(), graph["node_ids"])
    for p, f, c in zip(pos, found, nt["consensus_nt"].to_pylist()):
        if f:
            node_nt[p] = c or ""
    return A, node_type, node_side, node_nt


def flywire():
    import pandas as pd
    import pyarrow.feather as feather
    ann = pd.read_csv(lf.FLYWIRE / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False).drop_duplicates("root_id")
    ids = np.sort(ann["root_id"].to_numpy(dtype=np.int64))
    ann = ann.set_index("root_id").loc[ids]
    e = feather.read_table(lf.FLYWIRE / "proofread_connections_783.feather",
                           columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    pre = np.searchsorted(ids, e["pre_pt_root_id"].to_numpy(dtype=np.int64))
    post = np.searchsorted(ids, e["post_pt_root_id"].to_numpy(dtype=np.int64))
    ok = (pre < len(ids)) & (post < len(ids))
    ok[ok] &= (ids[pre[ok]] == e["pre_pt_root_id"].to_numpy()[ok]) & (ids[post[ok]] == e["post_pt_root_id"].to_numpy()[ok])
    n = len(ids)
    A = sparse.csr_array((e["syn_count"].to_numpy(dtype=float)[ok], (pre[ok], post[ok])), shape=(n, n))
    A.sum_duplicates()
    side = np.array([s if s in ("left", "right") else "" for s in ann["side"].fillna("")], dtype=object)
    return A, ann["cell_type"].fillna("").to_numpy(dtype=object), side, ann["top_nt"].fillna("").to_numpy(dtype=object)


def select(A, node_type, node_nt):
    """Step-2c rule, verbatim."""
    epg = np.flatnonzero(node_type == "EPG")
    out_epg = np.asarray(A[epg, :].sum(axis=0)).ravel()
    in_epg = np.asarray(A.T.tocsr()[epg, :].sum(axis=0)).ravel()
    to_type, from_type, members = defaultdict(float), defaultdict(float), defaultdict(list)
    for v in np.flatnonzero((out_epg > 0) | (in_epg > 0)):
        t = node_type[v]
        if t and t not in BASE:
            to_type[t] += out_epg[v]
            from_type[t] += in_epg[v]
    for v in range(len(node_type)):
        if node_type[v] in to_type:
            members[node_type[v]].append(v)
    chosen = {}
    for t in to_type:
        if to_type[t] >= 100 and from_type[t] >= 100:
            modal = Counter(node_nt[v] for v in members[t]).most_common(1)[0][0]
            if modal in ("gaba", "glutamate"):
                chosen[t] = {"neurons": len(members[t]), "EPG_to_X": int(to_type[t]), "X_to_EPG": int(from_type[t]), "nt": modal}
    return chosen, members


def evaluate(A, node_type, node_side, chosen, members, flip=False):
    base = [v for v in range(len(node_type)) if node_type[v] in BASE]
    nodes = np.array(sorted(base + [v for t in chosen for v in members[t]]))
    kind = [node_type[v] for v in nodes]
    side = [node_side[v] for v in nodes]
    w = A[nodes, :][:, nodes].toarray().T  # w[post, pre]
    inhib = {"Delta7"} | (set() if flip else set(chosen))
    sign = np.array([-1.0 if k in inhib else 1.0 for k in kind])
    W = (w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :]
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    res, theta, B, dual_src = lf.ring_pair(W, epg)
    u1, u2 = lf.u1u2(res)
    dual = dual_src @ np.linalg.inv(B.T @ dual_src)
    gamma = np.array([(1.0 if s == "left" else -1.0 if s == "right" else 0.0) if k.startswith("PEN") else 0.0
                      for k, s in zip(kind, side)])
    Q = dual.T @ (gamma[:, None] * W) @ B
    rho = float(np.linalg.norm((Q - Q.T) / 2) / np.linalg.norm(Q)) if np.linalg.norm(Q) > 0 else 0.0
    es = np.array([side[i] for i in epg])
    fold = {s: {"max_gap_deg": lf.max_gap(theta[es == s]), "resultant": float(abs(np.mean(np.exp(1j * theta[es == s]))))}
            for s in ("left", "right")}
    ratio = res["uniform_over_lead"]
    return {"neurons_total": int(len(nodes)), **res, "U1_pair": u1, "U2_circle": u2, "rho": rho,
            "G1_uniform_suppressed": bool(ratio is not None and ratio < 1), "G2_memory_pair": bool(u1 and u2),
            "G3_rotation": bool(rho >= 0.7), "report_fold": fold, "Q": Q.tolist()}


def run(name, A, node_type, node_side, node_nt):
    chosen, members = select(A, node_type, node_nt)
    main_res = evaluate(A, node_type, node_side, chosen, members)
    flip = evaluate(A, node_type, node_side, chosen, members, flip=True)
    out = {"chosen_types": chosen, "expanded": main_res,
           "report_sign_flip_control_uniform_over_lead": flip["uniform_over_lead"],
           "pass": main_res["G1_uniform_suppressed"] and main_res["G2_memory_pair"] and main_res["G3_rotation"]}
    print(name, json.dumps({"chosen": {k: (v["neurons"], v["X_to_EPG"], v["nt"]) for k, v in sorted(chosen.items())},
                            **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in main_res.items() if k != "Q"},
                            "flip_ratio": flip["uniform_over_lead"]}, indent=1, default=float), flush=True)
    return out


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    s17 = json.loads((LOOP / "step17_label_free_ring/results.json").read_text(encoding="utf-8"))
    M = run("malecns", *malecns())
    F = run("flywire", *flywire())
    a, b = set(M["chosen_types"]), set(F["chosen_types"])
    verdict = ("GLOBAL_INHIBITION_REPLICATED" if M["pass"] and F["pass"] else
               "METHOD_CONTROL_FAILED" if not M["pass"] else "GLOBAL_INHIBITION_NOT_REPLICATED")
    result = {"schema": "ce-a1-step18-global-inhibition-replication", "code_sha256": code_hash, "verdict": verdict,
              "uniform_over_lead_before": {"malecns": s17["malecns"]["uniform_over_lead"], "flywire": s17["flywire"]["uniform_over_lead"]},
              "chosen_type_overlap": {"both": sorted(a & b), "malecns_only": sorted(a - b), "flywire_only": sorted(b - a),
                                      "jaccard": len(a & b) / len(a | b) if a | b else None},
              "malecns": M, "flywire": F}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print(json.dumps({k: result[k] for k in ("verdict", "uniform_over_lead_before", "chosen_type_overlap")}, indent=1, default=float))


if __name__ == "__main__":
    main()
