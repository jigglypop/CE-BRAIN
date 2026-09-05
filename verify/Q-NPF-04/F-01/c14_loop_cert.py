# C14.  P3 channel identification certificate + P4 within-phase placebo + P6 power
# for candidate C1 (long-axis feedback-loop resonance) of verify/Q-NPF-04/spec.md.
#
# Statistic vector (DECLARED BEFORE ANY WORLD WAS RUN):
#   T1 = slope of measured loop period  1/f_q  on measured path term  x_q = L_q/v0 + tau_syn
#        over the KEPT loops of one animal.        C1 predicts 2; delay channel moves it.
#   T2 = mean over kept loops of the spectral peak sharpness  Q_q = f_q / FWHM_q
#        (damping-ratio proxy).                     coupling strength moves it.
#   T3 = mean over cells of log broadband baseline power outside every loop band.
#                                                   intrinsic gain moves it.
# Contrast is the early->late DIFFERENCE of each statistic, exactly as in c13.
#
# Pre-registered pass criteria (identical to the prior certificate, NOT retuned):
#   C-A  |z_k| >= 2.0 for every channel on the statistic vector
#   C-B  pairwise angle between channel response directions >= 15 deg
#   C-D  placebo (no learning) mean must sit within the null sd (z = 0 by construction)
#
# NO DATA PAYLOAD IS OPENED ANYWHERE IN THIS FILE.

import sys, os, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd_loop as F

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "result_c14_loop_cert.json")

# ------------------------------------------------------- P7: analysis constants
SEED = 20260902
N_REP = 200                # Monte-Carlo repetitions
N_FRAME = 2048             # frames per phase per cell (137.2 s at 0.0670 s)
WELCH_SEG = 512            # Welch segment length (frames) -> 34.3 s, df = 0.0292 Hz
WELCH_OVERLAP = 0.5        # Welch overlap fraction
DETREND = "linear"         # per-segment detrend
FMIN = 0.50                # Hz, lowest frequency admitted to peak search
FMAX = 6.50                # Hz, highest; DISC-1 keeps this strictly below Nyquist 7.463
NYQ_MARGIN = 0.87          # FMAX / Nyquist = 6.50/7.4627 = 0.871 (recorded, not tuned)
PEAK_PROM_SD = 3.0         # peak must exceed the local background by 3 background sd
BG_SMOOTH = 65             # bins of median smoothing that define the background
MIN_CELLS_PER_LOOP = 3     # DISC-2: a loop with fewer readout cells is discarded
# DISC-1 (ALIASING GUARD, decided from PATH LENGTHS ALONE, never from a spectrum).
# A loop whose UPPER-BOUND frequency 1/(2*(L/v_max + tau_syn)) exceeds ALIAS_KEEP * Nyquist
# is discarded before any statistic is computed.  v_max is a pre-registered upper bound on
# conduction velocity, so the rule uses only measured L and a declared constant: it cannot
# see the contrast.  Without it, a supra-Nyquist loop aliases to an arbitrary bin and its
# (L, 1/f) point destroys the regression (observed slope scatter 1.56-2.04 in smoke tests).
ALIAS_KEEP = 0.80          # fraction of Nyquist admitted
V_MIN_PRIOR = 0.080        # m/s, declared LOWER bound on conduction velocity
V_MAX_PRIOR = 0.125        # m/s, declared UPPER bound on conduction velocity
# SEL-1 (FUNDAMENTAL-SELECTION RULE).  A delayed feedback loop resonates on a COMB:
# the fundamental 1/(2 tau_loop) AND its odd harmonics.  For long loops a harmonic is
# often the LARGEST peak (measured here: L = 48 mm, fundamental 1.00 Hz at power 2.8
# versus the 7.03 Hz harmonic at 13.9).  An unrestricted argmax therefore returns a
# harmonic and destroys the period-vs-length regression (per-loop frequency sd up to
# 1.94 Hz at a bin width of 0.029 Hz -- misidentification, not measurement error).
# The peak search is therefore restricted to the window bracketed by the MEASURED path
# length and the two declared velocity bounds:
#     f in [ 1/(2(L/V_MIN + tau_syn)) , 1/(2(L/V_MAX + tau_syn)) ]
# This uses only L and declared constants, never the contrast, so P5 independence holds.
# The window is a factor V_MAX/V_MIN = 1.5625 wide, so it does NOT pin the answer: the
# delay channel's predicted shift (slope 2 -> 1.6) stays strictly inside it.
FWHM_FLOOR = 2             # bins; DISC-3 discard a peak whose FWHM cannot be measured
BB_BAND = (0.10, 0.40)     # Hz, broadband baseline band for T3 (below every loop peak)
TRAIN_PARITY = 1           # DISC/selection fold = ODD frames-blocks (P5, see below)
N_BLOCK = 8                # interleaved blocks the record is cut into for P5 splitting
EPS = 1e-300

