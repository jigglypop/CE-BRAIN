"""Reverse-proof of the post hoc fold map E1 on structure not used to find it (REVERSE_PROOF.md).

python reverse_proof.py run    refuses to run unless REVERSE_PROOF.md lists this code hash
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import numpy as np
from scipy import sparse

import ring_fold as rf

HERE = Path(__file__).resolve().parent
FAMILY = {"EPG": re.compile(r"^EPG\(PB08\)_([LR])([1-9])$"), "PEG": re.compile(r"^PEG\(PB07\)_([LR])([1-9])$"),
          "PEN_a": re.compile(r"^PEN_a\(PB06a\)_([LR])([1-9])$"), "PEN_b": re.compile(r"^PEN_b\(PB06b\)_([LR])([1-9])$"),
          "Delta7": re.compile(r"^Delta7\(PB15\)_")}
WITHIN = np.radians(22.5)


def phi(side, k):
    return np.radians(((8 - k) * 45.0) if side == "L" else ((k - 1.5) * 45.0)) % (2 * np.pi)


def unfolded(side, k):
    return np.radians((-k if side == "L" else k) * 22.5)


def wrap(a):
    return np.angle(np.exp(1j * a))


def align(predicted, observed):
    """Best global rotation and reflection of predicted onto observed; returns residuals (rad)."""
    best = None
    for s in (1, -1):
        r = rf.circ_mean(observed - s * predicted, np.ones(len(observed)))
        res = wrap(observed - s * predicted - r)
        if best is None or np.sum(res ** 2) < np.sum(best ** 2):
            best = res
    return best


def circ_corr(a, b):
    sa, sb = np.sin(a - rf.circ_mean(a, np.ones(len(a)))), np.sin(b - rf.circ_mean(b, np.ones(len(b))))
    return float(np.sum(sa * sb) / np.sqrt(np.sum(sa ** 2) * np.sum(sb ** 2)))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def eb_centroids(graph_module, epg_ids, epg_group, workers=8):
    """Mean postsynaptic coordinate of EB synapses onto each EPG group, plus all points for the ring plane."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.ipc as ipc
    path = graph_module.FLAT_DIR / "syn-partners-male-cns-v1.0-minconf-0.5.feather"
    order = np.argsort(epg_ids)
    ids, groups = epg_ids[order], epg_group[order]
    with pa.memory_map(str(path), "r") as source:
        reader = ipc.open_file(source)
        field = reader.get_batch(0).schema.get_field_index("primary_post")

        def work(batches):
            out = []
            for b in batches:
                post = b.column(b.schema.get_field_index("body_post")).to_numpy()
                at, hit = graph_module.locate(post, ids)
                if not hit.any():
                    continue
                roi = b.column(field)
                names = np.array(roi.dictionary.to_pylist() + [""])
                idx = pc.fill_null(roi.indices, -1).to_numpy()
                eb = hit & (names[idx] == "EB")
                if eb.any():
                    xyz = np.stack([b.column(b.schema.get_field_index(c)).to_numpy()[eb]
                                    for c in ("x_post", "y_post", "z_post")], axis=1).astype(float)
                    out.append((groups[at[eb]], xyz))
            return out
        n = reader.num_record_batches
        chunks = ([reader.get_batch(i) for i in range(s, min(s + 16, n))] for s in range(0, n, 16))
        parts = []
        with ThreadPoolExecutor(workers) as pool:
            for part in pool.map(work, chunks):
                parts += part
    g = np.concatenate([p[0] for p in parts])
    xyz = np.concatenate([p[1] for p in parts])
    return g, xyz


