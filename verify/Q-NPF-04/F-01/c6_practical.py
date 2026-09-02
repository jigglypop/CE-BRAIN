# C6. The certificate for a CONCRETE, non-oracle statistic on the ongoing-activity
# cross-spectrum, at the named data's N.  This is where P3 (channel certificate),
# P4 (within-phase placebo) and P6 (power at the named N) are decided together.
#
# Observable and zero point (P2).  w = per-frame calcium (or deconvolved) trace.
# Every statistic below is built after removing each cell's temporal mean over the
# analysis segment, and is then either a LOG POWER (so a per-cell scale a_i cancels
# in the early->late difference) or a COHERENCE / CROSS-SPECTRAL PHASE (which are
# exactly invariant to o_i -> a_i o_i + b_i for a_i>0).  Nothing depends on the
# fluorescence zero.
#
# Three statistics, chosen to map onto the three lines of (21.47):
#   S1 = mean_cells log( band power )            input gain enters as g^2, the loop
#                                                as |amplification|^2
#   S2 = mean_pairs atanh(coherence)             independent per-cell input noise
#                                                cancels -> LOOP gain only
#   S3 = rms_pairs (cross-spectral group delay)  phase slope -> conduction delay
# S1 responds to gain and to loop gain; S2 responds to loop gain only; S3 to delay.
# g enters S1 and S2 differently (it scales the input noise as well as the loop),
# Wbar enters only through the loop: that asymmetry is what separates them.
#
# Selection / contrast split (P5): Welch segments are split by parity.  Pairs are
# admitted using ODD segments of the reference phase only; every reported contrast
# uses EVEN segments only.
#
# Placebo (P4): early1 -> early2, i.e. the two halves of the SAME phase, with the
# identical estimator and identical segment counts as the real contrast.
#
# NO DATA PAYLOAD IS OPENED.

import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_c6_practical.json")

# ---- frozen analysis constants (P7) ----
RHO0 = 0.80              # operating point (loop gain)
TAU_M = 0.020            # s
V_AXON = 0.10            # m/s
SESSION_S = 1200.0       # s, UNVERIFIED for the named data -> swept in C4
PHASE_FRAC = 0.30
T_PHASE = int(round(SESSION_S * PHASE_FRAC / fwd.FRAME_DT))   # frames per phase
T_HALF = T_PHASE // 2    # every contrast uses T_HALF frames per side
LSEG = 128               # Welch segment length (frames) = 8.58 s
HOP = 64                 # 50% overlap
BAND_HZ = (0.15, 5.00)   # analysis band
N_PAIR = 150             # pairs per mouse (cap)
PAIR_KEEP_Q = 0.50       # keep the top 50% of candidate pairs by fold-A coherence
X_SD_TARGET = 0.30       # ongoing activation sd (same physiological setting as C4/C5)
N_REP = 120              # Monte-Carlo repetitions per world
NFFT_ONG = 4096          # frames per generated record

_FS = 1.0 / fwd.FRAME_DT
_FREQ = np.fft.rfftfreq(LSEG, fwd.FRAME_DT)
_BAND = (_FREQ >= BAND_HZ[0]) & (_FREQ <= BAND_HZ[1])
_WIN = np.hanning(LSEG)

WORLDS = {
    "true_all": (fwd.TH_GAIN, fwd.TH_EFF, fwd.TH_DEL),
    "gain_only": (fwd.TH_GAIN, 0.0, 0.0),
    "efficacy_only": (0.0, fwd.TH_EFF, 0.0),
    "delay_only": (0.0, 0.0, fwd.TH_DEL),
    "placebo": (0.0, 0.0, 0.0),
}


def transfer(circ, th, scale):
    """H(lam) = K_ca(w) M(w)^{-1} diag(g), on the rfft grid of NFFT_ONG frames."""
    n = circ["n"]
    g = circ["g"] * np.exp(th[0])
    W = circ["W"] * np.exp(th[1])
    tau = circ["tau_ax"] * np.exp(th[2]) + fwd.TAU_SYN
    lam = 2 * np.pi * np.fft.rfftfreq(NFFT_ONG, fwd.FRAME_DT)      # rad/s, 0..pi*fs
    ph = np.exp(-1j * lam[:, None, None] * tau[None, :, :])
    M = -(g[None, :, None] * W[None, :, :]) * ph
    idx = np.arange(n)
    M[:, idx, idx] += (1.0 + 1j * lam * circ["tau_m"])[:, None]
    Mi = np.linalg.inv(M)
    td, tr = fwd.CA_DECAY, fwd.CA_RISE
    K = (td / (1 + 1j * lam * td) - tr / (1 + 1j * lam * tr)) / (td - tr)
    H = Mi * g[None, None, :] * K[:, None, None]
    return H * np.sqrt(scale)


