"""A1 loop step 1: run A1 dynamics on the real MaleCNS head-direction ring weights (CONTRACT.md).

python ring_dynamics.py    refuses to run unless CONTRACT.md lists this code hash
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
ROOT = HERE.parents[2]
MALECNS = ROOT / "verify/MaleCNS"
TYPES = ("EPG", "PEN_a(PEN1)", "PEN_b(PEN2)", "PEG", "Delta7")
GLOM = re.compile(r"_([LR])([1-9])")
DT, CUE, FREE = 0.05, 20.0, 200.0


def phi(side, k):
    return np.radians(((8 - k) * 45.0) if side == "L" else ((k - 1.5) * 45.0)) % (2 * np.pi)


def load():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    spec = importlib.util.spec_from_file_location("g", MALECNS / "neuron_graph.py")
    gm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gm)
    graph = gm.load(MALECNS / "neuron_graph_result.json")
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    position, found = gm.locate(table["bodyId"].to_numpy(), graph["node_ids"])
    ty, inst = table["type"].to_pylist(), table["instance"].to_pylist()
    nodes, kind, label = [], [], []
    for i in np.flatnonzero(found):
        if ty[i] in TYPES:
            m = GLOM.search(inst[i] or "")
            nodes.append(int(position[i]))
            kind.append(ty[i])
            label.append((m.group(1), int(m.group(2))) if m else None)
    order = np.argsort(nodes)
    nodes = np.array(nodes)[order]
    kind = [kind[o] for o in order]
    label = [label[o] for o in order]
    n = len(graph["node_ids"])
    w = np.zeros((len(nodes), len(nodes)))
    lookup = {v: i for i, v in enumerate(nodes)}
    for a, v in enumerate(nodes):
        lo, hi = graph["indptr"][v], graph["indptr"][v + 1]
        for t, c in zip(graph["indices"][lo:hi], graph["weight"][lo:hi]):
            b = lookup.get(int(t))
            if b is not None:
                w[b, a] += c  # w[post, pre]
    return w, kind, label


def simulate(W_exc, W_inh, gE, gI, b, drive, cue, steps_cue, steps_free, record_every=20):
    r = np.zeros(W_exc.shape[0])
    trace = []
    for step in range(steps_cue + steps_free):
        inp = gE * W_exc @ r - gI * W_inh @ r + b + drive + (cue if step < steps_cue else 0)
        r += DT * (-r + np.clip(inp, 0, 1))
        if step >= steps_cue and (step - steps_cue) % record_every == 0:
            trace.append(r.copy())
    return r, np.array(trace)


def readout(r, epg, angles):
    z = np.sum(r[epg] * np.exp(1j * angles))
    total = r[epg].sum()
    return (float(np.angle(z)), float(abs(z) / total) if total > 0 else 0.0)


def fwhm(r, epg, labels):
    groups = sorted({labels[i] for i in epg}, key=lambda k: phi(*k))
    ang = np.array([phi(*k) for k in groups])
    val = np.array([np.mean([r[i] for i in epg if labels[i] == k]) for k in groups])
    grid = np.radians(np.arange(360))
    ext_a = np.r_[ang - 2 * np.pi, ang, ang + 2 * np.pi]
    ext_v = np.r_[val, val, val]
    fine = np.interp(grid, ext_a, ext_v)
    thr = fine.min() + (fine.max() - fine.min()) / 2
    return float(np.sum(fine >= thr)) if fine.max() > fine.min() else 360.0


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    w, kind, label = load()
    norm = w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)
    inhib = np.array([k == "Delta7" for k in kind])
    W_exc, W_inh = norm * ~inhib[None, :], norm * inhib[None, :]
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    angles = np.array([phi(*label[i]) for i in epg])
    pen = np.array([k.startswith("PEN") for k in kind])
    side = np.array([(label[i][0] if label[i] else "") for i in range(len(kind))])
    cue = np.zeros(len(kind))
    cue[epg] = np.maximum(0, np.cos(angles))
    steps_cue, steps_free = int(CUE / DT), int(FREE / DT)
    candidates = []
    for gE, gI, b in itertools.product((0.5, 1, 1.5, 2, 3, 4), (0.5, 1, 2, 3, 4, 6), (0.05, 0.1, 0.2, 0.4)):
        r, _ = simulate(W_exc, W_inh, gE, gI, b, 0.0, cue, steps_cue, steps_free)
        pos, strength = readout(r, epg, angles)
        ok = strength >= 0.5 and abs(np.degrees(pos)) <= 22.5 and r[epg].mean() > 0.01 and np.mean(r[epg] >= 1 - 1e-9) < 0.5
        candidates.append({"gE": gE, "gI": gI, "b": b, "R_b": strength, "position_deg": float(np.degrees(pos)),
                           "epg_mean": float(r[epg].mean()), "ok": bool(ok)})
    passing = [c for c in candidates if c["ok"]]
    result = {"schema": "ce-a1-step01-ring-dynamics", "code_sha256": code_hash,
              "neurons": {k: int(sum(x == k for x in kind)) for k in TYPES}, "grid_passing_T1": len(passing)}
    if not passing:
        result.update({"T1": False, "verdict": "A1_RING_DYNAMICS_NOT_SUPPORTED", "best_candidates":
                       sorted(candidates, key=lambda c: -c["R_b"])[:5]})
    else:
        best = max(passing, key=lambda c: c["R_b"])
        gE, gI, b = best["gE"], best["gI"], best["b"]
        r0, _ = simulate(W_exc, W_inh, gE, gI, b, 0.0, cue, steps_cue, steps_free)
        width = fwhm(r0, epg, label)
        velocities = {}
        for u in (-0.1, -0.05, -0.02, 0.02, 0.05, 0.1):
            drive = np.where(pen & (side == "L"), u, 0.0) + np.where(pen & (side == "R"), -u, 0.0)
            _, trace = simulate(W_exc, W_inh, gE, gI, b, drive, cue, steps_cue, int(100 / DT))
            pos = np.unwrap([readout(t, epg, angles)[0] for t in trace])
            span = int(80 / (DT * 20))
            velocities[u] = float(np.degrees(pos[-1] - pos[-1 - span]) / 80.0)
        us = np.array(sorted(velocities))
        vs = np.array([velocities[u] for u in us])
        k = float(us @ vs / (us @ us))
        r2 = float(1 - np.sum((vs - k * us) ** 2) / np.sum((vs - vs.mean()) ** 2)) if np.ptp(vs) > 0 else 0.0
        opposite = all(velocities[u] * velocities[-u] < 0 for u in (0.02, 0.05, 0.1))
        odd = all(abs(velocities[u] + velocities[-u]) <= 0.25 * np.mean(np.abs(vs)) for u in (0.02, 0.05, 0.1))
        t2 = opposite and r2 >= 0.9 and odd
        t3 = 70 <= width <= 130
        result.update({"T1": True, "selected": best, "T2": {"velocity_deg_per_tau": {str(u): v for u, v in velocities.items()},
                       "gain_deg_per_tau_per_u": k, "R2": r2, "opposite": opposite, "odd": odd, "pass": t2},
                       "T3": {"fwhm_deg": width, "literature": "~100 deg EB, ~90 deg PB (Turner-Evans 2017)", "pass": t3}})
        result["verdict"] = "A1_RING_DYNAMICS_SUPPORTED_L0" if t2 and t3 else "A1_RING_DYNAMICS_NOT_SUPPORTED"
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
