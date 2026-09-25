"""Python port of the Kim et al. 2019 (Nature 576:126) compass model (ModelDB 261585, MATLAB): Kim 2017 local ring
attractor of 32 compass (E-PG) wedges, 32 inhibitory visual ring neurons, angular-velocity turning term, and the
ring -> compass plasticity rule 'SOM inhib, Post-synaptically gated, input profile':

  tau dy/dt = -y + clip( W_ra y + 1 - W_in (r 2pi/ni) + vel (y_{i-1} - y_{i+1})/2 + inj 2pi/nw , 0, 1000 )
  dW_in/dt  = clip( W_in + 3 f_v eps y (W_max - r - W_in), 0, W_max ) - W_in          (f_v: normalised vel^2)

Parameters and stimulus construction follow main_config.m, param_*.m and sim_cond.m of the ModelDB code. The
MATLAB ode45 integration is replaced by forward Euler (dt = 2 ms = tau/25) with the authors' linear interpolation of
inputs between 10 ms samples.
"""
from __future__ import annotations

from pathlib import Path

import numba
import numpy as np
import scipy.io as sio

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data/external/kim_2019_modeldb_261585/261585-85711ed886eaa6ae377e555b74b9e6322ad6684c"

# main_config.m
DT = 0.01
NW, NI = 32, 32
TAU = 0.05
D_CONT, BETA_CONT = 0.2, 10.0
BUMP_WIDTH = np.pi / 2 * 1.2
VEL_1 = 0.1775
EPS, W_MAX = 0.5, 0.33
MAMP = 0.35
KAPPA_NARROW = 15.0
DT_INT = 0.002


def ring_params():
    """param_Ring_Attractor_check.m: discrete local model and its analytic bump (Kim 2017 suppl. eqs 13-21)."""
    m = NW / 2 / np.pi * BUMP_WIDTH
    c2d = 2 * np.pi / NW
    D = D_CONT / c2d ** 2
    alpha = (np.sin(np.pi / (m - 0.5 + 2)) * 2) ** 2 * D + 1
    beta = BETA_CONT * c2d
    omega = np.arcsin(np.sqrt((alpha - 1) / D) / 2) * 2
    M = int(np.ceil(2 * np.pi / omega - 2))
    phi = np.arctan(np.sin((M + 1) * omega) / (np.cos((M + 1) * omega) - 1))
    tmp = (1 - alpha) * np.sin(phi) + beta * (np.sin(omega) * np.cos(phi) / (1 - np.cos(omega)) + (M + 1) * np.sin(phi))
    A = 1 / tmp
    S = A * (np.sin(omega) * np.cos(phi) / (1 - np.cos(omega)) + (M + 1) * np.sin(phi))
    W = -beta * np.ones((NW, NW))
    for i in range(NW):
        W[i, i] = alpha - 2 * D - beta
        W[i, [(i - 1) % NW, (i + 1) % NW]] = D - beta
    Adm = max(A * (np.sin(omega * n - phi) + np.sin(phi)) for n in range(NW + 1))
    return {"alpha": alpha, "D": D, "beta": beta, "omega": omega, "M": M, "phi": phi, "A": A, "S": S, "A_peak": Adm, "W": W}


def von_mises(mu, kappa, n=NI):
    th = np.arange(n) * 2 * np.pi / n
    return np.exp(kappa * np.cos(th - mu))          # un-normalised pdf; min-max normalised below as in sim_cond.m


def moving_avg(a, span):
    """my_moving_avg.m (odd and even spans, truncated windows at the edges)."""
    a = np.asarray(a, float)
    n = a.size
    ns = span // 2
    out = np.empty(n)
    cs = np.r_[0.0, np.cumsum(a)]
    if span % 2 == 1:
        for i in range(n):
            lo, hi = max(0, i - ns), min(n, i + ns + 1)
            out[i] = (cs[hi] - cs[lo]) / (hi - lo)
    else:
        for i in range(n):
            lo, hi = max(0, i - ns), min(n, i + ns + 1)
            b = a[lo:hi].copy()
            if b.size == span + 1:
                b[0] = (b[0] + b[-1]) / 2
                b = b[:-1]
            out[i] = b.mean()
    return out


