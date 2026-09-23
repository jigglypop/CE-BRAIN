"""Reverse-proof v2: shift-free estimators for PEG / PEN (REVERSE_PROOF_v2.md).

python reverse_proof_v2.py    refuses to run unless REVERSE_PROOF_v2.md lists this code hash
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import sparse

import reverse_proof as rp
import ring_fold as rf

HERE = Path(__file__).resolve().parent
FAMILIES = ("PEG", "PEN_a", "PEN_b")
WITHIN = np.radians(22.5)
DELTAS = np.radians(np.arange(-90, 90.25, 0.5))


def profile_distance(adjacency, groups, side):
    profile = rf.unit((groups.T @ adjacency).toarray() if side == "out" else (adjacency @ groups).T.toarray())
    return np.arccos(np.clip(profile @ profile.T, -1, 1))


def fit_shift(labels, observed, transform=None):
    """Best Delta (and rotation/reflection unless a fixed transform is given) for phi + sigma*Delta."""
    best = None
    for delta in DELTAS:
        predicted = np.array([rp.phi(s, k) + (1 if s == "L" else -1) * delta for s, k in labels])
        if transform is None:
            res = rp.align(predicted, observed)
        else:
            reflect, rotate = transform
            res = rp.wrap(observed - reflect * predicted - rotate)
        if best is None or np.sum(res ** 2) < np.sum(best[1] ** 2):
            best = (delta, res)
    return best


def stream_eb(graph_module, epg_ids, pre_ids, workers=8):
    """EB synapse coordinates: postsynaptic points onto EPG and presynaptic points of the given bodies."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.ipc as ipc
    path = graph_module.FLAT_DIR / "syn-partners-male-cns-v1.0-minconf-0.5.feather"
    epg_sorted, pre_sorted = np.sort(epg_ids), np.sort(pre_ids)
    with pa.memory_map(str(path), "r") as source:
        reader = ipc.open_file(source)
        field = reader.get_batch(0).schema.get_field_index("primary_post")

        def work(batches):
            post_out, pre_out = [], []
            for b in batches:
                col = lambda c: b.column(b.schema.get_field_index(c)).to_numpy()
                roi = b.column(field)
                names = np.array(roi.dictionary.to_pylist() + [""])
                eb = names[pc.fill_null(roi.indices, -1).to_numpy()] == "EB"
                if not eb.any():
                    continue
                _, hit_post = graph_module.locate(col("body_post"), epg_sorted)
                _, hit_pre = graph_module.locate(col("body_pre"), pre_sorted)
                keep = eb & hit_post
                if keep.any():
                    post_out.append((col("body_post")[keep], np.stack([col(c)[keep] for c in ("x_post", "y_post", "z_post")], 1)))
                keep = eb & hit_pre
                if keep.any():
                    pre_out.append((col("body_pre")[keep], np.stack([col(c)[keep] for c in ("x_pre", "y_pre", "z_pre")], 1)))
            return post_out, pre_out
        n = reader.num_record_batches
        chunks = ([reader.get_batch(i) for i in range(s, min(s + 16, n))] for s in range(0, n, 16))
        post, pre = [], []
        with ThreadPoolExecutor(workers) as pool:
            for a, b in pool.map(work, chunks):
                post += a
                pre += b
    join = lambda parts: (np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts]).astype(float))
    return join(post), join(pre)


