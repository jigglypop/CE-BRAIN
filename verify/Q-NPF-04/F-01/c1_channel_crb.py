# C1. Channel identification certificate, ORACLE upper bound.
#
# Question: at the NAMED data's N (8 mice, 354 same-cell ROIs, 60 trials/phase,
# 14.93 Hz frames), can ANY unbiased estimator detect each of the three channels
# of eq. (21.47) SEPARATELY?  We compute the Cramer-Rao bound for the three log
# channel scales with the ENTIRE baseline circuit (W, g, tau, b, drive) treated
# as KNOWN.  Any real statistic has a larger standard error, so a failure here is
# structural, not a failure of statistic design.
#
# Pre-registered pass criteria (fixed before the grid was run):
#   C-A  z_k = |dtheta_k| / SE_k  >= 2.0  for all three channels
#   C-B  pairwise response angle  >= 15 deg   (angle from I: cos = I_kl/sqrt(I_kk I_ll))
#   C-C  |post-fit correlation|   <= 0.90     (from the CRB covariance I^{-1})
import sys, os, json, time, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c1_crb.json")
RHO_GRID  = (0.40, 0.60, 0.80, 0.90)
TAUM_GRID = (0.020, 0.050, 0.100)
V_GRID    = (0.10, 0.20, 0.40)
MODES     = ("counts", "ca")
JIT_GRID  = (fwd.SIG_JIT, 0.0)
DTH = np.array([fwd.TH_GAIN, fwd.TH_EFF, abs(fwd.TH_DEL)])
NAMES = ("gain", "efficacy", "delay")


def one_config(rho, taum, v, mode, jit):
    old_v, old_jit = fwd.V_AXON, fwd.SIG_JIT
    fwd.V_AXON, fwd.SIG_JIT = v, jit
    rng = np.random.default_rng(fwd.SEED)
    Is = []
    for n in fwd.CELLS_PER_MOUSE:
        c = fwd.make_circuit(n, rng, rho0=rho, tau_m=taum)
        Is.append(fwd.fisher_theta(c, mode))
    fwd.V_AXON, fwd.SIG_JIT = old_v, old_jit
    se, corr, Itot = fwd.crb_change(Is)
    z = DTH / se
    dI = np.sqrt(np.diag(Itot))
    cosI = Itot / np.outer(dI, dI)
    ang = np.degrees(np.arccos(np.clip(np.abs(cosI), 0, 1)))
    return dict(
        rho0=rho, tau_m=taum, v_axon=v, mode=mode, sig_jit=jit,
        se=[float(x) for x in se],
        z={NAMES[k]: float(z[k]) for k in range(3)},
        angle_deg={"gain-eff": float(ang[0, 1]), "gain-del": float(ang[0, 2]),
                   "eff-del": float(ang[1, 2])},
        postfit_corr={"gain-eff": float(corr[0, 1]), "gain-del": float(corr[0, 2]),
                      "eff-del": float(corr[1, 2])},
        pass_CA=bool(np.all(z >= 2.0)),
        pass_CB=bool(min(ang[0, 1], ang[0, 2], ang[1, 2]) >= 15.0),
        pass_CC=bool(max(abs(corr[0, 1]), abs(corr[0, 2]), abs(corr[1, 2])) <= 0.90),
        efficacy_magnitude_admissible=bool(rho * (1.0 + fwd.DW) < 1.0),
    )


def main():
    t0 = time.time()
    rows = []
    for mode, jit, rho, taum, v in itertools.product(MODES, JIT_GRID, RHO_GRID, TAUM_GRID, V_GRID):
        rows.append(one_config(rho, taum, v, mode, jit))
    res = dict(
        script="c1_channel_crb.py", seed=fwd.SEED, elapsed_s=round(time.time() - t0, 1),
        named_N=dict(mice=fwd.N_MICE, cells_per_mouse=list(fwd.CELLS_PER_MOUSE),
                     total_cells=int(sum(fwd.CELLS_PER_MOUSE)),
                     trials_per_phase=fwd.N_TRIAL_PHASE, cue_trials=list(fwd.CUE_TRIALS),
                     frame_dt=fwd.FRAME_DT, n_frame=fwd.N_FRAME),
        channel_magnitudes=dict(gain_dlog=float(fwd.TH_GAIN), efficacy_dlog=float(fwd.TH_EFF),
                                delay_dlog=float(fwd.TH_DEL), DG=fwd.DG, DW=fwd.DW, VFAC=fwd.VFAC),
        criteria=dict(C_A="z>=2.0 all channels", C_B="pairwise angle>=15deg",
                      C_C="|post-fit corr|<=0.90"),
        rows=rows,
    )
    n_pass = sum(1 for r in rows if r["pass_CA"] and r["pass_CB"] and r["pass_CC"])
    res["n_configs"] = len(rows)
    res["n_pass_all"] = n_pass
    res["n_pass_CA"] = sum(1 for r in rows if r["pass_CA"])
    res["max_z_delay"] = max(r["z"]["delay"] for r in rows)
    res["max_z_delay_row"] = max(rows, key=lambda r: r["z"]["delay"])
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in
                      ("elapsed_s", "n_configs", "n_pass_all", "n_pass_CA", "max_z_delay")},
                     ensure_ascii=False))
    print("max z_delay row:", json.dumps(res["max_z_delay_row"], ensure_ascii=False))


if __name__ == "__main__":
    main()
