"""Post-hoc diagnostics for step 43 (report only; the frozen verdict stands).
K3: over the full 400 s single-stripe probe, does the offset ever switch between the two learned offsets, with and
without plasticity during the probe? K4: does the 180 deg partial pairing take over when the probe starts inside the
newly mapped region (Kim 2019: success more likely then)?"""
import json
import numpy as np
import kim2019_model as km
import visual_map_learning as vml


def rotate_probe(cond, target_stripe_deg):
    """Same natural-turning trajectory, rotated so that the stripe starts at target_stripe_deg."""
    s0 = int(round(((target_stripe_deg - np.degrees(cond["stripe"][0])) % 360) / (360 / km.NI)))
    c = dict(cond)
    c["vis"] = np.roll(cond["vis"], s0, axis=0)
    c["stripe"] = np.mod(cond["stripe"] + s0 * 2 * np.pi / km.NI, 2 * np.pi)
    return c


out = []
for seed in vml.SEEDS:
    rng = np.random.default_rng(seed)
    ra = km.ring_params()
    W0 = rng.random((km.NW, km.NI)) * km.W_MAX
    y0 = rng.random(km.NW) * ra["A"]
    c1, c2 = km.condition("one_stripe", rng), km.condition("one_stripe", rng)
    y, W, _ = km.simulate(c1, W0, y0)
    y, W1, ys2 = km.simulate(c2, W, y)
    pre, _, _ = km.offset_stats(ys2, c2["stripe"])
    # consume rng exactly as in the frozen run (K2 conditions) so later draws match
    shift = int(round(((pre + 180.0) % 360.0) / vml.D_WEDGE))
    co = km.condition("opto", rng, span=360, imposed_shift=shift)
    cp = km.condition("one_stripe", rng)
    ct1, ct2 = km.condition("two_stripes", rng), km.condition("two_stripes", rng)
    y3, W3, _ = km.simulate(ct1, W1, y)
    y3, W3, ys_t = km.simulate(ct2, W3, y3)
    cp3 = km.condition("one_stripe", rng)
    res = {"seed": seed, "pre": pre}
    for learn in (True, False):
        _, _, ys3 = km.simulate(cp3, W3, y3, learn=learn)
        _, _, d = km.offset_stats(ys3, cp3["stripe"])
        a = np.abs((d - pre + 180) % 360 - 180) <= 45
        b = np.abs((d - pre - 180 + 180) % 360 - 180) <= 45
        lab = np.where(a, 0, np.where(b, 1, -1))
        lab = lab[lab >= 0]
        switches = int(np.sum(lab[1:] != lab[:-1]))
        res["probe_learn" if learn else "probe_nolearn"] = {"frac_pre": float(a.mean()), "frac_pre180": float(b.mean()), "switches": switches}
    # where was the bump at the end of two-stripe training, relative to stripe 1?
    _, _, dt_ = km.offset_stats(ys_t[:, -500:], ct2["stripe"][-500:])
    res["end_of_two_stripe_offset_rel_stripe1"] = float(np.degrees(np.angle(np.mean(np.exp(1j * np.radians(dt_))))))
    # K4 with the probe starting inside / outside the newly mapped region
    shift4 = int(round(((pre + 180.0) % 360.0) / vml.D_WEDGE)) + 20
    imposed4 = ((shift4 - 20) * vml.D_WEDGE) % 360
    co4 = km.condition("opto", rng, span=180, imposed_shift=shift4)
    y4, W4, _ = km.simulate(co4, W1, y)
    cp4 = km.condition("one_stripe", rng)
    stripe_mid_span = np.degrees(np.pi + (20 + 7) * 2 * np.pi / km.NI) % 360       # middle of the paired stripe range
    for where, tgt in (("inside", stripe_mid_span), ("outside", stripe_mid_span + 180)):
        cpr = rotate_probe(cp4, tgt)
        _, _, ys4 = km.simulate(cpr, W4, y4)
        e4, R4, _ = km.offset_stats(ys4[:, :int(100 / km.DT)], cpr["stripe"][:int(100 / km.DT)])
        res["K4_" + where] = {"offset": e4, "R": R4, "err_to_imposed": vml.circ_diff(e4, imposed4)}
    out.append(res)
    print(json.dumps(res, default=lambda v: round(float(v), 3)), flush=True)
json.dump(out, open("diag_k3_k4.json", "w"), indent=1, default=float)
k4_in = sum(abs(r["K4_inside"]["err_to_imposed"]) <= 45 and r["K4_inside"]["R"] >= 0.7 for r in out)
k4_out = sum(abs(r["K4_outside"]["err_to_imposed"]) <= 45 and r["K4_outside"]["R"] >= 0.7 for r in out)
sw = sum(r["probe_nolearn"]["switches"] > 0 for r in out)
print("K4 success inside/outside:", k4_in, k4_out, "| K3 probe without learning: flies with any switch", sw)
