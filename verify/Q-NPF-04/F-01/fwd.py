# Q-NPF-04 forward model: leaky recurrent circuit with axonal conduction delays,
# cue-locked drive, calcium observation, matched to the *named* data structure of
# Ottenheimer et al. 2023 (eLife 84604) as recorded in this repository's audit
# documents. NO DATA PAYLOAD IS OPENED ANYWHERE IN THIS FILE.
#
# Named-data facts used (source: paper/검증_원장/CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_*,
# verify/Q-NPF-03/local_data_inventory.md):
#   8 mice; same-cell primary triplets per mouse 54,52,33,17,35,62,38,63 (total 354)
#   trials/session 145-225; A1 early = first 60, late = last 60  -> N_TRIAL_PHASE = 60
#   cue1/cue2/cue3 exact time-ordered partition; min per-cue count in a 60-trial phase = 13
#   median frame interval 0.066948-0.067205 s  -> FRAME_DT = 0.0670 s (14.93 Hz)
#   arrays available: F, Fneu, spks (suite2p deconvolved), frameTimes, cue/lick timestamps
#
# Dynamics (chapter 21 eq. 21.27/21.46-21.48, linearised at the operating point):
#   tau_m xdot_i = -x_i + g_i [ sum_j W_ij x_j(t - tau_ij) + b_i u(t) ]
#   tau_ij = ell_ij / v + tau_syn
# Solved EXACTLY in the frequency domain (no delay discretisation error):
#   M(w)_ij = (1 + i w tau_m) delta_ij - g_i W_ij exp(-i w tau_ij)
#   X(w)    = M(w)^{-1} diag(g) b U(w)
#
# Three channels are separate scalar log-parameters, exactly the three lines of (21.47):
#   th[0] = log(gain scale)      -> g_i  -> exp(th0) g_i        (intrinsic excitability)
#   th[1] = log(efficacy scale)  -> W_ij -> exp(th1) W_ij       (long-term weight  Wbar)
#   th[2] = log(delay scale)     -> tau^ax_ij -> exp(th2) tau^ax_ij  (conduction velocity v)

import numpy as np

# ----------------------------------------------------------------------------
# FROZEN CONSTANTS  (every decision threshold / window / percentile is here)
# ----------------------------------------------------------------------------
SEED = 20260902

# --- named-data structure ---
CELLS_PER_MOUSE = (54, 52, 33, 17, 35, 62, 38, 63)   # Ottenheimer A2 primary triplets
N_MICE = 8
N_TRIAL_PHASE = 60                                    # early = first 60, late = last 60
CUE_TRIALS = (20, 20, 20)                             # 3-cue partition of 60 (audit min 13)
FRAME_DT = 0.0670                                     # s  (audit 0.066948-0.067205)
WIN_PRE = 0.5                                         # s before cue onset
WIN_POST = 3.0                                        # s after cue onset
N_FRAME = int(np.floor((WIN_PRE + WIN_POST) / FRAME_DT))   # = 52

# --- simulation grid ---
SIM_DT = 0.005                                        # s
NFFT = 1024                                           # 5.12 s period, Nyquist 100 Hz

# --- circuit ---
TAU_M = 0.020            # s, membrane time constant
P_CONN = 0.15            # connection probability
ELL_MIN = 100e-6         # m, local axon path length
ELL_MAX = 600e-6         # m
V_AXON = 0.20            # m/s, unmyelinated local cortical axon
TAU_SYN = 0.0015         # s, synaptic transmission delay
RHO0 = 0.70              # spectral radius of diag(g) W at baseline
G_LOGSD = 0.25           # lognormal sd of intrinsic gain across cells
W_LOGSD = 0.50           # lognormal sd of nonzero weights
DRIVE_FRAC = 0.50        # fraction of cells receiving cue drive
DRIVE_RISE = 0.050       # s
DRIVE_DECAY = 0.300      # s
DRIVE_AMP = 0.40         # dimensionless activation units (calibrated so the
                         # single-cell peak rate ratio is p50 4.4x / p90 9.6x baseline;
                         # calibration is to physiology, not to any result: _calib.py)

# --- observation ---
R_BASE = 4.0             # Hz, baseline firing rate; rate r = R_BASE * exp(x)
CA_RISE = 0.050          # s   GCaMP6f-like
CA_DECAY = 0.400         # s
IMG_SD_FRAC = 0.05       # imaging noise sd as a fraction of baseline calcium level

# --- trial-to-trial nuisance (rank-2 shared + private) ---
NU_G = 0.05              # variance of trial-shared multiplicative log-gain
SIG_JIT = 0.030          # s, sd of trial-shared cue-onset jitter
NU_P = 0.05              # variance of per-cell private multiplicative log-gain

