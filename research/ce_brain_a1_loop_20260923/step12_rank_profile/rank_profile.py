"""A1 step 12 (discovery, post hoc): does the CNS compress to a low-rank channel and expand again?

Stages by MaleCNS superclass. For each stage-to-stage synapse matrix M (pre x post), columns are
normalized to input fractions; effective rank = exp(entropy of normalized singular values)
(Roy & Vetterli 2007) and the rank capturing 90% of the squared Frobenius norm are reported next to
the smaller matrix dimension. A degree-preserving shuffle (same row and column sums, via
edge endpoint permutation of the binary pattern with weights carried) gives a null for each matrix.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import svds

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MALECNS = ROOT / "verify/MaleCNS"
STAGES = {
    "sensory_brain": {"ol_sensory", "cb_sensory"},
    "sensory_vnc": {"vnc_sensory", "sensory_ascending", "sensory_descending"},
    "optic_lobe": {"ol_intrinsic"},
    "visual_projection": {"visual_projection", "visual_centrifugal"},
    "central_brain": {"cb_intrinsic"},
    "descending": {"descending_neuron"},
    "ascending": {"ascending_neuron"},
    "vnc": {"vnc_intrinsic"},
    "motor": {"vnc_motor", "cb_motor"},
}
PATHS = [("sensory_brain", "optic_lobe"), ("optic_lobe", "visual_projection"), ("visual_projection", "central_brain"),
         ("central_brain", "descending"), ("descending", "vnc"), ("vnc", "motor"), ("sensory_vnc", "vnc"),
         ("vnc", "ascending"), ("ascending", "central_brain")]


def spectrum(M, k):
    M = M.tocsc().astype(float)
    colsum = np.asarray(M.sum(axis=0)).ravel()
    M = M @ sparse.diags(1 / np.where(colsum > 0, colsum, 1))
    k = min(k, min(M.shape) - 1)
    s = svds(M, k=k, return_singular_vectors=False)
    return np.sort(s)[::-1]


def summaries(s, frob2):
    p = s / s.sum()
    erank = float(np.exp(-np.sum(p * np.log(p + 1e-300))))
    cum = np.cumsum(s ** 2) / frob2
    r90 = int(np.searchsorted(cum, 0.9) + 1) if cum[-1] >= 0.9 else None
    return erank, r90, float(cum[-1])


def main():
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
    idx = {name: np.flatnonzero(np.isin(sc, list(members))) for name, members in STAGES.items()}
    counts = {name: int(len(v)) for name, v in idx.items()}
    print("stage sizes", counts, flush=True)
    rng = np.random.default_rng(20260923)
    out = []
    for a, b in PATHS:
        M = A[idx[a], :][:, idx[b]]
        M = M[:, np.asarray(M.sum(axis=0)).ravel() > 0]
        M = M[np.asarray(M.sum(axis=1)).ravel() > 0, :]
        if min(M.shape) < 3:
            continue
        colsum = np.asarray(M.sum(axis=0)).ravel()
        Mn = M @ sparse.diags(1 / colsum)
        frob2 = float(Mn.multiply(Mn).sum())
        k = min(600, min(M.shape) - 1)
        s = spectrum(M, k)
        erank, r90, covered = summaries(s, frob2)
        # degree-preserving-ish null: permute the post index of every synapse-bearing edge within the matrix
        coo = M.tocoo()
        perm_cols = rng.permutation(coo.col)
        null = sparse.coo_array((coo.data, (coo.row, perm_cols)), shape=M.shape).tocsr()
        null.sum_duplicates()
        s0 = spectrum(null, k)
        erank0, r90_0, _ = summaries(s0, float((null @ sparse.diags(1 / np.where(np.asarray(null.sum(axis=0)).ravel() > 0, np.asarray(null.sum(axis=0)).ravel(), 1))).power(2).sum()))
        row = {"from": a, "to": b, "pre": int(M.shape[0]), "post": int(M.shape[1]), "synapses": int(M.sum()),
               "k_computed": k, "erank": erank, "rank90": r90, "top_k_energy": covered,
               "erank_over_min_dim": erank / min(M.shape), "null_erank": erank0, "null_rank90": r90_0}
        out.append(row)
        print(json.dumps(row), flush=True)
    (HERE / "rank_profile.json").write_text(json.dumps({"stage_sizes": counts, "paths": out}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
