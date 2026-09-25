"""A1 step 43: does the literature learning rule of the fly compass (Kim et al. 2019 Nature; Fisher et al. 2019 Nature:
co-active ring and compass neurons depress ring->compass inhibition, compass activity alone potentiates it) reproduce
the reported learning facts when ported independently? (CONTRACT.md)

K1 map formation, K2 optogenetic remapping, K3 two-stripe experience -> two competing offsets and a doubled map,
K4 completion of a full map from a 180 deg pairing span. Ten simulated flies (seeds).

python visual_map_learning.py    refuses to run unless CONTRACT.md lists this code hash and kim2019_model.py hash
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kim2019_model as km  # noqa: E402

SEEDS = list(range(101, 111))
EARLY = 100.0                      # s of a probe used for the early offset
D_WEDGE = 360.0 / km.NW


def circ_diff(a, b):
    return float((a - b + 180.0) % 360.0 - 180.0)


def run(cond, W, y, learn=True):
    y, W, ys = km.simulate(cond, W, y, learn=learn)
    return y, W, ys


def offsets(ys, cond, t_from=0.0, t_to=None):
    i0 = int(t_from / km.DT)
    i1 = ys.shape[1] if t_to is None else int(t_to / km.DT)
    mean, R, d = km.offset_stats(ys[:, i0:i1], cond["stripe"][i0:i1])
    return mean, R, d


def mode_fractions(d_deg, centre):
    near = lambda c: float(np.mean(np.abs((d_deg - c + 180) % 360 - 180) <= 45))
    return near(centre), near(centre + 180.0)


def harmonic_ratio(W):
    """Mean over ring neurons of power at harmonic 2 / harmonic 1 of the weight profile across compass wedges."""
    F = np.fft.rfft(W - W.mean(0, keepdims=True), axis=0)
    p1, p2 = np.abs(F[1]) ** 2, np.abs(F[2]) ** 2
    return float(np.mean(p2) / max(np.mean(p1), 1e-15))


def one_fly(seed):
    rng = np.random.default_rng(seed)
    ra = km.ring_params()
    W0 = rng.random((km.NW, km.NI)) * km.W_MAX
    y0 = rng.random(km.NW) * ra["A"]
    out = {"seed": seed}
    # K1 map formation (two 400 s natural-turning single-stripe runs, W carried over as in main_sim.m)
    c1, c2 = km.condition("one_stripe", rng), km.condition("one_stripe", rng)
    y, W, ys1 = run(c1, W0, y0)
    first_mean, first_R, _ = offsets(ys1, c1)
    y, W1, ys2 = run(c2, W, y)
    pre, R1, d1 = offsets(ys2, c2)
    _, _, ysn = run(c2, W0, y0, learn=False)
    _, Rn, _ = offsets(ysn, c2)
    out["K1"] = {"first_run_R": first_R, "second_run_offset": pre, "second_run_R": R1, "no_learning_R": Rn,
                 "pass": bool(R1 >= 0.9 and Rn < 0.5), "harmonic2_over_1": harmonic_ratio(W1)}
    # K2 optogenetic remapping (360 deg span, 100 s), imposed offset = pre + 180 deg
    shift = int(round(((pre + 180.0) % 360.0) / D_WEDGE))
    imposed = shift * D_WEDGE
    co = km.condition("opto", rng, span=360, imposed_shift=shift)
    y2, W2, _ = run(co, W1, y)
    cp = km.condition("one_stripe", rng)
    _, _, ysp = run(cp, W2, y2)
    early, Re, _ = offsets(ysp, cp, 0.0, EARLY)
    out["K2"] = {"pre_offset": pre, "imposed_offset": imposed, "probe_early_offset": early, "probe_early_R": Re,
                 "err_to_imposed": circ_diff(early, imposed), "change_from_pre": circ_diff(early, pre),
                 "pass": bool(abs(circ_diff(early, imposed)) <= 45 and Re >= 0.7 and abs(circ_diff(early, pre)) >= 90)}
    # K3 two stripes (two 400 s runs), then single-stripe probe
    ct1, ct2 = km.condition("two_stripes", rng), km.condition("two_stripes", rng)
    y3, W3, _ = run(ct1, W1, y)
    y3, W3, _ = run(ct2, W3, y3)
    cp3 = km.condition("one_stripe", rng)
    _, _, ys3 = run(cp3, W3, y3)
    _, _, d3 = offsets(ys3, cp3, 0.0, 2 * EARLY)
    fa, fb = mode_fractions(d3, pre)
    h3 = harmonic_ratio(W3)
    out["K3"] = {"mode_pre_fraction": fa, "mode_pre_plus_180_fraction": fb, "harmonic2_over_1_after_two": h3,
                 "harmonic2_over_1_after_one": out["K1"]["harmonic2_over_1"],
                 "both_modes": bool(fa >= 0.1 and fb >= 0.1), "doubled_map": bool(h3 > 1.0)}
    # K4 partial span (180 deg, 100 s), imposed offset = pre + 180 deg; probe over full natural turning
    shift4 = int(round(((pre + 180.0) % 360.0) / D_WEDGE)) + 20       # 180-span stripe sequence starts 20 ring steps later
    imposed4 = (shift4 - 20) * D_WEDGE
    co4 = km.condition("opto", rng, span=180, imposed_shift=shift4)
    y4, W4, _ = run(co4, W1, y)
    cp4 = km.condition("one_stripe", rng)
    _, _, ys4 = run(cp4, W4, y4)
    e4, R4, _ = offsets(ys4, cp4, 0.0, EARLY)
    out["K4"] = {"imposed_offset": imposed4 % 360.0, "probe_early_offset": e4, "probe_early_R": R4, "err_to_imposed": circ_diff(e4, imposed4),
                 "pass": bool(abs(circ_diff(e4, imposed4)) <= 45 and R4 >= 0.7)}
    return out


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), HERE / "kim2019_model.py")}
    missing = [n for n, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    flies = []
    for s in SEEDS:
        f = one_fly(s)
        flies.append(f)
        print("fly", s, json.dumps({k: (v if not isinstance(v, dict) else {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()})
                                    for k, v in f.items()}, default=float), flush=True)
    n = len(flies)
    k1 = sum(f["K1"]["pass"] for f in flies)
    k2 = sum(f["K2"]["pass"] for f in flies)
    k3 = sum(f["K3"]["both_modes"] for f in flies)
    k3d = sum(f["K3"]["doubled_map"] for f in flies)
    k4 = sum(f["K4"]["pass"] for f in flies)
    crit = {"K1_map_formation": bool(k1 >= 8), "K2_opto_remapping": bool(k2 >= 8), "K3_two_offsets": bool(k3 >= 5),
            "K3_doubled_map": bool(k3d >= 8), "K4_partial_completion": bool(k4 >= 5)}
    ok = all(crit.values())
    result = {"schema": "ce-a1-step43-visual-map-learning", "hashes": hashes,
              "counts": {"K1": k1, "K2": k2, "K3_both_modes": k3, "K3_doubled": k3d, "K4": k4, "n": n}, "criteria": crit,
              "verdict": "LITERATURE_LEARNING_RULE_REPRODUCES_MAP_FACTS" if ok else "LITERATURE_LEARNING_RULE_DOES_NOT_REPRODUCE_ALL", "flies": flies}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], result["counts"], crit)


if __name__ == "__main__":
    main()
