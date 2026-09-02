# C5. Robustness of the C4 spectral result.  C4 passed under three idealisations
# and each one has to be paid for:
#   (i)   aliasing:  white input noise puts power above the 7.46 Hz Nyquist, and
#         a conduction delay of a few ms mostly lives THERE.  Sweep N_ALIAS.
#   (ii)  input-noise colour: white input is the most favourable case.  Real
#         synaptic input noise is low-pass.  Sweep tau_xi.
#   (iii) full n x n cross-spectrum vs the per-cell power spectra only.  The
#         oracle uses the whole cross-spectral matrix; estimating it needs
#         T >> n^2, and the named data has T/n^2 ~ 0.7.
# A result that survives only under (i)+(ii)+(iii) is not a result the named data
# can carry.

import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd
import c4_spectrum as c4

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c5_robust.json")

ALIAS_LIST = (0, 1, 3, 6)
TAU_XI_LIST = (0.000, 0.005, 0.020)     # s, input-noise correlation time
USE_DIAG = (False, True)
RHO, TAUM, SESS = 0.80, 0.020, 1200.0


def spec_obs(circ, th, scale, img, n_alias, tau_xi, diag_only):
    n = circ["n"]
    g = circ["g"] * np.exp(th[0])
    W = circ["W"] * np.exp(th[1])
    tau = circ["tau_ax"] * np.exp(th[2]) + fwd.TAU_SYN
    f = np.zeros((c4.N_LAM, n, n), complex)
    idx = np.arange(n)
    for k in range(-n_alias, n_alias + 1):
        w = c4._LAM * c4._FS + 2.0 * np.pi * c4._FS * k
        ph = np.exp(-1j * w[:, None, None] * tau[None, :, :])
        M = -(g[None, :, None] * W[None, :, :]) * ph
        M[:, idx, idx] += (1.0 + 1j * w * circ["tau_m"])[:, None]
        Mi = np.linalg.inv(M)
        sxi = 1.0 / (1.0 + (w * tau_xi) ** 2)              # input-noise colour
        Sg = Mi * ((g ** 2)[None, None, :])
        S = Sg @ np.conj(np.swapaxes(Mi, 1, 2))
        f += S * (np.abs(c4.kca(w)) ** 2 * sxi)[:, None, None]
    f = f * scale
    f[:, idx, idx] += img
    if diag_only:
        d = np.einsum("wii->wi", f).copy()
        f = np.zeros_like(f)
        f[:, idx, idx] = d
    return f


def fisher(circ, n_alias, tau_xi, diag_only, h=fwd.FD_H):
    raw = spec_obs(circ, (0, 0, 0), 1.0, 0.0, n_alias, tau_xi, False)
    var_raw = float(np.einsum("wii->wi", raw).real.mean(axis=1).sum() * c4._DLAM / np.pi)
    scale = (c4.X_SD_TARGET * fwd.R_BASE) ** 2 / max(var_raw, 1e-300)
    img = (fwd.IMG_SD_FRAC * fwd.R_BASE) ** 2
    f0 = spec_obs(circ, (0, 0, 0), scale, img, n_alias, tau_xi, diag_only)
    finv = np.linalg.inv(f0)
    A = []
    for k in range(3):
        tp = np.zeros(3); tp[k] = h
        tm = np.zeros(3); tm[k] = -h
        d = (spec_obs(circ, tp, scale, img, n_alias, tau_xi, diag_only)
             - spec_obs(circ, tm, scale, img, n_alias, tau_xi, diag_only)) / (2 * h)
        A.append(finv @ d)
    I = np.zeros((3, 3))
    for k in range(3):
        for l in range(k, 3):
            tr = np.einsum("wij,wji->w", A[k], A[l]).real
            I[k, l] = I[l, k] = (1.0 / (4 * np.pi)) * 2.0 * float(np.sum(tr)) * c4._DLAM
    return I


def main():
    t0 = time.time()
    dth = np.array([fwd.TH_GAIN, fwd.TH_EFF, abs(fwd.TH_DEL)])
    old_v = fwd.V_AXON
    fwd.V_AXON = c4.V_AXON_FIXED
    T = SESS * c4.PHASE_FRAC / fwd.FRAME_DT
    rows = []
    for diag_only in USE_DIAG:
        for na in ALIAS_LIST:
            for tx in TAU_XI_LIST:
                rng = np.random.default_rng(fwd.SEED)
                Iper = np.zeros((3, 3))
                for n in fwd.CELLS_PER_MOUSE:
                    c = fwd.make_circuit(n, rng, rho0=RHO, tau_m=TAUM)
                    Iper += fisher(c, na, tx, diag_only)
                Itot = T * Iper
                Cov = 2.0 * np.linalg.inv(Itot)
                se = np.sqrt(np.diag(Cov))
                corr = Cov / np.sqrt(np.outer(np.diag(Cov), np.diag(Cov)))
                dI = np.sqrt(np.diag(Itot))
                ang = np.degrees(np.arccos(np.clip(np.abs(Itot / np.outer(dI, dI)), 0, 1)))
                z = dth / se
                rows.append(dict(diag_only=bool(diag_only), n_alias=na, tau_xi=tx,
                                 z_gain=float(z[0]), z_eff=float(z[1]), z_delay=float(z[2]),
                                 angle_ge=float(ang[0, 1]), angle_gd=float(ang[0, 2]),
                                 angle_ed=float(ang[1, 2]), corr_ge=float(corr[0, 1]),
                                 pass_CA=bool(np.all(z >= 2.0)),
                                 pass_CB=bool(min(ang[0, 1], ang[0, 2], ang[1, 2]) >= 15.0)))
    fwd.V_AXON = old_v
    res = dict(script="c5_robust.py", seed=fwd.SEED, rho0=RHO, tau_m=TAUM,
               session_s=SESS, frames_per_phase=round(float(T)),
               total_cells=int(sum(fwd.CELLS_PER_MOUSE)),
               elapsed_s=round(time.time() - t0, 1),
               n_pass_all=sum(1 for r in rows if r["pass_CA"] and r["pass_CB"]),
               rows=rows)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%-10s %-7s %-8s %8s %8s %8s %8s %9s %6s" %
          ("cross-spec", "alias", "tau_xi", "z_gain", "z_eff", "z_delay", "ang_ge",
           "corr_ge", "pass"))
    for r in rows:
        print("%-10s %-7d %-8.3f %8.2f %8.2f %8.3f %8.2f %9.4f %6s" %
              ("diag" if r["diag_only"] else "full", r["n_alias"], r["tau_xi"],
               r["z_gain"], r["z_eff"], r["z_delay"], r["angle_ge"], r["corr_ge"],
               r["pass_CA"] and r["pass_CB"]))
    print("pass:", res["n_pass_all"], "/", len(rows), " elapsed", res["elapsed_s"])


if __name__ == "__main__":
    main()