def run():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "REVERSE_PROOF.md").read_text(encoding="utf-8"):
        raise SystemExit(f"REVERSE_PROOF.md does not list this code hash {code_hash}")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    graph_module = load(rf.MALECNS / "neuron_graph.py", "malecns_neuron_graph")
    roi_module = load(rf.MALECNS / "neuron_roi.py", "malecns_neuron_roi")
    graph = graph_module.load(rf.MALECNS / "neuron_graph_result.json")
    roi = roi_module.load(rf.MALECNS / "neuron_roi_result.json")
    ids, n = graph["node_ids"], len(graph["node_ids"])
    adjacency = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    with pa.memory_map(str(graph_module.SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    body, instance = table["bodyId"].to_numpy(), table["instance"].to_pylist()
    position, found = graph_module.locate(body, ids)
    members = {f: {} for f in FAMILY}
    for i, name in enumerate(instance):
        if not found[i] or name is None:
            continue
        for fam, pattern in FAMILY.items():
            m = pattern.match(name)
            if m and fam == "Delta7":
                members[fam][int(position[i])] = name
            elif m:
                members[fam].setdefault((m.group(1), int(m.group(2))), []).append(int(position[i]))
    node_label = {}
    for fam in ("EPG", "PEG", "PEN_a", "PEN_b"):
        for key, nodes in members[fam].items():
            for v in nodes:
                node_label[v] = key
    result = {"schema": "ce-cx-ring-fold-reverse-proof-v1", "code_sha256": code_hash}

    # discovery fit (not a test): E1 vs the v1 EPG MDS angles
    v1 = json.loads((HERE / "results_v1.json").read_text(encoding="utf-8"))
    keys = [(s[0], int(s[1:])) for s in v1["labels"]]
    res = align(np.array([phi(*k) for k in keys]), np.radians(v1["theta_deg"]))
    result["E1_discovery_fit"] = {"max_abs_deg": float(np.degrees(np.abs(res).max())),
                                  "median_abs_deg": float(np.degrees(np.median(np.abs(res))))}

    # RP1: Delta7 outputs gather anatomically distant targets at one heading
    targets = np.array(sorted(node_label))
    target_phi = np.array([phi(*node_label[v]) for v in targets])
    target_u = np.array([unfolded(*node_label[v]) for v in targets])
    target_pos = np.array([(-1 if node_label[v][0] == "L" else 1) * node_label[v][1] for v in targets], dtype=float)
    rows = []
    for v, name in sorted(members["Delta7"].items()):
        w = adjacency[[v], :][:, targets].toarray().ravel()
        if w.sum() == 0:
            continue
        mean_u = np.sum(w * target_pos) / w.sum()
        rows.append({"neuron_index": v, "instance": name, "weight": float(w.sum()),
                     "R_phi": float(abs(np.sum(w * np.exp(1j * target_phi))) / w.sum()),
                     "R_unfolded": float(abs(np.sum(w * np.exp(1j * target_u))) / w.sum()),
                     "u_sd": float(np.sqrt(np.sum(w * (target_pos - mean_u) ** 2) / w.sum()))})
    r_phi = np.array([r["R_phi"] for r in rows])
    r_u = np.array([r["R_unfolded"] for r in rows])
    u_sd = np.array([r["u_sd"] for r in rows])
    rp1 = {"neurons": len(rows), "median_R_phi": float(np.median(r_phi)), "median_R_unfolded": float(np.median(r_u)),
           "fraction_R_phi_gt_R_unfolded": float(np.mean(r_phi > r_u)), "median_u_sd": float(np.median(u_sd)),
           "per_neuron": rows}
    rp1["pass"] = rp1["median_R_phi"] >= 0.7 and rp1["fraction_R_phi_gt_R_unfolded"] >= 0.9 and rp1["median_u_sd"] >= 3
    result["RP1_delta7_fold"] = rp1

    # RP2: independent angle estimates for other families
    rp2 = {}
    for fam in ("PEG", "PEN_a", "PEN_b"):
        labels = sorted(members[fam], key=lambda k: (-1 if k[0] == "L" else 1) * k[1])
        indicator = rf.indicator(n, [(v, g) for g, k in enumerate(labels) for v in members[fam][k]], len(labels))
        theta, radius_cv, span = rf.mds_angles(rf.effective_distance(adjacency, indicator))
        res = align(np.array([phi(*k) for k in labels]), theta)
        rp2[fam] = {"groups": len(labels), "radius_cv": radius_cv, "span_deg": span,
                    "residual_deg": {f"{s}{k}": float(np.degrees(r)) for (s, k), r in zip(labels, res)},
                    "fraction_within_22_5": float(np.mean(np.abs(res) <= WITHIN))}
        rp2[fam]["pass"] = rp2[fam]["fraction_within_22_5"] >= 0.9
    rp2["pass"] = all(v["pass"] for v in rp2.values())
    result["RP2_other_families"] = rp2

    # RP3: EB physical ring angle of EPG dendritic synapses
    epg_keys = sorted(members["EPG"])
    epg_nodes = np.array([v for g, k in enumerate(epg_keys) for v in members["EPG"][k]])
    epg_group = np.array([g for g, k in enumerate(epg_keys) for v in members["EPG"][k]])
    group_of_syn, xyz = eb_centroids(graph_module, ids[epg_nodes], epg_group)
    centre = xyz.mean(axis=0)
    _, _, vt = np.linalg.svd(xyz - centre, full_matrices=False)
    plane = (xyz - centre) @ vt[:2].T
    psi = np.array([np.arctan2(*plane[group_of_syn == g].mean(axis=0)[::-1]) for g in range(len(epg_keys))])
    predicted = np.array([phi(*k) for k in epg_keys])
    res = align(predicted, psi)
    rp3 = {"eb_synapses": int(len(xyz)), "residual_deg": {f"{s}{k}": float(np.degrees(r)) for (s, k), r in zip(epg_keys, res)},
           "fraction_within_22_5": float(np.mean(np.abs(res) <= WITHIN)),
           "circular_correlation_abs": abs(circ_corr(predicted, psi)),
           "planarity_third_sv_ratio": float(np.linalg.svd(xyz - centre, compute_uv=False)[2] /
                                             np.linalg.svd(xyz - centre, compute_uv=False)[0])}
    rp3["pass"] = rp3["fraction_within_22_5"] >= 0.9 and rp3["circular_correlation_abs"] >= 0.9
    result["RP3_eb_physical_ring"] = rp3

    # RP4: PEN rotation in the EB (ROI-resolved)
    names = roi["roi_names"]
    width, eb = len(names), names.index("EB")
    dyad = roi["key"] // width
    in_eb = (roi["key"] % width) == eb
    pen_label = {v: (fam, k) for fam in ("PEN_a", "PEN_b") for k, nodes in members[fam].items() for v in nodes}
    epg_label = {v: k for k, nodes in members["EPG"].items() for v in nodes}
    pre, post = dyad // n, dyad % n
    pen_set, epg_set = np.array(sorted(pen_label)), np.array(sorted(epg_label))
    mask = in_eb & np.isin(pre, pen_set) & np.isin(post, epg_set)
    agg = {}
    for p, q, c in zip(pre[mask], post[mask], roi["count"][mask]):
        agg.setdefault(pen_label[int(p)], []).append((phi(*epg_label[int(q)]), float(c)))
    shifts = {}
    for (fam, (side, k)), pairs in sorted(agg.items()):
        angles, weights = np.array([a for a, _ in pairs]), np.array([c for _, c in pairs])
        shifts[f"{fam}_{side}{k}"] = float(np.degrees(wrap(rf.circ_mean(angles, weights) - phi(side, k))))
    side_mean = {s: float(np.degrees(rf.circ_mean(np.radians([v for key, v in shifts.items() if key.split("_")[-1][0] == s]),
                                                  np.ones(sum(key.split("_")[-1][0] == s for key in shifts)))))
                 for s in "LR"}
    rp4 = {"shift_deg": shifts, "mean_L": side_mean["L"], "mean_R": side_mean["R"]}
    rp4["pass"] = np.sign(side_mean["L"]) != np.sign(side_mean["R"]) and \
        all(11.25 <= abs(side_mean[s]) <= 67.5 for s in "LR")
    result["RP4_pen_rotation"] = rp4
    result["verdict"] = "E1_REVERSE_PROVED_STRUCTURE" if rp1["pass"] and rp2["pass"] and rp3["pass"] else "E1_NOT_REVERSE_PROVED"
    with (HERE / "results_reverse_proof.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    brief = {k: ({kk: vv for kk, vv in v.items() if kk != "per_neuron"} if isinstance(v, dict) else v)
             for k, v in result.items()}
    print(json.dumps(brief, indent=1, default=float))


if __name__ == "__main__":
    run()
