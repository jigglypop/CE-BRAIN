# C13. Channel identification certificate (P3) + within-phase placebo (P4) + power (P6)
# for the CONNECTION / GEODESIC candidate of verify/Q-NPF-04/spec.md.
#
# Candidate statistic vector (declared BEFORE any world was run):
#   S1 = metric-weighted regression slope of the acceleration contrast A = zdd - F
#        on the connection regressor Q = -Gamma zd zd            (card predicts 1, flat null 0)
#   S2 = mean over cells of the per-cell residual explained-variance improvement
#        EV_i = 1 - sum_t (u_i . R_geo)^2 / sum_t (u_i . R_flat)^2
#   S3 = population improvement ratio 1 - sum_t g(R_geo,R_geo) / sum_t g(R_flat,R_flat)
# with R_geo = zdd + Gamma zd zd - F  and  R_flat = zdd - F_flat.
#
# Metric (P1: estimand = CONDITIONAL output Fisher, eq. 21.41, h = cue identity, a
# design covariate whose law does not depend on z):
#   o_k ~ Poisson(lam_k(z)), lam_k(z) = exp(alpha_k + beta_k . z), k = 1..K_OUT
#   g_ab(z) = sum_k lam_k(z) beta_ka beta_kb          (exact Poisson Fisher)
#   d_c g_ab(z) = sum_k lam_k(z) beta_kc beta_ka beta_kb   (ANALYTIC, no lattice step)
#   Gamma^a_bc = 1/2 g^{ad}(d_b g_dc + d_c g_db - d_d g_bc)
# The readout (alpha, beta) and the chart U are fit on the TRAINING fold only and are
# then FROZEN for both phases, so the metric field is identical early and late; the
# contrast moves only because the population trajectory z(t) moves.
#
# NO DATA PAYLOAD IS OPENED ANYWHERE IN THIS FILE.

import sys, os, json, time, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "result_c13_geodesic_cert.json")

# ---------------------------------------------------------------- P7: constants
SEED = 20260902
RHO0 = 0.80            # operating point (loop gain); the delay channel's BEST oracle row
TAU_M = 0.020          # s
V_AXON = 0.10          # m/s
MODE = "ca"            # observable: calcium fluorescence at the frame grid
D_CHART = 3            # chart dimension
K_OUT = 4              # number of pre-specified future outputs
OUT_WIN_S = ((0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 3.0))   # s post cue
ANA_T = (0.0, 2.0)     # s post cue, analysis window for the geodesic contrast
SG_WIN = 9             # Savitzky-Golay window (frames) = 0.603 s
SG_ORD = 3             # SG polynomial order
GLM_ITERS = 25         # IRLS iterations
GLM_JITTER = 1e-8      # numerical solve jitter (NOT a rank-making ridge)
LAM_CLIP = (1e-3, 1e3) # clip on lam_k(z) when extrapolating along the trajectory
BEH_LOGSD = 0.40       # trial-to-trial sd of the behavioural log-rate
BEH_MEAN = 3.0         # mean output count per window
BEH_CALIB_TRIALS = 200 # calibration draws for the behaviour scale (seed offset 7777)
TRAIN_PARITY = 1       # training fold = ODD trials of the EARLY phase
N_REP = 200            # Monte-Carlo repetitions
EPS = 1e-300

ONSET_F = int(round(fwd.WIN_PRE / fwd.FRAME_DT))          # 7
_tf = (np.arange(fwd.N_FRAME) - ONSET_F) * fwd.FRAME_DT   # s relative to cue onset
ANA_IDX = np.where((_tf >= ANA_T[0]) & (_tf <= ANA_T[1]))[0]
OUT_IDX = [np.where((_tf >= a) & (_tf < b))[0] for a, b in OUT_WIN_S]

