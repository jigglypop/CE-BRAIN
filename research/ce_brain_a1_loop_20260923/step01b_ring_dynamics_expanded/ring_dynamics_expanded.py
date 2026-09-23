"""A1 loop step 1b: ring A1 dynamics on the expanded 297-neuron network (CONTRACT.md).

python ring_dynamics_expanded.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
spec = importlib.util.spec_from_file_location("ring_dynamics", LOOP / "step01_ring_dynamics/ring_dynamics.py")
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)
CHOSEN = sorted(json.loads((LOOP / "step02c_global_inhibition/results.json").read_text(encoding="utf-8"))["chosen_types"])
GLOM = re.compile(r"_([LR])([1-9])")


def load():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    spec = importlib.util.spec_from_file_location("g", rd.MALECNS / "neuron_graph.py")
    gm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gm)
    graph = gm.load(rd.MALECNS / "neuron_graph_result.json")
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    position, found = gm.locate(table["bodyId"].to_numpy(), graph["node_ids"])
    wanted = set(rd.TYPES) | set(CHOSEN)
    rows = []
    for p, f, t, s in zip(position, found, table["type"].to_pylist(), table["instance"].to_pylist()):
        if f and t in wanted:
            m = GLOM.search(s or "") if t in rd.TYPES else None
            rows.append((int(p), t, (m.group(1), int(m.group(2))) if m else None))
    rows.sort()
    nodes = np.array([r[0] for r in rows])
    lookup = {v: i for i, v in enumerate(nodes)}
    w = np.zeros((len(nodes), len(nodes)))
    for a, v in enumerate(nodes):
        lo, hi = graph["indptr"][v], graph["indptr"][v + 1]
        for t, c in zip(graph["indices"][lo:hi], graph["weight"][lo:hi]):
            b = lookup.get(int(t))
            if b is not None:
                w[b, a] += c
    return w, [r[1] for r in rows], [r[2] for r in rows]


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    w, kind, label = load()
    norm = w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)
    inhib = np.array([k == "Delta7" or k in CHOSEN for k in kind])
    W_exc, W_inh = norm * ~inhib[None, :], norm * inhib[None, :]
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    angles = np.array([rd.phi(*label[i]) for i in epg])
    pen = np.array([k.startswith("PEN") for k in kind])
    side = np.array([(label[i][0] if label[i] else "") for i in range(len(kind))])
    cue = np.zeros(len(kind))
    cue[epg] = np.maximum(0, np.cos(angles))
    steps_cue, steps_free = int(rd.CUE / rd.DT), int(rd.FREE / rd.DT)
    candidates = []
    for gE, gI, b in itertools.product((0.5, 1, 1.5, 2, 3, 4, 6, 8), (0.5, 1, 2, 3, 4, 6, 8), (0.05, 0.1, 0.2, 0.4)):
        r, _ = rd.simulate(W_exc, W_inh, gE, gI, b, 0.0, cue, steps_cue, steps_free)
        pos, strength = rd.readout(r, epg, angles)
        ok = strength >= 0.5 and abs(np.degrees(pos)) <= 22.5 and r[epg].mean() > 0.01 and np.mean(r[epg] >= 1 - 1e-9) < 0.5
        candidates.append({"gE": gE, "gI": gI, "b": b, "R_b": strength, "position_deg": float(np.degrees(pos)),
                           "epg_mean": float(r[epg].mean()), "ok": bool(ok)})
    passing = [c for c in candidates if c["ok"]]
    result = {"schema": "ce-a1-step01b-ring-dynamics-expanded", "code_sha256": code_hash, "neurons": len(kind),
              "grid": len(candidates), "grid_passing_T1": len(passing)}
    if not passing:
        result.update({"T1": False, "verdict": "A1_RING_DYNAMICS_EXPANDED_NOT_SUPPORTED",
                       "best_candidates": sorted(candidates, key=lambda c: -c["R_b"])[:5]})
    else:
        best = max(passing, key=lambda c: c["R_b"])
        gE, gI, b = best["gE"], best["gI"], best["b"]
        r0, _ = rd.simulate(W_exc, W_inh, gE, gI, b, 0.0, cue, steps_cue, steps_free)
        width = rd.fwhm(r0, epg, label)
        velocities = {}
        for u in (-0.1, -0.05, -0.02, 0.02, 0.05, 0.1):
            drive = np.where(pen & (side == "L"), u, 0.0) + np.where(pen & (side == "R"), -u, 0.0)
            _, trace = rd.simulate(W_exc, W_inh, gE, gI, b, drive, cue, steps_cue, int(100 / rd.DT))
            pos = np.unwrap([rd.readout(t, epg, angles)[0] for t in trace])
            span = int(80 / (rd.DT * 20))
            velocities[u] = float(np.degrees(pos[-1] - pos[-1 - span]) / 80.0)
        us = np.array(sorted(velocities))
        vs = np.array([velocities[u] for u in us])
        k = float(us @ vs / (us @ us))
        r2 = float(1 - np.sum((vs - k * us) ** 2) / np.sum((vs - vs.mean()) ** 2)) if np.ptp(vs) > 0 else 0.0
        opposite = all(velocities[u] * velocities[-u] < 0 for u in (0.02, 0.05, 0.1))
        odd = all(abs(velocities[u] + velocities[-u]) <= 0.25 * np.mean(np.abs(vs)) for u in (0.02, 0.05, 0.1))
        t2, t3 = opposite and r2 >= 0.9 and odd, 70 <= width <= 130
        result.update({"T1": True, "selected": best, "n_passing_examples": passing[:5],
                       "T2": {"velocity_deg_per_tau": {str(u): v for u, v in velocities.items()}, "gain_deg_per_tau_per_u": k,
                              "R2": r2, "opposite": opposite, "odd": odd, "pass": t2},
                       "T3": {"fwhm_deg": width, "pass": t3}})
        result["verdict"] = "A1_RING_DYNAMICS_EXPANDED_SUPPORTED_L0" if t2 and t3 else "A1_RING_DYNAMICS_EXPANDED_NOT_SUPPORTED"
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
