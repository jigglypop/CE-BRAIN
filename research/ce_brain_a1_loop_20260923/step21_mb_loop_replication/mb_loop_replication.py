"""A1 step 21: replicate the step-5 MBON->DAN same-compartment loop enrichment in FlyWire (CONTRACT.md).

Compartments come from a type -> compartment table read off MaleCNS instances (step-5 parser) and are
transferred to FlyWire by type name; FlyWire connectivity is not used to label anything.

python mb_loop_replication.py            full run; refuses unless CONTRACT.md lists this code hash
python mb_loop_replication.py --control  MaleCNS only with the type-table route (pre-freeze, writes nothing)
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
ROOT = HERE.parents[2]
FLYWIRE = ROOT / "data/external/flywire_783"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s5 = load("mbon_dan_loops", LOOP / "step05_mbon_dan_loops/mbon_dan_loops.py")
PERMUTATIONS, SEED = s5.PERMUTATIONS, s5.SEED
LIT_LOOP = ("MBON07", "PAM11")  # MBON-a1 -> PAM-a1 (Ichinose et al. 2015)


def malecns_tables():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    gm = load("g", s5.MALECNS / "neuron_graph.py")
    graph = gm.load(s5.MALECNS / "neuron_graph_result.json")
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    with pa.memory_map(str(gm.SOURCE_DIR / "neurotransmitters.feather"), "r") as source:
        nt = ipc.open_file(source).read_all()
    comp = defaultdict(set)
    for ty, cl, inst in zip(t["type"].to_pylist(), t["class"].to_pylist(), t["instance"].to_pylist()):
        if cl in ("MBON", "DAN") and ty:
            comp[(cl, ty)] |= s5.compartments(inst, ">" if cl == "MBON" else "<")
    return graph, gm, t, nt, {k: v for k, v in comp.items() if v}


def lookup(table, cl, ty):
    parts = [p.strip() for p in (ty or "").split(",") if p.strip()]
    out = set()
    for p in parts:
        out |= table.get((cl, p), set())
    return out


def malecns_neurons(graph, gm, t, nt, table):
    n = len(graph["node_ids"])
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    nt_of = dict(zip(nt["body"].to_pylist(), nt["consensus_nt"].to_pylist()))
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    mbon, dan = [], []
    for p, f, body, cl, ty in zip(pos, found, t["bodyId"].to_pylist(), t["class"].to_pylist(), t["type"].to_pylist()):
        if f and cl in ("MBON", "DAN"):
            c = lookup(table, cl, ty)
            if c:
                (mbon if cl == "MBON" else dan).append((int(p), c, ty, nt_of.get(body) or "unknown"))
    return A, mbon, dan


def flywire_neurons(table):
    import pandas as pd
    import pyarrow.feather as feather
    ann = pd.read_csv(FLYWIRE / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False).drop_duplicates("root_id")
    ann = ann[ann["cell_class"].isin(["MBON", "DAN"])].sort_values("root_id")
    mbon, dan, ids, unmapped = [], [], [], Counter()
    for rid, cl, ty, ntv in zip(ann["root_id"], ann["cell_class"], ann["cell_type"].fillna(""), ann["top_nt"].fillna("unknown")):
        c = lookup(table, cl, ty)
        if not c:
            unmapped[(cl, ty)] += 1
            continue
        (mbon if cl == "MBON" else dan).append((int(rid), c, ty, ntv))
        ids.append(int(rid))
    ids = np.array(sorted(ids), dtype=np.int64)
    e = feather.read_table(FLYWIRE / "proofread_connections_783.feather",
                           columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    out_total = e[e["pre_pt_root_id"].isin([m[0] for m in mbon])]["syn_count"].sum()
    e = e[e["pre_pt_root_id"].isin(ids) & e["post_pt_root_id"].isin(ids)]
    W = np.zeros((len(ids), len(ids)))
    np.add.at(W, (np.searchsorted(ids, e["pre_pt_root_id"].to_numpy(dtype=np.int64)),
                  np.searchsorted(ids, e["post_pt_root_id"].to_numpy(dtype=np.int64))), e["syn_count"].to_numpy(dtype=float))
    at = {r: i for i, r in enumerate(ids)}
    Wmd = W[np.ix_([at[m[0]] for m in mbon], [at[d[0]] for d in dan])]
    return Wmd, float(out_total), mbon, dan, dict(unmapped)


def enrichment(W, mbon, dan, mbon_out_total):
    same = np.array([[s5.overlap(m[1], d[1]) for d in dan] for m in mbon])
    total = W.sum()
    F = float(W[same].sum() / total)
    rng = np.random.default_rng(SEED)
    d_comp = [d[1] for d in dan]
    labels = sorted({frozenset(c) for c in d_comp}, key=lambda s: sorted(s))
    label_of = np.array([labels.index(frozenset(c)) for c in d_comp])
    M_same = np.array([[s5.overlap(m[1], set(lab)) for lab in labels] for m in mbon], dtype=float)
    null = np.array([np.sum(W * M_same[:, label_of[rng.permutation(len(dan))]]) / total for _ in range(PERMUTATIONS)])
    p = (1 + np.sum(null >= F)) / (PERMUTATIONS + 1)
    pair = defaultdict(float)
    by_nt = Counter()
    for i, m in enumerate(mbon):
        for j, d in enumerate(dan):
            if same[i, j] and W[i, j] > 0:
                pair[(m[2], d[2])] += W[i, j]
                by_nt[m[3]] += W[i, j]
    lit = float(sum(W[i, j] for i, m in enumerate(mbon) for j, d in enumerate(dan)
                    if m[2] == LIT_LOOP[0] and d[2] == LIT_LOOP[1]))
    return {"mbon_neurons": len(mbon), "dan_neurons": len(dan), "mbon_to_dan_synapses": int(total),
            "fraction_mbon_output_to_dan": float(total / mbon_out_total), "F_same_compartment": F,
            "null_mean": float(null.mean()), "null_q975": float(np.quantile(null, 0.975)), "p": float(p),
            "F_over_null": float(F / null.mean()), "lit_loop_MBON07_to_PAM11_synapses": lit,
            "loop_synapses_by_mbon_nt": {k: int(v) for k, v in by_nt.items()},
            "pair_loops": {f"{a}->{b}": float(v) for (a, b), v in sorted(pair.items(), key=lambda kv: -kv[1])}}


def main():
    graph, gm, t, nt, table = malecns_tables()
    A, mbon, dan = malecns_neurons(graph, gm, t, nt, table)
    m_idx, d_idx = np.array([m[0] for m in mbon]), np.array([d[0] for d in dan])
    M = enrichment(A[m_idx, :][:, d_idx].toarray(), mbon, dan, float(A[m_idx, :].sum()))
    if "--control" in sys.argv:
        print(json.dumps({k: v for k, v in M.items() if k != "pair_loops"}, indent=1, default=float))
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    Wf, out_f, mbon_f, dan_f, unmapped = flywire_neurons(table)
    F = enrichment(Wf, mbon_f, dan_f, out_f)
    r1 = F["F_same_compartment"] > F["null_q975"] and F["p"] < 0.01
    r2 = F["lit_loop_MBON07_to_PAM11_synapses"] >= 10
    r3 = F["F_over_null"] >= 2
    common = sorted(set(M["pair_loops"]) & set(F["pair_loops"]))
    from scipy.stats import spearmanr
    rho = float(spearmanr([M["pair_loops"][k] for k in common], [F["pair_loops"][k] for k in common]).statistic) if len(common) > 2 else None
    result = {"schema": "ce-a1-step21-mb-loop-replication", "code_sha256": code_hash,
              "R1_enriched": bool(r1), "R2_literature_loop": bool(r2), "R3_effect_size": bool(r3),
              "verdict": "MB_SAME_COMPARTMENT_LOOPS_REPLICATED" if r1 and r2 and r3 else "MB_SAME_COMPARTMENT_LOOPS_NOT_REPLICATED",
              "report_loop_pair_spearman": {"pairs_in_both": len(common), "rho": rho},
              "flywire_unmapped_types": {f"{k[0]}|{k[1]}": v for k, v in unmapped.items()},
              "malecns_type_route": M, "flywire": F}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    brief = lambda d: {k: v for k, v in d.items() if k != "pair_loops"}
    print(json.dumps({"verdict": result["verdict"], "R": [r1, r2, r3], "spearman": result["report_loop_pair_spearman"],
                      "unmapped": result["flywire_unmapped_types"], "malecns": brief(M), "flywire": brief(F),
                      "flywire_top_loops": list(F["pair_loops"].items())[:12]}, indent=1, default=float))


if __name__ == "__main__":
    main()
