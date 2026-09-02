# C3. (a) the delay-visibility / gain-efficacy-separability FRONTIER, resolved in
#         loop gain; (b) is the gain-efficacy collinearity an artefact of taking
#         the perturbations HOMOGENEOUS?  Six perturbation directions are tested.
#
# Directions (each a one-parameter family in a log amplitude th):
#   A gain_uni   g_i   -> g_i  e^{th}
#   B eff_uni    W_ij  -> W_ij e^{th}
#   C delay_uni  tau^ax_ij -> tau^ax_ij e^{th}
#   D gain_het   g_i   -> g_i  e^{th xi^g_i},    xi^g  ~ N(0,1), unit rms, frozen
#   E eff_het    W_ij  -> W_ij e^{th xi^W_ij},   xi^W  ~ N(0,1), unit rms, frozen
#   F eff_cue    W_ij  -> W_ij e^{th 1[j in cue-1 drive set]}   (targeted potentiation)
#
# The angle between two directions in the whitened data space is
#   cos = I_kl / sqrt(I_kk I_ll)
# with I the per-trial identification Fisher of the OBSERVED data, i.e. exactly
# "do these two mechanisms push the recordings in different directions".

import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "result_c3_frontier.json")

RHO_FINE = (0.40, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.84, 0.88, 0.92, 0.95)
DIRS = ("gain_uni", "eff_uni", "delay_uni", "gain_het", "eff_het", "eff_cue")


def make_patterns(circ, rng):
    n = circ["n"]
    xg = rng.standard_normal(n)
    xg = xg / np.sqrt((xg ** 2).mean())
    xw = rng.standard_normal((n, n))
    xw = xw / np.sqrt((xw ** 2).mean())
    cue1 = (circ["b"][0] > 0).astype(float)           # presynaptic cue-1 drive set
    XC = np.tile(cue1[None, :], (n, 1))               # W_ij depends on presyn j
    return dict(xg=xg, xw=xw, xc=XC)


def perturb(circ, pat, name, th):
    n = circ["n"]
    one_g, one_W = np.ones(n), np.ones((n, n))
    if name == "gain_uni":
        return fwd.solve_x_full(circ, one_g * np.exp(th), one_W, one_W)
    if name == "eff_uni":
        return fwd.solve_x_full(circ, one_g, one_W * np.exp(th), one_W)
    if name == "delay_uni":
        return fwd.solve_x_full(circ, one_g, one_W, one_W * np.exp(th))
    if name == "gain_het":
        return fwd.solve_x_full(circ, np.exp(th * pat["xg"]), one_W, one_W)
    if name == "eff_het":
        return fwd.solve_x_full(circ, one_g, np.exp(th * pat["xw"]), one_W)
    if name == "eff_cue":
        return fwd.solve_x_full(circ, one_g, np.exp(th * pat["xc"]), one_W)
    raise ValueError(name)


def fisher_dirs(circ, pat, mode, dirs, h=fwd.FD_H):
    K = len(dirs)
    mu0 = fwd.observe(fwd.solve_x(circ, (0, 0, 0)), mode)
    J = np.empty((K,) + mu0.shape)
    for k, nm in enumerate(dirs):
        J[k] = (fwd.observe(perturb(circ, pat, nm, +h), mode)
                - fwd.observe(perturb(circ, pat, nm, -h), mode)) / (2 * h)
    dmu_dt = np.gradient(mu0, fwd.FRAME_DT, axis=-1)
    I = np.zeros((K, K))
    wts = np.asarray(fwd.CUE_TRIALS, float) / float(fwd.N_TRIAL_PHASE)
    for c in range(3):
        D, U, C = fwd.noise_pieces(mu0[c], dmu_dt[c], mode)
        Jc = J[:, c].reshape(K, -1)
        Di = 1.0 / D
        A = Jc * Di[None, :]
        term = A @ Jc.T
        if U.shape[1] > 0:
            Kmat = np.linalg.inv(C) + U.T @ (U * Di[:, None])
            B = A @ U
            term = term - B @ np.linalg.solve(Kmat, B.T)
        I += wts[c] * term
    return I