def turning_data():
    """sim_cond.m: fly heading from pos_data.mat (88 LED columns), 10 ms samples."""
    pd_ = sio.loadmat(SRC / "pos_data.mat", squeeze_me=True, struct_as_record=False)["pos_data"]
    t_data, xp = np.asarray(pd_.time, float), np.asarray(pd_.xpos, float)
    ddt = np.median(np.diff(t_data[:100]))
    stride = int(round(DT / ddt))
    xpos = xp[::stride]
    xrad = np.mod(xpos / 88 * 2 * np.pi - np.pi - (2 * np.pi / 88 / 2), 2 * np.pi) - np.pi
    v = np.diff(xrad)
    v = np.r_[v[0], v]
    v = np.mod(v + np.pi, 2 * np.pi) - np.pi
    v = moving_avg(v / DT, 100)
    vel = v / np.pi * VEL_1
    mcshift = np.ceil(np.mod(xrad, 2 * np.pi) / (2 * np.pi) * NI).astype(int)
    return xrad, vel, mcshift


def add_noise(vis, vel, rng, opto=False):
    """sim_cond.m noise block: uniform noise on ring neurons (then 5-sample moving average) and on velocity."""
    v = vis.max() * 0.5 if vis.max() > 0 else 0.1
    vis = vis + v * (rng.random(vis.shape) - 0.5)
    vis = np.vstack([moving_avg(row, 5) for row in vis])
    vv = np.max(vel) * 0.2
    if vv == 0:
        vv = VEL_1 / 4
    vel = moving_avg(vel + vv * (rng.random(vel.shape) - 0.5), 5)
    return vis, vel


