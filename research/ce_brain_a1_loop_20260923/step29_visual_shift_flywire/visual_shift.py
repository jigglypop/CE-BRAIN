"""A1 step 29: replicate the MaleCNS T4/T5 shift-operator frame (visual study V1-V4) in FlyWire (CONTRACT.md).

Per T4 cell: synapse-weighted centroid of its Mi4 inputs minus that of its Mi9 inputs; per T5 cell: (Tm1 + Tm2)
minus Tm9; same hemisphere only; Codex column coordinates mapped to the plane X = (q - p)/2, Y = (p + q) * sqrt(3)/2
(unit = one column). Zero-length vectors are excluded (fixes the MaleCNS NaN defect).

python visual_shift.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FW = ROOT / "data/external/flywire_783"
PAIRS = {"T4": (("Mi4",), ("Mi9",)), "T5": (("Tm1", "Tm2"), ("Tm9",))}


def angle(u, v):
    return float(np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    import pandas as pd
    import pyarrow.feather as feather
    col = pd.read_csv(FW / "codex/column_assignment.csv.gz")
    col = col.drop_duplicates("root_id").set_index("root_id")
    xy = np.column_stack([(col["q"] - col["p"]) / 2.0, (col["p"] + col["q"]) * np.sqrt(3) / 2.0])
    pos = dict(zip(col.index.to_numpy(), map(tuple, xy)))
    ctype = col["type"].to_dict()
    hemi = col["hemisphere"].to_dict()
    post_types = {f"{f}{s}" for f in PAIRS for s in "abcd"}
    pre_types = {t for pl, mi in PAIRS.values() for t in pl + mi}
    post_ids = [r for r, t in ctype.items() if t in post_types]
    pre_ids = [r for r, t in ctype.items() if t in pre_types]
    e = feather.read_table(FW / "proofread_connections_783.feather", columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"]).to_pandas()
    e = e[e["post_pt_root_id"].isin(post_ids) & e["pre_pt_root_id"].isin(pre_ids)]
    e = e.groupby(["pre_pt_root_id", "post_pt_root_id"], as_index=False)["syn_count"].sum()
    result = {"schema": "ce-a1-step29-visual-shift-flywire", "code_sha256": code_hash, "eyes": {}}
    for side in ("right", "left"):
        eye = {}
        for family, (plus, minus) in PAIRS.items():
            for sub in "abcd":
                t = f"{family}{sub}"
                cells = [r for r in post_ids if ctype[r] == t and hemi[r] == side]
                sub_e = e[e["post_pt_root_id"].isin(cells)]
                vectors, zero = [], 0
                for cell, g in sub_e.groupby("post_pt_root_id"):
                    pre = g["pre_pt_root_id"].to_numpy()
                    w = g["syn_count"].to_numpy(dtype=float)
                    same = np.array([hemi[p] == side for p in pre])
                    if same.mean() < 0.8:
                        continue

                    def centre(types):
                        m = same & np.array([ctype[p] in types for p in pre])
                        if w[m].sum() == 0:
                            return None
                        pts = np.array([pos[p] for p in pre[m]])
                        return (w[m, None] * pts).sum(axis=0) / w[m].sum()
                    a, b = centre(plus), centre(minus)
                    if a is not None and b is not None:
                        v = a - b
                        if np.linalg.norm(v) < 1e-9:
                            zero += 1
                            continue
                        vectors.append(v)
                v = np.array(vectors)
                unit = v / np.linalg.norm(v, axis=1, keepdims=True)
                med = np.median(v, axis=0)
                eye[t] = {"neurons": int(len(v)), "zero_vectors_excluded": zero, "median_vector": med.tolist(),
                          "median_direction_deg": float(np.degrees(np.arctan2(med[1], med[0]))),
                          "R": float(np.linalg.norm(unit.mean(axis=0))), "median_magnitude": float(np.median(np.linalg.norm(v, axis=1)))}
        tests = {}
        for family in PAIRS:
            m = {s: np.array(eye[f"{family}{s}"]["median_vector"]) for s in "abcd"}
            ab, cd = angle(m["a"], m["b"]), angle(m["c"], m["d"])
            axis = angle(m["a"] - m["b"], m["c"] - m["d"])
            axis = min(axis, 180 - axis)
            v3 = all(eye[f"{family}{s}"]["R"] >= 0.7 and 0.5 <= eye[f"{family}{s}"]["median_magnitude"] <= 3 for s in "abcd")
            tests[family] = {"ab_deg": ab, "cd_deg": cd, "axes_deg": axis, "V1": ab >= 150 and cd >= 150, "V2": axis >= 45, "V3": bool(v3)}
        v4 = {s: angle(np.array(eye[f"T4{s}"]["median_vector"]), np.array(eye[f"T5{s}"]["median_vector"])) for s in "abcd"}
        tests["V4_T4_T5_same_frame_deg"] = v4
        tests["V4"] = all(x <= 30 for x in v4.values())
        tests["pass"] = bool(all(tests[f]["V1"] and tests[f]["V2"] and tests[f]["V3"] for f in PAIRS) and tests["V4"])
        result["eyes"][side] = {"subtypes": eye, "tests": tests}
    ok = all(r["tests"]["pass"] for r in result["eyes"].values())
    result["verdict"] = "A1_SHIFT_OPERATORS_REPLICATED_FLYWIRE" if ok else "A1_SHIFT_OPERATORS_NOT_REPLICATED_FLYWIRE"
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"])
    for side, r in result["eyes"].items():
        print("==", side, "pass", r["tests"]["pass"], "V4", r["tests"]["V4"])
        for f in PAIRS:
            print("  ", f, {k: (round(v, 1) if isinstance(v, float) else v) for k, v in r["tests"][f].items()})
        print("   V4", {k: round(v, 1) for k, v in r["tests"]["V4_T4_T5_same_frame_deg"].items()})
        for t, x in r["subtypes"].items():
            print("   ", t, "n", x["neurons"], "zero", x["zero_vectors_excluded"],
                  "dir %.1f R %.2f mag %.2f" % (x["median_direction_deg"], x["R"], x["median_magnitude"]))


if __name__ == "__main__":
    main()
