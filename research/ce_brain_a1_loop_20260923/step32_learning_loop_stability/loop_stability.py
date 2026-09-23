"""A1 step 32: does the rewrite-loop gain of an MB compartment predict how long its memory lasts? (CONTRACT.md)

Learning term candidate: g_ij' = -eta_c d_c(t) x_i x_j with d_c = d_ext + kappa_c * MBON_c output. kappa_c = fraction of
the compartment's DAN input that comes from MBONs of the same compartment. Literature targets: Aso & Rubin 2016 eLife
Fig 3B (1-day / immediate memory ratio, read from the published plot) for five DAN driver groups.

python loop_stability.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s5 = load("mbon_dan_loops", LOOP / "step05_mbon_dan_loops/mbon_dan_loops.py")
s21 = load("mb_loop_replication", LOOP / "step21_mb_loop_replication/mb_loop_replication.py")
GROUPS = {  # Aso & Rubin 2016 driver groups -> DAN type prefixes
    "G1_gamma1pedc_MB320C": ("PPL101",),
    "G2_a2a2_g2a1_MB099C": ("PPL103", "PPL105"),
    "G3_alpha1_MB043C": ("PAM11",),
    "G4_beta1_beta2_MB213B": ("PAM04", "PAM10"),
    "G5_gamma5_bp2a_MB315C_MB109B": ("PAM01", "PAM02"),
}
SENSITIVITY_G4 = ("PAM04", "PAM09", "PAM10")
RETENTION = {"G1_gamma1pedc_MB320C": 0.17, "G2_a2a2_g2a1_MB099C": 0.35, "G3_alpha1_MB043C": 0.60,
             "G4_beta1_beta2_MB213B": 0.67, "G5_gamma5_bp2a_MB315C_MB109B": 0.17}
FLEXIBILITY = {"G1_gamma1pedc_MB320C": 0.85, "G2_a2a2_g2a1_MB099C": 1.05, "G3_alpha1_MB043C": 0.35,
               "G4_beta1_beta2_MB213B": 0.55, "G5_gamma5_bp2a_MB315C_MB109B": 1.30}
RESISTANCE = {"G1_gamma1pedc_MB320C": 0.35, "G2_a2a2_g2a1_MB099C": 0.40, "G3_alpha1_MB043C": 0.95,
              "G4_beta1_beta2_MB213B": 0.30, "G5_gamma5_bp2a_MB315C_MB109B": 0.10}


def norm(c):
    return (c - {"B'2"}) | {"B'2a", "B'2m", "B'2p"} if "B'2" in c else c


def prefix(t):
    return (t or "").split("_")[0].split(",")[0]


def kappa(in_dan, mbon_to_dan, dan_types, mbon_comp, dan_comp, groups):
    """in_dan: dict dan -> total input synapses; mbon_to_dan: dict (mbon, dan) -> synapses."""
    out = {}
    for g, prefixes in groups.items():
        D = [d for d, t in dan_types.items() if prefix(t) in prefixes]
        comps = set().union(*[dan_comp[d] for d in D]) if D else set()
        tot = sum(in_dan.get(d, 0.0) for d in D)
        same = sum(w for (m, d), w in mbon_to_dan.items() if d in D and s5.overlap(mbon_comp[m], comps))
        any_mbon = sum(w for (m, d), w in mbon_to_dan.items() if d in D)
        out[g] = {"dan_neurons": len(D), "compartments": sorted(comps), "dan_input_synapses": tot,
                  "same_compartment_mbon_synapses": same, "kappa": same / tot if tot else None,
                  "kappa_any_mbon": any_mbon / tot if tot else None}
    return out


def malecns():
    graph, gm, t, nt, table = s21.malecns_tables()
    A, mbon, dan = s21.malecns_neurons(graph, gm, t, nt, table)
    m_idx = np.array([m[0] for m in mbon]); d_idx = np.array([d[0] for d in dan])
    W = A[m_idx, :][:, d_idx].toarray()
    tot = np.asarray(A[:, d_idx].sum(axis=0)).ravel()
    return ({d[0]: float(x) for d, x in zip(dan, tot)},
            {(mbon[i][0], dan[j][0]): float(W[i, j]) for i, j in zip(*np.nonzero(W))},
            {d[0]: d[2] for d in dan}, {m[0]: norm(m[1]) for m in mbon}, {d[0]: norm(d[1]) for d in dan})


def flywire():
    import pandas as pd
    import pyarrow.feather as feather
    graph, gm, t, nt, table = s21.malecns_tables()
    ann = pd.read_csv(s21.FLYWIRE / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False).drop_duplicates("root_id")
    ann = ann[ann["cell_class"].isin(["MBON", "DAN"])]
    mbon, dan = {}, {}
    for rid, cl, ty in zip(ann["root_id"], ann["cell_class"], ann["cell_type"].fillna("")):
        c = s21.lookup(table, cl, ty)
        if c:
            (mbon if cl == "MBON" else dan)[int(rid)] = (ty, norm(c))
    e = feather.read_table(s21.FLYWIRE / "proofread_connections_783.feather", columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    e = e[e["post_pt_root_id"].isin(dan.keys())]
    tot = e.groupby("post_pt_root_id")["syn_count"].sum().to_dict()
    md = e[e["pre_pt_root_id"].isin(mbon.keys())].groupby(["pre_pt_root_id", "post_pt_root_id"])["syn_count"].sum().to_dict()
    return ({int(k): float(v) for k, v in tot.items()}, {(int(a), int(b)): float(v) for (a, b), v in md.items()},
            {d: v[0] for d, v in dan.items()}, {m: v[1] for m, v in mbon.items()}, {d: v[1] for d, v in dan.items()})


def hemibrain():
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    A, ty, inst, sd, nt = h22.hemibrain()
    mb_re, dan_re = re.compile(r"^MBON\d"), re.compile(r"^(PAM|PPL1)\d")
    mbon = {v: norm(s5.compartments(inst[v], ">")) for v in range(len(ty)) if mb_re.match(ty[v])}
    dan = {v: norm(s5.compartments(inst[v], "<")) for v in range(len(ty)) if dan_re.match(ty[v])}
    mbon = {k: c for k, c in mbon.items() if c}
    dan = {k: c for k, c in dan.items() if c}
    d_idx = np.array(sorted(dan)); m_idx = np.array(sorted(mbon))
    tot = np.asarray(A[:, d_idx].sum(axis=0)).ravel()
    W = A[m_idx, :][:, d_idx].toarray()
    return ({int(d): float(x) for d, x in zip(d_idx, tot)}, {(int(m_idx[i]), int(d_idx[j])): float(W[i, j]) for i, j in zip(*np.nonzero(W))},
            {int(d): ty[d] for d in d_idx}, mbon, dan)


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    res = {}
    names = list(GROUPS)
    for name, fn in (("malecns", malecns), ("flywire", flywire), ("hemibrain", hemibrain)):
        in_dan, md, dt, mc, dc = fn()
        k = kappa(in_dan, md, dt, mc, dc, GROUPS)
        ks = kappa(in_dan, md, dt, mc, dc, {**GROUPS, "G4_beta1_beta2_MB213B": SENSITIVITY_G4})
        kv = np.array([k[g]["kappa"] for g in names])
        k1 = min(k["G3_alpha1_MB043C"]["kappa"], k["G4_beta1_beta2_MB213B"]["kappa"]) > max(k["G1_gamma1pedc_MB320C"]["kappa"], k["G5_gamma5_bp2a_MB315C_MB109B"]["kappa"])
        rho = float(spearmanr(kv, [RETENTION[g] for g in names]).statistic)
        res[name] = {"groups": k, "K1_stable_above_unstable": bool(k1), "K2_spearman_retention": rho, "K2": bool(rho >= 0.8),
                     "report_spearman_flexibility": float(spearmanr(kv, [FLEXIBILITY[g] for g in names]).statistic),
                     "report_spearman_dan_alone_resistance": float(spearmanr(kv, [RESISTANCE[g] for g in names]).statistic),
                     "report_spearman_retention_any_mbon": float(spearmanr([k[g]["kappa_any_mbon"] for g in names], [RETENTION[g] for g in names]).statistic),
                     "report_sensitivity_G4_with_PAM09": {"kappa_G4": ks["G4_beta1_beta2_MB213B"]["kappa"],
                                                          "spearman_retention": float(spearmanr([ks[g]["kappa"] for g in names], [RETENTION[g] for g in names]).statistic)}}
    ok = all(r["K1_stable_above_unstable"] and r["K2"] for r in res.values())
    result = {"schema": "ce-a1-step32-learning-loop-stability", "code_sha256": code_hash,
              "verdict": "REWRITE_LOOP_PREDICTS_MEMORY_STABILITY" if ok else "REWRITE_LOOP_DOES_NOT_PREDICT_STABILITY",
              "literature_retention": RETENTION, "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"])
    for n, r in res.items():
        print("==", n, "K1", r["K1_stable_above_unstable"], "rho %.3f" % r["K2_spearman_retention"],
              "flex %.2f resist %.2f anyMBON %.2f" % (r["report_spearman_flexibility"], r["report_spearman_dan_alone_resistance"], r["report_spearman_retention_any_mbon"]),
              "sensG4", {a: round(b, 3) for a, b in r["report_sensitivity_G4_with_PAM09"].items()})
        for g in names:
            x = r["groups"][g]
            print("   ", g, "DAN", x["dan_neurons"], x["compartments"], "kappa %.4f (any MBON %.4f)" % (x["kappa"], x["kappa_any_mbon"]),
                  "retention", RETENTION[g])


if __name__ == "__main__":
    main()