WORLDS = {
    "true_all":      (fwd.TH_GAIN, fwd.TH_EFF, fwd.TH_DEL),
    "gain_only":     (fwd.TH_GAIN, 0.0, 0.0),
    "efficacy_only": (0.0, fwd.TH_EFF, 0.0),
    "delay_only":    (0.0, 0.0, fwd.TH_DEL),
    "placebo":       (0.0, 0.0, 0.0),
}
WORLD_ORDER = ("true_all", "gain_only", "efficacy_only", "delay_only", "placebo")
STAT_NAMES = ("S1_slope", "S2_cell_EV", "S3_pop_improve")


# ---------------------------------------------------------------- SG derivatives
def _sg_coefs(win, order, deriv):
    half = win // 2
    x = np.arange(-half, half + 1, dtype=float)
    A = np.vander(x, order + 1, increasing=True)
    pinv = np.linalg.pinv(A)
    return pinv[deriv] * float(math.factorial(deriv))


_SG1 = _sg_coefs(SG_WIN, SG_ORD, 1) / fwd.FRAME_DT
_SG2 = _sg_coefs(SG_WIN, SG_ORD, 2) / fwd.FRAME_DT ** 2


def sg_deriv(y, coef):
    """y[..., frame] -> derivative at every ANA_IDX frame (full trace is available,
    so no edge extrapolation is used inside the analysis window)."""
    half = SG_WIN // 2
    out = np.empty(y.shape[:-1] + (ANA_IDX.size,))
    for j, t in enumerate(ANA_IDX):
        lo, hi = t - half, t + half + 1
        seg = y[..., lo:hi]
        out[..., j] = np.tensordot(seg, coef, axes=([-1], [0]))
    return out


# ---------------------------------------------------------------- force basis
def force_basis():
    """Phi(t) = [calcium-convolved cue drive, its derivative, 1] on ANA_IDX frames.
    The drive waveform and the calcium kernel are KNOWN experimental quantities."""
    t = np.arange(fwd.NFFT) * fwd.SIM_DT
    u = np.exp(-t / fwd.DRIVE_DECAY) - np.exp(-t / fwd.DRIVE_RISE)
    u = u / u.max()
    k = np.exp(-t / fwd.CA_DECAY) - np.exp(-t / fwd.CA_RISE)
    k = np.maximum(k, 0.0)
    k = k / k.sum()
    c = np.fft.irfft(np.fft.rfft(u) * np.fft.rfft(k), n=fwd.NFFT)
    c = c / c.max()
    c = np.roll(c, ONSET_F * int(round(fwd.FRAME_DT / fwd.SIM_DT)))
    c[: ONSET_F * int(round(fwd.FRAME_DT / fwd.SIM_DT))] = 0.0
    idx = np.clip(np.round(np.arange(fwd.N_FRAME) * fwd.FRAME_DT / fwd.SIM_DT
                           ).astype(int), 0, fwd.NFFT - 1)
    phi1 = c[idx]
    phi2 = np.gradient(phi1, fwd.FRAME_DT)
    Phi = np.stack([phi1[ANA_IDX], phi2[ANA_IDX], np.ones(ANA_IDX.size)], axis=1)
    return Phi


PHI = force_basis()                      # (T_ana, 3)
PHI_PINV = np.linalg.pinv(PHI)           # (3, T_ana)