def run():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "REVERSE_PROOF_v2.md").read_text(encoding="utf-8"):
        raise SystemExit(f"REVERSE_PROOF_v2.md does not list this code hash {code_hash}")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    graph_module = rp.load(rf.MALECNS / "neuron_graph.py", "malecns_neuron_graph")
    graph = graph_module.load(rf.MALECNS / "neuron_graph_result.json")
    ids, n = graph["node_ids"], len(graph["node_ids"])
    adjacency = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    with pa.memory_map(str(graph_module.SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    body, instance = table["bodyId"].to_numpy(), table["instance"].to_pylist()
    position, found = graph_module.locate(body, ids)
    members = {f: {} for f in ("EPG",) + FAMILIES}
    for i, name in enumerate(instance):
        if found[i] and name is not None:
            for fam in members:
                m = rp.FAMILY[fam].match(name)
                if m:
                    members[fam].setdefault((m.group(1), int(m.group(2))), []).append(int(position[i]))
    order = lambda keys: sorted(keys, key=lambda k: (-1 if k[0] == "L" else 1) * k[1])
    result = {"schema": "ce-cx-ring-fold-reverse-proof-v2", "code_sha256": code_hash, "RP2b_input_only": {},
              "RP2c_output_only": {}, "RP5_eb_physical_output": {}}
    for fam in FAMILIES:
        labels = order(members[fam])
        groups = rf.indicator(n, [(v, g) for g, k in enumerate(labels) for v in members[fam][k]], len(labels))
        theta_in, cv_in, span_in = rf.mds_angles(profile_distance(adjacency, groups, "in"))
        res = rp.align(np.array([rp.phi(*k) for k in labels]), theta_in)
        result["RP2b_input_only"][fam] = {"radius_cv": cv_in, "span_deg": span_in,
                                          "fraction_within_22_5": float(np.mean(np.abs(res) <= WITHIN)),
                                          "residual_deg": {f"{s}{k}": float(np.degrees(r)) for (s, k), r in zip(labels, res)}}
        result["RP2b_input_only"][fam]["pass"] = result["RP2b_input_only"][fam]["fraction_within_22_5"] >= 0.9
        theta_out, cv_out, span_out = rf.mds_angles(profile_distance(adjacency, groups, "out"))
        delta, res = fit_shift(labels, theta_out)
        result["RP2c_output_only"][fam] = {"radius_cv": cv_out, "span_deg": span_out, "delta_deg": float(np.degrees(delta)),
                                           "fraction_within_22_5": float(np.mean(np.abs(res) <= WITHIN))}
    # RP5: physical EB output angle in the EPG-defined ring frame
    epg_keys = order(members["EPG"])
    epg_of = {ids[v]: k for k, nodes in members["EPG"].items() for v in nodes}
    fam_of = {ids[v]: (fam, k) for fam in FAMILIES for k, nodes in members[fam].items() for v in nodes}
    (post_body, post_xyz), (pre_body, pre_xyz) = stream_eb(graph_module, np.array(list(epg_of)), np.array(list(fam_of)))
    centre = post_xyz.mean(axis=0)
    _, _, vt = np.linalg.svd(post_xyz - centre, full_matrices=False)
    angle_of = lambda xyz: np.arctan2(*((xyz - centre) @ vt[:2].T).mean(axis=0)[::-1])
    psi_epg = np.array([angle_of(post_xyz[[epg_of[b] == k for b in post_body]]) for k in epg_keys])
    phi_epg = np.array([rp.phi(*k) for k in epg_keys])
    best = None
    for reflect in (1, -1):
        rotate = rf.circ_mean(psi_epg - reflect * phi_epg, np.ones(len(epg_keys)))
        res = rp.wrap(psi_epg - reflect * phi_epg - rotate)
        if best is None or np.sum(res ** 2) < np.sum(best[2] ** 2):
            best = (reflect, rotate, res)
    reflect, rotate, epg_res = best
    result["EPG_frame"] = {"reflect": reflect, "rotate_deg": float(np.degrees(rotate)),
                           "max_abs_residual_deg": float(np.degrees(np.abs(epg_res).max())), "epg_eb_synapses": len(post_body)}
    tags = [fam_of[b] for b in pre_body]
    for fam in FAMILIES:
        labels = order(members[fam])
        present = [k for k in labels if any(t == (fam, k) for t in tags)]
        psi = np.array([angle_of(pre_xyz[[t == (fam, k) for t in tags]]) for k in present])
        delta, res = fit_shift(present, psi, (reflect, rotate))
        entry = {"groups_with_eb_output": len(present), "groups": len(labels), "delta_deg": float(np.degrees(delta)),
                 "fraction_within_22_5": float(np.mean(np.abs(res) <= WITHIN)) if len(present) else 0.0,
                 "residual_deg": {f"{s}{k}": float(np.degrees(r)) for (s, k), r in zip(present, res)},
                 "eb_output_synapses": int(sum(t[0] == fam for t in tags))}
        entry["pass"] = len(present) == len(labels) and entry["fraction_within_22_5"] >= 0.9
        result["RP5_eb_physical_output"][fam] = entry
    rp2b = all(v["pass"] for v in result["RP2b_input_only"].values())
    rp5 = all(v["pass"] for v in result["RP5_eb_physical_output"].values())
    result["verdict"] = "E1_REVERSE_PROVED_STRUCTURE_V2" if rp2b and rp5 else "E1_NOT_REVERSE_PROVED_V2"
    with (HERE / "results_reverse_proof_v2.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    run()
