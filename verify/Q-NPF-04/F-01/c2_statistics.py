# C2. Concrete candidate statistics: channel response matrix, collinearity,
#     within-phase placebo, all at the NAMED data's N.
#
# Every candidate is declared here BEFORE any of them is measured, together with
# its invariance class.  Preprocessing is fixed and results-blind:
#
#   raw  o_i[t,f]                       (f = 0..51 frames, -0.5..+3.0 s about cue)
#   AC   obar_i[t,f] = o_i[t,f] - mean_f o_i[t,f]        kills per-cell offset b_i
#   all statistics below are built from obar and are either ratios or normalised
#   moments, so the per-cell scale a_i either cancels outright or cancels in the
#   early->late difference (a_i is a within-session constant: F0 is computed once).
#
# SELECTION / CONTRAST SPLIT (P5).  Trials of each phase are split by parity into
# fold A (odd) and fold B (even).  Every cell/bin SELECTION is computed on fold A
# only; every reported CONTRAST is computed on fold B only.  The two folds are
# disjoint sets of trials, so selection is independent of the contrast.
#
# PLACEBO (P4).  early1 = first 30 trials of early, early2 = last 30 trials of
# early.  Exactly the same estimator; the truth is zero change.

import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- frozen analysis constants (P7: nothing lives only in code) -------------
FOLD_PARITY = "odd=selection(A), even=contrast(B)"
LAG_MAX_FRAMES = 8          # +-8 frames = +-0.536 s, cross-correlation window
SEL_FRAC = 0.50             # keep the top 50% of cells by fold-A response energy
XCORR_FLOOR = 0.05          # min fold-A |cross-covariance mass| to admit a pair
WIN_FF = (0.00, 0.40)       # s post-cue, "feedforward-dominated" window
WIN_REC = (0.40, 1.50)      # s post-cue, "recurrence-dominated" window
EPS = 1e-12
N_REP = 200                 # Monte-Carlo repetitions per world
N_BOOT = 2000               # mouse-level bootstrap draws

_t_frame = np.arange(fwd.N_FRAME) * fwd.FRAME_DT - fwd.WIN_PRE   # s, cue at 0
_ff = (_t_frame >= WIN_FF[0]) & (_t_frame < WIN_FF[1])
_rec = (_t_frame >= WIN_REC[0]) & (_t_frame < WIN_REC[1])


# ---------------------------------------------------------------- simulation
SHIFT_MAX = 20                 # sim samples = +-0.10 s, covers +-3.3 sd of SIG_JIT


def precompute(circ, th, mode):
    """mu[shift, cue, cell, frame] for every admissible onset-jitter shift."""
    x = fwd.solve_x(circ, th)
    out = []
    for s in range(-SHIFT_MAX, SHIFT_MAX + 1):
        out.append(fwd.observe(np.roll(x, s, axis=-1), mode))
    return np.stack(out, axis=0)


def gen_trials(mu_tab, mode, n_trial, rng):
    """o[cell, trial, frame] for one phase, cues pooled in CUE_TRIALS proportion."""
    n = mu_tab.shape[2]
    per_cue = np.round(np.asarray(fwd.CUE_TRIALS, float)
                       / sum(fwd.CUE_TRIALS) * n_trial).astype(int)
    per_cue[-1] = n_trial - per_cue[:-1].sum()
    out = np.empty((n, n_trial, fwd.N_FRAME))
    k = 0
    for c in range(3):
        m = int(per_cue[c])
        if m <= 0:
            continue
        sh = np.clip(np.round(fwd.SIG_JIT * rng.standard_normal(m) / fwd.SIM_DT),
                     -SHIFT_MAX, SHIFT_MAX).astype(int) + SHIFT_MAX
        sg = np.exp(np.sqrt(fwd.NU_G) * rng.standard_normal(m) - 0.5 * fwd.NU_G)
        sp = np.exp(np.sqrt(fwd.NU_P) * rng.standard_normal((n, m)) - 0.5 * fwd.NU_P)
        lam = mu_tab[sh, c] * sg[:, None, None] * sp.T[:, :, None]   # (m,n,F)
        lam = np.transpose(lam, (1, 0, 2))
        if mode == "counts":
            out[:, k:k + m] = rng.poisson(np.maximum(lam, 1e-9))
        else:
            out[:, k:k + m] = lam + (fwd.IMG_SD_FRAC * fwd.R_BASE) *                 rng.standard_normal(lam.shape)
        k += m
    return out


# ---------------------------------------------------------------- statistics
def _ac(o):
    return o - o.mean(axis=-1, keepdims=True)


def _xcov_centroid(a, b, lag_max=LAG_MAX_FRAMES):
    """Centroid lag (in seconds) of the cross-covariance of two AC traces.
    A COMMON linear filter k applied to both traces convolves the
    cross-covariance with (k star k), which is symmetric with zero first
    moment, so this centroid is INVARIANT to the calcium kernel.  It is also
    invariant to a_i,a_j (normalised) and to b_i,b_j (removed by AC)."""
    L = np.arange(-lag_max, lag_max + 1)
    num = np.empty(L.size)
    for q, s in enumerate(L):
        if s >= 0:
            num[q] = np.dot(a[s:], b[: a.size - s]) if s < a.size else 0.0
        else:
            num[q] = np.dot(a[: a.size + s], b[-s:])
    return L, num


