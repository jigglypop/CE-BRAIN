# Q-NPF-04 / C1 forward model: LONG-AXIS FEEDBACK LOOPS.
#
# Scope change (paper/진전_원장.md §2, 범위 확장 2026-09-04, user-fixed): the system
# is not one local patch but the whole neuraxis closed by long conduction paths.
# In a local patch the transport term is a micro-perturbation (that is why the delay
# channel scored z = 0.07/0.10/0.18 in result_c13_geodesic_cert.json). Around a long
# loop it is the FIRST-ORDER term.
#
# Structure.  N_LOOP separate negative-feedback loops per animal. Loop q has its own
# path length L_q (this is the regressor of the C1 prediction: several DISTINCT L per
# world, so the slope is identified without knowing v).  Each loop is a SINGLE-LIMB
# ring: the long axis is traversed ONCE per round trip and the return is local.
#     tau_m xdot_1 = -x_1 + g_1 [ -k * x_1(t - tau_q) + b_1 u(t) ]
#     tau_q = L_q / v + tau_syn
# TOPOLOGY IS LOAD-BEARING AND WAS FIXED BY THE PREDICTION, NOT BY A FIT.  A two-limb
# ring (both limbs long) has tau_loop = 2(L/v+tau_syn) and half-period tau_loop, giving
# 1/f = 4(L/v+tau_syn): slope 4, not 2.  Measured here before the certificate:
# two-limb slopes 4.269/4.018/4.057/4.002 across v in {0.5,0.2} and tau_m in {0.020,0.005}.
# The spec's own resonance equation  omega*tau_loop + arctan(omega*tau_m) = pi  carries a
# SINGLE arctan, i.e. one membrane pole in the loop, which is the single-limb ring.
# Resonance condition of the linearised loop, chapter-21 §5 form:
#     omega * tau_loop + arctan(omega * tau_m) = pi,   tau_loop = L/v + tau_syn
# so with tau_m << tau_loop,  1/f = 2 ( L/v + tau_syn ) + O(tau_m).   <-- C1 prediction
#
# The three channels are the same three lines as fwd.py, one scalar each:
#     th[0] = log gain scale       -> g_i        (intrinsic excitability)
#     th[1] = log efficacy scale   -> k          (coupling strength Wbar)
#     th[2] = log delay scale      -> tau^ax     (conduction velocity v; tau_syn FIXED)
# The delay channel scales only the L/v part, never tau_syn -- tau_syn is a synaptic
# transmission constant, not a transport time.
#
# Solved EXACTLY in the frequency domain, so no delay discretisation error.
#
# NO DATA PAYLOAD IS OPENED ANYWHERE IN THIS FILE.

import numpy as np

import fwd  # named-data structure constants (cells per mouse, trials, frame dt)

# ---------------------------------------------------------------------------
# FROZEN CONSTANTS  (P7: every threshold / window / percentile lives here)
# ---------------------------------------------------------------------------
SEED = 20260902

# --- named-data structure (inherited, unchanged) ---
CELLS_PER_MOUSE = fwd.CELLS_PER_MOUSE      # (54,52,33,17,35,62,38,63)
N_MICE = fwd.N_MICE                        # 8
N_TRIAL_PHASE = fwd.N_TRIAL_PHASE          # 60
FRAME_DT = fwd.FRAME_DT                    # 0.0670 s  -> Nyquist 7.463 Hz

# --- long-axis geometry ---
N_LOOP = 8                 # distinct feedback loops per animal
L_MIN = 0.008              # m, shortest loop path (whole-CNS scale, mouse neuraxis)
L_MAX = 0.060              # m, longest  loop path (head to lower-trunk sensory)
V_AXON_LOOP = 0.10         # m/s, long-range unmyelinated axon.  Chosen BEFORE the
                           # certificate so the whole predicted band 1.19-8.75 Hz is
                           # resolvable at the named frame rate (Nyquist 7.463 Hz);
                           # the top loop is deliberately left near/above Nyquist so the
                           # aliasing discard rule DISC-1 below has something to discard.
TAU_SYN_LOOP = 0.0020      # s, synaptic transmission delay in the loop
N_LIMB = 1                 # long-axis traversals per round trip (single-limb ring)

# --- loop dynamics ---
TAU_M_LOOP = 0.020         # s, membrane time constant
K_LOOP = 1.60              # dimensionless return-limb coupling (|k| > 1 -> sustained)
K_LOGSD = 0.15             # lognormal spread of k across loops
G_LOGSD = 0.25             # lognormal spread of intrinsic gain across cells
CELL_NOISE_SD = 0.30       # drive of the loop by internal noise (activation units)

# --- recording window (long enough to resolve the loop frequency) ---
REC_T = 20.0               # s of continuous recording per trial-block per phase
SIM_DT = 0.005             # s simulation grid
NFFT_LOOP = 4096           # 20.48 s at SIM_DT

# --- observation ---
R_BASE = fwd.R_BASE                 # 4.0 Hz baseline
CA_RISE = fwd.CA_RISE               # 0.050 s
CA_DECAY = fwd.CA_DECAY             # 0.400 s
IMG_SD_FRAC = fwd.IMG_SD_FRAC       # 0.05

# --- channel magnitudes (identical to the prior certificate: NOT retuned) ---
DG = fwd.DG                         # 0.10  gain     g -> 1.10 g
DW = fwd.DW                         # 0.18  efficacy k -> 1.18 k
VFAC = fwd.VFAC                     # 1.25  delay    v -> 1.25 v
TH_GAIN = float(np.log(1.0 + DG))   # +0.0953102
TH_EFF = float(np.log(1.0 + DW))    # +0.1655144
TH_DEL = float(np.log(1.0 / VFAC))  # -0.2231436

