"""A1 loop step 10: per-group rotation-equivariant phasors and their vector sum (CONTRACT.md).

python compose_v2.py    refuses to run unless CONTRACT.md lists this code hash
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


def wrap(a):
    return np.angle(np.exp(1j * a))


def prepare():
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
    (pre, post, xyz), _, (hout_b, hout_xyz) = fv.stream(gm, np.array(list(info)), np.array(hdb))
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
    hlist = sorted(set(hout_b.tolist()))
    psi = np.radians(np.array([scale * x_of(hout_xyz[hout_b == h]).mean() for h in hlist]))
    hindex = {h: j for j, h in enumerate(hlist)}
    W = np.zeros((len(bodies), len(hlist)))
    for b_i, b in enumerate(bodies):
        for h in post[pre == b]:
            j = hindex.get(int(h))
            if j is not None:
                W[b_i, j] += 1
    gidx = np.array([GROUPS.index(group[b]) for b in bodies])
    return W, np.radians(ph), psi, gidx


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    W, phi, psi, gidx = prepare()
    thetas = np.radians(np.arange(16) * 22.5)

    def z_of(theta, a):
        h = (a[gidx] * (1 + np.cos(theta - phi))) @ W
        return np.sum((h - h.mean()) * np.exp(1j * psi))
    c1, O, A = {}, {}, {}
    for k, g in enumerate(GROUPS):
        a = np.zeros(4)
        a[k] = 1.0
        zs = np.array([z_of(t, a) for t in thetas])
        ang = np.unwrap(np.angle(zs))
        slope, icpt = np.polyfit(thetas, ang, 1)
        resid = wrap(ang - (slope * thetas + icpt))
        O[g] = float(np.angle(np.mean(zs * np.exp(-1j * thetas))))
        A[g] = float(np.mean(np.abs(zs)))
        c1[g] = {"slope": float(slope), "resid_sd_deg": float(np.degrees(resid.std())),
                 "pass": 0.9 <= slope <= 1.1 and np.degrees(resid.std()) < 15}
    o = np.array([O[g] for g in GROUPS])
    ordered = np.sort(np.mod(np.degrees(o), 360))
    gaps = np.diff(np.r_[ordered, ordered[0] + 360])
    d_center = np.angle(np.exp(1j * O["dL"]) + np.exp(1j * O["dR"]))
    v_center = np.angle(np.exp(1j * O["vL"]) + np.exp(1j * O["vR"]))
    center_diff = float(np.degrees(abs(wrap(d_center - v_center))))
    c2 = {"offsets_deg": {g: float(np.degrees(O[g])) for g in GROUPS}, "amplitudes": A, "gaps_deg": gaps.tolist(),
          "d_v_center_difference_deg": center_diff,
          "pass": bool(np.all(np.abs(gaps - 90) <= 30)) and abs(center_diff - 180) <= 30}
    rng = np.random.default_rng(20260923)
    phasor = np.array([A[g] * np.exp(1j * O[g]) for g in GROUPS])
    gains = rng.uniform(0, 1, size=(500, 4))
    mags = np.abs(gains @ phasor)
    keep = gains[mags >= 0.5 * mags.max()]
    errs = []
    for a in keep:
        pred = np.angle(a @ phasor)
        for t in thetas:
            errs.append(abs(np.degrees(wrap(np.angle(z_of(t, a)) - t - pred))))
    errs = np.array(errs)
    c3 = {"gain_sets_used": int(len(keep)), "median_err_deg": float(np.median(errs)), "p90_err_deg": float(np.quantile(errs, 0.9)),
          "pass": np.median(errs) < 10 and np.quantile(errs, 0.9) < 20}
    ok = all(v["pass"] for v in c1.values()) and c2["pass"] and c3["pass"]
    result = {"schema": "ce-a1-step10-a2-composition-v2", "code_sha256": code_hash, "C1_per_group": c1, "C2_geometry": c2,
              "C3_mixture": c3, "verdict": "A2_PHASOR_BASIS_SUPPORTED_L0" if ok else "A2_PHASOR_BASIS_NOT_SUPPORTED"}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