# ---------------------------------------------------------------- trial generation
def draw_trials(mu, rng, n_trial_per_cue, beh_a, beh_c):
    """mu[cue,cell,frame] mean calcium.  Returns
       y[cue,trial,cell,frame]  observed (imaging noise included)
       o[cue,trial,K]           Poisson output counts (from the noise-free trial state)"""
    ncue, n, F = mu.shape
    y = np.empty((ncue, n_trial_per_cue, n, F))
    o = np.empty((ncue, n_trial_per_cue, K_OUT), dtype=float)
    fidx = np.arange(F, dtype=float)
    for c in range(ncue):
        for tr in range(n_trial_per_cue):
            d = fwd.SIG_JIT * rng.standard_normal()
            s = fidx - d / fwd.FRAME_DT
            i0 = np.clip(np.floor(s).astype(int), 0, F - 2)
            w = np.clip(s - i0, 0.0, 1.0)
            m = mu[c][:, i0] * (1 - w)[None, :] + mu[c][:, i0 + 1] * w[None, :]
            eta = np.sqrt(fwd.NU_G) * rng.standard_normal() - 0.5 * fwd.NU_G
            eps = np.sqrt(fwd.NU_P) * rng.standard_normal(n) - 0.5 * fwd.NU_P
            m = m * np.exp(eta) * np.exp(eps)[:, None]           # noise-free trial state
            y[c, tr] = m + (fwd.IMG_SD_FRAC * fwd.R_BASE) * rng.standard_normal((n, F))
            for k in range(K_OUT):
                q = float(beh_a[k] @ (m[:, OUT_IDX[k]].mean(axis=1) / fwd.R_BASE - 1.0))
                lam = BEH_MEAN * np.exp(beh_c[k] * q - 0.5 * BEH_LOGSD ** 2)
                o[c, tr, k] = rng.poisson(min(max(lam, 1e-6), 1e4))
    return y, o


def calib_beh(mu, rng, beh_a):
    """Scale c_k so that the behavioural log-rate has sd BEH_LOGSD."""
    n = mu.shape[1]
    F = mu.shape[2]
    fidx = np.arange(F, dtype=float)
    qs = np.zeros((K_OUT, BEH_CALIB_TRIALS))
    for tr in range(BEH_CALIB_TRIALS):
        c = tr % mu.shape[0]
        d = fwd.SIG_JIT * rng.standard_normal()
        s = fidx - d / fwd.FRAME_DT
        i0 = np.clip(np.floor(s).astype(int), 0, F - 2)
        w = np.clip(s - i0, 0.0, 1.0)
        m = mu[c][:, i0] * (1 - w)[None, :] + mu[c][:, i0 + 1] * w[None, :]
        eta = np.sqrt(fwd.NU_G) * rng.standard_normal() - 0.5 * fwd.NU_G
        eps = np.sqrt(fwd.NU_P) * rng.standard_normal(n) - 0.5 * fwd.NU_P
        m = m * np.exp(eta) * np.exp(eps)[:, None]
        for k in range(K_OUT):
            qs[k, tr] = float(beh_a[k] @ (m[:, OUT_IDX[k]].mean(axis=1) / fwd.R_BASE - 1.0))
    sd = qs.std(axis=1)
    return BEH_LOGSD / np.maximum(sd, 1e-9)


# ---------------------------------------------------------------- chart + readout
def fit_chart(y_train):
    """y_train[cue,trial,cell,frame] -> per-cell standardisation (P2: invariant to
    o_i -> a_i o_i + b_i) and the D_CHART-dim PCA chart."""
    flat = y_train.reshape(-1, y_train.shape[2], y_train.shape[3])   # (trials*, cell, F)
    mu_c = flat.mean(axis=(0, 2))
    sd_c = flat.std(axis=(0, 2))
    sd_c = np.where(sd_c > 1e-9, sd_c, 1.0)
    ystd = (y_train - mu_c[None, None, :, None]) / sd_c[None, None, :, None]
    mean_resp = ystd.mean(axis=1)                                    # (cue, cell, F)
    M = np.transpose(mean_resp, (1, 0, 2)).reshape(mean_resp.shape[1], -1)
    M = M - M.mean(axis=1, keepdims=True)
    U, S, _ = np.linalg.svd(M, full_matrices=False)
    return mu_c, sd_c, U[:, :D_CHART]


def project(y, mu_c, sd_c, U):
    ystd = (y - mu_c[..., None]) / sd_c[..., None]
    return np.tensordot(ystd, U, axes=([-2], [0]))       # (..., frame, D)


