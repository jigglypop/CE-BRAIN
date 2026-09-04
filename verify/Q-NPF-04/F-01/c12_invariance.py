# C12. P2 check: are the declared statistics actually invariant to the per-cell
# affine transform o_i -> a_i o_i + b_i ?  F-03 died because a zero shift alone
# moved its predicted quantity from 0.95 to 2.58.  a_i, b_i are drawn per cell and
# held FIXED across the two phases (F0 is computed once per session), which is the
# nuisance the named data actually has.
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd, c2_statistics as c2, c6_practical as c6

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c12_invariance.json")

def main():
    old = fwd.V_AXON; fwd.V_AXON = c6.V_AXON
    rng = np.random.default_rng(fwd.SEED)
    circ = fwd.make_circuit(50, rng, rho0=0.60, tau_m=0.020)
    res = {"script": "c12_invariance.py", "seed": fwd.SEED}

    # --- cue-evoked statistics -------------------------------------------------
    ref = c2.precompute(circ, (0.0, 0.0, 0.0), "counts")
    lat = c2.precompute(circ, (fwd.TH_GAIN, fwd.TH_EFF, fwd.TH_DEL), "counts")
    r1 = np.random.default_rng(11)
    a = np.exp(0.8 * rng.standard_normal(50))[:, None, None]
    b = (3.0 * rng.standard_normal(50))[:, None, None]
    o1 = c2.gen_trials(ref, "counts", 30, np.random.default_rng(5))
    o2 = c2.gen_trials(lat, "counts", 30, np.random.default_rng(6))
    d_raw = c2.contrast(o1, o2)
    d_aff = c2.contrast(a * o1 + b, a * o2 + b)
    res["cue_evoked"] = {k: dict(raw=float(d_raw[k]), affine=float(d_aff[k]),
                                 abs_diff=float(abs(d_aff[k] - d_raw[k])))
                         for k in c2.STATS}

    # --- ongoing-spectrum statistics ------------------------------------------
    sc = c6.calib_scale(circ)
    Href = c6.transfer(circ, (0.0, 0.0, 0.0), sc)
    Hlat = c6.transfer(circ, (fwd.TH_GAIN, fwd.TH_EFF, fwd.TH_DEL), sc)
    pi, pj = c6.pick_pairs(50, rng)
    ya = c6.gen(Href, np.random.default_rng(7), c6.T_HALF)
    yb = c6.gen(Hlat, np.random.default_rng(8), c6.T_HALF)
    aa = np.exp(0.8 * rng.standard_normal(50))[None, :]
    bb = (3.0 * rng.standard_normal(50))[None, :]

    def cstat(y1, y2):
        Y1, Y2 = c6.segfft(y1), c6.segfft(y2)
        _, coh, gdi = c6.stats(Y1[0::2], pi, pj)
        keep = coh >= np.quantile(coh, 1 - c6.PAIR_KEEP_Q)
        s1, _, g1 = c6.stats(Y1[1::2], pi[keep], pj[keep])
        s2, _, g2 = c6.stats(Y2[1::2], pi[keep], pj[keep])
        z = gdi[keep]
        return np.concatenate([s2 - s1, [np.dot(z, g2 - g1) / (np.dot(z, z) + 1e-300)]])

    e_raw = cstat(ya, yb)
    e_aff = cstat(aa * ya + bb, aa * yb + bb)
    nm = ("S1_logpow", "S2_coh", "S3_gdrms", "S4_gdscale")
    res["ongoing_spectrum"] = {nm[i]: dict(raw=float(e_raw[i]), affine=float(e_aff[i]),
                                           abs_diff=float(abs(e_aff[i] - e_raw[i])))
                               for i in range(4)}
    fwd.V_AXON = old
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for grp in ("cue_evoked", "ongoing_spectrum"):
        print("---", grp)
        print("%-16s %14s %14s %12s" % ("statistic", "raw", "o->a*o+b", "|diff|"))
        for k, v in res[grp].items():
            print("%-16s %14.6f %14.6f %12.3e" % (k, v["raw"], v["affine"], v["abs_diff"]))

if __name__ == "__main__":
    main()