def calib_scale(circ):
    H = transfer(circ, (0.0, 0.0, 0.0), 1.0)
    v = float(np.mean(np.sum(np.abs(H) ** 2, axis=2).mean(axis=1)) * 2.0 / NFFT_ONG)
    return (X_SD_TARGET * fwd.R_BASE) ** 2 / max(v, 1e-300)


def gen(H, rng, nframe):
    """One ongoing record y[frame,cell] from the transfer H."""
    nf, n, _ = H.shape
    xi = (rng.standard_normal((nf, n)) + 1j * rng.standard_normal((nf, n))) \
        / np.sqrt(2.0) * np.sqrt(NFFT_ONG)
    xi[0] = xi[0].real * np.sqrt(2.0)
    Y = np.einsum("fij,fj->fi", H, xi)
    y = np.fft.irfft(Y, n=NFFT_ONG, axis=0)[:nframe]
    y = y + (fwd.IMG_SD_FRAC * fwd.R_BASE) * rng.standard_normal(y.shape)
    return y


def segfft(y):
    """Welch segments -> Y[seg, freq, cell] on the analysis band."""
    T, n = y.shape
    starts = np.arange(0, T - LSEG + 1, HOP)
    segs = np.stack([y[s:s + LSEG] for s in starts], axis=0)
    segs = segs - segs.mean(axis=1, keepdims=True)          # per-cell AC per segment
    Y = np.fft.rfft(segs * _WIN[None, :, None], axis=1)
    return Y[:, _BAND, :]


def stats(Y, pi, pj):
    """S1, S2, S3 from segment FFTs Y[seg,freq,cell] and pair index arrays."""
    P = (np.abs(Y) ** 2).mean(axis=0)                        # (freq, cell)
    S1 = float(np.mean(np.log(P.sum(axis=0) + 1e-300)))
    C = (Y[:, :, pi] * np.conj(Y[:, :, pj])).mean(axis=0)    # (freq, pair)
    Pi, Pj = P[:, pi], P[:, pj]
    coh2 = np.abs(C) ** 2 / (Pi * Pj + 1e-300)
    cbar = np.sqrt(np.clip(coh2.mean(axis=0), 0.0, 0.999))
    S2 = float(np.mean(np.arctanh(cbar)))
    # group delay: weighted least-squares slope of unwrapped phase vs angular freq
    w = 2 * np.pi * _FREQ[_BAND]
    ph = np.unwrap(np.angle(C), axis=0)
    wt = coh2
    sw = wt.sum(axis=0) + 1e-300
    mw = (wt * w[:, None]).sum(axis=0) / sw
    mp = (wt * ph).sum(axis=0) / sw
    num = (wt * (w[:, None] - mw) * (ph - mp)).sum(axis=0)
    den = (wt * (w[:, None] - mw) ** 2).sum(axis=0) + 1e-300
    gd = -num / den                                          # s
    S3 = float(np.sqrt(np.mean(gd ** 2)))
    return np.array([S1, S2, S3]), coh2.mean(axis=0), gd


def pick_pairs(n, rng):
    iu = np.triu_indices(n, 1)
    m = iu[0].size
    sel = rng.permutation(m)[: min(N_PAIR, m)]
    return iu[0][sel], iu[1][sel]


def contrast(Ha, Hb, pi, pj, rng):
    """Two records of T_HALF frames each; selection on odd segments of the
    reference (a) record, contrast on even segments of both."""
    ya, yb = gen(Ha, rng, T_HALF), gen(Hb, rng, T_HALF)
    Ya, Yb = segfft(ya), segfft(yb)
    # fold A (odd segments of the reference record): SELECTION + INSTRUMENT only
    _, coh_a_odd, gd_inst = stats(Ya[0::2], pi, pj)
    thr = np.quantile(coh_a_odd, 1.0 - PAIR_KEEP_Q)
    keep = coh_a_odd >= thr
    if keep.sum() < 5:
        keep = np.ones_like(keep, bool)
    # fold B (even segments): CONTRAST only
    sa, _, gda = stats(Ya[1::2], pi[keep], pj[keep])
    sb, _, gdb = stats(Yb[1::2], pi[keep], pj[keep])
    d = sb - sa
    # S4: instrumental regression of the paired group-delay CHANGE on the fold-A
    # group delay.  Under tau -> e^th tau with gd proportional to the axonal part
    # this estimates e^th - 1.  The instrument comes from disjoint segments, so
    # measurement noise in gd does not attenuate the slope (P5, P8).
    z = gd_inst[keep]
    S4 = float(np.dot(z, gdb - gda) / (np.dot(z, z) + 1e-300))
    return np.concatenate([d, [S4]])


