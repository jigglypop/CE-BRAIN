"""One compass model on the fly lattice: the step 42 ring (Kim 2017 local model at the Noorman 2024 optimum, 16
directions, threshold-linear) + PEN-like side-ring self-motion input + Kim et al. 2019 ring-neuron -> E-PG plasticity
(32 azimuthal ring neurons, inhibitory, 'SOM inhib, post-synaptically gated').

  tau dy/dt = -y + [ W_ra y + c + v(t) A y - W_in r(t) 2pi/32 + inj(t) ]_+          tau = 50 ms (Kim 2019)
  dW_in/dt  = clip( W_in + 3 f_v eps' y (W_max - r - W_in), 0, W_max ) - W_in
  v(t) = omega(t) / g   (g: bump speed per unit v, calibrated so that bump speed = fly angular velocity)

Kim 2019 ratios are kept relative to the ring's own bump: eps' y_peak = eps y_peak(Kim 2019); optogenetic current per
wedge / y_peak as in Kim 2019. Visual inputs, noise, velocity trace and the learning-rate profile f_v come from the
step 43 port of the authors' sim_cond.m.
"""
from __future__ import annotations

from pathlib import Path
import sys

import numba
import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
sys.path.insert(0, str(LOOP / "step41_few_neuron_attractor"))
sys.path.insert(0, str(LOOP / "step43_visual_map_learning"))
import tl_ring as tl  # noqa: E402
import kim2019_model as km  # noqa: E402

NW = 16
ANG = np.arange(NW) * 360.0 / NW
RING = {"alpha": 2.500, "D": 1.5, "beta": 1.0}      # step 42 local_opt
C = 1.0
TAU = 0.05
DT_INT = 0.002
W_RA = tl.local_ring(RING["alpha"], RING["D"], RING["beta"])
A_GEN = tl.generator(W_RA)
KIM_RA = km.ring_params()
KIM_INJ_PER_WEDGE = km.MAMP * 2 * 2 * np.pi / km.NW          # Kim 2019 opto current per wedge (ww_mamp * 2pi/nw)


@numba.njit(cache=True)
def _integrate(y, W, Wra, Agen, c, vis, v, inj, fv, learn, dt_int, dt, tau, eps, wmax, sample_every):
    nw, ni = W.shape
    T = v.size
    sub = int(round(dt / dt_int))
    n_out = (T - 1) // sample_every + 1
    ys = np.zeros((nw, n_out))
    k = 0
    tmp = np.empty(nw)
    for i in range(T - 1):
        if i % sample_every == 0:
            ys[:, k] = y
            k += 1
        for s in range(sub):
            f = s / sub
            vv = (1 - f) * v[i] + f * v[i + 1]
            fvv = (1 - f) * fv[i] + f * fv[i + 1]
            for a in range(nw):
                acc = 0.0
                for b in range(nw):
                    acc += (Wra[a, b] + vv * Agen[a, b]) * y[b]
                vis_cur = 0.0
                for b in range(ni):
                    rb = (1 - f) * vis[b, i] + f * vis[b, i + 1]
                    vis_cur += W[a, b] * rb * 2 * np.pi / ni
                x = acc + c - vis_cur + (1 - f) * inj[a, i] + f * inj[a, i + 1]
                tmp[a] = x if x > 0.0 else 0.0
            if learn:
                for a in range(nw):
                    for b in range(ni):
                        rb = (1 - f) * vis[b, i] + f * vis[b, i + 1]
                        w_new = W[a, b] + 3 * fvv * eps * y[a] * (wmax - rb - W[a, b])
                        if w_new < 0.0:
                            w_new = 0.0
                        if w_new > wmax:
                            w_new = wmax
                        W[a, b] += dt_int * (w_new - W[a, b])
            for a in range(nw):
                y[a] += dt_int * (tmp[a] - y[a]) / tau
    if k < n_out:
        ys[:, k] = y                       # final state (the step 43 port left this column at zero)
    return y, W, ys


def natural_bump():
    r, _, _ = tl.run(W_RA, C, [(20.0, tl.cue(0.0), 0.0), (100.0, 0.0, 0.0)])
    return r


def speed_gain():
    """Bump speed (deg/s) per unit v in darkness, from a linear fit over +-v (tau = 50 ms)."""
    y0 = natural_bump()
    vs = np.array([-0.2, -0.1, 0.1, 0.2])
    sp = []
    for v in vs:
        T = int(10.0 / km.DT)
        _, _, ys = _integrate(y0.copy(), np.zeros((NW, km.NI)), W_RA, A_GEN, C, np.zeros((km.NI, T)), np.full(T, v), np.zeros((NW, T)),
                              np.zeros(T), False, DT_INT, km.DT, TAU, 0.0, km.W_MAX, 1)
        ph = np.degrees(np.unwrap(np.angle(np.exp(1j * np.radians(ANG)) @ ys)))
        t = np.arange(ph.size) * km.DT
        m = t > 2.0
        sp.append(np.polyfit(t[m], ph[m], 1)[0])
    sp = np.array(sp)
    return float(sp @ vs / (vs @ vs)), dict(zip([float(x) for x in vs], [float(x) for x in sp]))


Y_PEAK = float(natural_bump().max())
EPS = km.EPS * KIM_RA["A_peak"] / Y_PEAK
INJ_PEAK = KIM_INJ_PER_WEDGE / KIM_RA["A_peak"] * Y_PEAK
G_SPEED, _ = speed_gain()


def omega_deg(cond):
    """Kim's sim_vel back to fly angular velocity (deg/s): sim_vel = omega / pi * vel_1."""
    return cond["vel"] / km.VEL_1 * 180.0


def injection(stripe_rad, imposed_deg):
    """Kim 2019 opto profile (von Mises kappa 10, flattened top) on the 16 wedges, centred at stripe + imposed."""
    out = np.zeros((NW, stripe_rad.size))
    th = np.radians(ANG)
    for i, s in enumerate(stripe_rad):
        p = np.exp(10.0 * np.cos(th - (s + np.radians(imposed_deg))))
        p[p > p.max() / 2] = p.max()
        p = (p - p.min()) / (p.max() - p.min())
        out[:, i] = INJ_PEAK * p
    return out


def simulate(cond, W, y0, learn=True, inj=None, dark=False):
    vis = np.zeros_like(cond["vis"]) if dark else np.ascontiguousarray(cond["vis"])
    v = omega_deg(cond) / G_SPEED
    fv = km.learning_rate_profile(cond["vel"])
    inj = np.zeros((NW, v.size)) if inj is None else np.ascontiguousarray(inj)
    return _integrate(np.array(y0, float), np.array(W, float), W_RA, A_GEN, C, vis, v.astype(float), inj, fv, learn,
                      DT_INT, km.DT, TAU, EPS, km.W_MAX, 1)


def offset_stats(ys, stripe_rad):
    ph = np.angle(np.exp(1j * np.radians(ANG)) @ ys)
    d = np.angle(np.exp(1j * (ph - stripe_rad[: ph.size])))
    z = np.mean(np.exp(1j * d))
    return float(np.degrees(np.angle(z))), float(np.abs(z)), np.degrees(d)


def heading_tracking(ys, cond):
    """Darkness: bump position vs integrated fly heading (unwrapped); returns drift of their difference."""
    ph = np.degrees(np.unwrap(np.angle(np.exp(1j * np.radians(ANG)) @ ys)))
    hd = np.cumsum(omega_deg(cond)) * km.DT
    hd = hd[: ph.size] - hd[0] + ph[0]
    return ph - hd
