"""Post-hoc diagnostic for step 30 (does NOT change the frozen verdict): which (dp, dq) offsets carry the lateral
coupling in FlyWire (tests the 60-degree neighbour assumption), and MaleCNS for comparison (dh1, dh2)."""
from __future__ import annotations

import importlib.util
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("vs", HERE / "visual_spectrum.py")
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)


def offsets_table(C, keys):
    S = (C + C.T) / 2
    index = {k: i for i, k in enumerate(keys)}
    acc = defaultdict(list)
    for k, i in index.items():
        for dp in (-2, -1, 0, 1, 2):
            for dq in (-2, -1, 0, 1, 2):
                if (dp, dq) == (0, 0):
                    continue
                j = index.get((k[0] + dp, k[1] + dq))
                if j is not None:
                    acc[(dp, dq)].append(S[i, j])
    return {f"{dp},{dq}": float(np.mean(v)) for (dp, dq), v in sorted(acc.items())}


def main():
    import pandas as pd
    out = {}
    # FlyWire right: rebuild keys (p, q) in the same order as vs.flywire
    col = pd.read_csv(vs.FW / "codex/column_assignment.csv.gz").drop_duplicates("root_id")
    d = vs.load("discover", vs.VIS / "discover.py")
    for side in ("right",):
        c = col[(col["hemisphere"] == side) & col["type"].isin(d.MODULAR)]
        counts = c.groupby("column_id").size()
        cid = sorted(counts[counts >= vs.MIN_MEMBERS].index)
        pq = c.groupby("column_id")[["p", "q"]].first().loc[cid]
        keys = list(zip(pq["p"].astype(int), pq["q"].astype(int)))
        C, _ = vs.flywire(side)
        out[f"flywire_{side}"] = offsets_table(C, keys)
    graph, cols = d.columns("R")
    keys = sorted(k for k, v in cols.items() if len(v) >= vs.MIN_MEMBERS)
    C, _ = vs.malecns("R")
    out["malecns_R"] = offsets_table(C, keys)
    (HERE / "diag_neighbors.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for k, t in out.items():
        top = sorted(t.items(), key=lambda kv: -kv[1])[:10]
        print(k, [(o, round(v, 1)) for o, v in top])


if __name__ == "__main__":
    main()
