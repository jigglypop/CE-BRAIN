"""A1 loop step 5: are MBON->DAN synapses enriched for same-compartment loops? (CONTRACT.md)

python mbon_dan_loops.py    refuses to run unless CONTRACT.md lists this code hash
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
ROOT = HERE.parents[2]
MALECNS = ROOT / "verify/MaleCNS"
TOKEN = re.compile(r"B'[12][amp]*|B[12]|a'[1-3]|a[1-3]|y[1-5]|pedc?")
PERMUTATIONS, SEED = 10000, 20260923


def compartments(instance, split_char):
    m = re.search(r"\(([^)]*)\)", instance or "")
    if not m:
        return set()
    body = m.group(1).split(split_char)[0]
    out = set()
    for tok in TOKEN.findall(body):
        if tok.startswith("B'2") and len(tok) > 3:
            out.update("B'2" + c for c in tok[3:])
        elif tok.startswith("ped"):
            out.add("ped")
        else:
            out.add(tok)
    return out


def overlap(a, b):
    if a & b:
        return True
    expand = lambda s: {x for x in s if x.startswith("B'2")}
    return ("B'2" in a and expand(b)) or ("B'2" in b and expand(a))


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
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    with pa.memory_map(str(gm.SOURCE_DIR / "neurotransmitters.feather"), "r") as source:
        nt = ipc.open_file(source).read_all()
    nt_of = dict(zip(nt["body"].to_pylist(), nt["consensus_nt"].to_pylist()))
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    mbon, dan = [], []
    for p, f, body, cl, inst in zip(pos, found, t["bodyId"].to_pylist(), t["class"].to_pylist(), t["instance"].to_pylist()):
        if not f:
            continue
        if cl == "MBON":
            c = compartments(inst, ">")
            if c:
                mbon.append((int(p), c, inst, nt_of.get(body) or "unknown"))
        elif cl == "DAN":
            c = compartments(inst, "<")
            if c:
                dan.append((int(p), c, inst))
    m_idx = np.array([m[0] for m in mbon])
    d_idx = np.array([d[0] for d in dan])
    W = A[m_idx, :][:, d_idx].toarray()                       # MBON x DAN synapses
    mbon_out_total = float(A[m_idx, :].sum())
    same = np.array([[overlap(m[1], d[1]) for d in dan] for m in mbon])
    total = W.sum()
    F = float(W[same].sum() / total)
    rng = np.random.default_rng(SEED)
    d_comp = [d[1] for d in dan]
    null = np.empty(PERMUTATIONS)
    # vectorised permutation: same-compartment indicator depends only on the DAN label assignment
    labels = sorted({frozenset(c) for c in d_comp}, key=lambda s: sorted(s))
    label_of = np.array([labels.index(frozenset(c)) for c in d_comp])
    M_same = np.array([[overlap(m[1], set(lab)) for lab in labels] for m in mbon], dtype=float)  # MBON x label
    for k in range(PERMUTATIONS):
        perm_labels = label_of[rng.permutation(len(dan))]
        null[k] = float(np.sum(W * M_same[:, perm_labels]) / total)
    p = (1 + np.sum(null >= F)) / (PERMUTATIONS + 1)
    q975 = float(np.quantile(null, 0.975))
    loops = []
    for i, m in enumerate(mbon):
        for j, d in enumerate(dan):
            if same[i, j] and W[i, j] > 0:
                loops.append((W[i, j], m[2], d[2], m[3]))
    top = defaultdict(float)
    for w, mi, di, _ in loops:
        top[(mi.split("_")[0], di.split("_")[0])] += w
    by_nt = Counter()
    for w, _, _, ntv in loops:
        by_nt[ntv] += w
    result = {"schema": "ce-a1-step05-mbon-dan-loops", "code_sha256": code_hash,
              "mbon_neurons": len(mbon), "dan_neurons": len(dan), "mbon_to_dan_synapses": int(total),
              "fraction_mbon_output_to_dan": float(total / mbon_out_total),
              "F_same_compartment": F, "null_mean": float(null.mean()), "null_q975": q975, "p": float(p),
              "L1": bool(F > q975 and p < 0.01),
              "same_compartment_loop_synapses_by_mbon_nt": {k: int(v) for k, v in by_nt.items()},
              "top_same_compartment_loops": [{"mbon": k[0], "dan": k[1], "synapses": int(v)}
                                             for k, v in sorted(top.items(), key=lambda kv: -kv[1])[:15]]}
    result["verdict"] = "SAME_COMPARTMENT_LOOPS_ENRICHED" if result["L1"] else "SAME_COMPARTMENT_LOOPS_NOT_ENRICHED"
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
