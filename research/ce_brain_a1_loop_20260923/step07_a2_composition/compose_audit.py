"""AUDIT copy (only change: hDeltaB drive is mean-subtracted before the population vector, i.e. first-harmonic readout).

A1 loop step 7: does the real PFN->hDeltaB wiring compute a four-phasor vector sum? (CONTRACT.md)

python compose.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fb_vectors", HERE.parent / "step03_fb_vector_memory/fb_vectors.py")
fv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fv)
GROUPS = ("dL", "dR", "vL", "vR")


def wrap_rad(a):
    return np.angle(np.exp(1j * a))


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    import pyarrow as pa
    import pyarrow.ipc as ipc
    spec_g = importlib.util.spec_from_file_location("g", fv.MALECNS / "neuron_graph.py")
    gm = importlib.util.module_from_spec(spec_g)
    spec_g.loader.exec_module(gm)
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    info, hdb = {}, []
    for body, t, inst in zip(table["bodyId"].to_pylist(), table["type"].to_pylist(), table["instance"].to_pylist()):
        m = fv.PFN.match(inst or "")
        if m:
            info[body] = (m.group(1), m.group(2), int(m.group(3)))
        elif t == "hDeltaB":
            hdb.append(body)
    (pre, post, xyz), (hin_b, hin_xyz), (hout_b, hout_xyz) = fv.stream(gm, np.array(list(info)), np.array(hdb))
    centre = xyz.mean(axis=0)
    axis = np.linalg.svd(xyz - centre, full_matrices=False)[2][0]
    x_of = lambda p: (p - centre) @ axis
    bodies = sorted(set(pre.tolist()))
    group = {b: info[b][0][-1] + info[b][1] for b in bodies}
    names = sorted(set(group.values()))
    xs = np.array([x_of(xyz[pre == b]).mean() for b in bodies])
    ph = np.array([fv.phi_unwrapped(info[b][1], info[b][2]) for b in bodies])
    design = np.column_stack([ph] + [[1.0 if group[b] == g else 0.0 for b in bodies] for g in names])
    scale = 1.0 / np.linalg.lstsq(design, xs, rcond=None)[0][0]
    axon = {h: x_of(hout_xyz[hout_b == h]).mean() for h in set(hout_b.tolist())}
    hlist = sorted(axon)
    psi = np.radians(np.array([scale * axon[h] for h in hlist]))
    W = np.zeros((len(bodies), len(hlist)))
    hindex = {h: j for j, h in enumerate(hlist)}
    for b_i, b in enumerate(bodies):
        targets = post[(pre == b)]
        for h in targets:
            j = hindex.get(int(h))
            if j is not None:
                W[b_i, j] += 1
    phi = np.radians(ph)
    # group offsets O_k exactly as in step 3
    O = {}
    for g in names:
        offs = []
        for b_i, b in enumerate(bodies):
            if group[b] == g and W[b_i].sum() > 0:
                p = np.angle(np.sum(W[b_i] * np.exp(1j * psi)))
                offs.append(wrap_rad(p - phi[b_i]))
        O[g] = float(np.angle(np.sum(np.exp(1j * np.array(offs)))))
    gidx = np.array([GROUPS.index(group[b]) for b in bodies])
    thetas = np.radians(np.arange(16) * 22.5)

    def output(theta, a):
        r = a[gidx] * (1 + np.cos(theta - phi))
        h = r @ W
        z = np.sum((h - h.mean()) * np.exp(1j * psi))
        return np.angle(z), abs(z)
    # C1
    ones = np.ones(4)
    out1 = np.unwrap([output(t, ones)[0] for t in thetas])
    slope, intercept = np.polyfit(thetas, out1, 1)
    resid = wrap_rad(out1 - (slope * thetas + intercept))
    c1 = {"slope": float(slope), "resid_sd_deg": float(np.degrees(resid.std())),
          "pass": 0.9 <= slope <= 1.1 and np.degrees(resid.std()) < 15}
    # C2, C3
    rng = np.random.default_rng(20260923)
    O_vec = np.exp(1j * np.array([O[g] for g in GROUPS]))
    diffs, mags_model, mags_pred = [], [], []
    for _ in range(200):
        a = rng.uniform(0, 1, 4)
        pred_phase = np.angle(np.sum(a * O_vec))
        mags_pred.append(abs(np.sum(a * O_vec)))
        m_acc = []
        for t in thetas:
            p, m = output(t, a)
            diffs.append(wrap_rad(p - t - pred_phase))
            m_acc.append(m)
        mags_model.append(np.mean(m_acc))
    diffs = np.array(diffs)
    c = np.angle(np.mean(np.exp(1j * diffs)))
    err = np.degrees(np.abs(wrap_rad(diffs - c)))
    c2 = {"global_constant_deg": float(np.degrees(c)), "median_abs_err_deg": float(np.median(err)),
          "p90_abs_err_deg": float(np.quantile(err, 0.9)), "pass": np.median(err) < 15 and np.quantile(err, 0.9) < 30}
    r = float(np.corrcoef(mags_model, mags_pred)[0, 1])
    c3 = {"corr_magnitude": r, "pass": r >= 0.9}
    ok = c1["pass"] and c2["pass"] and c3["pass"]
    result = {"schema": "ce-a1-step07-a2-composition-audit", "code_sha256": code_hash, "offsets_deg": {g: float(np.degrees(v)) for g, v in O.items()},
              "pfn_neurons": len(bodies), "hdb_neurons": len(hlist), "pfn_to_hdb_synapses": int(W.sum()),
              "C1": c1, "C2": c2, "C3": c3,
              "verdict": "A2_PHASOR_SUM_SUPPORTED_L0" if ok else "A2_PHASOR_SUM_NOT_SUPPORTED"}
    with (HERE / "results_audit_mean_subtracted.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
