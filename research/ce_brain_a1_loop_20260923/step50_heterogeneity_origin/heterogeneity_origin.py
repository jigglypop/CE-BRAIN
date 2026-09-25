"""A1 step 50: is the neuron-level heterogeneity that creates wells (steps 47-49) reproducible structure or
individual/measurement variability, and is it beyond what the ring tolerates? (CONTRACT.md)

Networks and flows as in step 48 (E, I = symmetric flow-normalised parts; directions = PB glomerulus labels, E1).
Q1  16x16 direction kernel of K = E - I (mean input per neuron of direction a from all neurons of direction b);
    deviation from its circulant mean; correlation MaleCNS vs hemibrain; null = 2000 consistent relabellings.
Q2  E-PG count per direction, MaleCNS vs hemibrain.
Q3  drift field: signed hold error of the step 47 N2 network (gain from step 47) at 64 cue positions;
    correlation MaleCNS vs hemibrain; null = the 63 circular shifts of the hemibrain field.
Q4  tolerance: uniform ring with 3 units per direction built from the MaleCNS direction kernels of E and I,
    multiplicative lognormal noise sigma on every weight, best gain within +-20 %, retention (22.5 deg, 64 cues).
    Heterogeneity measured as d = ||X - X1||_F / ||X1||_F (X1 = angle-averaged kernel at the pair offsets),
    the same measure for the synthetic noise and for the connectome.

python heterogeneity_origin.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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


hr = load("homeostatic_ring", LOOP / "step48_homeostatic_scaling/homeostatic_ring.py")
nl, c46 = hr.nl, hr.c46
SIGMAS = (0.0, 0.02, 0.05, 0.1, 0.2, 0.3)
SEEDS = (1, 2, 3)
N_NULL = 2000
PAIR = ("malecns", "hemibrain")


def dirs_of(ang):
    return np.round(np.degrees(ang) / 22.5).astype(int) % 16


def direction_kernel(K, ang):
    d = dirs_of(ang)
    out = np.zeros((16, 16))
    for a in range(16):
        for b in range(16):
            ia, ib = np.flatnonzero(d == a), np.flatnonzero(d == b)
            if ia.size and ib.size:
                out[a, b] = K[np.ix_(ia, ib)].sum(1).mean()
    return out


def deviation(Kd):
    m = np.array([np.mean([Kd[a, (a - k) % 16] for a in range(16)]) for k in range(16)])
    return np.array([[Kd[a, b] - m[(a - b) % 16] for b in range(16)] for a in range(16)])


def perm_corr(x, y, seed):
    r = float(np.corrcoef(x.ravel(), y.ravel())[0, 1])
    rng = np.random.default_rng(seed)
    null = np.array([np.corrcoef(x.ravel(), y[np.ix_(p, p)].ravel())[0, 1] for p in (rng.permutation(16) for _ in range(N_NULL))])
    return {"r": r, "null_p95": float(np.percentile(null, 95)), "p": float((1 + np.sum(null >= r)) / (1 + N_NULL))}


def q1(Ms):
    out = {}
    for part, f in (("K", lambda M: M["E"] - M["I"]), ("E", lambda M: M["E"]), ("I", lambda M: M["I"])):
        dev = [deviation(direction_kernel(f(Ms[k]), Ms[k]["ang"])) for k in PAIR]
        out[part] = perm_corr(dev[0], dev[1], 20260925)
    return out


def q2(Ms):
    c = {k: np.bincount(dirs_of(Ms[k]["ang"]), minlength=16) for k in PAIR}
    return {"counts": {k: v.tolist() for k, v in c.items()}, "identical": bool(np.array_equal(*c.values())),
            "corr": float(np.corrcoef(*c.values())[0, 1]), "n_equal_directions": int(np.sum(c[PAIR[0]] == c[PAIR[1]]))}


def clusters(finals):
    """End positions grouped as in step 47 (a new group when > 11.25 deg from every earlier one): [position, count]."""
    ends = []
    for f in sorted(np.mod(finals, 360)):
        near = [e for e in ends if abs((f - e[0] + 180) % 360 - 180) <= 11.25]
        if near:
            near[0][1] += 1
        else:
            ends.append([float(f), 1])
    return ends


def q3(Ms, s47):
    fields = {}
    for k in PAIR:
        g = s47["datasets"][k]["networks"]["0.0"]["g"]
        e = nl.hold_errors(g * (Ms[k]["E"] - Ms[k]["I"]), Ms[k]["ang"], nl.CUES)
        fields[k] = e
    a, b = fields[PAIR[0]], fields[PAIR[1]]
    r = float(np.corrcoef(a, b)[0, 1])
    null = np.array([np.corrcoef(a, np.roll(b, s))[0, 1] for s in range(1, a.size)])
    ends = {k: clusters((nl.CUES + fields[k]) % 360) for k in PAIR}
    return {"r": r, "p": float((1 + np.sum(null >= r)) / a.size), "best_shift_deg": float(5.625 * (1 + int(np.argmax(null)))),
            "fields": {k: v.tolist() for k, v in fields.items()}, "end_positions": ends}


def rel_dev(X, X1):
    return float(np.linalg.norm(X - X1) / np.linalg.norm(X1))


def smooth_part(X, ang):
    k16 = nl.kernel16(X, ang)
    return nl.at_offsets((k16 + k16[(-np.arange(16)) % 16]) / 2, ang)


def observed(M):
    return {part: rel_dev(M[part], smooth_part(M[part], M["ang"])) for part in ("E", "I")}


def q4(M, g_star):
    ang3 = np.radians(np.repeat(np.arange(16) * 22.5, 3))
    kE, kI = nl.kernel16(M["E"], M["ang"]), nl.kernel16(M["I"], M["ang"])
    E3 = nl.at_offsets((kE + kE[(-np.arange(16)) % 16]) / 2, ang3)
    I3 = nl.at_offsets((kI + kI[(-np.arange(16)) % 16]) / 2, ang3)
    g1 = g_star * 16 / ang3.size
    rows = []
    for s in SIGMAS:
        for seed in (SEEDS if s > 0 else SEEDS[:1]):
            rng = np.random.default_rng(seed)
            En = E3 * np.exp(s * rng.standard_normal(E3.shape) - s * s / 2)
            In = I3 * np.exp(s * rng.standard_normal(I3.shape) - s * s / 2)
            row = {"sigma": s, "seed": seed, "d_E": rel_dev(En, E3), "d_I": rel_dev(In, I3)}
            bg = nl.best_gain(En - In, ang3, g1)
            e = None if bg is None else nl.hold_errors(bg[0] * (En - In), ang3, nl.CUES)
            if e is None:
                row.update({"retention": 0.0, "failed": True})
            else:
                row.update({"g_over_mapped": bg[0] / g1, "retention": float(np.mean(np.abs(e) <= 22.5)), "max_abs_err": float(np.max(np.abs(e))),
                            "median_abs_err": float(np.median(np.abs(e))), "end_positions": nl.wells((nl.CUES + e) % 360)})
            rows.append(row)
            print("   Q4", json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
    mean_ret = {str(s): float(np.mean([r["retention"] for r in rows if r["sigma"] == s])) for s in SIGMAS}
    mean_d = {str(s): float(np.mean([r["d_E"] for r in rows if r["sigma"] == s])) for s in SIGMAS}
    crit = next((s for s in SIGMAS if mean_ret[str(s)] < 0.8), None)
    return {"rows": rows, "mean_retention": mean_ret, "mean_d_E": mean_d, "sigma_crit": crit,
            "d_crit": None if crit is None else mean_d[str(crit)]}


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step48_homeostatic_scaling/homeostatic_ring.py", LOOP / "step47_neuron_level_wells/neuron_level_wells.py",
            LOOP / "step46_connectome_ring_class/connectome_ring_class.py", LOOP / "step41_few_neuron_attractor/tl_ring.py",
            LOOP / "step41_few_neuron_attractor/few_neuron_ring.py", LOOP / "step42_kim_support_ring/kim_support_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    s46 = json.loads((LOOP / "step46_connectome_ring_class/results.json").read_text(encoding="utf-8"))
    s47 = json.loads((LOOP / "step47_neuron_level_wells/results.json").read_text(encoding="utf-8"))
    ds = c46.datasets()
    Ms = {k: hr.matrices(*ds[k]) for k in ("malecns", "hemibrain", "flywire")}
    res = {"Q1": q1(Ms), "Q2": q2(Ms)}
    print("Q1", json.dumps(res["Q1"]), "\nQ2", json.dumps(res["Q2"]), flush=True)
    res["Q3"] = q3(Ms, s47)
    print("Q3 r", res["Q3"]["r"], "p", res["Q3"]["p"], "ends", res["Q3"]["end_positions"], flush=True)
    res["observed_d"] = {k: observed(M) for k, M in Ms.items()}
    print("observed d", json.dumps(res["observed_d"]), flush=True)
    res["Q4"] = q4(Ms["malecns"], s46["datasets"]["malecns"]["variants"]["connectome"]["g_star"])
    p1, p3 = res["Q1"]["K"]["p"] < 0.05, res["Q3"]["p"] < 0.05
    res["reproducibility"] = "STRUCTURE" if (p1 and p3) else "IDIOSYNCRATIC" if not (p1 or p3) else "MIXED"
    d_obs = min(v["E"] for v in res["observed_d"].values())
    res["P_tolerance_exceeded"] = bool(res["Q4"]["d_crit"] is not None and d_obs > res["Q4"]["d_crit"])
    result = {"schema": "ce-a1-step50-heterogeneity-origin", "hashes": hashes, **res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("reproducibility", res["reproducibility"], "tolerance_exceeded", res["P_tolerance_exceeded"], "d_obs(E) min", d_obs,
          "d_crit", res["Q4"]["d_crit"], "mean retention", res["Q4"]["mean_retention"])


if __name__ == "__main__":
    main()
