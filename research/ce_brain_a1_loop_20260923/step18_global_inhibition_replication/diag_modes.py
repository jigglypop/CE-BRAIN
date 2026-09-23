"""Post-hoc diagnostic for step 18 (does NOT change the frozen verdict METHOD_CONTROL_FAILED).

What is the mode right below the memory pair in the expanded operator? EPG harmonic powers of the top
non-uniform modes, measured against the label-free pair angle theta (both datasets) and, for MaleCNS,
against the E1 glomerulus angle phi.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re

import numpy as np
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("gi", HERE / "gi_replication.py")
gi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gi)
lf = gi.lf
GLOM = re.compile(r"_([LR])([1-9])")


def powers(v, ang):
    tot = np.sum(np.abs(v) ** 2)
    return [float((abs(np.sum(v * np.exp(-1j * m * ang))) ** 2 + (abs(np.sum(v * np.exp(1j * m * ang))) ** 2 if m else 0))
                  / (len(v) * tot)) for m in (0, 1, 2, 3)]


def modes(A, node_type, node_side, node_nt, inst=None):
    chosen, members = gi.select(A, node_type, node_nt)
    base = [v for v in range(len(node_type)) if node_type[v] in gi.BASE]
    nodes = np.array(sorted(base + [v for t in chosen for v in members[t]]))
    kind = [node_type[v] for v in nodes]
    w = A[nodes, :][:, nodes].toarray().T
    sign = np.array([-1.0 if (k == "Delta7" or k in chosen) else 1.0 for k in kind])
    W = (w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :]
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    _, theta, _, _ = lf.ring_pair(W, epg)
    lam, right = eig(W)
    order = np.argsort(-lam.real)
    phi = None
    if inst is not None:
        lab = [GLOM.search(inst[nodes[i]] or "") for i in epg]
        phi = np.array([lf.phi(m.group(1), int(m.group(2))) for m in lab])
    rows = []
    for k in order[:10]:
        v = right[epg, k]
        # EPG share of the mode's squared norm (is the mode even on EPG?)
        share = float(np.sum(np.abs(v) ** 2) / np.sum(np.abs(right[:, k]) ** 2))
        ring_share = float(np.sum(np.abs(right[[i for i, t in enumerate(kind) if t in chosen], k]) ** 2) / np.sum(np.abs(right[:, k]) ** 2))
        r = {"re": round(float(lam[k].real), 4), "im": round(float(lam[k].imag), 4), "P_theta": [round(x, 3) for x in powers(v, theta)],
             "epg_norm_share": round(share, 3), "inhib_norm_share": round(ring_share, 3)}
        if phi is not None:
            r["P_phi_E1"] = [round(x, 3) for x in powers(v, phi)]
        rows.append(r)
    return rows


def main():
    import pyarrow as pa
    import pyarrow.ipc as ipc
    A, t, s, nt = gi.malecns()
    gm = gi.load("g", lf.MALECNS / "neuron_graph.py")
    graph = gm.load(lf.MALECNS / "neuron_graph_result.json")
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        ann = ipc.open_file(source).read_all()
    inst = np.full(len(t), "", dtype=object)
    pos, found = gm.locate(ann["bodyId"].to_numpy(), graph["node_ids"])
    for p, f, x in zip(pos, found, ann["instance"].to_pylist()):
        if f:
            inst[p] = x or ""
    out = {"note": "post-hoc diagnostic; frozen verdict unchanged", "malecns": modes(A, t, s, nt, inst), "flywire": modes(*gi.flywire())}
    (HERE / "diag_modes.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for name in ("malecns", "flywire"):
        print(name)
        for r in out[name]:
            print("  ", r)


if __name__ == "__main__":
    main()
