# C8. POSITIVE CONTROL for the delay statistic S4 (and S3), plus the minimum
# detectable delay change (MDE) at the named N.  If S4 does not respond even to
# a huge conduction-velocity change, the C6/C7 certificate would be measuring a
# broken estimator rather than a property of the data.  VFAC is swept from the
# pre-registered 1.25 up to 8.0 (tau_ax shrinks by up to 8x).
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd, c6_practical as c6

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c8_poscontrol.json")
VFAC_LIST = (1.25, 2.0, 4.0, 8.0)
RHO = 0.60
N_REP = 150

def main():
    t0 = time.time()
    c6.RHO0 = RHO
    old_v = fwd.V_AXON; fwd.V_AXON = c6.V_AXON
    rng0 = np.random.default_rng(fwd.SEED)
    ths = [(0.0, 0.0, float(np.log(1.0 / v))) for v in VFAC_LIST]
    draws = {i: np.zeros((N_REP, 4)) for i in range(len(VFAC_LIST) + 1)}   # last = placebo
    for mi, n in enumerate(fwd.CELLS_PER_MOUSE):
        c = fwd.make_circuit(n, rng0, rho0=RHO, tau_m=c6.TAU_M)
        sc = c6.calib_scale(c)
        pi, pj = c6.pick_pairs(n, rng0)
        H_ref = c6.transfer(c, (0.0, 0.0, 0.0), sc)
        for wi, th in enumerate(ths + [(0.0, 0.0, 0.0)]):
            H_w = H_ref if wi == len(ths) else c6.transfer(c, th, sc)
            rng = np.random.default_rng(fwd.SEED + 7000 * (wi + 1) + mi)
            for r in range(N_REP):
                draws[wi][r] += c6.contrast(H_ref, H_w, pi, pj, rng)
    fwd.V_AXON = old_v
    for k in draws: draws[k] /= float(fwd.N_MICE)
    pl = draws[len(ths)]
    se = pl.std(axis=0, ddof=1); mu0 = pl.mean(axis=0)
    rows = []
    for wi, v in enumerate(VFAC_LIST):
        z = (draws[wi].mean(axis=0) - mu0) / se
        rows.append(dict(vfac=v, dlog_tau=float(np.log(1.0 / v)),
                         z=[float(x) for x in z],
                         norm=float(np.linalg.norm(z)),
                         mean=[float(x) for x in draws[wi].mean(axis=0)]))
    # MDE: |z| grows ~linearly in |dlog tau| for small changes -> read the slope
    ref = rows[0]
    slope = abs(ref["z"][3]) / abs(ref["dlog_tau"]) if ref["dlog_tau"] else 0.0
    res = dict(script="c8_poscontrol.py", seed=fwd.SEED, rho0=RHO, n_rep=N_REP,
               null_sd=[float(x) for x in se], placebo_mean=[float(x) for x in mu0],
               rows=rows, S4_z_per_unit_dlogtau=float(slope),
               elapsed_s=round(time.time() - t0, 1))
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("null sd:", np.round(se, 5), "placebo mean:", np.round(mu0, 5))
    print("%-7s %10s %9s %9s %9s %9s %9s" % ("VFAC","dlog_tau","z_S1","z_S2","z_S3","z_S4","|z|"))
    for r in rows:
        print("%-7.2f %10.4f %9.3f %9.3f %9.3f %9.3f %9.3f" %
              (r["vfac"], r["dlog_tau"], r["z"][0], r["z"][1], r["z"][2], r["z"][3], r["norm"]))
    print("elapsed", res["elapsed_s"])

if __name__ == "__main__":
    main()
