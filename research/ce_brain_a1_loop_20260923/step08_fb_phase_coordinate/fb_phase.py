"""A1 loop step 8: does compartment-split hDeltaB geometry give a ~180 deg shift on the PFN scale? (CONTRACT.md)

python fb_phase.py    refuses to run unless CONTRACT.md lists this code hash
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


def two_means(x, iters=100):
    lo, hi = np.quantile(x, 0.25), np.quantile(x, 0.75)
    for _ in range(iters):
        assign = np.abs(x - hi) < np.abs(x - lo)
        if assign.all() or (~assign).all():
            break
        new_lo, new_hi = x[~assign].mean(), x[assign].mean()
        if np.isclose(new_lo, lo) and np.isclose(new_hi, hi):
            break
        lo, hi = new_lo, new_hi
    return assign, lo, hi


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
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
    scale = abs(1.0 / np.linalg.lstsq(design, xs, rcond=None)[0][0])
    rows = []
    for h in sorted(set(hin_b.tolist()) | set(hout_b.tolist())):
        xin, xout = x_of(hin_xyz[hin_b == h]), x_of(hout_xyz[hout_b == h])
        allx = np.r_[xin, xout]
        is_out = np.r_[np.zeros(len(xin), bool), np.ones(len(xout), bool)]
        if len(xout) < 5 or len(xin) < 5:
            continue
        assign, lo, hi = two_means(allx)
        frac_hi = is_out[assign].mean() if assign.any() else 0.0
        frac_lo = is_out[~assign].mean() if (~assign).any() else 0.0
        axon_is_hi = frac_hi >= frac_lo
        axon_mask = assign if axon_is_hi else ~assign
        polarity = float(np.mean(axon_mask[is_out]))
        sep = abs(hi - lo) * scale
        rows.append({"body": int(h), "inputs": int(len(xin)), "outputs": int(len(xout)),
                     "output_fraction_in_axon_cluster": polarity, "dendrite_axon_deg": float(sep)})
    pol = np.array([r["output_fraction_in_axon_cluster"] for r in rows])
    sep = np.array([r["dendrite_axon_deg"] for r in rows])
    p8a = float(np.mean(pol >= 0.7))
    result = {"schema": "ce-a1-step08-fb-phase", "code_sha256": code_hash, "deg_per_x_unit": float(scale),
              "hdb_neurons": len(rows), "P8a": {"fraction_polarized": p8a, "pass": p8a >= 0.75},
              "P8b": {"median_sep_deg": float(np.median(sep)), "iqr_deg": np.quantile(sep, [0.25, 0.75]).tolist(),
                      "pass": 135 <= float(np.median(sep)) <= 225},
              "per_neuron": rows}
    result["verdict"] = "FB_PHASE_COORDINATE_SUPPORTED" if result["P8a"]["pass"] and result["P8b"]["pass"] \
        else "FB_PHASE_COORDINATE_NOT_SUPPORTED"
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps({k: v for k, v in result.items() if k != "per_neuron"}, indent=1, default=float))
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
