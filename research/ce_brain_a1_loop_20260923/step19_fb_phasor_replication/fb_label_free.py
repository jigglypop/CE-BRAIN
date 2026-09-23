"""A1 step 19: label-free, coordinate-free FB four-phasor geometry in MaleCNS and FlyWire (CONTRACT.md).

Heading phase of each PFN = its PB input projected on the step-17 label-free ring pair. Relative
offsets of the four PFN groups (d/v x soma side) = within-hDeltaB comparison of the input phase each
group delivers (the FB coordinate cancels). Geometry test = step-10 C2' (gaps 90+-30, d/v centres 180+-30).

python fb_label_free.py            full run; refuses unless CONTRACT.md lists this code hash
python fb_label_free.py --control  MaleCNS method control only (pre-freeze calibration, writes nothing)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lf = load("label_free_ring", LOOP / "step17_label_free_ring/label_free_ring.py")
PFN_TYPES, HDB = ("PFNd", "PFNv"), "hDeltaB"
GROUPS = ("dL", "dR", "vL", "vR")
PFN_INST = re.compile(r"^(PFNd|PFNv)\(PB0[45]\)_([LR])([1-9])_C\d+$")
SEED, N_NULL = 20260923, 200


def wrap(a):
    return np.angle(np.exp(1j * a))


def malecns():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    gm = load("g", lf.MALECNS / "neuron_graph.py")
    graph = gm.load(lf.MALECNS / "neuron_graph_result.json")
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    want = set(lf.TYPES) | set(PFN_TYPES) | {HDB}
    ty, soma, inst = t["type"].to_pylist(), t["somaSide"].to_pylist(), t["instance"].to_pylist()
    rows = sorted((int(pos[i]), ty[i], {"L": "left", "R": "right"}.get(soma[i], ""), inst[i] or "")
                  for i in np.flatnonzero(found) if ty[i] in want)
    nodes = [r[0] for r in rows]
    w = lf.submatrix(graph["indptr"], graph["indices"], graph["weight"], nodes)
    return w, [r[1] for r in rows], [r[2] for r in rows], [r[3] for r in rows]


def flywire():
    import pandas as pd
    import pyarrow.feather as feather
    ann = pd.read_csv(lf.FLYWIRE / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False).drop_duplicates("root_id")
    ann = ann[ann["cell_type"].isin(set(lf.TYPES) | set(PFN_TYPES) | {HDB})].sort_values("root_id")
    ids = ann["root_id"].to_numpy(dtype=np.int64)
    e = feather.read_table(lf.FLYWIRE / "proofread_connections_783.feather",
                           columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    e = e[e["pre_pt_root_id"].isin(ids) & e["post_pt_root_id"].isin(ids)]
    w = np.zeros((len(ids), len(ids)))
    np.add.at(w, (np.searchsorted(ids, e["post_pt_root_id"].to_numpy(dtype=np.int64)),
                  np.searchsorted(ids, e["pre_pt_root_id"].to_numpy(dtype=np.int64))), e["syn_count"].to_numpy(dtype=float))
    side = [s if s in ("left", "right") else "" for s in ann["side"].fillna("")]
    return w, list(ann["cell_type"]), side, [""] * len(ids)


def offsets(beta, m, gidx):
    """Joint circular fit beta[j,k] = c_j - O_k (weights m); gauge O_dL = 0."""
    O = np.zeros(len(GROUPS))
    for _ in range(200):
        c = np.angle(np.sum(m * np.exp(1j * (beta + O[None, :])), axis=1))
        O = np.angle(np.sum(m * np.exp(1j * (c[:, None] - beta)), axis=0))
    O = wrap(O - O[0])
    c = np.angle(np.sum(m * np.exp(1j * (beta + O[None, :])), axis=1))
    consistency = np.abs(np.sum(m * np.exp(1j * (c[:, None] - beta - O[None, :])), axis=0)) / np.maximum(m.sum(axis=0), 1e-12)
    return O, consistency


def geometry(O):
    deg = np.mod(np.degrees(O), 360)
    ordered = np.sort(deg)
    gaps = np.diff(np.r_[ordered, ordered[0] + 360])
    d_c = np.angle(np.exp(1j * O[0]) + np.exp(1j * O[1]))
    v_c = np.angle(np.exp(1j * O[2]) + np.exp(1j * O[3]))
    diff = float(np.degrees(abs(wrap(d_c - v_c))))
    return {"offsets_deg": {g: float(np.degrees(o)) for g, o in zip(GROUPS, O)}, "gaps_deg": gaps.tolist(),
            "d_v_center_difference_deg": diff,
            "within_pair_sep_deg": {"d": float(np.degrees(abs(wrap(O[0] - O[1])))), "v": float(np.degrees(abs(wrap(O[2] - O[3]))))},
            "pass": bool(np.all(np.abs(gaps - 90) <= 30) and abs(diff - 180) <= 30)}


def analyse(w, kind, side, inst, rng):
    base = np.array([i for i, k in enumerate(kind) if k in lf.TYPES])
    pfn = np.array([i for i, k in enumerate(kind) if k in PFN_TYPES and side[i]])
    hdb = np.array([i for i, k in enumerate(kind) if k == HDB])
    kb = [kind[i] for i in base]
    W = lf.operator(w[np.ix_(base, base)], kb)
    epg = np.array([i for i, k in enumerate(kb) if k == "EPG"])
    res, theta, B, _ = lf.ring_pair(W, epg)
    z = (B[:, 0] + 1j * B[:, 1]) * np.array([-1.0 if k == "Delta7" else 1.0 for k in kb])
    w_in = w[np.ix_(pfn, base)]
    S = w_in @ z
    alpha = np.angle(S)
    coherence = np.abs(S) / np.maximum(w_in @ np.abs(z), 1e-12)
    gidx = np.array([GROUPS.index(kind[i][-1] + side[i][0].upper()) for i in pfn])
    Wph = w[np.ix_(hdb, pfn)]  # hDeltaB (post) x PFN (pre)

    def fit(a):
        V = np.stack([Wph[:, gidx == k] @ np.exp(1j * a[gidx == k]) for k in range(len(GROUPS))], axis=1)
        return offsets(np.angle(V), np.abs(V), gidx)
    O, cons = fit(alpha)
    geo = geometry(O)
    null_pass = 0
    for _ in range(N_NULL):
        a = alpha.copy()
        for k in range(len(GROUPS)):
            sel = np.flatnonzero(gidx == k)
            a[sel] = a[rng.permutation(sel)]
        null_pass += geometry(fit(a)[0])["pass"]
    out = {"counts": {"pfn": {g: int(np.sum(gidx == k)) for k, g in enumerate(GROUPS)}, "hdb": int(len(hdb))},
           "ring_pair_lambda": res["lambda_pair"], "pfn_input_coherence_median": float(np.median(coherence)),
           "C2_geometry": geo, "group_consistency": {g: float(c) for g, c in zip(GROUPS, cons)},
           "group_input_amplitude": {g: float(np.abs(Wph[:, gidx == k]).sum()) for k, g in enumerate(GROUPS)},
           "null_pass_rate": null_pass / N_NULL, "null_ok": bool(null_pass / N_NULL <= 0.05)}
    labels = [PFN_INST.match(inst[i]) for i in pfn]
    if any(labels):
        ok = [j for j, m in enumerate(labels) if m]
        ph = np.array([lf.phi(labels[j].group(2), int(labels[j].group(3))) for j in ok])
        best = max((abs(np.mean(np.exp(1j * (alpha[ok] - s * ph)))), s) for s in (1, -1))
        off = np.angle(np.mean(np.exp(1j * (alpha[ok] - best[1] * ph))))
        resid = np.degrees(np.abs(wrap(alpha[ok] - best[1] * ph - off)))
        out["D0_alpha_vs_E1"] = {"R": float(best[0]), "orientation": int(best[1]),
                                 "median_abs_residual_deg": float(np.median(resid)), "pass": bool(best[0] >= 0.9)}
        s10 = json.loads((LOOP / "step10_a2_composition_v2/results.json").read_text(encoding="utf-8"))["C2_geometry"]["offsets_deg"]
        ref = np.radians([s10[g] for g in GROUPS])
        fits = []
        for s in (1, -1):
            rot = np.angle(np.mean(np.exp(1j * (ref - s * O))))
            fits.append((float(np.degrees(np.max(np.abs(wrap(ref - s * O - rot))))), s))
        out["report_vs_step10_max_dev_deg"] = min(fits)
    return out


def main():
    rng = np.random.default_rng(SEED)
    if "--control" in sys.argv:
        print(json.dumps(analyse(*malecns(), rng), indent=1, default=float))
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    M = analyse(*malecns(), rng)
    F = analyse(*flywire(), rng)
    m_ok = M["D0_alpha_vs_E1"]["pass"] and M["C2_geometry"]["pass"] and M["null_ok"]
    f_ok = F["C2_geometry"]["pass"] and F["null_ok"]
    verdict = ("FB_PHASOR_GEOMETRY_REPLICATED" if m_ok and f_ok else
               "METHOD_CONTROL_FAILED" if not m_ok else "FB_PHASOR_GEOMETRY_NOT_REPLICATED")
    result = {"schema": "ce-a1-step19-fb-phasor-label-free", "code_sha256": code_hash, "seed": SEED, "verdict": verdict,
              "malecns": M, "flywire": F}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
