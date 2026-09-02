# C10. The REJECTED-CANDIDATE table: nine concrete cue-evoked statistics measured
# at the named N (8 mice, 354 cells, 60 trials/phase, 3 cues, 14.93 Hz), with the
# within-phase placebo (early1->early2) as the null.  The C1 Cramer-Rao bound says
# no cue-evoked statistic can beat it; this table is the empirical confirmation and
# the record of what was tried and discarded.
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd, c2_statistics as c2

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c10_cue.json")
RHO, TAUM, VAX, MODE = 0.60, 0.020, 0.10, "counts"
N_REP = 200
WORLDS = {"true_all": (fwd.TH_GAIN, fwd.TH_EFF, fwd.TH_DEL),
          "gain_only": (fwd.TH_GAIN, 0.0, 0.0),
          "efficacy_only": (0.0, fwd.TH_EFF, 0.0),
          "delay_only": (0.0, 0.0, fwd.TH_DEL),
          "placebo": (0.0, 0.0, 0.0)}

def main():
    t0 = time.time()
    old_v = fwd.V_AXON; fwd.V_AXON = VAX
    wn = list(WORLDS)
    K = len(c2.STATS)
    draws = {w: np.zeros((N_REP, K)) for w in wn}
    rng0 = np.random.default_rng(fwd.SEED)
    for mi, n in enumerate(fwd.CELLS_PER_MOUSE):
        circ = fwd.make_circuit(n, rng0, rho0=RHO, tau_m=TAUM)
        ref = c2.precompute(circ, (0.0, 0.0, 0.0), MODE)
        for wi, w in enumerate(wn):
            tab = ref if w == "placebo" else c2.precompute(circ, WORLDS[w], MODE)
            rng = np.random.default_rng(fwd.SEED + 300 * (wi + 1) + mi)
            for r in range(N_REP):
                # placebo uses 30/30 within early; real contrast uses 30 early / 30 late
                o_pre = c2.gen_trials(ref, MODE, fwd.N_TRIAL_PHASE // 2, rng)
                o_post = c2.gen_trials(tab, MODE, fwd.N_TRIAL_PHASE // 2, rng)
                d = c2.contrast(o_pre, o_post)
                draws[w][r] += np.array([d[k] for k in c2.STATS])
    fwd.V_AXON = old_v
    for w in wn:
        draws[w] /= float(fwd.N_MICE)
    pl = draws["placebo"]
    se = pl.std(axis=0, ddof=1); mu0 = pl.mean(axis=0)
    Z = {w: (draws[w].mean(axis=0) - mu0) / np.where(se > 0, se, np.inf) for w in wn}
    Mch = np.stack([Z["gain_only"], Z["efficacy_only"], Z["delay_only"]], axis=0)
    nrm = np.linalg.norm(np.nan_to_num(Mch), axis=1)
    Mn = np.nan_to_num(Mch)
    cos = (Mn @ Mn.T) / (np.outer(nrm, nrm) + 1e-300)
    ang = np.degrees(np.arccos(np.clip(np.abs(cos), 0, 1)))
    res = dict(script="c10_cue_candidates.py", seed=fwd.SEED, rho0=RHO, tau_m=TAUM,
               v_axon=VAX, mode=MODE, n_rep=N_REP, stats=list(c2.STATS),
               null_sd=[float(x) for x in se], placebo_mean=[float(x) for x in mu0],
               z={w: [float(x) for x in Z[w]] for w in wn},
               channel_norms=[float(x) for x in nrm],
               channel_angles_deg=dict(gain_eff=float(ang[0, 1]),
                                       gain_delay=float(ang[0, 2]),
                                       eff_delay=float(ang[1, 2])),
               per_statistic_channel_z={
                   c2.STATS[j]: dict(gain=float(Z["gain_only"][j]),
                                     efficacy=float(Z["efficacy_only"][j]),
                                     delay=float(Z["delay_only"][j]))
                   for j in range(K)},
               elapsed_s=round(time.time() - t0, 1))
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%-16s %10s %10s %10s" % ("statistic", "z_gain", "z_efficacy", "z_delay"))
    for j, nm in enumerate(c2.STATS):
        print("%-16s %10.3f %10.3f %10.3f" %
              (nm, Z["gain_only"][j], Z["efficacy_only"][j], Z["delay_only"][j]))
    print("\nchannel |z| (all 9 statistics jointly):", np.round(nrm, 3))
    print("angles deg:", {k: round(v, 2) for k, v in res["channel_angles_deg"].items()})
    print("elapsed", res["elapsed_s"])

if __name__ == "__main__":
    main()
