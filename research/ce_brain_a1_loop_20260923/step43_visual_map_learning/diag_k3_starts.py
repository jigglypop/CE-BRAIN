"""Post-hoc (report only): after two-stripe learning, does the selected offset depend on where a single-stripe probe
starts (two learned offsets, one selected per trial)? Eight probe starts per fly, plasticity off during the probe."""
import json
import numpy as np
import kim2019_model as km
import visual_map_learning as vml


def rotate_probe(cond, target_stripe_deg):
    s0 = int(round(((target_stripe_deg - np.degrees(cond["stripe"][0])) % 360) / (360 / km.NI)))
    c = dict(cond)
    c["vis"] = np.roll(cond["vis"], s0, axis=0)
    c["stripe"] = np.mod(cond["stripe"] + s0 * 2 * np.pi / km.NI, 2 * np.pi)
    return c


rows = []
for seed in vml.SEEDS:
    rng = np.random.default_rng(seed)
    ra = km.ring_params()
    W0 = rng.random((km.NW, km.NI)) * km.W_MAX
    y0 = rng.random(km.NW) * ra["A"]
    c1, c2 = km.condition("one_stripe", rng), km.condition("one_stripe", rng)
    y, W, _ = km.simulate(c1, W0, y0)
    y, W1, ys2 = km.simulate(c2, W, y)
    pre, _, _ = km.offset_stats(ys2, c2["stripe"])
    shift = int(round(((pre + 180.0) % 360.0) / vml.D_WEDGE))
    km.condition("opto", rng, span=360, imposed_shift=shift)
    km.condition("one_stripe", rng)
    ct1, ct2 = km.condition("two_stripes", rng), km.condition("two_stripes", rng)
    y3, W3, _ = km.simulate(ct1, W1, y)
    y3, W3, _ = km.simulate(ct2, W3, y3)
    cp3 = km.condition("one_stripe", rng)
    sel = []
    for k in range(8):
        cpr = rotate_probe(cp3, np.degrees(cp3["stripe"][0]) + 45 * k)
        _, _, ys = km.simulate(cpr, W3, y3, learn=False)
        m, R, d = km.offset_stats(ys[:, :int(100 / km.DT)], cpr["stripe"][:int(100 / km.DT)])
        dp = vml.circ_diff(m, pre)
        sel.append("pre" if abs(dp) <= 45 else ("pre+180" if abs(abs(dp) - 180) <= 45 else "other"))
    rows.append({"seed": seed, "selected": sel, "n_pre": sel.count("pre"), "n_pre180": sel.count("pre+180"), "n_other": sel.count("other")})
    print(rows[-1], flush=True)
both = sum(r["n_pre"] > 0 and r["n_pre180"] > 0 for r in rows)
print("flies where both learned offsets are selected across the 8 probe starts:", both, "/", len(rows))
json.dump(rows, open("diag_k3_starts.json", "w"), indent=1)