_FREQ = np.fft.rfftfreq(NFFT_LOOP, SIM_DT)
_W_RAD = 2.0 * np.pi * _FREQ


def loop_lengths(rng, n_loop=N_LOOP):
    """Distinct half-path lengths L_q (m), log-spaced with jitter, sorted."""
    base = np.exp(np.linspace(np.log(L_MIN), np.log(L_MAX), n_loop))
    jit = np.exp(0.05 * rng.standard_normal(n_loop))
    return np.sort(base * jit)


def make_animal(n_cell, rng):
    """One animal: N_LOOP long-axis loops, cells assigned to loops."""
    L = loop_lengths(rng)
    k = K_LOOP * np.exp(K_LOGSD * rng.standard_normal(N_LOOP) - 0.5 * K_LOGSD ** 2)
    g = np.exp(G_LOGSD * rng.standard_normal(n_cell) - 0.5 * G_LOGSD ** 2)
    # each cell reads out one node of one loop
    loop_of = rng.integers(0, N_LOOP, size=n_cell)
    node_of = rng.integers(0, 2, size=n_cell)
    return dict(n=n_cell, L=L, k=k, g=g, loop_of=loop_of, node_of=node_of)


def loop_period_pred(L, v=V_AXON_LOOP, tau_syn=TAU_SYN_LOOP):
    """C1 pre-registered prediction, tau_m -> 0 limit:  1/f = 2 (L/v + tau_syn)."""
    return N_LIMB * (L / v + tau_syn)


def loop_freq_exact(L, k, v=V_AXON_LOOP, tau_syn=TAU_SYN_LOOP, tau_m=TAU_M_LOOP):
    """Exact resonance root of  omega*tau_loop + arctan(omega*tau_m) = pi,
    tau_loop = L/v + tau_syn.  Solved by bisection (monotone in omega)."""
    tl = N_LIMB * (L / v + tau_syn)
    lo, hi = 1e-9, np.pi / tl
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        f = mid * tl + np.arctan(mid * tau_m) - np.pi
        if f > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi) / (2.0 * np.pi)


def loop_transfer(L, k, th, tau_m=TAU_M_LOOP):
    """Closed-loop transfer of the 2-node ring at each FFT frequency, with the three
    channel scales applied.  Returns H(omega) for node 1 driven by unit noise, and
    the same for node 2.  th = (log gain, log efficacy, log delay)."""
    gs = np.exp(th[0])
    ks = k * np.exp(th[1])
    tau_ax = (L / V_AXON_LOOP) * np.exp(th[2])       # delay channel scales transport only
    tau_limb = tau_ax + TAU_SYN_LOOP                  # tau_syn is NOT scaled
    a = 1.0 + 1j * _W_RAD * tau_m                     # leaky-membrane pole
    e = np.exp(-1j * _W_RAD * tau_limb)
    # single-limb inhibitory ring:  (a + gs*ks*e) X = gs * noise
    den = a + gs * ks * e
    H1 = gs / den
    # second observable node: same loop seen after one more local (undelayed) stage
    H2 = gs * (1.0 / (1.0 + 1j * _W_RAD * tau_m)) / den
    return H1, H2


def cell_spectra(animal, th):
    """Per-cell power spectrum of the latent activation x_i(omega), shape (n, nf)."""
    n = animal["n"]
    S = np.empty((n, _W_RAD.size))
    Hs = {}
    for q in range(N_LOOP):
        Hs[q] = loop_transfer(animal["L"][q], animal["k"][q], th)
    for i in range(n):
        q = animal["loop_of"][i]
        H = Hs[q][animal["node_of"][i]]
        gi = animal["g"][i]
        S[i] = (CELL_NOISE_SD * gi) ** 2 * np.abs(H) ** 2
    return S


def simulate_traces(animal, th, rng, n_frame):
    """Generate observed calcium traces, shape (n_cell, n_frame), at the named
    data's frame rate.  Latent x is a Gaussian process with the closed-loop
    spectrum; rate r = R_BASE*exp(x); calcium = causal kernel; frames subsampled."""
    n = animal["n"]
    S = cell_spectra(animal, th)                       # (n, nf)
    nf = _W_RAD.size
    # random-phase realisation with the given power spectrum
    amp = np.sqrt(np.maximum(S, 0.0) * NFFT_LOOP)
    ph = rng.random((n, nf)) * 2 * np.pi
    Xw = amp * np.exp(1j * ph)
    Xw[:, 0] = 0.0                                     # zero mean
    x = np.fft.irfft(Xw, n=NFFT_LOOP, axis=-1)
    r = R_BASE * np.exp(x - 0.5 * x.var(axis=-1, keepdims=True))
    t = np.arange(NFFT_LOOP) * SIM_DT
    kern = np.exp(-t / CA_DECAY) - np.exp(-t / CA_RISE)
    kern = np.maximum(kern, 0.0)
    kern = kern / kern.sum()
    c = np.fft.irfft(np.fft.rfft(r, axis=-1) * np.fft.rfft(kern)[None, :],
                     n=NFFT_LOOP, axis=-1)
    step = int(round(FRAME_DT / SIM_DT))               # 13.4 -> 13
    idx = (np.arange(n_frame) * step) % NFFT_LOOP
    y = c[:, idx]
    y = y + (IMG_SD_FRAC * R_BASE) * rng.standard_normal(y.shape)
    return y
