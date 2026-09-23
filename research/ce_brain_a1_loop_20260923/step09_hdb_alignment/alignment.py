"""A1 loop step 9: why did the PFN->hDeltaB composition not rotate? (CONTRACT.md)

python alignment.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fv = load("fb_vectors", LOOP / "step03_fb_vector_memory/fb_vectors.py")
fp = load("fb_phase", LOOP / "step08_fb_phase_coordinate/fb_phase.py")


def R(angles):
    return float(abs(np.mean(np.exp(1j * np.asarray(angles))))) if len(angles) else 0.0


def cmean(angles):
    return float(np.angle(np.mean(np.exp(1j * np.asarray(angles)))))


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    gm = load("g", fv.MALECNS / "neuron_graph.py")
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
    slope = np.linalg.lstsq(design, xs, rcond=None)[0][0]
    scale = 1.0 / slope  # signed: x -> degrees in the E1 frame
    phi_of = {b: np.radians(fv.phi_unwrapped(info[b][1], info[b][2])) for b in bodies}
    rows = []
    for h in sorted(set(hout_b.tolist())):
        xin, xout = x_of(hin_xyz[hin_b == h]), x_of(hout_xyz[hout_b == h])
        allx = np.r_[xin, xout]
        is_out = np.r_[np.zeros(len(xin), bool), np.ones(len(xout), bool)]
        assign, lo, hi = fp.two_means(allx)
        axon_hi = is_out[assign].mean() >= is_out[~assign].mean()
        x_axon, x_dend = (hi, lo) if axon_hi else (lo, hi)
        psi_axon, psi_dend = np.radians(scale * x_axon), np.radians(scale * x_dend)
        m = post == h
        syn_x = x_of(xyz[m])
        syn_phi = np.array([phi_of[b] for b in pre[m]])
        on_axon = np.abs(syn_x - x_axon) < np.abs(syn_x - x_dend)
        beta = lambda sel: float(np.angle(np.sum(np.exp(1j * syn_phi[sel])))) if sel.any() else np.nan
        rows.append({"body": int(h), "psi_axon": float(psi_axon), "psi_dend": float(psi_dend),
                     "beta_all": beta(np.ones(len(syn_phi), bool)), "beta_axon": beta(on_axon), "beta_dend": beta(~on_axon),
                     "pfn_synapses": int(m.sum()), "fraction_on_axon": float(on_axon.mean()) if m.any() else np.nan})
    psi = np.array([r["psi_axon"] for r in rows])
    d_all = [np.angle(np.exp(1j * (r["psi_axon"] - r["beta_all"]))) for r in rows if np.isfinite(r["beta_all"])]
    d_ax = [np.angle(np.exp(1j * (r["psi_axon"] - r["beta_axon"]))) for r in rows if np.isfinite(r["beta_axon"])]
    d_de = [np.angle(np.exp(1j * (r["psi_axon"] - r["beta_dend"]))) for r in rows if np.isfinite(r["beta_dend"])]
    result = {"schema": "ce-a1-step09-hdb-alignment", "code_sha256": code_hash, "hdb": len(rows),
              "Q1_coverage": {"resultant": R(psi), "psi_axon_deg_sorted": sorted(np.degrees(psi).round(1).tolist()),
                              "pass": R(psi) <= 0.3},
              "Q2_alignment_all": {"R": R(d_all), "mean_offset_deg": float(np.degrees(cmean(d_all))), "pass": R(d_all) >= 0.7},
              "Q3_by_compartment": {"R_axon_inputs": R(d_ax), "mean_offset_axon_deg": float(np.degrees(cmean(d_ax))),
                                    "R_dend_inputs": R(d_de), "mean_offset_dend_deg": float(np.degrees(cmean(d_de))),
                                    "offset_difference_deg": float(np.degrees(np.angle(np.exp(1j * (cmean(d_ax) - cmean(d_de)))))),
                                    "pass": R(d_ax) >= 0.7 and R(d_de) >= 0.7},
              "per_neuron": rows}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps({k: v for k, v in result.items() if k != "per_neuron"}, indent=1, default=float))


if __name__ == "__main__":
    main()