def fit_glm(Z, O):
    """Poisson IRLS.  Z[(trial,cue,k), D], O[(trial,cue,k)] per output k separately."""
    alpha = np.zeros(K_OUT)
    beta = np.zeros((K_OUT, D_CHART))
    for k in range(K_OUT):
        X = np.concatenate([np.ones((Z[k].shape[0], 1)), Z[k]], axis=1)
        w = np.zeros(D_CHART + 1)
        w[0] = np.log(max(O[k].mean(), 1e-3))
        for _ in range(GLM_ITERS):
            eta = np.clip(X @ w, -20, 20)
            lam = np.exp(eta)
            grad = X.T @ (O[k] - lam)
            H = (X * lam[:, None]).T @ X + GLM_JITTER * np.eye(D_CHART + 1)
            try:
                step = np.linalg.solve(H, grad)
            except np.linalg.LinAlgError:
                break
            w = w + step
            if np.max(np.abs(step)) < 1e-8:
                break
        alpha[k] = w[0]
        beta[k] = w[1:]
    return alpha, beta


# ---------------------------------------------------------------- geometry
def metric_and_gamma(z, alpha, beta):
    """z[T,D] -> g[T,D,D], Gamma[T,D,D,D] (Gamma^a_bc)."""
    lam = np.exp(np.clip(z @ beta.T + alpha[None, :], -20, 20))
    lam = np.clip(lam, LAM_CLIP[0], LAM_CLIP[1])                     # (T,K)
    g = np.einsum("tk,ka,kb->tab", lam, beta, beta)
    dg = np.einsum("tk,kc,ka,kb->tcab", lam, beta, beta, beta)       # d_c g_ab
    ginv = np.linalg.inv(g + 1e-12 * np.eye(D_CHART)[None])
    # Gamma^a_bc = 1/2 g^{ad} ( d_b g_dc + d_c g_db - d_d g_bc )
    A = np.einsum("tbdc->tdbc", dg)      # d_b g_dc  indexed [t,d,b,c]
    B = np.einsum("tcdb->tdbc", dg)      # d_c g_db
    C = np.einsum("tdbc->tdbc", dg)      # d_d g_bc
    Gam = 0.5 * np.einsum("tad,tdbc->tabc", ginv, A + B - C)
    return g, Gam, lam


def geodesic_stats(zc, U, alpha, beta, WF, WF_flat):
    """zc[cue,T,D] trajectory on the contrast fold.  Returns (S1,S2,S3)."""
    num = den = 0.0
    ge = gf = 0.0
    rg_cell = None
    rf_cell = None
    for c in range(zc.shape[0]):
        zfull = zc[c]                       # (F,D) full frame grid
        z = zfull[ANA_IDX]                  # (T,D)
        zd = sg_deriv(zfull.T, _SG1).T      # (T,D)
        zdd = sg_deriv(zfull.T, _SG2).T
        g, Gam, _ = metric_and_gamma(z, alpha, beta)
        Q = -np.einsum("tabc,tb,tc->ta", Gam, zd, zd)
        A = zdd - PHI @ WF[c]
        Af = zdd - PHI @ WF_flat[c]
        num += float(np.einsum("ta,tab,tb->", Q, g, A))
        den += float(np.einsum("ta,tab,tb->", Q, g, Q))
        Rg = A - Q
        ge += float(np.einsum("ta,tab,tb->", Rg, g, Rg))
        gf += float(np.einsum("ta,tab,tb->", Af, g, Af))
        rg = Rg @ U.T                      # (T, cell)
        rf = Af @ U.T
        rg_cell = rg ** 2 if rg_cell is None else rg_cell + rg ** 2
        rf_cell = rf ** 2 if rf_cell is None else rf_cell + rf ** 2
    S1 = num / (den + EPS)
    S3 = 1.0 - ge / (gf + EPS)
    EVi = 1.0 - rg_cell.sum(axis=0) / (rf_cell.sum(axis=0) + EPS)
    S2 = float(np.mean(EVi))
    return np.array([S1, S2, S3]), EVi


