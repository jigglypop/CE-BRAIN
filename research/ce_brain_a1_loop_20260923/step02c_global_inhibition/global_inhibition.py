"""A1 loop step 2c: is there a connectome global-inhibition loop that tames the uniform mode? (CONTRACT.md)

python global_inhibition.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rd = module("ring_dynamics", LOOP / "step01_ring_dynamics/ring_dynamics.py")
sf = module("ring_spectrum_fixed", LOOP / "step02b_ring_spectrum_fixed/ring_spectrum_fixed.py")
BASE = set(rd.TYPES)
GLOM = re.compile(r"_([LR])([1-9])")


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    gm = module("g", rd.MALECNS / "neuron_graph.py")
    graph = gm.load(rd.MALECNS / "neuron_graph_result.json")
    ids, n = graph["node_ids"], len(graph["node_ids"])
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        ann = ipc.open_file(source).read_all()
    with pa.memory_map(str(gm.SOURCE_DIR / "neurotransmitters.feather"), "r") as source:
        nt = ipc.open_file(source).read_all()
    node_type = np.full(n, "", dtype=object)
    node_inst = np.full(n, "", dtype=object)
    pos, found = gm.locate(ann["bodyId"].to_numpy(), ids)
    for p, f, t, s in zip(pos, found, ann["type"].to_pylist(), ann["instance"].to_pylist()):
        if f:
            node_type[p], node_inst[p] = t or "", s or ""
    node_nt = np.full(n, "", dtype=object)
    pos, found = gm.locate(nt["body"].to_numpy(), ids)
    for p, f, c in zip(pos, found, nt["consensus_nt"].to_pylist()):
        if f:
            node_nt[p] = c or ""
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    epg = np.flatnonzero(node_type == "EPG")
    out_epg = np.asarray(A[epg, :].sum(axis=0)).ravel()   # EPG -> x
    in_epg = np.asarray(A[:, epg].sum(axis=1)).ravel()    # x -> EPG
    to_type, from_type, members = defaultdict(float), defaultdict(float), defaultdict(list)
    for v in np.flatnonzero((out_epg > 0) | (in_epg > 0)):
        t = node_type[v]
        if t and t not in BASE:
            to_type[t] += out_epg[v]
            from_type[t] += in_epg[v]
    for v in range(n):
        if node_type[v] in to_type:
            members[node_type[v]].append(v)
    chosen = {}
    for t in to_type:
        if to_type[t] >= 100 and from_type[t] >= 100:
            modal = Counter(node_nt[v] for v in members[t]).most_common(1)[0][0]
            if modal in ("gaba", "glutamate"):
                chosen[t] = {"neurons": len(members[t]), "EPG_to_X": int(to_type[t]), "X_to_EPG": int(from_type[t]), "nt": modal}
    base_nodes = [v for v in range(n) if node_type[v] in BASE]
    extra_nodes = [v for t in chosen for v in members[t]]
    nodes = np.array(sorted(base_nodes + extra_nodes))
    kind = [node_type[v] for v in nodes]
    label = []
    for v in nodes:
        m = GLOM.search(node_inst[v]) if node_type[v] in BASE else None
        label.append((m.group(1), int(m.group(2))) if m else None)
    w = A[nodes, :][:, nodes].toarray().T  # w[post, pre]
    sign = np.array([-1.0 if (k == "Delta7" or k in chosen) else 1.0 for k in kind])
    Wn = (w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :]
    epg_idx = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    angles = np.array([rd.phi(*label[i]) for i in epg_idx])
    res = sf.analyse(Wn, kind, label, epg_idx, angles)
    ratio = res["uniform"]["re"] / res["lead"]["re"]
    g1 = ratio < 1
    g2 = res["S1"] and res["S2"]
    g3 = res["S3"]
    result = {"schema": "ce-a1-step02c-global-inhibition", "code_sha256": code_hash,
              "verdict": "GLOBAL_INHIBITION_LOOP_SUPPORTED" if g1 and g2 and g3 else "GLOBAL_INHIBITION_LOOP_NOT_SUPPORTED",
              "chosen_types": chosen, "neurons_total": len(nodes), "uniform_over_lead_before": 1.2807257034460466,
              "uniform_over_lead_after": ratio, "G1": g1, "G2": g2, "G3": g3, "analysis": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps({k: v for k, v in result.items() if k != "analysis"}, indent=1, default=float))
    print(json.dumps({k: res.get(k) for k in ("lead", "partner", "uniform", "span_cos_sin_R2", "rho_rotation", "report")}, indent=1, default=float))


if __name__ == "__main__":
    main()