def pooled(rho, taum, v, mode, jit, dirs):
    old_v, old_j = fwd.V_AXON, fwd.SIG_JIT
    fwd.V_AXON, fwd.SIG_JIT = v, jit
    rng = np.random.default_rng(fwd.SEED)
    Itot = np.zeros((len(dirs), len(dirs)))
    for n in fwd.CELLS_PER_MOUSE:
        c = fwd.make_circuit(n, rng, rho0=rho, tau_m=taum)
        pat = make_patterns(c, rng)
        Itot += fwd.N_TRIAL_PHASE * fisher_dirs(c, pat, mode, dirs)
    fwd.V_AXON, fwd.SIG_JIT = old_v, old_j
    Cov = 2.0 * np.linalg.inv(Itot)                    # early->late change
    se = np.sqrt(np.diag(Cov))
    corr = Cov / np.sqrt(np.outer(np.diag(Cov), np.diag(Cov)))
    dI = np.sqrt(np.diag(Itot))
    ang = np.degrees(np.arccos(np.clip(np.abs(Itot / np.outer(dI, dI)), 0, 1)))
    return se, corr, ang


def main():
    t0 = time.time()
    res = {"script": "c3_frontier.py", "seed": fwd.SEED}

    # ---- (a) frontier in loop gain, at the delay-friendliest corner ----------
    dth = np.array([fwd.TH_GAIN, fwd.TH_EFF, abs(fwd.TH_DEL)])
    front = []
    for rho in RHO_FINE:
        se, corr, ang = pooled(rho, 0.020, 0.10, "counts", fwd.SIG_JIT,
                               ("gain_uni", "eff_uni", "delay_uni"))
        z = dth / se
        front.append(dict(rho0=rho, z_gain=float(z[0]), z_eff=float(z[1]),
                          z_delay=float(z[2]), angle_ge=float(ang[0, 1]),
                          angle_gd=float(ang[0, 2]), angle_ed=float(ang[1, 2]),
                          corr_ge=float(corr[0, 1]),
                          product_z_delay_x_angle_ge=float(z[2] * ang[0, 1]),
                          eff_magnitude_admissible=bool(rho * (1 + fwd.DW) < 1.0)))
    res["frontier_tau_m_0.020_v_0.10_counts_jit_0.030"] = front
    res["frontier_note"] = ("C-A needs z_delay>=2, C-B needs angle_ge>=15deg; "
                            "the two move in opposite directions with loop gain")

    # ---- (b) is the gain-efficacy collinearity an artefact of homogeneity? ---
    het = {}
    for rho in (0.60, 0.80):
        se, corr, ang = pooled(rho, 0.020, 0.10, "counts", fwd.SIG_JIT, DIRS)
        het["rho0=%.2f" % rho] = dict(
            dirs=list(DIRS),
            angle_deg=[[round(float(ang[i, j]), 3) for j in range(len(DIRS))]
                       for i in range(len(DIRS))],
            postfit_corr=[[round(float(corr[i, j]), 4) for j in range(len(DIRS))]
                          for i in range(len(DIRS))],
            se=[float(x) for x in se])
    res["heterogeneous_directions"] = het
    res["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("%-6s %8s %8s %8s %8s %9s %6s" %
          ("rho0", "z_gain", "z_eff", "z_delay", "ang_ge", "corr_ge", "adm"))
    for r in front:
        print("%-6.2f %8.2f %8.2f %8.3f %8.2f %9.4f %6s" %
              (r["rho0"], r["z_gain"], r["z_eff"], r["z_delay"], r["angle_ge"],
               r["corr_ge"], r["eff_magnitude_admissible"]))
    for k, v in het.items():
        print("\n--- pairwise angle (deg), %s ---" % k)
        print("%-11s" % "", " ".join("%10s" % d for d in DIRS))
        for i, d in enumerate(DIRS):
            print("%-11s" % d, " ".join("%10.2f" % v["angle_deg"][i][j]
                                        for j in range(len(DIRS))))
    print("elapsed", res["elapsed_s"])


if __name__ == "__main__":
    main()
