"""A1 step 45: one compass model on the fly lattice (16 E-PG directions, Kim local ring at the Noorman optimum,
PEN-like self-motion input at gain 1, Kim 2019 ring-neuron plasticity) -- does it reproduce the map-learning facts on
real fly turning (Kim 2019 pos_data) and track heading in darkness? (CONTRACT.md)

python full_compass.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
sys.path.insert(0, str(HERE))
import compass_model as cm  # noqa: E402
km, tl = cm.km, cm.tl

SEEDS = list(range(301, 311))
N_STARTS = 8
EARLY = 100.0


def circ_diff(a, b):
    return float((a - b + 180.0) % 360.0 - 180.0)


def rotate_probe(cond, target_stripe_deg):
    s0 = int(round(((target_stripe_deg - np.degrees(cond["stripe"][0])) % 360) / (360 / km.NI)))
    c = dict(cond)
    c["vis"] = np.roll(cond["vis"], s0, axis=0)
    c["stripe"] = np.mod(cond["stripe"] + s0 * 2 * np.pi / km.NI, 2 * np.pi)
    return c


def early(ys, cond, t=EARLY):
    n = int(t / km.DT)
    return cm.offset_stats(ys[:, :n], cond["stripe"][:n])


def harmonic_ratio(W):
    F = np.fft.rfft(W - W.mean(0, keepdims=True), axis=0)
    return float(np.mean(np.abs(F[2]) ** 2) / max(np.mean(np.abs(F[1]) ** 2), 1e-15))


def dark_tracking(W, y, cond):
    _, _, ys = cm.simulate(cond, W, y, learn=False, dark=True)
    err = cm.heading_tracking(ys, cond)
    n20 = int(20.0 / km.DT)
    drift20 = [abs(err[i + n20] - err[i]) for i in range(0, err.size - n20, n20)]
    return {"median_abs_drift_20s_deg": float(np.median(drift20)), "p90_abs_drift_20s_deg": float(np.percentile(drift20, 90)),
            "end_abs_error_deg": float(abs(err[-1] - err[0]))}


def one_fly(seed):
    rng = np.random.default_rng(seed)
    W0 = rng.random((cm.NW, km.NI)) * km.W_MAX
    y0 = cm.natural_bump() * (0.5 + rng.random(cm.NW))
    out = {"seed": seed}
    c1, c2 = km.condition("one_stripe", rng), km.condition("one_stripe", rng)
    y, W, _ = cm.simulate(c1, W0, y0)
    y, W1, ys2 = cm.simulate(c2, W, y)
    pre, R1, _ = cm.offset_stats(ys2, c2["stripe"])
    _, _, ysn = cm.simulate(c2, W0, y0, learn=False)
    _, Rn, _ = cm.offset_stats(ysn, c2["stripe"])
    out["K1"] = {"offset": pre, "R": R1, "no_learning_R": Rn, "pass": bool(R1 >= 0.9), "improves": bool(R1 > Rn)}
    # darkness tracking after learning (report), optimal vs 5 % detuned ring
    cd = km.condition("one_stripe", rng)
    out["D1_dark_tracking"] = dark_tracking(W1, y, cd)
    # K2 opto 360 span, imposed = pre + 180
    imposed = (pre + 180.0) % 360.0
    co = km.condition("opto", rng, span=360)
    y2, W2, _ = cm.simulate(co, W1, y, inj=cm.injection(co["stripe"], imposed))
    cp = km.condition("one_stripe", rng)
    _, _, ysp = cm.simulate(cp, W2, y2)
    e2, R2, _ = early(ysp, cp)
    out["K2"] = {"imposed": imposed, "offset": e2, "R": R2,
                 "pass": bool(abs(circ_diff(e2, imposed)) <= 45 and R2 >= 0.7 and abs(circ_diff(e2, pre)) >= 90)}
    # K3 two stripes -> doubled map; probes from N_STARTS starts, plasticity off
    ct1, ct2 = km.condition("two_stripes", rng), km.condition("two_stripes", rng)
    y3, W3, _ = cm.simulate(ct1, W1, y)
    y3, W3, _ = cm.simulate(ct2, W3, y3)
    cp3 = km.condition("one_stripe", rng)
    sel = []
    for k in range(N_STARTS):
        cpr = rotate_probe(cp3, np.degrees(cp3["stripe"][0]) + 360.0 / N_STARTS * k)
        _, _, ys = cm.simulate(cpr, W3, y3, learn=False)
        m, R, _ = early(ys, cpr)
        dp = circ_diff(m, pre)
        sel.append("pre" if abs(dp) <= 45 else ("pre+180" if abs(abs(dp) - 180) <= 45 else "other"))
    h3 = harmonic_ratio(W3)
    out["K3"] = {"harmonic2_over_1": h3, "harmonic2_over_1_one_stripe": harmonic_ratio(W1), "doubled": bool(h3 > 1.0),
                 "selected": sel, "both": bool("pre" in sel and "pre+180" in sel)}
    # K4 180 span partial pairing, imposed = pre + 180; probes inside / outside the paired stripe range
    co4 = km.condition("opto", rng, span=180)
    y4, W4, _ = cm.simulate(co4, W1, y, inj=cm.injection(co4["stripe"], imposed))
    cp4 = km.condition("one_stripe", rng)
    mid = np.degrees(np.pi + (20 + 7) * 2 * np.pi / km.NI) % 360
    for where, tgt in (("inside", mid), ("outside", mid + 180.0)):
        cpr = rotate_probe(cp4, tgt)
        _, _, ys4 = cm.simulate(cpr, W4, y4)
        e4, R4, _ = early(ys4, cpr)
        out["K4_" + where] = {"offset": e4, "R": R4, "pass": bool(abs(circ_diff(e4, imposed)) <= 45 and R4 >= 0.7)}
    return out


def detuned_dark_report(seed):
    """Report: same learning on the 5 % detuned ring, then darkness tracking (effect of Noorman tuning on real turns)."""
    saved = cm.W_RA.copy(), cm.A_GEN.copy(), cm.G_SPEED
    try:
        cm.W_RA = tl.local_ring(cm.RING["alpha"] * 0.95, cm.RING["D"], cm.RING["beta"])
        cm.A_GEN = tl.generator(cm.W_RA)
        cm.G_SPEED, _ = cm.speed_gain()
        rng = np.random.default_rng(seed)
        W0 = rng.random((cm.NW, km.NI)) * km.W_MAX
        y0 = cm.natural_bump() * (0.5 + rng.random(cm.NW))
        c1, c2 = km.condition("one_stripe", rng), km.condition("one_stripe", rng)
        y, W, _ = cm.simulate(c1, W0, y0)
        y, W1, ys2 = cm.simulate(c2, W, y)
        _, R1, _ = cm.offset_stats(ys2, c2["stripe"])
        cd = km.condition("one_stripe", rng)
        return {"K1_R": R1, "D1_dark_tracking": dark_tracking(W1, y, cd), "speed_gain": cm.G_SPEED}
    finally:
        cm.W_RA, cm.A_GEN, cm.G_SPEED = saved


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), HERE / "compass_model.py", LOOP / "step41_few_neuron_attractor/tl_ring.py", LOOP / "step43_visual_map_learning/kim2019_model.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [n for n, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    flies = []
    for s in SEEDS:
        f = one_fly(s)
        flies.append(f)
        print(json.dumps(f, default=lambda v: round(float(v), 3)), flush=True)
    det = [detuned_dark_report(s) for s in SEEDS[:5]]
    print("detuned report", json.dumps(det, default=lambda v: round(float(v), 3)), flush=True)
    sel = [x for f in flies for x in f["K3"]["selected"]]
    frac_new = sel.count("pre+180") / max(sel.count("pre") + sel.count("pre+180"), 1)
    counts = {"K1": sum(f["K1"]["pass"] for f in flies), "K1_improves": sum(f["K1"]["improves"] for f in flies),
              "K2": sum(f["K2"]["pass"] for f in flies), "K3_doubled": sum(f["K3"]["doubled"] for f in flies),
              "K3_both": sum(f["K3"]["both"] for f in flies), "K3_frac_new": frac_new,
              "K4_inside": sum(f["K4_inside"]["pass"] for f in flies), "K4_outside": sum(f["K4_outside"]["pass"] for f in flies), "n": len(flies)}
    crit = {"K1": counts["K1"] >= 8 and counts["K1_improves"] >= 8, "K2": counts["K2"] >= 8, "K3_doubled": counts["K3_doubled"] >= 8,
            "K3_prime": counts["K3_both"] >= 8 and 0.3 <= frac_new <= 0.7,
            "K4_prime": counts["K4_inside"] >= 6 and counts["K4_inside"] > counts["K4_outside"]}
    crit = {k: bool(v) for k, v in crit.items()}
    result = {"schema": "ce-a1-step45-fly-lattice-compass", "hashes": hashes, "calibration": {"y_peak": cm.Y_PEAK, "eps": cm.EPS, "inj_peak": cm.INJ_PEAK,
              "speed_gain_deg_s_per_v": cm.G_SPEED}, "counts": counts, "criteria": crit,
              "report_dark_tracking_optimal": [f["D1_dark_tracking"] for f in flies], "report_detuned": det,
              "verdict": "ONE_COMPASS_MODEL_REPRODUCES_MAP_FACTS" if all(crit.values()) else "ONE_COMPASS_MODEL_DOES_NOT_REPRODUCE_ALL", "flies": flies}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], counts, crit)


if __name__ == "__main__":
    main()
