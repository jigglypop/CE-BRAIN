"""A1 step 64 hypothesis models (pre-registered in CONTRACT.md): ten NREM extensions H0-H9 of the step 58 compass ring.

Shared by all: Kim local ring at the Noorman optimum (16 units, tau 20 ms, dt 1 ms), step 58 schedule (exploration with
the head-direction cue; home cage wake / NREM blocks; NREM up 0.5-1.0 s with drive C_UP, down 0.1-0.3 s with drive -1),
home-cage wake generator = random walk D_W = -ln(0.977)/0.3 relayed with gain 1 (step 62), step 58 spike generation.
Only NREM differs:
  H0  drive on/off only (no NREM relay).                                       no parameter
  H1  short synaptic facilitation (Mongillo 2008 STP on the neighbour excitation, step 61 ring, U0 0.2, tau_d 0.2 s,
      sigma 0.05 = step 61 wake calibration); no NREM relay.                    tau_f, g_E
  H2  held generator, relayed heading jittered by an OU process (tau 0.1 s).   A, S      (step 62)
  H3  wandering generator (random walk D).                                     A, D      (step 63)
  H4  H2 + T-channel rebound gating of the relay: de-inactivation h rises in down states (tau_h+ 100 ms) and decays in
      up states (tau_h- 20 ms) (Smith et al. 2000 IFB); the tuned relay is scaled by (1 - h) and a uniform burst
      A B h / h_ref is added, B = IFB burst-to-tonic rate ratio (calibrated below).   A, S
  H5  H3 + the same rebound gating.                                             A, D
  H6  NREM recurrent gains: neighbour excitation x g_E, global inhibition x g_I; no NREM relay.   g_E, g_I
  H7  NREM ring noise x m, OU-coloured with correlation time tau_n (0 = white); no NREM relay.     m, tau_n
  H8  NREM adaptation (ACh low: slow AHP on; Sanchez-Vives et al. 2000 tau 1-10 s -> tau_a 1 s) with strength g_a,
      plus a held generator relayed without jitter (weak pull).                g_a, A
  H9  the relay is a population of IFB thalamocortical cells with the Smith 2000 parameters (16 directions x M cells,
      OU input noise sd 1 uA/cm^2, tau 5 ms as in Elijah et al. 2015), tonic currents set to the Taube 1995 anterior
      thalamic HD rates (background 1.99 Hz, peak 41.08 Hz) on the tonic branch, corticothalamic depolarisation
      withdrawn in NREM down states, output normalised by 41.08 Hz and filtered by a 5 ms synapse; wandering
      generator as H3.   A, D
      Noise: Elijah's IFB stimulus amplitude 0.5 uA/cm^2 (their sd 1.0 leaves no tonic branch below 3.8 Hz, so the
      Taube background cannot be tonic with it).
Random numbers: numpy draws in the fastcore order (ring noise, then generator steps); the IFB cell noise comes from a
separate numpy generator seeded (seed, 9), so H9 shares its ring noise and generator steps with H3 / H5 at the same seed.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
for _p in (HERE, LOOP / "fastcore"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import models as fm  # noqa: E402
import ring_kernels as rk  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


se = fm.se
st = _load("stp_trace", LOOP / "step61_stp_trace/stp_trace.py")
CH, ANG, K, DT = fm.CH, fm.ANG, fm.K, se.DT
D_W = -np.log(0.977) / 0.3
GAIN = json.loads((LOOP / "step58_sleep_equation/results.json").read_text(encoding="utf-8"))["gain"]
SIGMA, SIGMA_STP, GE_STP = 0.2, 0.05, 0.3                  # step 58 and step 61 wake calibrations
U0_STP, TAU_D_STP = 0.2, 0.2                                # Mongillo et al. 2008
TAU_ETA = 0.1                                               # step 62 jitter correlation time
TAU_H_PLUS, TAU_H_MINUS = 100.0, 20.0                       # ms, Smith et al. 2000 (Elijah et al. 2015 text: 100 ms)
TAU_A = 1.0                                                 # s, Sanchez-Vives, Nowak & McCormick 2000 (1-10 s)
ALPHA, DD, BETA = 2.5, 1.5, 1.0                             # Kim local ring (step 42)
# IFB (Smith et al. 2000 as used by Elijah et al. 2015): uF/cm^2, mS/cm^2, mV, ms
C_M, G_L, E_L, G_T, E_T, V_TH, V_H, V_RESET = 2.0, 0.035, -65.0, 0.07, 120.0, -35.0, -60.0, -50.0
SIG_OU, TAU_OU = 0.5, 5.0                                   # uA/cm^2 (Elijah et al. 2015 IFB stimulus amplitude), ms
E_HM, E_HP = math.exp(-1.0 / TAU_H_MINUS), math.exp(-1.0 / TAU_H_PLUS)
I_TONIC_MIN = 0.6                                           # uA/cm^2: tonic branch starts (no time below V_h)
BURST_WIN = 50                                              # ms after up onset counted as the rebound burst
RATE_BG, RATE_PEAK = 1.99, 41.08                            # Hz, Taube 1995 Table 1 (ATN HD cells)
M_IFB, TAU_SYN = 40, 5.0                                    # cells per direction; ms synaptic decay


# ----------------------------------------------------------------------------------------------------- ring kernels
@njit(cache=True)
def ring_switch_chunk(W0, W1, use1, r, c, noise, ext, k, rates_out):
    """Ring step with W1 where use1[t] (NREM) and W0 elsewhere. Returns (r, ok); ok False if a rate exceeds 1e4."""
    n = r.size
    W0T, W1T = W0.T.copy(), W1.T.copy()
    tmp = np.empty(n)
    for t in range(c.size):
        if use1[t]:
            rk._matvec_t(W1T, r, tmp)
        else:
            rk._matvec_t(W0T, r, tmp)
        for i in range(n):
            v = tmp[i] + c[t] + noise[t, i] + ext[t, i]
            if v < 0.0:
                v = 0.0
            r[i] = r[i] + k * (-r[i] + v)
            rates_out[t, i] = r[i]
            if r[i] > 1e4:
                return r, False
    return r, True


@njit(cache=True)
def ring_noise_chunk(W, r, c, z, nrem, sig_w, sig_n, e_n, q_n, white_n, eta, ext, k, rates_out):
    """Ring step with noise sig_w z in wake and sig_n eta in NREM; eta = z (white) or OU(e_n, q_n) of z (unit sd)."""
    n = r.size
    WT = W.T.copy()
    tmp = np.empty(n)
    for t in range(c.size):
        rk._matvec_t(WT, r, tmp)
        for i in range(n):
            if white_n:
                eta[i] = z[t, i]
            else:
                eta[i] = e_n * eta[i] + q_n * z[t, i]
            nz = sig_n * eta[i] if nrem[t] else sig_w * z[t, i]
            v = tmp[i] + c[t] + nz + ext[t, i]
            if v < 0.0:
                v = 0.0
            r[i] = r[i] + k * (-r[i] + v)
            rates_out[t, i] = r[i]
            if r[i] > 1e4:
                return r, False
    return r, True


@njit(cache=True)
def ring_adapt_nrem_chunk(W, r, ad, c, noise, ext, nrem, g_a, k, ka, rates_out):
    """Ring step with adaptation current -g_a ad in NREM only; ad tracks r with rate ka = dt / tau_a in all states."""
    n = r.size
    WT = W.T.copy()
    tmp = np.empty(n)
    for t in range(c.size):
        rk._matvec_t(WT, r, tmp)
        for i in range(n):
            v = tmp[i] + c[t] + noise[t, i] + ext[t, i]
            if nrem[t]:
                v -= g_a * ad[i]
            if v < 0.0:
                v = 0.0
            r[i] = r[i] + k * (-r[i] + v)
            ad[i] = ad[i] + ka * (r[i] - ad[i])
            rates_out[t, i] = r[i]
            if r[i] > 1e4:
                return r, False
    return r, True


@njit(cache=True)
def rebound_h(h, nrem, down, e_plus, e_minus, h_out):
    """T-channel de-inactivation of the relay: recovers towards 1 in NREM down states, inactivates otherwise."""
    for j in range(nrem.size):
        if nrem[j] and down[j]:
            h = 1.0 - (1.0 - h) * e_plus
        else:
            h = h * e_minus
        h_out[j] = h
    return h


# ------------------------------------------------------------------------------------------------------ IFB relay
@njit(cache=True)
def _seed(s):
    np.random.seed(s)


@njit(cache=True)
def _ifb_step(V, h, I):
    """One 1 ms step of the IFB cell; returns (V, h, spiked). T channel open (m_inf = 1) while V > V_H."""
    m = 1.0 if V > V_H else 0.0
    dV = (I - G_L * (V - E_L) - G_T * m * h * (V - E_T)) / C_M
    if V > V_H:
        h = h * E_HM
    else:
        h = 1.0 - (1.0 - h) * E_HP
    V = V + dV
    if V >= V_TH:
        return V_RESET, h, True
    return V, h, False


@njit(cache=True)
def ifb_rate(I_mean, T_ms, seed):
    """(rate Hz, fraction of time below V_h) of one IFB cell with OU input noise at mean current I_mean (1 s burn-in)."""
    _seed(seed)
    e_ou = math.exp(-1.0 / TAU_OU)
    q_ou = SIG_OU * math.sqrt(1.0 - e_ou * e_ou)
    V, h, eta, n, below = E_L, 0.0, 0.0, 0, 0
    for t in range(T_ms + 1000):
        eta = e_ou * eta + q_ou * np.random.standard_normal()
        V, h, s = _ifb_step(V, h, I_mean + eta)
        if t >= 1000:
            if s:
                n += 1
            if V < V_H:
                below += 1
    return n / (T_ms / 1000.0), below / T_ms


@njit(cache=True)
def ifb_burst(I_ct, down_ms, win_ms, n_cells, seed):
    """Rate (Hz) of untuned IFB cells in the first win_ms after a down state of down_ms (I_ct withdrawn), after 1 s tonic."""
    _seed(seed)
    e_ou = math.exp(-1.0 / TAU_OU)
    q_ou = SIG_OU * math.sqrt(1.0 - e_ou * e_ou)
    n, hsum = 0, 0.0
    for c in range(n_cells):
        V, h, eta = E_L, 0.0, 0.0
        for t in range(1000 + down_ms + win_ms):
            eta = e_ou * eta + q_ou * np.random.standard_normal()
            on = 1.0 if (t < 1000 or t >= 1000 + down_ms) else 0.0
            if t == 1000 + down_ms:
                hsum += h
            V, h, s = _ifb_step(V, h, on * I_ct + eta)
            if s and t >= 1000 + down_ms:
                n += 1
    return n / (n_cells * win_ms / 1000.0), hsum / n_cells


def calibrate_ifb(T_ms=200000, seed=64):
    """Tonic-branch currents for the Taube 1995 rates (bisection on [I_TONIC_MIN, 6] with common random numbers) and
    the burst ratio B: equal extra spikes, B * tau_h- = (burst spikes per cell in 50 ms after a 0.2 s down state,
    minus the tonic expectation) / 41.08 Hz, so that the H4/H5 term A B h(t) / h_ref carries the IFB burst."""
    def solve(target):
        lo, hi = I_TONIC_MIN, 6.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if ifb_rate(mid, T_ms, seed)[0] < target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    i_bg = solve(RATE_BG)
    i_pk = solve(RATE_PEAK)
    burst_rate, h_on = ifb_burst(i_bg, 200, BURST_WIN, 4000, seed + 1)
    extra = burst_rate * BURST_WIN / 1000.0 - RATE_BG * BURST_WIN / 1000.0
    rb, pb = ifb_rate(i_bg, T_ms, seed + 2), ifb_rate(i_pk, T_ms, seed + 2)
    return {"I_ct": i_bg, "I_hd": i_pk - i_bg, "rate_bg": rb[0], "below_vh_bg": rb[1], "rate_pk": pb[0], "below_vh_pk": pb[1],
            "burst_rate_50ms_after_0p2s_down": burst_rate, "extra_spikes_per_cell": extra, "h_at_up_onset": h_on,
            "B": extra / (RATE_PEAK * TAU_H_MINUS / 1000.0), "h_ref": 1.0 - math.exp(-200.0 / TAU_H_PLUS)}


@njit(cache=True)
def ifb_relay_chunk(V, h, eta, trace, zi, psi, s_on, g_rel, I_ct, I_hd, ang, e_syn, norm, ext_out):
    """Relay output (ring input) of 16 x M_IFB IFB cells: cell current = s_on I_ct + I_hd vonMises(psi) + OU noise
    driven by the pre-drawn standard normals zi (m, 16 M_IFB)."""
    e_ou = math.exp(-1.0 / TAU_OU)
    q_ou = SIG_OU * math.sqrt(1.0 - e_ou * e_ou)
    nd = ang.size
    for t in range(psi.size):
        for i in range(nd):
            f = math.exp(4.0 * (math.cos(ang[i] - psi[t]) - 1.0))
            base = s_on[t] * I_ct + I_hd * f
            cnt = 0
            for j in range(M_IFB):
                q = i * M_IFB + j
                eta[q] = e_ou * eta[q] + q_ou * zi[t, q]
                v1, h1, s = _ifb_step(V[q], h[q], base + eta[q])
                V[q] = v1
                h[q] = h1
                if s:
                    cnt += 1
            trace[i] = e_syn * trace[i] + cnt
            ext_out[t, i] = g_rel[t] * trace[i] * norm


# --------------------------------------------------------------------------------------------------- simulators
def _masks(sched):
    c, head, states = sched
    down = np.isnan(c)
    return np.where(down, se.C_DOWN_PRIMARY, c), head, down, fm.nrem_mask(sched)


def _generator(kind, theta, eta, head, nrem, down, m, rng, a_nrem, spread, sd_w):
    """Generator heading psi and relay gain a for one chunk; draws exactly as fastcore sim_pull / sim_wander."""
    psi, a = np.empty(m), np.empty(m)
    if kind == "pull":                                          # held generator, OU jitter of sd `spread` degrees
        z1, z2 = rng.standard_normal(m), rng.standard_normal(m)
        theta, eta = fm._pull_chunk(theta, eta, head, nrem, down, z1, z2, sd_w, np.radians(spread),
                                    np.exp(-DT / TAU_ETA), a_nrem, psi, a)
    else:                                                       # wandering generator, diffusion `spread` rad^2/s
        z = rng.standard_normal(m)
        theta = fm._wander_chunk(theta, head, nrem, down, z, sd_w, np.sqrt(2 * spread * DT), a_nrem, psi, a)
    return theta, eta, psi, a


def simulate(hyp, p, rng, sched, seed=0, ifb=None):
    """Rates (n, 16) float32 (unit-major) for hypothesis hyp with parameters p; None if the ring blows up."""
    c, head, down, nrem = _masks(sched)
    n = c.size
    rates = np.empty((n, 16), dtype=np.float32, order="F")
    zb, eb = np.empty((CH, 16)), np.empty((CH, 16))
    sd_w = np.sqrt(2 * D_W * DT)
    theta, eta = 0.0, 0.0
    r = np.zeros(16)
    kind, a_nrem, spread = {"H0": ("pull", 0.0, 0.0), "H1": ("pull", 0.0, 0.0), "H2": ("pull", p.get("A"), p.get("S")),
                            "H3": ("wander", p.get("A"), p.get("D")), "H4": ("pull", p.get("A"), p.get("S")),
                            "H5": ("wander", p.get("A"), p.get("D")), "H6": ("pull", 0.0, 0.0), "H7": ("pull", 0.0, 0.0),
                            "H8": ("pull", p.get("A"), 0.0), "H9": ("wander", 0.0, p.get("D"))}[hyp]
    sigma = SIGMA_STP if hyp == "H1" else SIGMA
    if hyp == "H1":
        u, x = np.full(16, U0_STP), np.ones(16)
    if hyp in ("H4", "H5"):
        h, e_plus, e_minus = 0.0, np.exp(-1.0 / TAU_H_PLUS), np.exp(-1.0 / TAU_H_MINUS)
        hb = np.empty(CH)
    if hyp == "H6":
        S_ = np.roll(np.eye(16), 1, axis=1)
        W1 = (ALPHA - 2 * DD) * np.eye(16) + p["g_E"] * DD * (S_ + S_.T) - p["g_I"] * BETA * np.ones((16, 16))
    if hyp == "H7":
        tau_n = p["tau_n"]
        white = tau_n == 0.0
        e_n = 0.0 if white else np.exp(-DT / tau_n)
        q_n = 1.0 if white else np.sqrt(1 - e_n * e_n)
        eta_n = np.zeros(16)
    if hyp == "H8":
        ad = np.zeros(16)
    if hyp == "H9":
        rng_ifb = np.random.default_rng([int(seed), 9])
        V, hh, et, tr = np.full(16 * M_IFB, E_L), np.zeros(16 * M_IFB), np.zeros(16 * M_IFB), np.zeros(16)
        e_syn = np.exp(-1.0 / TAU_SYN)
        norm = (1 - e_syn) / (M_IFB * RATE_PEAK * 1e-3)
        s_on = np.where(nrem & down, 0.0, 1.0)
        g_rel = np.where(nrem, p["A"], 1.0)
    for i0 in range(0, n, CH):
        m = min(CH, n - i0)
        sl = slice(i0, i0 + m)
        noise = fm._noise(rng, 1.0 if hyp == "H7" else sigma, zb, m)
        theta, eta, psi, a = _generator(kind, theta, eta, head[sl], nrem[sl], down[sl], m, rng, a_nrem, spread, sd_w)
        out = rates[sl]
        if hyp in ("H0", "H2", "H3"):
            r = rk.ring_chunk(se.W, r, c[sl], noise, rk.von_mises_input(ANG, psi, a, eb[:m]), K, out)
            ok = True
        elif hyp == "H1":
            r, u, x = rk.ring_stp_chunk(st.E, st.R, p["g_E"], r, u, x, c[sl], noise, rk.von_mises_input(ANG, psi, a, eb[:m]), K, DT,
                                        GAIN, U0_STP, TAU_D_STP, p["tau_f"], out)
            ok = True
        elif hyp in ("H4", "H5"):
            h = rebound_h(h, nrem[sl], down[sl], e_plus, e_minus, hb[:m])
            up_n = nrem[sl] & ~down[sl]
            gate = np.where(up_n, 1.0 - hb[:m], 1.0)
            ext = rk.von_mises_input(ANG, psi, a * gate, eb[:m])
            ext += np.where(up_n, p["A"] * ifb["B"] * hb[:m] / ifb["h_ref"], 0.0)[:, None]
            r = rk.ring_chunk(se.W, r, c[sl], noise, ext, K, out)
            ok = True
        elif hyp == "H6":
            r, ok = ring_switch_chunk(se.W, W1, nrem[sl], r, c[sl], noise, rk.von_mises_input(ANG, psi, a, eb[:m]), K, out)
        elif hyp == "H7":
            r, ok = ring_noise_chunk(se.W, r, c[sl], noise, nrem[sl], SIGMA, SIGMA * p["m"], e_n, q_n, white, eta_n,
                                     rk.von_mises_input(ANG, psi, a, eb[:m]), K, out)
        elif hyp == "H8":
            r, ok = ring_adapt_nrem_chunk(se.W, r, ad, c[sl], noise, rk.von_mises_input(ANG, psi, a, eb[:m]), nrem[sl], p["g_a"],
                                          K, DT / TAU_A, out)
        else:                                                   # H9: IFB relay replaces the smooth relay in every state
            ext = eb[:m]
            zi = rng_ifb.standard_normal((m, 16 * M_IFB), dtype=np.float32)
            ifb_relay_chunk(V, hh, et, tr, zi, psi, s_on[sl], g_rel[sl], ifb["I_ct"], ifb["I_hd"], ANG, e_syn, norm, ext)
            r = rk.ring_chunk(se.W, r, c[sl], noise, ext, K, out)
            ok = True
        if not ok or not np.isfinite(r).all() or r.max() > 1e4:
            return None
    return rates