def stat_vector(o_sel, o_con, sel_mask=None):
    """o_sel: fold-A array (n,trial,F) used ONLY for selection.
       o_con: fold-B array (n,trial,F) used ONLY for the contrast.
    Returns a dict of the nine candidate statistics."""
    n = o_sel.shape[0]
    A = _ac(o_sel)
    B = _ac(o_con)
    Ea = (A ** 2).mean(axis=(1, 2))                   # fold-A energy per cell
    if sel_mask is None:
        thr = np.quantile(Ea, 1.0 - SEL_FRAC)
        sel_mask = Ea >= thr
    S = np.where(sel_mask)[0]
    Bs = B[S]
    mB = Bs.mean(axis=1)                               # (nS,F) trial-mean, fold B
    pop = mB.mean(axis=0)                              # population mean trace
    Eb = (Bs ** 2).mean(axis=(1, 2))                   # fold-B energy per cell

    out = {}
    # Q1 log population energy
    out["Q1_logE"] = float(np.log(Eb.mean() + EPS))
    # Q2 variance-mean power exponent (the F-03 statistic; baseline to be rejected)
    mu_cf = Bs.mean(axis=1).ravel()
    s2_cf = Bs.var(axis=1, ddof=1).ravel()
    ok = (mu_cf > EPS) & (s2_cf > EPS)
    if ok.sum() > 4:
        out["Q2_p"] = float(np.polyfit(np.log(mu_cf[ok]), np.log(s2_cf[ok]), 1)[0])
    else:
        out["Q2_p"] = np.nan
    # population centroid latency (common-mode; confounded with onset jitter)
    w = np.maximum(pop - pop.min(), 0.0)
    out["Q3_lat_pop"] = float(np.dot(_t_frame, w) / (w.sum() + EPS))
    # per-cell centroid lag against the population trace  -> Q4, Q5
    lags = np.empty(S.size)
    for q in range(S.size):
        L, c = _xcov_centroid(mB[q], pop)
        cc = np.maximum(c, 0.0)
        lags[q] = np.dot(L, cc) / (cc.sum() + EPS) * fwd.FRAME_DT
    out["Q4_lat_sd"] = float(np.std(lags))
    # pairwise lag RMS on fold-A-admitted pairs
    mA = A[S].mean(axis=1)
    keep = []
    for q in range(S.size):
        La, ca = _xcov_centroid(mA[q], mA.mean(axis=0))
        if np.abs(np.maximum(ca, 0).sum()) > XCORR_FLOOR * (np.abs(ca).sum() + EPS):
            keep.append(q)
    keep = np.array(keep, int) if keep else np.arange(S.size)
    out["Q5_pairlag_rms"] = float(np.sqrt(np.mean(lags[keep] ** 2)))
    # Q6 temporal second moment (closed-loop width), scale invariant
    w2 = np.maximum(pop - pop.min(), 0.0)
    tbar = np.dot(_t_frame, w2) / (w2.sum() + EPS)
    out["Q6_width"] = float(np.sqrt(np.dot((_t_frame - tbar) ** 2, w2) / (w2.sum() + EPS)))
    # Q7 recurrent index: log ratio of two windows of the SAME cell (a_i cancels)
    e_ff = (Bs[:, :, _ff] ** 2).mean(axis=(1, 2))
    e_rec = (Bs[:, :, _rec] ** 2).mean(axis=(1, 2))
    out["Q7_recidx"] = float(np.median(np.log(e_rec + EPS) - np.log(e_ff + EPS)))
    # Q8 per-cell log energy (used only through its early->late difference)
    out["_percell_logE"] = np.log(Eb + EPS)
    out["_sel_mask"] = sel_mask
    # Q9 noise correlation: trial-to-trial residual after removing the trial mean
    R = Bs - Bs.mean(axis=1, keepdims=True)
    Rf = R.reshape(S.size, -1)
    Rf = Rf / (np.linalg.norm(Rf, axis=1, keepdims=True) + EPS)
    C = Rf @ Rf.T
    iu = np.triu_indices(S.size, 1)
    out["Q9_rsc"] = float(np.mean(C[iu])) if S.size > 1 else np.nan
    return out


SCALARS = ("Q1_logE", "Q2_p", "Q3_lat_pop", "Q4_lat_sd", "Q5_pairlag_rms",
           "Q6_width", "Q7_recidx", "Q9_rsc")


def contrast(o_pre, o_post):
    """early->late contrast vector.  Selection uses fold A of the PRE phase only."""
    A_pre, B_pre = o_pre[:, 0::2], o_pre[:, 1::2]
    A_post, B_post = o_post[:, 0::2], o_post[:, 1::2]
    s_pre = stat_vector(A_pre, B_pre)
    mask = s_pre["_sel_mask"]
    s_post = stat_vector(A_post, B_post, sel_mask=mask)
    d = {k: s_post[k] - s_pre[k] for k in SCALARS}
    # Q8 dispersion of the per-cell log-energy change (a_i cancels exactly)
    d["Q8_dlogE_sd"] = float(np.std(s_post["_percell_logE"] - s_pre["_percell_logE"]))
    return d


STATS = SCALARS + ("Q8_dlogE_sd",)