WORLDS = {
    "true_all":      (F.TH_GAIN, F.TH_EFF, F.TH_DEL),
    "gain_only":     (F.TH_GAIN, 0.0, 0.0),
    "efficacy_only": (0.0, F.TH_EFF, 0.0),
    "delay_only":    (0.0, 0.0, F.TH_DEL),
    "placebo":       (0.0, 0.0, 0.0),
}
WORLD_ORDER = ("true_all", "gain_only", "efficacy_only", "delay_only", "placebo")
STAT_NAMES = ("T1_slope", "T2_sharpness", "T3_baseline_power")


# ------------------------------------------------------------------ spectra
def welch(y, dt=F.FRAME_DT, nseg=WELCH_SEG, ov=WELCH_OVERLAP):
    """y[cell, frame] -> (freq, P[cell, nf]) one-sided Welch PSD, Hann, linear detrend."""
    n, T = y.shape
    step = int(nseg * (1 - ov))
    starts = range(0, T - nseg + 1, step)
    win = np.hanning(nseg)
    u = (win ** 2).sum()
    acc = None
    cnt = 0
    tt = np.arange(nseg, dtype=float)
    A = np.vstack([tt, np.ones_like(tt)]).T
    Apinv = np.linalg.pinv(A)
    for s in starts:
        seg = y[:, s:s + nseg]
        if DETREND == "linear":
            coef = seg @ Apinv.T
            seg = seg - coef @ A.T
        Y = np.fft.rfft(seg * win[None, :], axis=-1)
        P = (np.abs(Y) ** 2) / (u / dt)
        acc = P if acc is None else acc + P
        cnt += 1
    freq = np.fft.rfftfreq(nseg, dt)
    return freq, acc / max(cnt, 1)


def med_smooth(p, w):
    """Running median background, odd window w, edge-replicated."""
    h = w // 2
    pad = np.pad(p, (h, h), mode="edge")
    out = np.empty_like(p)
    for i in range(p.size):
        out[i] = np.median(pad[i:i + w])
    return out


def peak_and_width(freq, p, fwin=None):
    """Locate the dominant peak and measure f, FWHM.  If fwin = (lo, hi) is given
    (SEL-1, from the measured path length), the search is confined to it.
    Returns (f_peak, fwhm, ok)."""
    lo_f = FMIN if fwin is None else max(FMIN, fwin[0])
    hi_f = FMAX if fwin is None else min(FMAX, fwin[1])
    band = (freq >= lo_f) & (freq <= hi_f)
    if band.sum() < 5:
        return np.nan, np.nan, False
    bg = med_smooth(p, BG_SMOOTH)
    resid = p - bg
    # Background scale is estimated over the FULL admissible band, not over the SEL-1
    # window.  Inside a narrow window the peak itself dominates the sd and inflates the
    # threshold, so a window-local sd would reject genuine peaks (measured: only 2 of 7
    # loops survived both folds).  The full band is the honest noise reference and it is
    # the same quantity the unwindowed version of this test used.
    full = (freq >= FMIN) & (freq <= FMAX)
    sd = np.std(resid[full])
    idx = np.where(band)[0]
    j = idx[np.argmax(resid[idx])]
    if resid[j] < PEAK_PROM_SD * max(sd, EPS):
        return np.nan, np.nan, False                       # DISC-4: no admissible peak
    half = bg[j] + 0.5 * resid[j]
    lo = j
    while lo > 0 and p[lo] > half:
        lo -= 1
    hi = j
    while hi < p.size - 1 and p[hi] > half:
        hi += 1
    if (hi - lo) < FWHM_FLOOR:
        return freq[j], np.nan, False                      # DISC-3
    # parabolic refinement of the peak location on the log spectrum
    if 0 < j < p.size - 1:
        y0, y1, y2 = np.log(max(p[j - 1], EPS)), np.log(max(p[j], EPS)), np.log(max(p[j + 1], EPS))
        d = y0 - 2 * y1 + y2
        sh = 0.5 * (y0 - y2) / d if abs(d) > 1e-12 else 0.0
        sh = float(np.clip(sh, -0.5, 0.5))
    else:
        sh = 0.0
    df = freq[1] - freq[0]
    return freq[j] + sh * df, (hi - lo) * df, True


