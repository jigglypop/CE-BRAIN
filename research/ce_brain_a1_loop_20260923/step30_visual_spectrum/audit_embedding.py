"""Audit copy for step 30 (does NOT change the frozen verdict): FlyWire embedding corrected to the 120-degree basis
(X = p - q/2, Y = q*sqrt(3)/2; see diag_neighbors.json) plus the largest-common-component fix (audit_components.py).
The choice between the two diagonals uses the coupling itself (one bit), disclosed."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vs = load("vs", HERE / "visual_spectrum.py")
ac = load("ac", HERE / "audit_components.py")


def flywire_fixed(side):
    import pandas as pd
    C, _ = vs.flywire(side)
    d = vs.load("discover", vs.VIS / "discover.py")
    col = pd.read_csv(vs.FW / "codex/column_assignment.csv.gz").drop_duplicates("root_id")
    c = col[(col["hemisphere"] == side) & col["type"].isin(d.MODULAR)]
    counts = c.groupby("column_id").size()
    cid = sorted(counts[counts >= vs.MIN_MEMBERS].index)
    pq = c.groupby("column_id")[["p", "q"]].first().loc[cid]
    xy = np.column_stack([pq["p"] - pq["q"] / 2.0, pq["q"] * np.sqrt(3) / 2.0])
    return C, xy


def main():
    rng = np.random.default_rng(vs.SEED)
    out = {}
    for s in ("right", "left"):
        C, xy = flywire_fixed(s)
        idx = ac.common_component(C, xy)
        r = vs.analyse(C[np.ix_(idx, idx)], xy[idx], rng)
        r["dropped_columns"] = int(len(xy) - len(idx))
        out[f"flywire_{s}"] = r
        print(s, "dropped", r["dropped_columns"], {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if not isinstance(v, (list, dict))},
              "ratio", {a: round(b, 3) for a, b in r["report_eigen_ratio_2_over_1"].items()})
    prev = json.loads((HERE / "results_component_audit.json").read_text(encoding="utf-8"))["eyes"]
    allp = all(r["M1"] and r["M2"] and r["M3_null"] for r in out.values()) and all(prev[k]["M1"] and prev[k]["M2"] and prev[k]["M3_null"] for k in ("malecns_R", "malecns_L"))
    (HERE / "results_embedding_audit.json").write_text(json.dumps({"note": "audit copy; frozen verdict unchanged", "all_four_eyes_pass": allp, "flywire": out}, indent=1, default=float), encoding="utf-8")
    print("four eyes pass (MaleCNS from component audit + FlyWire corrected):", allp)


if __name__ == "__main__":
    main()