# --- channel magnitudes (pre-registered; = the prior card's forward-world settings) ---
DG = 0.10                # gain     g -> 1.10 g
DW = 0.18                # efficacy W -> 1.18 W
VFAC = 1.25              # delay    v -> 1.25 v, i.e. tau^ax -> tau^ax / 1.25
TH_GAIN = np.log(1.0 + DG)      # +0.095310
TH_EFF = np.log(1.0 + DW)       # +0.165514
TH_DEL = np.log(1.0 / VFAC)     # -0.223144

# --- numerical differentiation step for the identification Fisher ---
FD_H = 0.02              # log units, central difference


# ----------------------------------------------------------------------------
def make_circuit(n, rng, rho0=RHO0, tau_m=TAU_M):
    """One mouse's baseline circuit. Returns dict of arrays."""
    A = (rng.random((n, n)) < P_CONN).astype(float)
    np.fill_diagonal(A, 0.0)
    W = A * np.exp(W_LOGSD * rng.standard_normal((n, n)) - 0.5 * W_LOGSD ** 2)
    g = np.exp(G_LOGSD * rng.standard_normal(n) - 0.5 * G_LOGSD ** 2)
    ell = ELL_MIN + (ELL_MAX - ELL_MIN) * rng.random((n, n))
    tau_ax = ell / V_AXON                       # s, the v-dependent part
    # scale W so that rho(diag(g) W) = rho0
    ev = np.linalg.eigvals(g[:, None] * W)
    r = np.max(np.abs(ev))
    W = W * (rho0 / r)
    # three cue drives, each hitting a random half of the cells
    b = np.zeros((3, n))
    for c in range(3):
        idx = rng.permutation(n)[: max(1, int(round(DRIVE_FRAC * n)))]
        b[c, idx] = DRIVE_AMP * np.exp(0.3 * rng.standard_normal(idx.size) - 0.045)
    return dict(n=n, W=W, g=g, tau_ax=tau_ax, b=b, tau_m=tau_m)


def drive_spectrum():
    """FFT of the cue drive waveform u(t) on the simulation grid."""
    t = np.arange(NFFT) * SIM_DT
    u = np.exp(-t / DRIVE_DECAY) - np.exp(-t / DRIVE_RISE)
    u = u / u.max()
    return np.fft.rfft(u), t


_U_HAT, _T_SIM = drive_spectrum()
_W_RAD = 2.0 * np.pi * np.fft.rfftfreq(NFFT, SIM_DT)


def solve_x_full(circ, gmul, Wmul, taumul):
    """Exact frequency-domain solution with ELEMENTWISE multipliers.
    gmul (n,), Wmul (n,n), taumul (n,n) multiply g_i, W_ij, tau^ax_ij."""
    n = circ["n"]
    g = circ["g"] * gmul
    W = circ["W"] * Wmul
    tau = circ["tau_ax"] * taumul + TAU_SYN
    nf = _W_RAD.size
    # M(w) = (1 + i w tau_m) I - diag(g) W exp(-i w tau)
    ph = np.exp(-1j * _W_RAD[:, None, None] * tau[None, :, :])       # (nf,n,n)
    M = -(g[None, :, None] * W[None, :, :]) * ph
    diag = (1.0 + 1j * _W_RAD * circ["tau_m"])
    M[:, np.arange(n), np.arange(n)] += diag[:, None]
    rhs = (g[None, :, None] * circ["b"].T[None, :, :]) * _U_HAT[:, None, None]  # (nf,n,3)
    Xw = np.linalg.solve(M, rhs)                                     # (nf,n,3)
    x = np.fft.irfft(Xw, n=NFFT, axis=0)                             # (T,n,3)
    return np.transpose(x, (2, 1, 0))                                # (3,n,T)


def solve_x(circ, th):
    """th = (log gain scale, log efficacy scale, log delay scale), homogeneous."""
    return solve_x_full(circ, np.exp(th[0]), np.exp(th[1]), np.exp(th[2]))


def ca_kernel():
    t = np.arange(NFFT) * SIM_DT
    k = np.exp(-t / CA_DECAY) - np.exp(-t / CA_RISE)
    k = np.maximum(k, 0.0)
    k = k / k.sum()          # unit DC gain for the DISCRETE convolution below
    return np.fft.rfft(k)


_K_HAT = ca_kernel()
# index of cue onset on the simulation grid, then the frame sample points
_ONSET = int(round(WIN_PRE / SIM_DT))
_FRAME_IDX = np.clip(
    np.round((np.arange(N_FRAME) * FRAME_DT) / SIM_DT).astype(int), 0, NFFT - 1
)