# ------------------------------------------------------------------ statistics
def stats_one_animal(animal, y_sel, y_con):
    """y_sel : selection fold  (defines WHICH loops are kept and their peak windows)
       y_con : contrast fold   (supplies the numbers that enter T1,T2,T3)
    P5: the two folds are disjoint interleaved blocks of the record, so loop
    selection is independent of the contrast that is regressed."""
    freq, Ps = welch(y_sel)
    _, Pc = welch(y_con)
    x_list, T_list, Q_list = [], [], []
    nyq = 0.5 / F.FRAME_DT
    for q in range(F.N_LOOP):
        cells = np.where(animal["loop_of"] == q)[0]
        if cells.size < MIN_CELLS_PER_LOOP:
            continue                                        # DISC-2
        f_ub = 1.0 / (2.0 * (animal["L"][q] / V_MAX_PRIOR + F.TAU_SYN_LOOP))
        if f_ub > ALIAS_KEEP * nyq:
            continue                                        # DISC-1 aliasing guard
        fwin = (1.0 / (2.0 * (animal["L"][q] / V_MIN_PRIOR + F.TAU_SYN_LOOP)),
                1.0 / (2.0 * (animal["L"][q] / V_MAX_PRIOR + F.TAU_SYN_LOOP)))   # SEL-1
        ps = Ps[cells].mean(axis=0)
        f_s, _, ok_s = peak_and_width(freq, ps, fwin)
        if not ok_s:
            continue                                        # selection-fold admission
        pc = Pc[cells].mean(axis=0)
        f_c, w_c, ok_c = peak_and_width(freq, pc, fwin)
        if not ok_c or not np.isfinite(w_c) or w_c <= 0:
            continue
        x_list.append(animal["L"][q] / F.V_AXON_LOOP + F.TAU_SYN_LOOP)
        T_list.append(1.0 / f_c)
        Q_list.append(f_c / w_c)
    if len(x_list) < 3:
        return None
    x = np.array(x_list); T = np.array(T_list); Q = np.array(Q_list)
    A = np.vstack([x, np.ones_like(x)]).T
    slope = float(np.linalg.lstsq(A, T, rcond=None)[0][0])
    # T3 : broadband baseline power outside every loop band
    bb = (freq >= BB_BAND[0]) & (freq <= BB_BAND[1])
    T3 = float(np.mean(np.log(np.maximum(Pc[:, bb].mean(axis=1), EPS))))
    return np.array([slope, float(np.mean(Q)), T3])


def blocks_split(n_frame, n_block=N_BLOCK, parity=TRAIN_PARITY):
    """Interleaved block split of the record into selection / contrast folds."""
    edges = np.linspace(0, n_frame, n_block + 1).astype(int)
    sel, con = [], []
    for b in range(n_block):
        idx = np.arange(edges[b], edges[b + 1])
        (sel if b % 2 == parity else con).append(idx)
    return np.concatenate(sel), np.concatenate(con)


SEL_IDX, CON_IDX = blocks_split(N_FRAME)


def run_rep(animals, rep):
    out = {}
    for mi, animal in enumerate(animals):
        rng_e = np.random.default_rng(SEED + 1000 * rep + mi)
        y_e = F.simulate_traces(animal, (0.0, 0.0, 0.0), rng_e, N_FRAME)
        S_e = stats_one_animal(animal, y_e[:, SEL_IDX], y_e[:, CON_IDX])
        if S_e is None:
            continue
        for w in WORLD_ORDER:
            rng_l = np.random.default_rng(SEED + 500000 + 1000 * rep + 37 * mi
                                          + 7 * WORLD_ORDER.index(w))
            y_l = F.simulate_traces(animal, WORLDS[w], rng_l, N_FRAME)
            S_l = stats_one_animal(animal, y_l[:, SEL_IDX], y_l[:, CON_IDX])
            if S_l is None:
                continue
            out.setdefault(w, []).append(S_l - S_e)
        out.setdefault("_S_early", []).append(S_e)
    return {k: np.mean(np.array(v), axis=0) for k, v in out.items() if len(v) > 0}


