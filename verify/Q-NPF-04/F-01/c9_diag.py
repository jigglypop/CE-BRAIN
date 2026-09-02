# C9. Diagnostic: is the delay statistic broken, or is the delay physically
# invisible at 14.93 Hz?  Three noise-free checks.
#   (a) TRUE per-pair cross-spectral group delay, baseline vs VFAC, and the true
#       value of S4's estimand (slope of the paired change on the baseline).
#   (b) where in frequency the ORACLE's delay information sits (per-frequency
#       contribution to the Whittle Fisher I_delay,delay).
#   (c) does widening the analysis band to the full 0..Nyquist recover it?
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd, c6_practical as c6

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c9_diag.json")
RHO, TAUM = 0.60, 0.020
VFACS = (1.25, 2.0, 4.0, 8.0)
NF = 512

def true_gd(circ, th, band):
    """Noise-free per-pair group delay from the exact model cross-spectrum."""
    lam = np.linspace(1e-4, np.pi, NF)
    w = lam / fwd.FRAME_DT
    n = circ["n"]
    g = circ["g"] * np.exp(th[0]); W = circ["W"] * np.exp(th[1])
    tau = circ["tau_ax"] * np.exp(th[2]) + fwd.TAU_SYN
    ph = np.exp(-1j * w[:, None, None] * tau[None, :, :])
    M = -(g[None, :, None] * W[None, :, :]) * ph
    idx = np.arange(n)
    M[:, idx, idx] += (1.0 + 1j * w * circ["tau_m"])[:, None]
    Mi = np.linalg.inv(M)
    S = (Mi * (g ** 2)[None, None, :]) @ np.conj(np.swapaxes(Mi, 1, 2))
    f = w / (2 * np.pi)
    m = (f >= band[0]) & (f <= band[1])
    iu = np.triu_indices(n, 1)
    C = S[:, iu[0], iu[1]][m]
    P = np.einsum("wii->wi", S).real[m]
    coh2 = np.abs(C) ** 2 / (P[:, iu[0]] * P[:, iu[1]] + 1e-300)
    ww = w[m][:, None]; pha = np.unwrap(np.angle(C), axis=0); wt = coh2
    sw = wt.sum(0) + 1e-300
    num = (wt * (ww - (wt * ww).sum(0) / sw) * (pha - (wt * pha).sum(0) / sw)).sum(0)
    den = (wt * (ww - (wt * ww).sum(0) / sw) ** 2).sum(0) + 1e-300
    return -num / den, float(np.mean(coh2))

def main():
    old_v = fwd.V_AXON; fwd.V_AXON = c6.V_AXON
    rng = np.random.default_rng(fwd.SEED)
    circ = fwd.make_circuit(63, rng, rho0=RHO, tau_m=TAUM)
    res = {"script": "c9_diag.py", "seed": fwd.SEED, "rho0": RHO, "n": 63}
    for band, tag in (((0.15, 5.0), "band_0.15_5.0"), ((0.15, 7.4), "band_0.15_7.4")):
        g0, c0 = true_gd(circ, (0, 0, 0), band)
        rows = []
        for v in VFACS:
            g1, c1 = true_gd(circ, (0, 0, float(np.log(1 / v))), band)
            d = g1 - g0
            slope = float(np.dot(g0, d) / np.dot(g0, g0))
            rows.append(dict(vfac=v, true_S4_estimand=slope,
                             rms_gd_base_ms=float(np.sqrt(np.mean(g0 ** 2)) * 1e3),
                             rms_gd_change_ms=float(np.sqrt(np.mean(d ** 2)) * 1e3),
                             rel_rms_change=float(np.sqrt(np.mean(d ** 2))
                                                  / np.sqrt(np.mean(g0 ** 2))),
                             mean_coh2=c1))
        res[tag] = dict(mean_coh2_base=c0, rows=rows)
    # (b) where the oracle's delay information sits in frequency
    import c5_robust as c5
    lamF = c5.c4._LAM
    def spec(th):
        return c5.spec_obs(circ, th, 1.0, (fwd.IMG_SD_FRAC * fwd.R_BASE) ** 2, 0, 0.0, False)
    h = fwd.FD_H
    f0 = spec((0, 0, 0)); finv = np.linalg.inv(f0)
    d3 = (spec((0, 0, h)) - spec((0, 0, -h))) / (2 * h)
    A = finv @ d3
    tr = np.einsum("wij,wji->w", A, A).real
    fr = lamF / fwd.FRAME_DT / (2 * np.pi)
    cum = np.cumsum(tr) / tr.sum()
    q = [float(fr[np.searchsorted(cum, p)]) for p in (0.25, 0.50, 0.75, 0.90)]
    res["oracle_delay_info_frequency_quantiles_Hz"] = dict(q25=q[0], q50=q[1],
                                                           q75=q[2], q90=q[3])
    res["oracle_delay_info_frac_below_5Hz"] = float(cum[np.searchsorted(fr, 5.0)])
    fwd.V_AXON = old_v
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for tag in ("band_0.15_5.0", "band_0.15_7.4"):
        print("\n---", tag, " mean coh^2 base = %.4f" % res[tag]["mean_coh2_base"])
        print("%-7s %16s %16s %16s %12s" % ("VFAC","true_S4_estimand","rms_gd_base_ms",
                                            "rms_gd_chg_ms","rel_change"))
        for r in res[tag]["rows"]:
            print("%-7.2f %16.5f %16.3f %16.4f %12.5f" %
                  (r["vfac"], r["true_S4_estimand"], r["rms_gd_base_ms"],
                   r["rms_gd_change_ms"], r["rel_rms_change"]))
    print("\noracle delay-information frequency quantiles (Hz):",
          res["oracle_delay_info_frequency_quantiles_Hz"])
    print("fraction of oracle delay information below 5 Hz: %.4f"
          % res["oracle_delay_info_frac_below_5Hz"])

if __name__ == "__main__":
    main()
