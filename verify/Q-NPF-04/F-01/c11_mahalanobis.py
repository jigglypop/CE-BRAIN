# C11. Correct the channel-norm and angle computation.  In C7/C10 the channel
# "size" was the Euclidean norm of a vector of correlated z-scores, which
# overstates the evidence (C10's Euclidean norms exceeded the C1 Cramer-Rao
# bound, which is impossible for a valid statistic).  The right quantity uses the
# NULL COVARIANCE of the statistic vector:
#     |d|_Sigma^2 = d^T Sigma^{-1} d ,   cos = d_k^T Sigma^{-1} d_l / (|d_k| |d_l|)
# with Sigma estimated from the within-phase placebo draws.  This is bounded by
# the Cramer-Rao bound and is the correct space in which to ask whether two
# channels push the data in different directions.
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd, c2_statistics as c2, c6_practical as c6

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c11_maha.json")
CH = ("gain_only", "efficacy_only", "delay_only")

def summarize(draws, names):
    P = draws["placebo"]
    Sig = np.cov(P, rowvar=False)
    if Sig.ndim == 0:
        Sig = Sig.reshape(1, 1)
    cond = float(np.linalg.cond(Sig))
    Si = np.linalg.inv(Sig)
    mu0 = P.mean(axis=0)
    d = {w: draws[w].mean(axis=0) - mu0 for w in draws}
    nrm = {w: float(np.sqrt(max(d[w] @ Si @ d[w], 0.0))) for w in draws}
    ang = {}
    for a in range(3):
        for b in range(a + 1, 3):
            ka, kb = CH[a], CH[b]
            c = float(d[ka] @ Si @ d[kb] / (nrm[ka] * nrm[kb] + 1e-300))
            ang["%s-%s" % (ka[:4], kb[:4])] = float(np.degrees(np.arccos(min(abs(c), 1.0))))
    return dict(stat_names=list(names), null_cov_cond=cond,
                maha_norm=nrm, angles_deg=ang,
                per_stat_z={w: [float(x) for x in
                                (draws[w].mean(axis=0) - mu0) / P.std(axis=0, ddof=1)]
                            for w in draws})

# ---------------- cue-evoked endpoint ----------------
def cue(rho=0.60, n_rep=200):
    fwd.V_AXON_OLD = fwd.V_AXON; fwd.V_AXON = 0.10
    W = {"true_all": (fwd.TH_GAIN, fwd.TH_EFF, fwd.TH_DEL),
         "gain_only": (fwd.TH_GAIN, 0, 0), "efficacy_only": (0, fwd.TH_EFF, 0),
         "delay_only": (0, 0, fwd.TH_DEL), "placebo": (0, 0, 0)}
    K = len(c2.STATS)
    draws = {w: np.zeros((n_rep, K)) for w in W}
    rng0 = np.random.default_rng(fwd.SEED)
    for mi, n in enumerate(fwd.CELLS_PER_MOUSE):
        circ = fwd.make_circuit(n, rng0, rho0=rho, tau_m=0.020)
        ref = c2.precompute(circ, (0.0, 0.0, 0.0), "counts")
        for wi, w in enumerate(W):
            tab = ref if w == "placebo" else c2.precompute(circ, W[w], "counts")
            rng = np.random.default_rng(fwd.SEED + 300 * (wi + 1) + mi)
            for r in range(n_rep):
                a = c2.gen_trials(ref, "counts", fwd.N_TRIAL_PHASE // 2, rng)
                b = c2.gen_trials(tab, "counts", fwd.N_TRIAL_PHASE // 2, rng)
                dd = c2.contrast(a, b)
                draws[w][r] += np.array([dd[k] for k in c2.STATS])
    fwd.V_AXON = fwd.V_AXON_OLD
    for w in draws: draws[w] /= float(fwd.N_MICE)
    return summarize(draws, c2.STATS)

# ---------------- ongoing-spectrum endpoint ----------------
def ongoing(rho, n_rep=150):
    c6.RHO0 = rho
    old = fwd.V_AXON; fwd.V_AXON = c6.V_AXON
    wn = list(c6.WORLDS)
    draws = {w: np.zeros((n_rep, 4)) for w in wn}
    rng0 = np.random.default_rng(fwd.SEED)
    for mi, n in enumerate(fwd.CELLS_PER_MOUSE):
        circ = fwd.make_circuit(n, rng0, rho0=rho, tau_m=c6.TAU_M)
        sc = c6.calib_scale(circ); pi, pj = c6.pick_pairs(n, rng0)
        Href = c6.transfer(circ, (0.0, 0.0, 0.0), sc)
        for wi, w in enumerate(wn):
            Hw = Href if w == "placebo" else c6.transfer(circ, c6.WORLDS[w], sc)
            rng = np.random.default_rng(fwd.SEED + 1000 * (wi + 1) + mi)
            for r in range(n_rep):
                draws[w][r] += c6.contrast(Href, Hw, pi, pj, rng)
            if w != "placebo": del Hw
        del Href
    fwd.V_AXON = old
    for w in draws: draws[w] /= float(fwd.N_MICE)
    return summarize(draws, ("S1_logpow", "S2_coh", "S3_gdrms", "S4_gdscale"))

def main():
    t0 = time.time()
    res = {"script": "c11_mahalanobis.py", "seed": fwd.SEED,
           "criteria": {"C_A": "maha_norm >= 2.0 for each of the three channels",
                        "C_B": "all three pairwise whitened angles >= 15 deg"}}
    res["cue_evoked_rho0.60"] = cue()
    for rho in (0.40, 0.60, 0.80):
        res["ongoing_spectrum_rho%.2f" % rho] = ongoing(rho)
    for k, v in res.items():
        if not isinstance(v, dict) or "maha_norm" not in v:
            continue
        n = v["maha_norm"]
        v["pass_CA"] = bool(min(n[c] for c in CH) >= 2.0)
        v["pass_CB"] = bool(min(v["angles_deg"].values()) >= 15.0)
    res["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%-26s %8s %8s %8s | %8s %8s %8s | %5s %5s" %
          ("endpoint", "gain", "effic", "delay", "g-e", "g-d", "e-d", "C-A", "C-B"))
    for k, v in res.items():
        if not isinstance(v, dict) or "maha_norm" not in v: continue
        n = v["maha_norm"]; a = v["angles_deg"]
        ks = list(a.keys())
        print("%-26s %8.3f %8.3f %8.3f | %8.2f %8.2f %8.2f | %5s %5s" %
              (k, n["gain_only"], n["efficacy_only"], n["delay_only"],
               a[ks[0]], a[ks[1]], a[ks[2]], v["pass_CA"], v["pass_CB"]))
        print("%-26s null-cov cond = %.3g ; true_all maha = %.2f" %
              ("", v["null_cov_cond"], n["true_all"]))
    print("elapsed", res["elapsed_s"])

if __name__ == "__main__":
    main()
