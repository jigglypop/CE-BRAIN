"""A1 step 25: does the spectrum alone fix the bump width? (CONTRACT.md)

Threshold-linear dynamics tau x' = -x + [g W x]_+ are homogeneous, so the persistent bump is the nonlinear
eigenvector x = [W x]_+ / |.|, independent of g. Law: a rotation-invariant ring with harmonic gains
J_m = lambda_m / lambda_1 (m = 0, 1, 2) has a bump whose FWHM follows from J alone (width_core.law_width).
Compared with the connectome's own nonlinear eigenvector in three individuals, with extra uniform inhibition c.

python width_law.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wc = load("width_core", HERE / "width_core.py")
iso = load("isometry", LOOP / "step23_isometry_generator/isometry.py")
gi = load("gi_replication", LOOP / "step18_global_inhibition_replication/gi_replication.py")
lf = iso.lf
C_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
AGREE_DEG, AGREE_FRAC, LIT = 20.0, 0.8, (80.0, 120.0)
ITERS = 4000


def malecns():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    A, ty, sd, nt = gi.malecns()
    gm = load("g", lf.MALECNS / "neuron_graph.py")
    graph = gm.load(lf.MALECNS / "neuron_graph_result.json")
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    inst = np.full(len(ty), "", dtype=object)
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    for p, f, s in zip(pos, found, t["instance"].to_pylist()):
        if f:
            inst[p] = s or ""
    return A, ty, inst, nt


def flywire():
    A, ty, sd, nt = gi.flywire()
    return A, ty, None, nt


def hemibrain():
    h22 = load("hemibrain_third", LOOP / "step22_hemibrain_third/hemibrain_third.py")
    A, ty, inst, sd, nt = h22.hemibrain()
    return A, ty, inst, nt


def build(A, ty, inst, nt):
    chosen, members = gi.select(A, ty, nt)
    base = [v for v in range(len(ty)) if ty[v] in gi.BASE]
    nodes = np.array(sorted(base + [v for t in chosen for v in members[t]]))
    kind = [ty[v] for v in nodes]
    w = A[nodes, :][:, nodes].toarray().T
    sign = np.array([-1.0 if (k == "Delta7" or k in chosen) else 1.0 for k in kind])
    W = (w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :]
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    if inst is not None:
        ang = np.array([(lambda m: lf.phi(m.group(1), int(m.group(2))))(lf.GLOM.search(inst[nodes[i]])) for i in epg])
        basis = "E1_labels"
    else:
        bnodes = np.array(sorted(base))
        wb = A[bnodes, :][:, bnodes].toarray().T
        kb = [ty[v] for v in bnodes]
        ang = lf.ring_pair(lf.operator(wb, kb), np.array([i for i, k in enumerate(kb) if k == "EPG"]))[1]
        basis = "label_free"
    return W, epg, ang, basis, sorted(chosen)


def spectrum(W, epg, ang):
    lam, left, right = eig(W, left=True, right=True)
    p1 = iso.harmonic_pair(lam, left, right, epg, ang, 1)
    p2 = iso.harmonic_pair(lam, left, right, epg, ang, 2)
    order = np.argsort(-lam.real)
    P0 = np.array([iso.powers(right[epg, k], ang)[0] for k in order])
    uni = [lam[k].real for k, p in zip(order, P0) if p >= 0.5]
    lam0 = float(uni[0]) if uni else float(lam[order[int(np.argmax(P0))]].real)
    lam1 = float(np.mean(p1[0]["lambda"])) if p1 else None
    lam2 = float(np.mean(p2[0]["lambda"])) if p2 else None
    return {"lambda0": lam0, "lambda1": lam1, "lambda2": lam2, "uniform_like_found": bool(uni)}


def bump(W, epg, ang):
    x = np.zeros(W.shape[0])
    x[epg] = np.maximum(np.cos(ang), 0)
    x /= np.linalg.norm(x)
    change = None
    for _ in range(ITERS):
        new = np.maximum(W @ x, 0)
        nrm = np.linalg.norm(new)
        if nrm == 0:
            return None, None, None
        new /= nrm
        change = float(np.max(np.abs(new - x)))
        x = new
    bins = np.mod(np.round(ang / np.radians(22.5)).astype(int), 16)
    prof = np.array([x[epg][bins == b].mean() if np.any(bins == b) else np.nan for b in range(16)])
    ok = ~np.isnan(prof)
    width = wc.fwhm_profile(prof[ok], np.radians(22.5) * np.arange(16)[ok])
    peaks = int(np.sum((prof[ok] > np.roll(prof[ok], 1)) & (prof[ok] >= np.roll(prof[ok], -1)) & (prof[ok] > 0.5 * np.nanmax(prof))))
    return width, change, peaks


def run(name, A, ty, inst, nt):
    W, epg, ang, basis, chosen = build(A, ty, inst, nt)
    rows = []
    for c in C_GRID:
        sp0 = spectrum(W, epg, ang)
        Wc = W.copy()
        if c > 0:
            Wc[:, epg] -= c * sp0["lambda1"] / len(epg)
        sp = spectrum(Wc, epg, ang)
        J = {0: sp["lambda0"] / sp["lambda1"], 1: 1.0}
        if sp["lambda2"] is not None:
            J[2] = sp["lambda2"] / sp["lambda1"]
        law = wc.law_width(J)
        sim, change, peaks = bump(Wc, epg, ang)
        agree = law is not None and sim is not None and abs(sim - law) <= AGREE_DEG
        rows.append({"c": c, **sp, "J": J, "law_fwhm": law, "sim_fwhm": sim, "last_change": change, "peaks": peaks, "agree": bool(agree)})
    base_row = rows[0]
    return {"basis": basis, "inhibitory_types": chosen, "grid": rows,
            "W1_point_c0": bool(base_row["agree"]),
            "W2_literature_c0": bool(base_row["sim_fwhm"] is not None and LIT[0] <= base_row["sim_fwhm"] <= LIT[1])}


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    res = {name: run(name, *loader()) for name, loader in (("malecns", malecns), ("flywire", flywire), ("hemibrain", hemibrain))}
    agree = [r["agree"] for d in res.values() for r in d["grid"]]
    w1 = all(d["W1_point_c0"] for d in res.values()) and np.mean(agree) >= AGREE_FRAC
    w2 = all(d["W2_literature_c0"] for d in res.values())
    result = {"schema": "ce-a1-step25-width-law", "code_sha256": code_hash, "W1_law": bool(w1), "W1_agree_fraction": float(np.mean(agree)),
              "W2_literature": bool(w2), "verdict": "WIDTH_LAW_SUPPORTED_THREE_INDIVIDUALS" if w1 and w2 else
              ("WIDTH_LAW_HOLDS_LITERATURE_MISSED" if w1 else "WIDTH_LAW_NOT_SUPPORTED"), "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], "agree_frac", round(result["W1_agree_fraction"], 3))
    for n, d in res.items():
        print("==", n, d["basis"], "W1(c0)", d["W1_point_c0"], "W2", d["W2_literature_c0"])
        for r in d["grid"]:
            print("   c", r["c"], "J0 %.3f J2 %s" % (r["J"][0], None if 2 not in r["J"] else round(r["J"][2], 3)),
                  "law", None if r["law_fwhm"] is None else round(r["law_fwhm"], 1), "sim", r["sim_fwhm"],
                  "peaks", r["peaks"], "chg", None if r["last_change"] is None else "%.1e" % r["last_change"], "agree", r["agree"])


if __name__ == "__main__":
    main()