def condition(kind, rng, span=360, imposed_shift=0, t_opto=100.0):
    """Returns dict(t, vel, vis (NI x T), inj (NW x T), stripe_pos (rad, per sample) or None)."""
    if kind in ("one_stripe", "two_stripes"):
        xrad, vel, mcshift = turning_data()
        a = von_mises(np.pi, KAPPA_NARROW)
        a = (a - a.min()) / (a.max() - a.min()) * MAMP
        vis = np.stack([np.roll(a, s) for s in mcshift], axis=1)
        if kind == "two_stripes":
            vis = vis + np.roll(vis, NI // 2, axis=0)
            vis = (vis - vis.min()) / (vis.max() - vis.min()) * MAMP
        inj = np.zeros((NW, vis.shape[1]))
        stripe = np.mod(np.pi + mcshift * 2 * np.pi / NI, 2 * np.pi)
    elif kind == "opto":
        a = von_mises(np.pi, KAPPA_NARROW)
        a = (a - a.min()) / (a.max() - a.min()) * MAMP
        npts = int(round(1.5 / DT))
        if span == 360:
            step, nstep, start_v, start_w = NI // 8, 8, 0, 0
        elif span == 180:
            step, nstep, start_v, start_w = NI // 16, 8, 20, 0
        else:
            raise ValueError(span)
        seq_v = np.concatenate([np.full(npts, start_v + k * step) for k in range(nstep)])
        seq_w = np.concatenate([np.full(npts, start_w + k * step) for k in range(nstep)])
        if span == 360:
            seq_v = np.r_[seq_v, seq_v, seq_v[::-1], seq_v[::-1]]
            seq_w = np.r_[seq_w, seq_w, seq_w[::-1], seq_w[::-1]]
        else:
            seq_v = np.r_[seq_v, seq_v[::-1]]
            seq_w = np.r_[seq_w, seq_w[::-1]]
        reps = int(np.ceil(t_opto / DT / seq_v.size))
        mcshift = np.tile(seq_v, reps)
        wwshift = np.tile(seq_w, reps) + imposed_shift
        vis = np.stack([np.roll(a, s) for s in mcshift], axis=1)
        ww = von_mises(np.pi, 10.0, NW)
        ww[ww > ww.max() / 2] = ww.max()
        ww = (ww - ww.min()) / (ww.max() - ww.min()) * MAMP * 2
        inj = np.stack([np.roll(ww, s) for s in wwshift], axis=1)
        vel = np.zeros(mcshift.size)
        stripe = np.mod(np.pi + mcshift * 2 * np.pi / NI, 2 * np.pi)
    else:
        raise ValueError(kind)
    vis = vis - vis.min()
    if vis.max() > 0:
        vis = vis / vis.max() * MAMP
    vis, vel = add_noise(vis, vel, rng)
    return {"t": np.arange(vel.size) * DT, "vel": vel, "vis": vis, "inj": inj, "stripe": stripe}


@numba.njit(cache=True)
def _integrate(y, W, Wra, vis, vel, inj, fv, learn, dt_int, dt, tau, eps, wmax, sample_every):
    nw, ni = W.shape
    T = vel.size
    sub = int(round(dt / dt_int))
    n_out = (T - 1) // sample_every + 1
    ys = np.zeros((nw, n_out))
    k = 0
    for i in range(T - 1):
        if i % sample_every == 0:
            ys[:, k] = y
            k += 1
        for s in range(sub):
            f = s / sub
            r = (1 - f) * vis[:, i] + f * vis[:, i + 1]
            v = ((1 - f) * vel[i] + f * vel[i + 1]) * nw / 2 / np.pi
            jj = (1 - f) * inj[:, i] + f * inj[:, i + 1]
            fvv = (1 - f) * fv[i] + f * fv[i + 1]
            tmp = np.empty(nw)
            for a in range(nw):
                acc = 0.0
                for b in range(nw):
                    acc += Wra[a, b] * y[b]
                vis_cur = 0.0
                for b in range(ni):
                    vis_cur += W[a, b] * r[b] * 2 * np.pi / ni
                turn = v * (y[(a - 1) % nw] - y[(a + 1) % nw]) / 2
                x = acc + 1.0 - vis_cur + turn + jj[a] * 2 * np.pi / nw
                if x > 1000.0:
                    x = 1000.0
                if x < 0.0:
                    x = 0.0
                tmp[a] = x
            if learn:
                for a in range(nw):
                    for b in range(ni):
                        w_new = W[a, b] + 3 * fvv * eps * y[a] * (wmax - r[b] - W[a, b])
                        if w_new < 0.0:
                            w_new = 0.0
                        if w_new > wmax:
                            w_new = wmax
                        W[a, b] += dt_int * (w_new - W[a, b])
            for a in range(nw):
                y[a] += dt_int * (tmp[a] - y[a]) / tau
    return y, W, ys


def learning_rate_profile(vel):
    tmp = vel ** 2
    return tmp / (tmp.mean() + 1.5 * tmp.std())


def simulate(cond, W, y0, learn=True, sample_every=1):
    ra = ring_params()
    fv = learning_rate_profile(cond["vel"])
    y, W, ys = _integrate(np.array(y0, float), np.array(W, float), ra["W"], np.ascontiguousarray(cond["vis"]), cond["vel"].astype(float),
                          np.ascontiguousarray(cond["inj"]), fv, learn, DT_INT, DT, TAU, EPS, W_MAX, sample_every)
    return y, W, ys


def pva(ys):
    th = np.arange(NW) * 2 * np.pi / NW
    z = np.exp(1j * th) @ ys
    return np.angle(z), np.abs(z) / np.maximum(ys.sum(0), 1e-12)


def offset_stats(ys, stripe, sample_every=1):
    """Bump position minus stripe position; circular mean (deg) and resultant length."""
    ph, strength = pva(ys)
    s = stripe[::sample_every][: ph.size]
    d = np.angle(np.exp(1j * (ph - s)))
    z = np.mean(np.exp(1j * d))
    return float(np.degrees(np.angle(z))), float(np.abs(z)), np.degrees(d)