def fit_force(zt, alpha, beta):
    """Training-fold force fit.  Returns WF (curved, from zdd + Gamma zd zd) and
    WF_flat (from zdd alone), each (cue, 3, D)."""
    WF, WFf = [], []
    for c in range(zt.shape[0]):
        zfull = zt[c]
        z = zfull[ANA_IDX]
        zd = sg_deriv(zfull.T, _SG1).T
        zdd = sg_deriv(zfull.T, _SG2).T
        _, Gam, _ = metric_and_gamma(z, alpha, beta)
        Y = zdd + np.einsum("tabc,tb,tc->ta", Gam, zd, zd)
        WF.append(PHI_PINV @ Y)
        WFf.append(PHI_PINV @ zdd)
    return np.array(WF), np.array(WFf)


# ---------------------------------------------------------------- one mouse
def prep_mouse(n, rng_circ):
    circ = fwd.make_circuit(n, rng_circ, rho0=RHO0, tau_m=TAU_M)
    mus = {}
    for name, th in WORLDS.items():
        mus[name] = fwd.observe(fwd.solve_x(circ, th), MODE)
    mus["_base"] = mus["placebo"]
    a = rng_circ.standard_normal((K_OUT, n))
    a = a / np.linalg.norm(a, axis=1, keepdims=True)
    return circ, mus, a


def run_rep(mouse_pack, rep):
    """One Monte-Carlo repetition -> dict world -> delta-stat vector (3,)."""
    out = {}
    for mi, (n, mus, beh_a, beh_c) in enumerate(mouse_pack):
        rng = np.random.default_rng(SEED + 1000 * rep + mi)
        ntr = fwd.N_TRIAL_PHASE // 3                      # 20 trials per cue
        y_e, o_e = draw_trials(mus["_base"], rng, ntr, beh_a, beh_c)
        tr_idx = np.arange(ntr)
        train = tr_idx[tr_idx % 2 == TRAIN_PARITY]
        test = tr_idx[tr_idx % 2 != TRAIN_PARITY]
        mu_c, sd_c, U = fit_chart(y_e[:, train])
        # GLM design from TRAINING trials
        zt_all = project(y_e[:, train], mu_c, sd_c, U)     # (cue,trial,frame,D)
        Zk, Ok = [], []
        for k in range(K_OUT):
            Zk.append(zt_all[:, :, OUT_IDX[k], :].mean(axis=2).reshape(-1, D_CHART))
            Ok.append(o_e[:, train, k].reshape(-1))
        alpha, beta = fit_glm(Zk, Ok)
        # training-fold trajectory (trial mean over training trials) -> force fit
        z_train = project(y_e[:, train].mean(axis=1), mu_c, sd_c, U)
        WF, WFf = fit_force(z_train, alpha, beta)
        # EARLY statistic on the contrast fold
        z_early = project(y_e[:, test].mean(axis=1), mu_c, sd_c, U)
        S_e, _ = geodesic_stats(z_early, U, alpha, beta, WF, WFf)
        for w in WORLD_ORDER:
            rng_l = np.random.default_rng(SEED + 500000 + 1000 * rep + 37 * mi
                                          + 7 * WORLD_ORDER.index(w))
            y_l, _ = draw_trials(mus[w], rng_l, ntr, beh_a, beh_c)
            z_late = project(y_l[:, test].mean(axis=1), mu_c, sd_c, U)
            S_l, _ = geodesic_stats(z_late, U, alpha, beta, WF, WFf)
            out.setdefault(w, []).append(S_l - S_e)
        out.setdefault("_S_early", []).append(S_e)
    return {k: np.mean(np.array(v), axis=0) for k, v in out.items()}


