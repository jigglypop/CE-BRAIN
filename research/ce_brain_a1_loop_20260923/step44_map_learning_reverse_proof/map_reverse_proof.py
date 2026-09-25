"""A1 step 44: reverse proof of the step 43 post-hoc findings on new simulated flies (seeds 201-210). (CONTRACT.md)

Same port (step 43 kim2019_model.py) and procedures (step 43 visual_map_learning.py functions) with the conditional
forms reported by the literature: K3' two learned offsets selected per trial across probe starts (Fisher 2019 'half');
K4' partial-span remapping succeeds when the probe starts inside the newly mapped region (Kim 2019, flies 6/10).

python map_reverse_proof.py    refuses to run unless CONTRACT.md lists this code hash and the step 43 hashes
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
S43 = HERE.parent / "step43_visual_map_learning"
sys.path.insert(0, str(S43))
import kim2019_model as km  # noqa: E402
import visual_map_learning as vml  # noqa: E402

SEEDS = list(range(201, 211))
N_STARTS = 8


def rotate_probe(cond, target_stripe_deg):
    s0 = int(round(((target_stripe_deg - np.degrees(cond["stripe"][0])) % 360) / (360 / km.NI)))
    c = dict(cond)
    c["vis"] = np.roll(cond["vis"], s0, axis=0)
    c["stripe"] = np.mod(cond["stripe"] + s0 * 2 * np.pi / km.NI, 2 * np.pi)
    return c


def early(ys, cond, t=100.0):
    n = int(t / km.DT)
    return km.offset_stats(ys[:, :n], cond["stripe"][:n])


def one_fly(seed):
    rng = np.random.default_rng(seed)
    ra = km.ring_params()
    W0 = rng.random((km.NW, km.NI)) * km.W_MAX
    y0 = rng.random(km.NW) * ra["A"]
    out = {"seed": seed}
    c1, c2 = km.condition("one_stripe", rng), km.condition("one_stripe", rng)
    y, W, _ = km.simulate(c1, W0, y0)
    y, W1, ys2 = km.simulate(c2, W, y)
    pre, R1, _ = km.offset_stats(ys2, c2["stripe"])
    _, _, ysn = km.simulate(c2, W0, y0, learn=False)
    _, Rn, _ = km.offset_stats(ysn, c2["stripe"])
    out["K1"] = {"offset": pre, "R": R1, "no_learning_R": Rn, "pass": bool(R1 >= 0.9 and Rn < 0.5)}
    # K2 (360 deg opto, imposed = pre + 180)
    shift = int(round(((pre + 180.0) % 360.0) / vml.D_WEDGE))
    imposed = shift * vml.D_WEDGE
    co = km.condition("opto", rng, span=360, imposed_shift=shift)
    y2, W2, _ = km.simulate(co, W1, y)
    cp = km.condition("one_stripe", rng)
    _, _, ysp = km.simulate(cp, W2, y2)
    e2, R2, _ = early(ysp, cp)
    out["K2"] = {"imposed": imposed, "offset": e2, "R": R2,
                 "pass": bool(abs(vml.circ_diff(e2, imposed)) <= 45 and R2 >= 0.7 and abs(vml.circ_diff(e2, pre)) >= 90)}
    # K3 two stripes -> doubled map, then probes from N_STARTS positions (plasticity off)
    ct1, ct2 = km.condition("two_stripes", rng), km.condition("two_stripes", rng)
    y3, W3, _ = km.simulate(ct1, W1, y)
    y3, W3, _ = km.simulate(ct2, W3, y3)
    cp3 = km.condition("one_stripe", rng)
    sel = []
    for k in range(N_STARTS):
        cpr = rotate_probe(cp3, np.degrees(cp3["stripe"][0]) + 360.0 / N_STARTS * k)
        _, _, ys = km.simulate(cpr, W3, y3, learn=False)
        m, R, _ = early(ys, cpr)
        dp = vml.circ_diff(m, pre)
        sel.append("pre" if abs(dp) <= 45 else ("pre+180" if abs(abs(dp) - 180) <= 45 else "other"))
    out["K3"] = {"harmonic2_over_1": vml.harmonic_ratio(W3), "doubled": bool(vml.harmonic_ratio(W3) > 1.0), "selected": sel,
                 "both": bool("pre" in sel and "pre+180" in sel)}
    # K4 180 deg partial span, imposed = pre + 180; probes starting inside / outside the paired stripe range
    shift4 = int(round(((pre + 180.0) % 360.0) / vml.D_WEDGE)) + 20
    imposed4 = ((shift4 - 20) * vml.D_WEDGE) % 360
    co4 = km.condition("opto", rng, span=180, imposed_shift=shift4)
    y4, W4, _ = km.simulate(co4, W1, y)
    cp4 = km.condition("one_stripe", rng)
    mid = np.degrees(np.pi + (20 + 7) * 2 * np.pi / km.NI) % 360
    for where, tgt in (("inside", mid), ("outside", mid + 180.0)):
        cpr = rotate_probe(cp4, tgt)
        _, _, ys4 = km.simulate(cpr, W4, y4)
        e4, R4, _ = early(ys4, cpr)
        out["K4_" + where] = {"offset": e4, "R": R4, "pass": bool(abs(vml.circ_diff(e4, imposed4)) <= 45 and R4 >= 0.7)}
    return out


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), S43 / "kim2019_model.py", S43 / "visual_map_learning.py")}
    missing = [n for n, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    flies = []
    for s in SEEDS:
        f = one_fly(s)
        flies.append(f)
        print(json.dumps(f, default=lambda v: round(float(v), 3)), flush=True)
    n = len(flies)
    sel = [x for f in flies for x in f["K3"]["selected"]]
    frac_new = sel.count("pre+180") / max(sel.count("pre") + sel.count("pre+180"), 1)
    counts = {"K1": sum(f["K1"]["pass"] for f in flies), "K2": sum(f["K2"]["pass"] for f in flies),
              "K3_doubled": sum(f["K3"]["doubled"] for f in flies), "K3_both": sum(f["K3"]["both"] for f in flies),
              "K3_frac_new": frac_new, "K4_inside": sum(f["K4_inside"]["pass"] for f in flies),
              "K4_outside": sum(f["K4_outside"]["pass"] for f in flies), "n": n}
    crit = {"K1": counts["K1"] >= 8, "K2": counts["K2"] >= 8, "K3_doubled": counts["K3_doubled"] >= 8,
            "K3_prime": counts["K3_both"] >= 8 and 0.3 <= frac_new <= 0.7,
            "K4_prime": counts["K4_inside"] >= 6 and counts["K4_inside"] > counts["K4_outside"]}
    crit = {k: bool(v) for k, v in crit.items()}
    result = {"schema": "ce-a1-step44-map-learning-reverse-proof", "hashes": hashes, "counts": counts, "criteria": crit,
              "verdict": "LEARNING_RULE_REPRODUCES_MAP_FACTS" if all(crit.values()) else "LEARNING_RULE_DOES_NOT_REPRODUCE_ALL", "flies": flies}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], counts, crit)


if __name__ == "__main__":
    main()