def main():
    t0 = time.time()
    old_v = fwd.V_AXON
    fwd.V_AXON = V_AXON
    rng0 = np.random.default_rng(fwd.SEED)
    wnames = list(WORLDS.keys())
    draws = {w: np.zeros((N_REP, 4)) for w in wnames}
    for mi, n in enumerate(fwd.CELLS_PER_MOUSE):
        c = fwd.make_circuit(n, rng0, rho0=RHO0, tau_m=TAU_M)
        sc = calib_scale(c)
        pi, pj = pick_pairs(n, rng0)
        H_ref = transfer(c, (0.0, 0.0, 0.0), sc)
        for wi, wname in enumerate(wnames):
            H_w = H_ref if wname == "placebo" else transfer(c, WORLDS[wname], sc)
            rng = np.random.default_rng(fwd.SEED + 1000 * (wi + 1) + mi)
            for r in range(N_REP):
                draws[wname][r] += contrast(H_ref, H_w, pi, pj, rng)
            if wname != "placebo":
                del H_w
        del H_ref
    fwd.V_AXON = old_v
    for w in wnames:
        draws[w] /= float(fwd.N_MICE)

    pl = draws["placebo"]
    se = pl.std(axis=0, ddof=1)                              # null sd of the contrast
    mu0 = pl.mean(axis=0)                                    # placebo bias
    res = {"script": "c6_practical.py", "seed": fwd.SEED,
           "constants": dict(RHO0=RHO0, TAU_M=TAU_M, V_AXON=V_AXON,
                             SESSION_S=SESSION_S, PHASE_FRAC=PHASE_FRAC,
                             T_PHASE=T_PHASE, T_HALF=T_HALF, LSEG=LSEG, HOP=HOP,
                             BAND_HZ=list(BAND_HZ), N_PAIR=N_PAIR,
                             PAIR_KEEP_Q=PAIR_KEEP_Q, X_SD_TARGET=X_SD_TARGET,
                             N_REP=N_REP, NFFT_ONG=NFFT_ONG,
                             cells_per_mouse=list(fwd.CELLS_PER_MOUSE)),
           "placebo_mean": [float(x) for x in mu0],
           "null_sd": [float(x) for x in se],
           "worlds": {}}
    R = {}
    for wname, D in draws.items():
        d = D.mean(axis=0) - mu0
        z = d / se
        R[wname] = z
        res["worlds"][wname] = dict(
            mean_contrast=[float(x) for x in D.mean(axis=0)],
            z_vs_placebo=[float(x) for x in z],
            sd=[float(x) for x in D.std(axis=0, ddof=1)])
    # channel response matrix (rows = channels, cols = S1,S2,S3), in null-sd units
    Mch = np.stack([R["gain_only"], R["efficacy_only"], R["delay_only"]], axis=0)
    nrm = np.linalg.norm(Mch, axis=1)
    cosm = (Mch @ Mch.T) / (np.outer(nrm, nrm) + 1e-300)
    ang = np.degrees(np.arccos(np.clip(np.abs(cosm), 0, 1)))
    res["channel_response_matrix_in_null_sd"] = [[float(v) for v in row] for row in Mch]
    res["channel_norms"] = [float(v) for v in nrm]
    res["channel_angles_deg"] = dict(
        gain_eff=float(ang[0, 1]), gain_delay=float(ang[0, 2]), eff_delay=float(ang[1, 2]))
    res["pass_CA_each_channel_norm_ge_2"] = bool(np.all(nrm >= 2.0))
    res["pass_CB_all_angles_ge_15"] = bool(min(ang[0, 1], ang[0, 2], ang[1, 2]) >= 15.0)
    res["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("null sd (S1,S2,S3):", np.round(se, 5), " placebo mean:", np.round(mu0, 5))
    print("%-14s %9s %9s %9s %9s %9s" % ("world","z_S1","z_S2","z_S3","z_S4","|z|"))
    for wname in WORLDS:
        z = R[wname]
        print("%-14s %9.3f %9.3f %9.3f %9.3f %9.3f" %
              (wname, z[0], z[1], z[2], z[3], float(np.linalg.norm(z))))
    print("angles deg:", {k: round(v, 2) for k, v in res["channel_angles_deg"].items()})
    print("C-A", res["pass_CA_each_channel_norm_ge_2"],
          " C-B", res["pass_CB_all_angles_ge_15"], " elapsed", res["elapsed_s"])


if __name__ == "__main__":
    main()
