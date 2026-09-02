# C4. The last rescue route for the delay channel: the CLOSED-LOOP SPECTRUM of
# ongoing activity over a whole session, which is the endpoint the Q-NPF-04 spec's
# design hint points at ("in a recurrent circuit delay changes the closed-loop
# spectrum").  This uses far more samples than the 60 cue-locked trials.
#
#   ongoing:  tau_m xdot = -x + g[ W x(t-tau) + xi ],  xi white per cell
#   continuous spectrum   S_x(w) = M(w)^{-1} diag(g^2) M(w)^{-H}
#   observed              S_y(w) = |K_ca(w)|^2 S_x(w)  + flat imaging noise
#   sampled at f_s = 1/FRAME_DT with ALIASING folded in (+-N_ALIAS folds)
#   Whittle Fisher per frame  I_kl = (1/4pi) \int tr(f^-1 d_k f  f^-1 d_l f) dlam
#
# Baseline circuit again treated as KNOWN -> oracle bound.
# Session length is NOT in this repository's audit documents, so it is swept.
# NO DATA PAYLOAD IS OPENED.

import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c4_spectrum.json")

# ---- frozen constants for this check ----
N_LAM = 192                  # quadrature points on (0, pi]
N_ALIAS = 6                  # aliasing folds each side (|K_ca| at 97 Hz is ~4e-3)
SESSION_S = (600.0, 1200.0, 2400.0)   # s, swept: audit gives trials 145-225 only
PHASE_FRAC = 0.30            # fraction of a session covered by the first/last 60 trials
X_SD_TARGET = 0.30           # ongoing activation sd (rate fluctuates by ~ +-35%)
RHO_LIST = (0.60, 0.80, 0.90)
TAUM_LIST = (0.020, 0.050)
V_AXON_FIXED = 0.10          # m/s, the delay-friendliest value in the C1 grid

_LAM = (np.arange(N_LAM) + 0.5) / N_LAM * np.pi
_DLAM = np.pi / N_LAM
_FS = 1.0 / fwd.FRAME_DT


def kca(w):
    """Analytic transfer of the difference-of-exponentials calcium kernel,
    normalised to K(0)=1 (exact; avoids extrapolating the FFT grid)."""
    td, tr = fwd.CA_DECAY, fwd.CA_RISE
    return (td / (1 + 1j * w * td) - tr / (1 + 1j * w * tr)) / (td - tr)


def spec_obs(circ, th, scale, img):
    """Aliased observed discrete spectral density f(lam), shape (N_LAM,n,n).
    `scale` and `img` are fixed at the theta=0 operating point."""
    n = circ["n"]
    g = circ["g"] * np.exp(th[0])
    W = circ["W"] * np.exp(th[1])
    tau = circ["tau_ax"] * np.exp(th[2]) + fwd.TAU_SYN
    f = np.zeros((N_LAM, n, n), complex)
    idx = np.arange(n)
    for k in range(-N_ALIAS, N_ALIAS + 1):
        w = _LAM * _FS + 2.0 * np.pi * _FS * k                # rad/s
        ph = np.exp(-1j * w[:, None, None] * tau[None, :, :])
        M = -(g[None, :, None] * W[None, :, :]) * ph
        M[:, idx, idx] += (1.0 + 1j * w * circ["tau_m"])[:, None]
        Mi = np.linalg.inv(M)
        Sg = Mi * (g ** 2)[None, None, :]                     # M^{-1} diag(g^2)
        S = Sg @ np.conj(np.swapaxes(Mi, 1, 2))               # ... M^{-H}
        f += S * (np.abs(kca(w)) ** 2)[:, None, None]
    f = f * scale
    f[:, idx, idx] += img
    return f


def calibrate(circ):
    """Fix the signal/noise scale at theta=0: set the observed ongoing sd of the
    filtered signal to X_SD_TARGET*R_BASE and the imaging floor to
    IMG_SD_FRAC*R_BASE, so the SNR is a declared physiological quantity."""
    f = spec_obs(circ, (0, 0, 0), 1.0, 0.0)
    # Var = (1/2pi) int_{-pi}^{pi} f dlam = (1/pi) sum_{lam>0} f dlam  (f is even)
    var_raw = float(np.einsum("wii->wi", f).real.mean(axis=1).sum() * _DLAM / np.pi)
    scale = (X_SD_TARGET * fwd.R_BASE) ** 2 / max(var_raw, 1e-300)
    # a flat density img satisfies Var_img = img, so the floor is the variance itself
    img = (fwd.IMG_SD_FRAC * fwd.R_BASE) ** 2
    return scale, img