def observe(x, mode):
    """x[cue,cell,T] activation -> mean observable mu[cue,cell,frame].
    mode = 'counts' : per-frame spike count, best case (idealised deconvolution)
           'ca'     : calcium fluorescence sampled at the frame grid
    The response is placed so that cue onset sits WIN_PRE into the window; the
    pre-cue frames therefore carry the baseline level."""
    r = R_BASE * np.exp(x)                                # Hz
    if mode == "counts":
        s = r
    elif mode == "ca":
        s = np.fft.irfft(np.fft.rfft(r, axis=-1) * _K_HAT[None, None, :],
                         n=NFFT, axis=-1)
    else:
        raise ValueError(mode)
    # roll so the response onset sits WIN_PRE into the analysis window; the
    # pre-cue segment is the baseline level (x=0 -> r=R_BASE; the calcium kernel
    # has unit area so the convolved baseline is also R_BASE)
    s = np.roll(s, _ONSET, axis=-1)
    s[..., :_ONSET] = R_BASE
    mu = s[..., _FRAME_IDX]
    if mode == "counts":
        mu = mu * FRAME_DT                                # counts per frame
    return mu


def mu_of_theta(circ, th, mode):
    return observe(solve_x(circ, th), mode)


def noise_pieces(mu, dmu_dt, mode):
    """Return (D, U, C) with Sigma = diag(D) + U C U^T for ONE cue,
    flattened over (cell, frame).
    D : Poisson/shot + imaging + private multiplicative
    U : [mu, dmu/dt] shared trial-gain and shared onset-jitter directions
    C : diag(NU_G, SIG_JIT^2)"""
    m = mu.reshape(-1)
    d = dmu_dt.reshape(-1)
    if mode == "counts":
        shot = np.maximum(m, 1e-9)                        # Poisson
        img = 0.0
    else:
        shot = 0.0
        img = (IMG_SD_FRAC * R_BASE) ** 2
    D = shot + img + NU_P * m ** 2
    cols, var = [], []
    if NU_G > 0:
        cols.append(m); var.append(NU_G)
    if SIG_JIT > 0:
        cols.append(d); var.append(SIG_JIT ** 2)
    if not cols:                     # no shared nuisance: Sigma is diagonal
        return D, np.zeros((m.size, 0)), np.zeros((0, 0))
    U = np.stack(cols, axis=1)
    C = np.diag(var)
    return D, U, C


def fisher_theta(circ, mode, th0=(0.0, 0.0, 0.0), h=FD_H):
    """Per-trial identification Fisher matrix for th = (log gain, log efficacy,
    log delay), summed over the three cues weighted by CUE_TRIALS/60.
    The baseline circuit (W, g, tau, b) is treated as KNOWN -- this is an
    ORACLE bound, so the resulting CRB is a lower bound on the standard error
    of any unbiased estimator of the three channel scales."""
    th0 = np.asarray(th0, float)
    mu0 = mu_of_theta(circ, th0, mode)                    # (3,n,F)
    J = np.empty((3,) + mu0.shape)                        # (param,cue,cell,frame)
    for k in range(3):
        tp = th0.copy(); tp[k] += h
        tm = th0.copy(); tm[k] -= h
        J[k] = (mu_of_theta(circ, tp, mode) - mu_of_theta(circ, tm, mode)) / (2 * h)
    dmu_dt = np.gradient(mu0, FRAME_DT, axis=-1)
    I = np.zeros((3, 3))
    wts = np.asarray(CUE_TRIALS, float) / float(N_TRIAL_PHASE)
    for c in range(3):
        D, U, C = noise_pieces(mu0[c], dmu_dt[c], mode)
        Jc = J[:, c].reshape(3, -1)                       # (3, n*F)
        Di = 1.0 / D
        A = Jc * Di[None, :]                              # (3, m)
        term = A @ Jc.T
        if U.shape[1] > 0:
            # Woodbury:  Sinv = Di - Di U (Cinv + U^T Di U)^{-1} U^T Di
            UtDiU = U.T @ (U * Di[:, None])
            Kmat = np.linalg.inv(C) + UtDiU
            B = A @ U
            term = term - B @ np.linalg.solve(Kmat, B.T)
        I += wts[c] * term
    return I


def crb_change(I_per_trial_by_mouse, n_trial=N_TRIAL_PHASE):
    """CRB for the early->late CHANGE in the three log-channel scales, pooling
    mice. Both phases are estimated, so Var(delta) = 2 * Var(single phase)."""
    Itot = np.zeros((3, 3))
    for I1 in I_per_trial_by_mouse:
        Itot += n_trial * I1
    Cov = 2.0 * np.linalg.inv(Itot)
    se = np.sqrt(np.diag(Cov))
    dd = np.sqrt(np.outer(np.diag(Cov), np.diag(Cov)))
    corr = Cov / dd
    return se, corr, Itot
