"""Post hoc control: intrinsic curvature of the physical medulla sheet on the same column lattice.

Column position = mean presynaptic coordinate of its modular columnar neurons inside ME(side).
Edge length = 3D Euclidean distance between neighbouring column positions; the Regge deficits of
this polyhedral surface are its discrete Gaussian curvature. Compared with the wiring metric (E2).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json

import numpy as np

import discover as d
import reverse_proof as rp


def column_positions(side, keys, cols):
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.ipc as ipc
    graph_module = d.load_module("malecns_neuron_graph", d.MALECNS / "neuron_graph.py")
    graph = graph_module.load(d.MALECNS / "neuron_graph_result.json", verify_hash=False)
    body_to_col = {int(graph["node_ids"][v]): g for g, k in enumerate(keys) for v in cols[k]}
    bodies = np.array(sorted(body_to_col))
    col_of = np.array([body_to_col[b] for b in bodies])
    roi_name = f"ME({side})"
    path = graph_module.FLAT_DIR / "syn-partners-male-cns-v1.0-minconf-0.5.feather"
    with pa.memory_map(str(path), "r") as source:
        reader = ipc.open_file(source)
        field = reader.get_batch(0).schema.get_field_index("primary_post")

        def work(batches):
            sums, counts = np.zeros((len(keys), 3)), np.zeros(len(keys))
            for b in batches:
                pre = b.column(b.schema.get_field_index("body_pre")).to_numpy()
                at, hit = graph_module.locate(pre, bodies)
                if not hit.any():
                    continue
                roi = b.column(field)
                names = np.array(roi.dictionary.to_pylist() + [""])
                keep = hit & (names[pc.fill_null(roi.indices, -1).to_numpy()] == roi_name)
                if keep.any():
                    xyz = np.stack([b.column(b.schema.get_field_index(c)).to_numpy()[keep] for c in ("x_pre", "y_pre", "z_pre")], 1)
                    g = col_of[at[keep]]
                    np.add.at(sums, g, xyz)
                    counts += np.bincount(g, minlength=len(keys))
            return sums, counts
        n = reader.num_record_batches
        chunks = ([reader.get_batch(i) for i in range(s, min(s + 16, n))] for s in range(0, n, 16))
        total, count = np.zeros((len(keys), 3)), np.zeros(len(keys))
        with ThreadPoolExecutor(8) as pool:
            for s, c in pool.map(work, chunks):
                total += s
                count += c
    return total / np.maximum(count, 1)[:, None], count


def main():
    out = {}
    for side in ("R", "L"):
        graph, cols = d.columns(side)
        keys = sorted(k for k, v in cols.items() if len(v) >= 10)
        pos, count = column_positions(side, keys, cols)
        lattice = rp.Lattice(keys)
        length = np.array([np.linalg.norm(pos[i] - pos[j]) for i, j in lattice.edges])
        dv = lattice.deficits(length)
        prof = d.profile_distance(graph, cols, keys)
        wiring = lattice.deficits(np.array([prof[i, j] for i, j in lattice.edges]))
        value_p, value_w = dict(zip(lattice.interior, dv)), dict(zip(lattice.interior, wiring))
        smooth = lambda value, k: sum(value.get((k[0] + a, k[1] + b), 0) for a in range(-2, 3) for b in range(-2, 3)
                                      if max(abs(a), abs(b), abs(a - b)) <= 2)
        sp = np.array([smooth(value_p, k) for k in lattice.interior])
        sw = np.array([smooth(value_w, k) for k in lattice.interior])
        out[side] = {"columns": len(keys), "min_synapses_per_column": int(count.min()),
                     "physical_integrated_sr": float(dv.sum()), "physical_implied_step_deg": rp.implied_step_deg(dv),
                     "physical_deficit_sd_deg": float(np.degrees(dv.std())),
                     "wiring_integrated_sr": float(wiring.sum()),
                     "smoothed_corr_physical_vs_wiring": float(np.corrcoef(sp, sw)[0, 1]),
                     "mean_neighbour_distance_nm_units": float(length.mean())}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