def whittle_fisher(circ, h=fwd.FD_H):
    scale, img = calibrate(circ)
    f0 = spec_obs(circ, (0, 0, 0), scale, img)
    finv = np.linalg.inv(f0)
    A = []
    for k in range(3):
        tp = np.zeros(3); tp[k] = h
        tm = np.zeros(3); tm[k] = -h
        d = (spec_obs(circ, tp, scale, img) - spec_obs(circ, tm, scale, img)) / (2 * h)
        A.append(finv @ d)
    I = np.zeros((3, 3))
    for k in range(3):
        for l in range(k, 3):
            tr = np.einsum("wij,wji->w", A[k], A[l]).real
            I[k, l] = I[l, k] = (1.0 / (4 * np.pi)) * 2.0 * float(np.sum(tr)) * _DLAM
    return I


def main():
    t0 = time.time()
    dth = np.array([fwd.TH_GAIN, fwd.TH_EFF, abs(fwd.TH_DEL)])
    old_v = fwd.V_AXON
    fwd.V_AXON = V_AXON_FIXED
    rows = []
    for rho in RHO_LIST:
        for taum in TAUM_LIST:
            rng = np.random.default_rng(fwd.SEED)
            Iper = np.zeros((3, 3))
            for n in fwd.CELLS_PER_MOUSE:
                c = fwd.make_circuit(n, rng, rho0=rho, tau_m=taum)
                Iper += whittle_fisher(c)
            for sess in SESSION_S:
                T = sess * PHASE_FRAC / fwd.FRAME_DT
                Itot = T * Iper
                Cov = 2.0 * np.linalg.inv(Itot)
                se = np.sqrt(np.diag(Cov))
                corr = Cov / np.sqrt(np.outer(np.diag(Cov), np.diag(Cov)))
                dI = np.sqrt(np.diag(Itot))
                ang = np.degrees(np.arccos(np.clip(np.abs(Itot / np.outer(dI, dI)), 0, 1)))
                z = dth / se
                rows.append(dict(rho0=rho, tau_m=taum, v_axon=V_AXON_FIXED,
                                 session_s=sess, frames_per_phase=round(float(T)),
                                 z_gain=float(z[0]), z_eff=float(z[1]), z_delay=float(z[2]),
                                 angle_ge=float(ang[0, 1]), angle_gd=float(ang[0, 2]),
                                 angle_ed=float(ang[1, 2]), corr_ge=float(corr[0, 1]),
                                 pass_CA=bool(np.all(z >= 2.0)),
                                 pass_CB=bool(min(ang[0, 1], ang[0, 2], ang[1, 2]) >= 15.0)))
    fwd.V_AXON = old_v
    res = dict(script="c4_spectrum.py", seed=fwd.SEED,
               endpoint="ongoing-activity closed-loop spectrum, whole session",
               n_lam=N_LAM, n_alias=N_ALIAS, phase_frac=PHASE_FRAC,
               x_sd_target=X_SD_TARGET, v_axon=V_AXON_FIXED,
               elapsed_s=round(time.time() - t0, 1),
               n_pass_all=sum(1 for r in rows if r["pass_CA"] and r["pass_CB"]),
               rows=rows)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%-5s %-6s %-7s %8s %8s %8s %8s %8s %9s" %
          ("rho", "tau_m", "sess_s", "frames", "z_gain", "z_eff", "z_delay",
           "ang_ge", "corr_ge"))
    for r in rows:
        print("%-5.2f %-6.3f %-7.0f %8d %8.2f %8.2f %8.3f %8.2f %9.4f" %
              (r["rho0"], r["tau_m"], r["session_s"], r["frames_per_phase"],
               r["z_gain"], r["z_eff"], r["z_delay"], r["angle_ge"], r["corr_ge"]))
    print("pass both C-A and C-B:", res["n_pass_all"], "/", len(rows),
          " elapsed", res["elapsed_s"])


if __name__ == "__main__":
    main()
