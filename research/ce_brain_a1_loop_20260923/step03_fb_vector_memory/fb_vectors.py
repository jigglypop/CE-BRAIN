"""A1 loop step 3: do PFN->hDeltaB offsets build four orthogonal vectors in the FB? (CONTRACT.md)

python fb_vectors.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MALECNS = ROOT / "verify/MaleCNS"
PFN = re.compile(r"^(PFNd|PFNv)\(PB0[45]\)_([LR])([1-9])_C\d+$")


def phi_unwrapped(side, k):
    return (8 - k) * 45.0 if side == "L" else (k - 1.5) * 45.0


def wrap(deg):
    return (deg + 180.0) % 360.0 - 180.0


def circ_mean_deg(values, weights=None):
    w = np.ones(len(values)) if weights is None else np.asarray(weights, float)
    return float(np.degrees(np.angle(np.sum(w * np.exp(1j * np.radians(values))))))


def stream(gm, pfn_ids, hdb_ids):
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.ipc as ipc
    path = gm.FLAT_DIR / "syn-partners-male-cns-v1.0-minconf-0.5.feather"
    pfn_sorted, hdb_sorted = np.sort(pfn_ids), np.sort(hdb_ids)
    with pa.memory_map(str(path), "r") as source:
        reader = ipc.open_file(source)
        field = reader.get_batch(0).schema.get_field_index("primary_post")

        def work(batches):
            out = {"pfn": [], "hdb_in": [], "hdb_out": []}
            for b in batches:
                col = lambda c: b.column(b.schema.get_field_index(c)).to_numpy()
                roi = b.column(field)
                names = np.array(roi.dictionary.to_pylist() + [""])
                fb = names[pc.fill_null(roi.indices, -1).to_numpy()] == "FB"
                if not fb.any():
                    continue
                pre, post = col("body_pre"), col("body_post")
                _, pre_pfn = gm.locate(pre, pfn_sorted)
                _, pre_hdb = gm.locate(pre, hdb_sorted)
                _, post_hdb = gm.locate(post, hdb_sorted)
                xyz_pre = lambda m: np.stack([col(c)[m] for c in ("x_pre", "y_pre", "z_pre")], 1)
                xyz_post = lambda m: np.stack([col(c)[m] for c in ("x_post", "y_post", "z_post")], 1)
                m = fb & pre_pfn
                if m.any():
                    out["pfn"].append((pre[m], post[m], xyz_pre(m)))
                m = fb & post_hdb
                if m.any():
                    out["hdb_in"].append((post[m], xyz_post(m)))
                m = fb & pre_hdb
                if m.any():
                    out["hdb_out"].append((pre[m], xyz_pre(m)))
            return out
        n = reader.num_record_batches
        chunks = ([reader.get_batch(i) for i in range(s, min(s + 16, n))] for s in range(0, n, 16))
        acc = {"pfn": [], "hdb_in": [], "hdb_out": []}
        with ThreadPoolExecutor(8) as pool:
            for part in pool.map(work, chunks):
                for k in acc:
                    acc[k] += part[k]
    cat = lambda parts, i: np.concatenate([p[i] for p in parts])
    return ((cat(acc["pfn"], 0), cat(acc["pfn"], 1), cat(acc["pfn"], 2).astype(float)),
            (cat(acc["hdb_in"], 0), cat(acc["hdb_in"], 1).astype(float)),
            (cat(acc["hdb_out"], 0), cat(acc["hdb_out"], 1).astype(float)))


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    spec = importlib.util.spec_from_file_location("g", MALECNS / "neuron_graph.py")
    gm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gm)
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    info, hdb = {}, []
    for body, t, inst in zip(table["bodyId"].to_pylist(), table["type"].to_pylist(), table["instance"].to_pylist()):
        m = PFN.match(inst or "")
        if m:
            info[body] = (m.group(1), m.group(2), int(m.group(3)))
        elif t == "hDeltaB":
            hdb.append(body)
    (pre, post, xyz), (hin_b, hin_xyz), (hout_b, hout_xyz) = stream(gm, np.array(list(info)), np.array(hdb))
    centre = xyz.mean(axis=0)
    axis = np.linalg.svd(xyz - centre, full_matrices=False)[2][0]
    x_of = lambda p: (p - centre) @ axis
    # F1: common-slope topography of PFN output centroids
    bodies = sorted(set(pre.tolist()))
    groups = {b: info[b][0][-1] + info[b][1] for b in bodies}  # 'dL', 'dR', 'vL', 'vR'
    names = sorted(set(groups.values()))
    xs = np.array([x_of(xyz[pre == b]).mean() for b in bodies])
    ph = np.array([phi_unwrapped(info[b][1], info[b][2]) for b in bodies])
    design = np.column_stack([ph] + [[1.0 if groups[b] == g else 0.0 for b in bodies] for g in names])
    coef, *_ = np.linalg.lstsq(design, xs, rcond=None)
    fit = design @ coef
    r2 = float(1 - np.sum((xs - fit) ** 2) / np.sum((xs - xs.mean()) ** 2))
    scale = 1.0 / coef[0]  # degrees per x unit
    # hDeltaB compartments
    dend = {h: x_of(hin_xyz[hin_b == h]).mean() for h in set(hin_b.tolist())}
    axon = {h: x_of(hout_xyz[hout_b == h]).mean() for h in set(hout_b.tolist())}
    sep = [wrap(scale * (axon[h] - dend[h])) for h in dend if h in axon]
    offsets, compartments = {g: [] for g in names}, {g: [0, 0] for g in names}
    for b in bodies:
        mask = (pre == b) & np.isin(post, list(axon))
        if not mask.any():
            continue
        targets, where = post[mask], x_of(xyz[mask])
        psi = circ_mean_deg([scale * axon[h] for h in targets])
        offsets[groups[b]].append(wrap(psi - phi_unwrapped(info[b][1], info[b][2])))
        for h, xw in zip(targets, where):
            if h in dend:
                compartments[groups[b]][0 if abs(xw - dend[h]) < abs(xw - axon[h]) else 1] += 1
    O = {g: circ_mean_deg(v) for g, v in offsets.items()}
    dd, dv = wrap(O["dL"] - O["dR"]), wrap(O["vL"] - O["vR"])
    f2 = 67.5 <= abs(dd) <= 112.5 and 67.5 <= abs(dv) <= 112.5 and np.sign(dd) != np.sign(dv)
    ordered = np.sort(np.mod(list(O.values()), 360))
    gaps = np.diff(np.r_[ordered, ordered[0] + 360])
    f3 = bool(np.all(np.abs(gaps - 90) <= 30))
    result = {"schema": "ce-a1-step03-fb-vectors", "code_sha256": code_hash,
              "pfn_neurons": {g: int(sum(groups[b] == g for b in bodies)) for g in names}, "pfn_fb_synapses": int(len(pre)),
              "F1": {"R2": r2, "deg_per_x_unit": float(scale), "pass": r2 >= 0.8},
              "group_offsets_deg": O, "per_neuron_offsets_deg": offsets,
              "F2": {"delta_d": dd, "delta_v": dv, "pass": bool(f2)},
              "F3": {"gaps_deg": gaps.tolist(), "pass": f3},
              "report": {"hdb_dendrite_to_axon_deg": {"median_abs": float(np.median(np.abs(sep))), "values": sep},
                         "pfn_synapses_nearer_hdb_dendrite_vs_axon": compartments}}
    result["verdict"] = "FB_FOUR_VECTOR_BASIS_SUPPORTED" if result["F1"]["pass"] and f2 and f3 else "FB_FOUR_VECTOR_BASIS_NOT_SUPPORTED"
    with (HERE / "results.json").open("x", encoding="utf-8") as stream_out:
        json.dump(result, stream_out, indent=2, default=float)
    print(json.dumps({k: v for k, v in result.items() if k != "per_neuron_offsets_deg"}, indent=1, default=float))


if __name__ == "__main__":
    main()
