"""A1 step 49: are the wells of the per-neuron connectome ring (step 47) caused by unequal input totals (excitability)
or by the connection patterns? Static proxy of completed homeostatic scaling: every E-PG's excitatory and inhibitory
input totals set to the population means, patterns unchanged. (CONTRACT.md)

Networks (threshold-linear, c = 1; step 48 E and I = symmetric parts of the step 47 flows):
  N2_rn      E_i. * mean(rowsum E) / rowsum E_i ,  I_i. likewise      (post-synaptic scaling; breaks symmetry)
  N2_rn_sym  symmetric part of N2_rn                                     (report)
  N1_rn      same normalisation of the step 47 N1 (angle-averaged weights, actual cell counts) (report)
Gain: best within +-20 % of g1 = g* 16 / n (minimal hold error, 16 positions). Velocity: PEN difference, rows scaled
with E.

python input_totals.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
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


def rownorm(M):
    rs = M.sum(1)
    return M * (rs.mean() / np.where(np.abs(rs) > 1e-12, rs, 1.0))[:, None], rs.mean() / np.where(np.abs(rs) > 1e-12, rs, 1.0)


def evaluate(K, A, ang, g1, label):
    bg = nl.best_gain(K, ang, g1)
    if bg is None:
        print("   ", label, "no usable gain", flush=True)
        return {"exists": False}
    t = hr.tests(bg[0] * K, bg[0] * A, ang)
    t["g"], t["g_over_mapped"] = bg[0], bg[0] / g1
    print("   ", label, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in t.items() if k not in ("rotation", "S2")}),
          "rot", round(t.get("rotation", {}).get("slow_over_fast_gain", float("nan")), 3), "S2", t.get("S2", {}).get("ratio_180_over_90"), flush=True)
    return t


def analyse(M, g_star):
    ang = M["ang"]
    n = ang.size
    g1 = g_star * 16 / n
    E_rn, sE = rownorm(M["E"])
    I_rn, _ = rownorm(M["I"])
    K_rn = E_rn - I_rn
    A_rn = sE[:, None] * M["A_pen"]
    k16 = c46.symmetrise(nl.kernel16(M["E"] - M["I"], ang))
    K1 = nl.at_offsets(k16, ang)
    K1 = (K1 + K1.T) / 2
    K1_rn = rownorm(np.maximum(K1, 0))[0] - rownorm(np.maximum(-K1, 0))[0]
    a16 = nl.kernel16(M["A_pen"], ang)
    a16 = (a16 - a16[(-np.arange(16)) % 16]) / 2
    A1 = nl.at_offsets(a16, ang)
    A1 = (A1 - A1.T) / 2
    res = {"n_epg": int(n), "rowsum_cv_before": {"E": float(M["E"].sum(1).std() / M["E"].sum(1).mean()), "I": float(M["I"].sum(1).std() / M["I"].sum(1).mean())}}
    res["N2_rn"] = evaluate(K_rn, A_rn, ang, g1, "N2_rn")
    res["N2_rn_sym"] = evaluate((K_rn + K_rn.T) / 2, (A_rn - A_rn.T) / 2, ang, g1, "N2_rn_sym")
    res["N1_rn"] = evaluate(K1_rn, A1, ang, g1, "N1_rn")
    a = res["N2_rn"]
    res["H1"] = bool(a.get("retention_22p5", 0) >= 0.8 and a.get("distinct_end_positions", 0) >= 12)
    res["H2_C1"] = bool(a.get("C1", False))
    r2 = a.get("S2", {}).get("ratio_180_over_90")
    res["H3_S2"] = bool(r2 is not None and 0.8 <= r2 <= 1.25)
    return res


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
    res = {}
    for name, data in c46.datasets().items():
        print("==", name, flush=True)
        res[name] = analyse(hr.matrices(*data), s46["datasets"][name]["variants"]["connectome"]["g_star"])
    h1 = {k: v["H1"] for k, v in res.items()}
    result = {"schema": "ce-a1-step49-input-totals", "hashes": hashes, "H1_per_dataset": h1,
              "H2_per_dataset": {k: v["H2_C1"] for k, v in res.items()}, "H3_per_dataset": {k: v["H3_S2"] for k, v in res.items()},
              "verdict": "INPUT_TOTALS_EXPLAIN_WELLS" if sum(h1.values()) >= 2 else "WELLS_FROM_CONNECTION_PATTERNS", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], h1, result["H2_per_dataset"], result["H3_per_dataset"])


if __name__ == "__main__":
    main()