def main():
    t0 = time.time()
    old_v, old_taum = fwd.V_AXON, fwd.TAU_M
    fwd.V_AXON = V_AXON
    rng_circ = np.random.default_rng(SEED)
    mouse_pack = []
    for n in fwd.CELLS_PER_MOUSE:
        circ, mus, beh_a = prep_mouse(n, rng_circ)
        rng_cal = np.random.default_rng(SEED + 7777 + n)
        beh_c = calib_beh(mus["_base"], rng_cal, beh_a)
        mouse_pack.append((n, mus, beh_a, beh_c))
    fwd.V_AXON = old_v

    reps = []
    for r in range(N_REP):
        reps.append(run_rep(mouse_pack, r))
        if (r + 1) % 5 == 0:
            print("rep", r + 1, "%.1fs" % (time.time() - t0), flush=True)

    res = {}
    for w in WORLD_ORDER:
        arr = np.array([x[w] for x in reps])              # (rep, 3)
        res[w] = dict(mean=arr.mean(axis=0).tolist(), sd=arr.std(axis=0, ddof=1).tolist())
    S_early = np.array([x["_S_early"] for x in reps])
    pl = np.array([x["placebo"] for x in reps])
    null_sd = pl.std(axis=0, ddof=1)
    pl_mean = pl.mean(axis=0)
    table = {}
    for w in WORLD_ORDER:
        arr = np.array([x[w] for x in reps])
        table[w] = dict(
            mean=arr.mean(axis=0).tolist(),
            z=[float((arr.mean(axis=0)[j] - pl_mean[j]) / max(null_sd[j], 1e-30))
               for j in range(3)],
        )
    # channel response matrix in null-sd units, and pairwise angles
    Rmat = np.array([table[w]["z"] for w in ("gain_only", "efficacy_only", "delay_only")])
    norms = np.linalg.norm(Rmat, axis=1)
    ang = {}
    nm = ("gain", "efficacy", "delay")
    for i in range(3):
        for j in range(i + 1, 3):
            d = norms[i] * norms[j]
            cs = float(Rmat[i] @ Rmat[j] / d) if d > 1e-12 else 0.0
            ang["%s-%s" % (nm[i], nm[j])] = float(np.degrees(np.arccos(np.clip(abs(cs), 0, 1))))

    out = dict(
        script="c13_geodesic_cert.py", seed=SEED, elapsed_s=round(time.time() - t0, 1),
        constants=dict(RHO0=RHO0, TAU_M=TAU_M, V_AXON=V_AXON, MODE=MODE,
                       D_CHART=D_CHART, K_OUT=K_OUT, OUT_WIN_S=OUT_WIN_S,
                       ANA_T=ANA_T, N_ANA_FRAME=int(ANA_IDX.size),
                       SG_WIN=SG_WIN, SG_ORD=SG_ORD, GLM_ITERS=GLM_ITERS,
                       GLM_JITTER=GLM_JITTER, LAM_CLIP=LAM_CLIP,
                       BEH_LOGSD=BEH_LOGSD, BEH_MEAN=BEH_MEAN,
                       BEH_CALIB_TRIALS=BEH_CALIB_TRIALS,
                       TRAIN_PARITY=TRAIN_PARITY, N_REP=N_REP,
                       trials_per_phase=fwd.N_TRIAL_PHASE,
                       cells_per_mouse=list(fwd.CELLS_PER_MOUSE)),
        stat_names=list(STAT_NAMES),
        S_early=dict(mean=S_early.mean(axis=0).tolist(),
                     sd=S_early.std(axis=0, ddof=1).tolist()),
        null_sd=null_sd.tolist(), placebo_mean=pl_mean.tolist(),
        table=table,
        channel_response_matrix=Rmat.tolist(),
        channel_norms=norms.tolist(),
        pairwise_angle_deg=ang,
    )
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in
                      ("null_sd", "placebo_mean", "channel_norms", "pairwise_angle_deg")},
                     indent=1))
    for w in WORLD_ORDER:
        print(w, [round(x, 4) for x in table[w]["mean"]],
              "z", [round(x, 3) for x in table[w]["z"]])
    print("S_early", [round(x, 4) for x in S_early.mean(axis=0)])
    fwd.TAU_M = old_taum


if __name__ == "__main__":
    main()
