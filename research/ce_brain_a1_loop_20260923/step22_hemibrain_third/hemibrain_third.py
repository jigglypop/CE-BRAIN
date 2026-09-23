"""A1 step 22: hemibrain v1.2 as a third individual for steps 17-21 (CONTRACT.md).

H1 ring operator (step 17), H2 global inhibition (step 18), H3 FB four phasors (step 19) and the
22.5 deg question (step 20), H4 MB same-compartment loops (step 21). The memory pair is chosen among
modes that live on EPG (EPG norm share >= 0.10), fixing the step-18 criterion defect.

python hemibrain_third.py              full run; refuses unless CONTRACT.md lists this code hash
python hemibrain_third.py --calibrate  corrected pair criterion on MaleCNS and FlyWire only (writes nothing)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import numpy as np
from scipy import sparse
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
ROOT = HERE.parents[2]
HB = ROOT / "data/external/hemibrain_v1_2"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lf = load("label_free_ring", LOOP / "step17_label_free_ring/label_free_ring.py")
gi = load("gi_replication", LOOP / "step18_global_inhibition_replication/gi_replication.py")
fb = load("fb_label_free", LOOP / "step19_fb_phasor_replication/fb_label_free.py")
s20 = load("path_decomp", LOOP / "step20_fb_shift_localization/path_decomp.py")
s5 = load("mbon_dan_loops", LOOP / "step05_mbon_dan_loops/mbon_dan_loops.py")
s21 = load("mb_loop_replication", LOOP / "step21_mb_loop_replication/mb_loop_replication.py")
GLOM = re.compile(r"_([LR])([1-9])")
MIN_EPG_SHARE, SEED, N_NULL = 0.10, 20260923, 200


def ring_pair_v2(W, epg):
    lam, left, right = eig(W, left=True, right=True)
    order = np.argsort(-lam.real)
    modes = []
    for k in order:
        v = right[epg, k]
        p0 = abs(np.sum(v)) ** 2 / (len(v) * np.sum(np.abs(v) ** 2))
        share = float(np.sum(np.abs(v) ** 2) / np.sum(np.abs(right[:, k]) ** 2))
        modes.append((k, lam[k], float(p0), share))
    uniform = [m for m in modes if m[2] >= 0.5]
    rest = [m for m in modes if m[2] < 0.5 and m[3] >= MIN_EPG_SHARE]
    (k1, l1, _, s1), (k2, l2, _, s2), (k3, l3, _, s3) = rest[:3]
    if abs(l1.imag) > 1e-9 * max(1.0, abs(l1.real)):
        span = np.column_stack([right[:, k1].real, right[:, k1].imag])
        dual_src = np.column_stack([left[:, k1].real, left[:, k1].imag])
    else:
        span = np.column_stack([right[:, k1].real, right[:, k2].real])
        dual_src = np.column_stack([left[:, k1].real, left[:, k2].real])
    X = span[epg]
    ev, U = np.linalg.eigh(X.T @ X / len(epg))
    B = span @ (U @ np.diag(1 / np.sqrt(np.maximum(ev, 1e-300))) @ U.T)
    xy = B[epg]
    r = np.linalg.norm(xy, axis=1)
    theta = np.mod(np.arctan2(xy[:, 1], xy[:, 0]), 2 * np.pi)
    res = {"lambda_uniform": [float(m[1].real) for m in uniform[:2]], "lambda_pair": [float(l1.real), float(l2.real)],
           "lambda_pair_imag": [float(l1.imag), float(l2.imag)], "lambda_next": float(l3.real),
           "epg_share_pair_next": [s1, s2, s3], "pair_gap": float((l1.real - l2.real) / abs(l1.real)),
           "isolation": float((l2.real - l3.real) / abs(l1.real)), "radius_cv": float(r.std() / r.mean()),
           "max_gap_deg": lf.max_gap(theta), "resultant": float(abs(np.mean(np.exp(1j * theta)))),
           "uniform_over_lead": float(uniform[0][1].real / l1.real) if uniform else None}
    return res, theta, B, dual_src


def analyse_ring(w, kind, side, label, rng, sign_types, null=True):
    sign = np.array([-1.0 if k in sign_types else 1.0 for k in kind])
    W = (w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :]
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    res, theta, B, dual_src = ring_pair_v2(W, epg)
    u1, u2 = lf.u1u2(res)
    dual = dual_src @ np.linalg.inv(B.T @ dual_src)
    gamma = np.array([(1.0 if s == "left" else -1.0 if s == "right" else 0.0) if k.startswith("PEN") else 0.0
                      for k, s in zip(kind, side)])
    Q = dual.T @ (gamma[:, None] * W) @ B
    rho = float(np.linalg.norm((Q - Q.T) / 2) / np.linalg.norm(Q)) if np.linalg.norm(Q) > 0 else 0.0
    es = np.array([side[i] for i in epg])
    fold = {s: {"max_gap_deg": lf.max_gap(theta[es == s]), "resultant": float(abs(np.mean(np.exp(1j * theta[es == s]))))}
            for s in ("left", "right")}
    out = {**res, "U1_pair": u1, "U2_circle": u2, "rho": rho, "U3_rotation": bool(rho >= 0.7), "fold": fold,
           "U5_fold": bool(all(fold[s]["max_gap_deg"] <= 90 and fold[s]["resultant"] <= 0.3 for s in fold))}
    if null:
        types = sorted(set(kind))
        members = {t: np.array([i for i, k in enumerate(kind) if k == t]) for t in types}
        passes = 0
        for _ in range(N_NULL):
            wn = np.zeros_like(w)
            for a in types:
                for b in types:
                    wn[np.ix_(members[a], members[b])] = w[np.ix_(rng.permutation(members[a]), rng.permutation(members[b]))]
            try:
                Wn = (wn / np.maximum(wn.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :]
                passes += all(lf.u1u2(ring_pair_v2(Wn, epg)[0]))
            except (ValueError, np.linalg.LinAlgError):
                pass
        out["null_pass_rate"] = passes / N_NULL
        out["U4_null"] = bool(passes / N_NULL <= 0.05)
    lab = [(j, label[i]) for j, i in enumerate(epg) if label[i]]
    if lab:
        th = np.array([theta[j] for j, _ in lab])
        ph = np.array([lf.phi(*l) for _, l in lab])
        best = max((abs(np.mean(np.exp(1j * (th - s * ph)))), s) for s in (1, -1))
        out["U0_theta_vs_E1_R"] = float(best[0])
        out["U0"] = bool(best[0] >= 0.9)
    return out


def side_of(inst):
    m = GLOM.search(inst or "")
    if m:
        return {"L": "left", "R": "right"}[m.group(1)]
    return {"_L": "left", "_R": "right"}.get((inst or "")[-2:], "")


def hemibrain():
    import pandas as pd
    neu = pd.read_csv(HB / "exported-traced-adjacencies-v1.2/traced-neurons.csv").drop_duplicates("bodyId").sort_values("bodyId")
    con = pd.read_csv(HB / "exported-traced-adjacencies-v1.2/traced-total-connections.csv")
    nt = pd.read_feather(HB / "hemibrain-v1.2-body-mean-neurotransmitters.feather")
    ids = neu["bodyId"].to_numpy(dtype=np.int64)
    pre = np.searchsorted(ids, con["bodyId_pre"].to_numpy(dtype=np.int64))
    post = np.searchsorted(ids, con["bodyId_post"].to_numpy(dtype=np.int64))
    ok = (pre < len(ids)) & (post < len(ids))
    ok[ok] &= (ids[pre[ok]] == con["bodyId_pre"].to_numpy()[ok]) & (ids[post[ok]] == con["bodyId_post"].to_numpy()[ok])
    A = sparse.csr_array((con["weight"].to_numpy(dtype=float)[ok], (pre[ok], post[ok])), shape=(len(ids), len(ids)))
    A.sum_duplicates()
    ntp = nt["predicted_nt"].reindex(ids).fillna("").to_numpy(dtype=object)
    inst = neu["instance"].fillna("").to_numpy(dtype=object)
    return A, neu["type"].fillna("").to_numpy(dtype=object), inst, np.array([side_of(s) for s in inst], dtype=object), ntp


def sub(A, nodes):
    return A[nodes, :][:, nodes].toarray().T  # w[post, pre]


def calibrate():
    rng = np.random.default_rng(SEED)
    out = {}
    for name, loader in (("malecns", gi.malecns), ("flywire", gi.flywire)):
        A, ty, sd, nt = loader()
        base = np.array([v for v in range(len(ty)) if ty[v] in gi.BASE])
        kb = [ty[v] for v in base]
        r5 = analyse_ring(sub(A, base), kb, [sd[v] for v in base], [None] * len(base), rng, {"Delta7"}, null=False)
        chosen, members = gi.select(A, ty, nt)
        nodes = np.array(sorted(list(base) + [v for t in chosen for v in members[t]]))
        kn = [ty[v] for v in nodes]
        rx = analyse_ring(sub(A, nodes), kn, [sd[v] for v in nodes], [None] * len(nodes), rng, {"Delta7"} | set(chosen), null=False)
        pick = lambda r: {k: r[k] for k in ("lambda_pair", "lambda_next", "epg_share_pair_next", "pair_gap", "isolation",
                                            "U1_pair", "U2_circle", "rho", "uniform_over_lead")}
        out[name] = {"five_type": pick(r5), "expanded": pick(rx)}
    print(json.dumps(out, indent=1, default=float))


def main():
    if "--calibrate" in sys.argv:
        calibrate()
        return
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    rng = np.random.default_rng(SEED)
    A, ty, inst, sd, nt = hemibrain()
    glom = lambda v: (lambda m: (m.group(1), int(m.group(2))) if m else None)(GLOM.search(inst[v]) if ty[v] in gi.BASE else None)
    base = np.array([v for v in range(len(ty)) if ty[v] in gi.BASE])
    counts = {t: int(np.sum(ty == t)) for t in sorted(gi.BASE | {"PFNd", "PFNv", "hDeltaB"})}
    # H1 ring operator
    H1 = analyse_ring(sub(A, base), [ty[v] for v in base], [sd[v] for v in base], [glom(v) for v in base], rng, {"Delta7"})
    h1 = all(H1[k] for k in ("U0", "U1_pair", "U2_circle", "U3_rotation", "U4_null", "U5_fold"))
    # H2 global inhibition
    chosen, members = gi.select(A, ty, nt)
    nodes = np.array(sorted(list(base) + [v for t in chosen for v in members[t]]))
    kn, sn, ln = [ty[v] for v in nodes], [sd[v] for v in nodes], [glom(v) for v in nodes]
    H2 = analyse_ring(sub(A, nodes), kn, sn, ln, rng, {"Delta7"} | set(chosen), null=False)
    H2["sign_flip_uniform_over_lead"] = analyse_ring(sub(A, nodes), kn, sn, ln, rng, {"Delta7"}, null=False)["uniform_over_lead"]
    H2["chosen_types"] = chosen
    H2["G1"] = bool(H2["uniform_over_lead"] is not None and H2["uniform_over_lead"] < 1)
    H2["G2"] = bool(H2["U1_pair"] and H2["U2_circle"])
    H2["G3"] = bool(H2["U3_rotation"])
    h2 = H2["G1"] and H2["G2"] and H2["G3"]
    # H3 FB four phasors + 22.5 deg question
    fbn = np.array(sorted(list(base) + [v for v in range(len(ty)) if ty[v] in ("PFNd", "PFNv", "hDeltaB")]))
    H3 = fb.analyse(sub(A, fbn), [ty[v] for v in fbn], [sd[v] for v in fbn], [inst[v] for v in fbn], rng)
    s19 = json.loads((LOOP / "step19_fb_phasor_replication/results.json").read_text(encoding="utf-8"))
    h_off = H3["C2_geometry"]["offsets_deg"]
    H3["vs_malecns"] = s20.compare(s19["malecns"]["C2_geometry"]["offsets_deg"], h_off)
    H3["vs_flywire"] = s20.compare(s19["flywire"]["C2_geometry"]["offsets_deg"], h_off)
    H3["class_vs_malecns"], H3["class_vs_flywire"] = s20.classify(H3["vs_malecns"]), s20.classify(H3["vs_flywire"])
    h3 = H3["D0_alpha_vs_E1"]["pass"] and H3["C2_geometry"]["pass"] and H3["null_ok"]
    h3b = H3["class_vs_malecns"] == "clean"
    # H4 MB same-compartment loops (compartments straight from hemibrain instances)
    mb_re, dan_re = re.compile(r"^MBON\d"), re.compile(r"^(PAM|PPL1)\d")
    mbon = [(v, s5.compartments(inst[v], ">"), ty[v], nt[v] or "unknown") for v in range(len(ty)) if mb_re.match(ty[v])]
    dan = [(v, s5.compartments(inst[v], "<"), ty[v], nt[v] or "unknown") for v in range(len(ty)) if dan_re.match(ty[v])]
    # bare "B'2" overlaps every B'2x (step-5 rule); expand it so s5.overlap always returns a bool
    norm = lambda c: (c - {"B'2"}) | {"B'2a", "B'2m", "B'2p"} if "B'2" in c else c
    mbon = [(v, norm(c), t, n) for v, c, t, n in mbon if c]
    dan = [(v, norm(c), t, n) for v, c, t, n in dan if c]
    mi, di = np.array([m[0] for m in mbon]), np.array([d[0] for d in dan])
    H4 = s21.enrichment(A[mi, :][:, di].toarray(), mbon, dan, float(A[mi, :].sum()))
    H4["R1"] = bool(H4["F_same_compartment"] > H4["null_q975"] and H4["p"] < 0.01)
    H4["R2"] = bool(H4["lit_loop_MBON07_to_PAM11_synapses"] >= 10)
    H4["R3"] = bool(H4["F_over_null"] >= 2)
    h4 = H4["R1"] and H4["R2"] and H4["R3"]
    result = {"schema": "ce-a1-step22-hemibrain-third", "code_sha256": code_hash, "seed": SEED, "neurons": int(len(ty)),
              "counts": counts,
              "verdicts": {"H1_ring_operator": bool(h1), "H2_global_inhibition": bool(h2), "H3_fb_geometry": bool(h3),
                           "H3b_matches_malecns_not_flywire_shift": bool(h3b), "H4_mb_loops": bool(h4)},
              "H1": H1, "H2": H2, "H3": H3, "H4": H4}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    brief = lambda d: {k: v for k, v in d.items() if k not in ("pair_loops", "Q", "chosen_types")}
    print(json.dumps({"verdicts": result["verdicts"], "counts": counts, "H1": brief(H1), "H2": brief(H2),
                      "H2_chosen": {k: (v["neurons"], v["X_to_EPG"], v["nt"]) for k, v in chosen.items()},
                      "H3": brief(H3), "H4": brief(H4), "H4_top": list(H4["pair_loops"].items())[:10]}, indent=1, default=float))


if __name__ == "__main__":
    main()
