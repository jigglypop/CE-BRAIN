"""A1 reverse-proof V: are T4/T5 constant antisymmetric shift operators on the fixed column lattice?

python shift_operators.py    refuses to run unless ALGORITHM_A1.md lists this code hash
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import sparse

import discover as d

HERE = Path(__file__).resolve().parent
PAIRS = {"T4": (("Mi4",), ("Mi9",)), "T5": (("Tm1", "Tm2"), ("Tm9",))}
E1, E2 = np.array([1.0, 0.0]), np.array([-0.5, np.sqrt(3) / 2])


def direction_deg(v):
    return float(np.degrees(np.arctan2(v[1], v[0])))


def angle_between(u, v):
    return float(np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "ALGORITHM_A1.md").read_text(encoding="utf-8"):
        raise SystemExit(f"ALGORITHM_A1.md does not list this code hash {code_hash}")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    gm = d.load_module("malecns_neuron_graph", d.MALECNS / "neuron_graph.py")
    graph = gm.load(d.MALECNS / "neuron_graph_result.json")
    n = len(graph["node_ids"])
    incoming = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n)).tocsc()
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    h1 = table["assignedOlHex1"].to_numpy(zero_copy_only=False)
    h2 = table["assignedOlHex2"].to_numpy(zero_copy_only=False)
    ty, root, soma = table["type"].to_pylist(), table["rootSide"].to_pylist(), table["somaSide"].to_pylist()
    position, found = gm.locate(table["bodyId"].to_numpy(), graph["node_ids"])
    xy = np.full((n, 2), np.nan)
    node_type, node_side = np.full(n, "", dtype=object), np.full(n, "", dtype=object)
    for i in np.flatnonzero(found):
        node_type[position[i]] = ty[i] or ""
        node_side[position[i]] = root[i] or soma[i] or ""
        if not np.isnan(h1[i]):
            xy[position[i]] = h1[i] * E1 + h2[i] * E2
    result = {"schema": "ce-a1-shift-operators-v1", "code_sha256": code_hash, "eyes": {}}
    for side in ("R", "L"):
        eye = {}
        for family, (plus, minus) in PAIRS.items():
            for sub in "abcd":
                cells = np.flatnonzero(node_type == f"{family}{sub}")
                vectors = []
                for c in cells:
                    lo, hi = incoming.indptr[c], incoming.indptr[c + 1]
                    src, w = incoming.indices[lo:hi], incoming.data[lo:hi]
                    ok = ~np.isnan(xy[src, 0]) & (node_side[src] == side)
                    if ok.sum() == 0 or np.mean(node_side[src[~np.isnan(xy[src, 0])]] == side) < 0.8:
                        continue

                    def centre(types):
                        m = ok & np.isin(node_type[src], types)
                        return (w[m, None] * xy[src[m]]).sum(axis=0) / w[m].sum() if w[m].sum() > 0 else None
                    a, b = centre(plus), centre(minus)
                    if a is not None and b is not None:
                        vectors.append(a - b)
                v = np.array(vectors)
                unit = v / np.linalg.norm(v, axis=1, keepdims=True)
                med = np.median(v, axis=0)
                eye[f"{family}{sub}"] = {"neurons": len(v), "median_vector": med.tolist(),
                                         "median_direction_deg": direction_deg(med),
                                         "R": float(np.linalg.norm(unit.mean(axis=0))),
                                         "median_magnitude": float(np.median(np.linalg.norm(v, axis=1)))}
        tests = {}
        for family in PAIRS:
            vec = {s: np.array(eye[f"{family}{s}"]["median_vector"]) for s in "abcd"}
            ab, cd = angle_between(vec["a"], vec["b"]), angle_between(vec["c"], vec["d"])
            axes = angle_between(vec["a"] - vec["b"], vec["c"] - vec["d"])
            axes = min(axes, 180 - axes)
            tests[family] = {"V1_ab_deg": ab, "V1_cd_deg": cd, "V1": ab >= 150 and cd >= 150,
                             "V2_axis_angle_deg": axes, "V2": axes >= 45,
                             "V3": all(eye[f"{family}{s}"]["R"] >= 0.7 and 0.5 <= eye[f"{family}{s}"]["median_magnitude"] <= 3
                                       for s in "abcd")}
        v4 = {s: angle_between(np.array(eye[f"T4{s}"]["median_vector"]), np.array(eye[f"T5{s}"]["median_vector"]))
              for s in "abcd"}
        tests["V4_T4_T5_same_frame_deg"] = v4
        tests["V4"] = all(x <= 30 for x in v4.values())
        tests["pass"] = all(tests[f][k] for f in PAIRS for k in ("V1", "V2", "V3")) and tests["V4"]
        result["eyes"][side] = {"subtypes": eye, "tests": tests}
    result["verdict"] = "A1_SHIFT_OPERATORS_REVERSE_PROVED" if all(e["tests"]["pass"] for e in result["eyes"].values()) \
        else "A1_SHIFT_OPERATORS_NOT_PROVED"
    with (HERE / "results_shift_operators.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
