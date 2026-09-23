"""A1 step 17: label-free spectral ring test of the head-direction operator in MaleCNS and FlyWire (CONTRACT.md).

Same operator as step 2b (EPG, PEN_a, PEN_b, PEG, Delta7; input-normalised; Delta7 negative), but no
glomerulus labels: the memory pair is whitened on its EPG components, Gamma uses soma side, and the
fold signature asks whether each PB half (soma side) covers the whole circle.

python label_free_ring.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re

import numpy as np
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MALECNS = ROOT / "verify/MaleCNS"
FLYWIRE = ROOT / "data/external/flywire_783"
TYPES = ("EPG", "PEN_a(PEN1)", "PEN_b(PEN2)", "PEG", "Delta7")
GLOM = re.compile(r"_([LR])([1-9])")
SEED, N_NULL = 20260923, 200


def phi(side, k):
    return np.radians(((8 - k) * 45.0) if side == "L" else ((k - 1.5) * 45.0)) % (2 * np.pi)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def submatrix(indptr, indices, weight, nodes):
    lookup = {v: i for i, v in enumerate(nodes)}
    w = np.zeros((len(nodes), len(nodes)))
    for a, v in enumerate(nodes):
        for t, c in zip(indices[indptr[v]:indptr[v + 1]], weight[indptr[v]:indptr[v + 1]]):
            b = lookup.get(int(t))
            if b is not None:
                w[b, a] += c  # w[post, pre]
    return w


def malecns():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    gm = load("g", MALECNS / "neuron_graph.py")
    graph = gm.load(MALECNS / "neuron_graph_result.json")
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    ty, inst, soma = t["type"].to_pylist(), t["instance"].to_pylist(), t["somaSide"].to_pylist()
    rows = sorted((int(pos[i]), ty[i], soma[i], GLOM.search(inst[i] or "")) for i in np.flatnonzero(found) if ty[i] in TYPES)
    nodes = [r[0] for r in rows]
    kind = [r[1] for r in rows]
    side = [{"L": "left", "R": "right"}.get(r[2], "") for r in rows]
    label = [(r[3].group(1), int(r[3].group(2))) if r[3] else None for r in rows]
    w = submatrix(graph["indptr"], graph["indices"], graph["weight"], nodes)
    return w, kind, side, label


def flywire():
    import pandas as pd
    import pyarrow.feather as feather
    ann = pd.read_csv(FLYWIRE / "Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False).drop_duplicates("root_id")
    ann = ann[ann["cell_type"].isin(TYPES)].sort_values("root_id")
    ids = ann["root_id"].to_numpy(dtype=np.int64)
    e = feather.read_table(FLYWIRE / "proofread_connections_783.feather",
                           columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    e = e[e["pre_pt_root_id"].isin(ids) & e["post_pt_root_id"].isin(ids)]
    pre = np.searchsorted(ids, e["pre_pt_root_id"].to_numpy(dtype=np.int64))
    post = np.searchsorted(ids, e["post_pt_root_id"].to_numpy(dtype=np.int64))
    w = np.zeros((len(ids), len(ids)))
    np.add.at(w, (post, pre), e["syn_count"].to_numpy(dtype=float))
    side = [s if s in ("left", "right") else "" for s in ann["side"].fillna("")]
    return w, list(ann["cell_type"]), side, [None] * len(ids)


def operator(w, kind):
    sign = np.array([-1.0 if k == "Delta7" else 1.0 for k in kind])
    return (w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :]


def ring_pair(W, epg):
    """Label-free memory pair: modes by real part, skip uniform-like (P0 >= 0.5 on EPG), take the next two."""
    lam, left, right = eig(W, left=True, right=True)
    order = np.argsort(-lam.real)
    modes = []
    for k in order:
        v = right[epg, k]
        p0 = abs(np.sum(v)) ** 2 / (len(v) * np.sum(np.abs(v) ** 2))
        modes.append((k, lam[k], float(p0)))
    uniform = [m for m in modes if m[2] >= 0.5]
    rest = [m for m in modes if m[2] < 0.5]
    (k1, l1, _), (k2, l2, _), (k3, l3, _) = rest[:3]
    gap = float((l1.real - l2.real) / abs(l1.real))
    isolation = float((l2.real - l3.real) / abs(l1.real))
    if abs(l1.imag) > 1e-9 * max(1.0, abs(l1.real)):
        span = np.column_stack([right[:, k1].real, right[:, k1].imag])
        dual_src = np.column_stack([left[:, k1].real, left[:, k1].imag])
    else:
        span = np.column_stack([right[:, k1].real, right[:, k2].real])
        dual_src = np.column_stack([left[:, k1].real, left[:, k2].real])
    X = span[epg]
    C = X.T @ X / len(epg)
    ev, U = np.linalg.eigh(C)
    white = U @ np.diag(1 / np.sqrt(np.maximum(ev, 1e-300))) @ U.T
    B = span @ white
    xy = B[epg]
    r = np.linalg.norm(xy, axis=1)
    theta = np.mod(np.arctan2(xy[:, 1], xy[:, 0]), 2 * np.pi)
    return {"lambda_uniform": [float(m[1].real) for m in uniform[:2]], "lambda_pair": [float(l1.real), float(l2.real)],
            "lambda_pair_imag": [float(l1.imag), float(l2.imag)], "lambda_next": float(l3.real),
            "pair_gap": gap, "isolation": isolation, "radius_cv": float(r.std() / r.mean()),
            "max_gap_deg": max_gap(theta), "resultant": float(abs(np.mean(np.exp(1j * theta)))),
            "eig_condition": float(ev.max() / max(ev.min(), 1e-300)),
            "uniform_over_lead": float(uniform[0][1].real / l1.real) if uniform else None}, theta, B, dual_src


def max_gap(theta):
    s = np.sort(theta)
    return float(np.degrees(np.max(np.diff(np.r_[s, s[0] + 2 * np.pi]))))


def u1u2(res):
    u1 = res["pair_gap"] <= 0.10 and res["isolation"] >= 0.10
    u2 = res["radius_cv"] <= 0.25 and res["max_gap_deg"] <= 60 and res["resultant"] <= 0.25
    return bool(u1), bool(u2)


def analyse(w, kind, side, label, rng):
    W = operator(w, kind)
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    res, theta, B, dual_src = ring_pair(W, epg)
    u1, u2 = u1u2(res)
    dual = dual_src @ np.linalg.inv(B.T @ dual_src)
    gamma = np.array([(1.0 if s == "left" else -1.0 if s == "right" else 0.0) if k.startswith("PEN") else 0.0
                      for k, s in zip(kind, side)])
    Q = dual.T @ (gamma[:, None] * W) @ B
    rho = float(np.linalg.norm((Q - Q.T) / 2) / np.linalg.norm(Q)) if np.linalg.norm(Q) > 0 else 0.0
    es = np.array([side[i] for i in epg])
    fold = {}
    for s in ("left", "right"):
        th = theta[es == s]
        fold[s] = {"n": int(len(th)), "max_gap_deg": max_gap(th) if len(th) > 1 else 360.0,
                   "resultant": float(abs(np.mean(np.exp(1j * th)))) if len(th) else 1.0}
    u5 = all(fold[s]["max_gap_deg"] <= 90 and fold[s]["resultant"] <= 0.3 for s in ("left", "right"))
    z = {s: np.mean(np.exp(8j * theta[es == s])) for s in ("left", "right")}
    interleave = {"R8_left": float(abs(z["left"])), "R8_right": float(abs(z["right"])),
                  "offset_deg_8theta": float(np.degrees(np.angle(z["right"] / z["left"])) % 360) if abs(z["left"]) > 0 else None}
    # null: permute neuron identities within each type, independently per (post type, pre type) block
    types = sorted(set(kind))
    members = {t: np.array([i for i, k in enumerate(kind) if k == t]) for t in types}
    passes = 0
    for _ in range(N_NULL):
        wn = np.zeros_like(w)
        for a in types:
            for b in types:
                ra, cb = members[a], members[b]
                wn[np.ix_(ra, cb)] = w[np.ix_(rng.permutation(ra), rng.permutation(cb))]
        try:
            rn, *_ = ring_pair(operator(wn, kind), epg)
            passes += all(u1u2(rn))
        except (ValueError, np.linalg.LinAlgError):
            pass
    out = {"neurons": {t: int(len(members[t])) for t in types}, **res, "U1_pair": u1, "U2_circle": u2,
           "Q": Q.tolist(), "rho": rho, "U3_rotation": bool(rho >= 0.7), "fold_by_soma_side": fold,
           "U5_fold": bool(u5), "report_interleave_8theta": interleave,
           "null_block_permutation_pass_rate": passes / N_NULL, "U4_null": bool(passes / N_NULL <= 0.05),
           "rotation_rate_rad_per_tau_per_u": float((Q[1, 0] - Q[0, 1]) / 2 / res["lambda_pair"][0])}
    if any(label):
        lab = [(i, label[i]) for i in epg if label[i]]
        th = np.array([theta[list(epg).index(i)] for i, _ in lab])
        ph = np.array([phi(*l) for _, l in lab])
        best = max(((abs(np.mean(np.exp(1j * (th - s * ph)))), s) for s in (1, -1)))
        off = np.angle(np.mean(np.exp(1j * (th - best[1] * ph))))
        resid = np.degrees(np.abs(np.angle(np.exp(1j * (th - best[1] * ph - off)))))
        out["U0_phase_vs_E1"] = {"R": float(best[0]), "orientation": int(best[1]), "median_abs_residual_deg": float(np.median(resid)),
                                 "pass": bool(best[0] >= 0.9)}
        pen = [i for i, k in enumerate(kind) if k.startswith("PEN") and label[i] and side[i]]
        out["report_pen_soma_vs_glomerulus_side_agreement"] = float(np.mean(
            [(side[i] == "left") == (label[i][0] == "L") for i in pen]))
        eg = [i for i in epg if label[i] and side[i]]
        out["report_epg_soma_vs_glomerulus_side_agreement"] = float(np.mean(
            [(side[i] == "left") == (label[i][0] == "L") for i in eg]))
    out["raw_counts_report"] = {k: v for k, v in ring_pair(w * np.array([-1.0 if k == "Delta7" else 1.0 for k in kind])[None, :], epg)[0].items()}
    return out, theta


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    rng = np.random.default_rng(SEED)
    M, thM = analyse(*malecns(), rng)
    F, thF = analyse(*flywire(), rng)
    keys = ("U1_pair", "U2_circle", "U3_rotation", "U4_null", "U5_fold")
    m_ok = M["U0_phase_vs_E1"]["pass"] and all(M[k] for k in keys)
    f_ok = all(F[k] for k in keys)
    verdict = ("LABEL_FREE_RING_OPERATOR_REPLICATED" if m_ok and f_ok else
               "METHOD_CONTROL_FAILED" if not m_ok else "LABEL_FREE_RING_OPERATOR_NOT_REPLICATED")
    result = {"schema": "ce-a1-step17-label-free-ring", "code_sha256": code_hash, "seed": SEED, "verdict": verdict,
              "malecns": M, "flywire": F, "theta_epg": {"malecns": thM.tolist(), "flywire": thF.tolist()}}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    brief = lambda d: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()
                       if k not in ("Q", "raw_counts_report")}
    print(json.dumps({"malecns": brief(M), "flywire": brief(F), "verdict": verdict}, indent=1, default=float))


if __name__ == "__main__":
    main()