def main():
    t0 = time.time()
    rng_c = np.random.default_rng(SEED)
    animals = [F.make_animal(n, rng_c) for n in F.CELLS_PER_MOUSE]

    reps = []
    for r in range(N_REP):
        reps.append(run_rep(animals, r))
        if (r + 1) % 10 == 0:
            print("rep", r + 1, "%.1fs" % (time.time() - t0), flush=True)

    pl = np.array([x["placebo"] for x in reps if "placebo" in x])
    null_sd = pl.std(axis=0, ddof=1)
    pl_mean = pl.mean(axis=0)
    S_early = np.array([x["_S_early"] for x in reps if "_S_early" in x])

    table = {}
    for w in WORLD_ORDER:
        arr = np.array([x[w] for x in reps if w in x])
        table[w] = dict(
            n_rep=int(arr.shape[0]),
            mean=arr.mean(axis=0).tolist(),
            sd=arr.std(axis=0, ddof=1).tolist(),
            z=[float((arr.mean(axis=0)[j] - pl_mean[j]) / max(null_sd[j], 1e-30))
               for j in range(3)],
        )
    Rmat = np.array([table[w]["z"] for w in ("gain_only", "efficacy_only", "delay_only")])
    norms = np.linalg.norm(Rmat, axis=1)
    ang, nm = {}, ("gain", "efficacy", "delay")
    for i in range(3):
        for j in range(i + 1, 3):
            d = norms[i] * norms[j]
            cs = float(Rmat[i] @ Rmat[j] / d) if d > 1e-12 else 0.0
            ang["%s-%s" % (nm[i], nm[j])] = float(np.degrees(np.arccos(np.clip(abs(cs), 0, 1))))

    pass_CA = bool(np.all(np.abs(Rmat).max(axis=1) >= 2.0))
    pass_CB = bool(min(ang.values()) >= 15.0)

    out = dict(
        script="c14_loop_cert.py", seed=SEED, elapsed_s=round(time.time() - t0, 1),
        candidate="C1 long-axis feedback-loop resonance",
        constants=dict(
            N_REP=N_REP, N_FRAME=N_FRAME, WELCH_SEG=WELCH_SEG,
            WELCH_OVERLAP=WELCH_OVERLAP, DETREND=DETREND, FMIN=FMIN, FMAX=FMAX,
            NYQ_MARGIN=NYQ_MARGIN, PEAK_PROM_SD=PEAK_PROM_SD, BG_SMOOTH=BG_SMOOTH,
            MIN_CELLS_PER_LOOP=MIN_CELLS_PER_LOOP, FWHM_FLOOR=FWHM_FLOOR,
            BB_BAND=list(BB_BAND), TRAIN_PARITY=TRAIN_PARITY, N_BLOCK=N_BLOCK,
            ALIAS_KEEP=ALIAS_KEEP, V_MIN_PRIOR=V_MIN_PRIOR, V_MAX_PRIOR=V_MAX_PRIOR,
            N_LOOP=F.N_LOOP, L_MIN=F.L_MIN, L_MAX=F.L_MAX, V_AXON=F.V_AXON_LOOP,
            TAU_SYN=F.TAU_SYN_LOOP, N_LIMB=F.N_LIMB, TAU_M=F.TAU_M_LOOP,
            K_LOOP=F.K_LOOP, K_LOGSD=F.K_LOGSD, G_LOGSD=F.G_LOGSD,
            CELL_NOISE_SD=F.CELL_NOISE_SD, SIM_DT=F.SIM_DT, NFFT=F.NFFT_LOOP,
            FRAME_DT=F.FRAME_DT, DG=F.DG, DW=F.DW, VFAC=F.VFAC,
            cells_per_mouse=list(F.CELLS_PER_MOUSE),
        ),
        stat_names=list(STAT_NAMES),
        S_early=dict(mean=S_early.mean(axis=0).tolist(),
                     sd=S_early.std(axis=0, ddof=1).tolist()),
        null_sd=null_sd.tolist(), placebo_mean=pl_mean.tolist(),
        table=table,
        channel_response_matrix=Rmat.tolist(),
        channel_norms=norms.tolist(),
        pairwise_angle_deg=ang,
        criteria=dict(C_A="max|z| >= 2 per channel", C_B="pairwise angle >= 15 deg"),
        pass_CA=pass_CA, pass_CB=pass_CB,
    )
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(dict(null_sd=out["null_sd"], placebo_mean=out["placebo_mean"],
                          norms=out["channel_norms"], ang=ang,
                          pass_CA=pass_CA, pass_CB=pass_CB), indent=1))
    for w in WORLD_ORDER:
        print(w, [round(x, 4) for x in table[w]["mean"]],
              "z", [round(x, 3) for x in table[w]["z"]])
    print("S_early", [round(x, 4) for x in S_early.mean(axis=0)])


if __name__ == "__main__":
    main()
