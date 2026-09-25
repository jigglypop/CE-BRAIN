"""Compiled (numba) integration kernels for the A1 compass-ring family used in steps 58-64.

The random numbers (ring noise, generator steps, spikes) are drawn in numpy in exactly the same call order as the
step 58/61/63 Python loops; only the deterministic loops are compiled. Dynamics (threshold-linear,
tau dr/dt = -r + [input]_+):
  ring_chunk        input = W r + c + noise + ext
  ring_stp_chunk    input = (gE E diag(u x / U0) + R) r + c + noise + ext, with Mongillo 2008 u, x dynamics
  ring_adapt_chunk  input = W r - g_a a + c + noise + ext,  tau_a da/dt = -a + r   (spike-frequency adaptation)
All kernels take and return the running state, so a session is integrated chunk by chunk.
The matrix-vector product runs column by column so the compiler vectorises over rows; every row still adds its terms
in the order j = 0..n-1 (no fused multiply-add), so each row sum is the same number as in a row-by-row loop.
"""
from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def _matvec_t(WT, r, out):
    """out = W r from WT = W transposed (C order); row i sums W[i, 0] r[0] + W[i, 1] r[1] + ... in that order."""
    n = r.size
    for i in range(n):
        out[i] = 0.0
    for j in range(n):
        rj = r[j]
        for i in range(n):
            out[i] += WT[j, i] * rj


@njit(cache=True)
def ring_chunk(W, r, c, noise, ext, k, rates_out):
    n = r.size
    WT = W.T.copy()
    tmp = np.empty(n)
    for t in range(c.size):
        _matvec_t(WT, r, tmp)
        for i in range(n):
            v = tmp[i] + c[t] + noise[t, i] + ext[t, i]
            if v < 0.0:
                v = 0.0
            r[i] = r[i] + k * (-r[i] + v)
            rates_out[t, i] = r[i]
    return r


@njit(cache=True)
def ring_stp_chunk(E, R, gE, r, u, x, c, noise, ext, k, dt, gain, U0, tau_d, tau_f, rates_out):
    n = r.size
    ET, RT = E.T.copy(), R.T.copy()
    tmp = np.empty(n)
    for t in range(c.size):
        for j in range(n):
            Rj = gain * r[j]
            u[j] = u[j] + dt * ((U0 - u[j]) / tau_f + U0 * (1.0 - u[j]) * Rj)
            x[j] = x[j] + dt * ((1.0 - x[j]) / tau_d - u[j] * x[j] * Rj)
            if x[j] < 0.0:
                x[j] = 0.0
            elif x[j] > 1.0:
                x[j] = 1.0
        for i in range(n):
            tmp[i] = 0.0
        for j in range(n):                                          # Weff[i, j] = gE E[i, j] (u_j x_j / U0) + R[i, j]
            f = u[j] * x[j] / U0
            rj = r[j]
            for i in range(n):
                tmp[i] += (gE * ET[j, i] * f + RT[j, i]) * rj
        for i in range(n):
            v = tmp[i] + c[t] + noise[t, i] + ext[t, i]
            if v < 0.0:
                v = 0.0
            r[i] = r[i] + k * (-r[i] + v)
            rates_out[t, i] = r[i]
    return r, u, x


@njit(cache=True)
def ring_adapt_chunk(W, r, a, c, noise, ext, k, dt, tau_a, g_a, rates_out):
    n = r.size
    WT = W.T.copy()
    tmp = np.empty(n)
    for t in range(c.size):
        _matvec_t(WT, r, tmp)
        for i in range(n):
            v = tmp[i] - g_a * a[i] + c[t] + noise[t, i] + ext[t, i]
            if v < 0.0:
                v = 0.0
            r[i] = r[i] + k * (-r[i] + v)
            a[i] = a[i] + dt * (-a[i] + r[i]) / tau_a
            rates_out[t, i] = r[i]
    return r, a


def von_mises_input(ang, centre, amp, out=None):
    """(m, 16) input amp_t * exp(4 (cos(ang - centre_t) - 1)); rows with nan centre or zero amp are 0.
    Same numpy operations in the same order as the step 58 expression (so the same numbers), evaluated in place in
    `out` (a reusable buffer) when most rows are on, and only on the rows that are on otherwise."""
    centre = np.asarray(centre, float)
    amp = np.broadcast_to(np.asarray(amp, float), centre.shape)
    out = np.empty((centre.size, ang.size)) if out is None else out
    on = ~np.isnan(centre) & (amp != 0.0)
    if 2 * np.count_nonzero(on) > on.size:
        np.subtract(ang[None, :], np.nan_to_num(centre)[:, None], out=out)
        np.cos(out, out=out)
        out -= 1.0
        out *= 4.0
        np.exp(out, out=out)
        out *= amp[:, None]
        out[~on] = 0.0
    else:
        out[:] = 0.0
        if on.any():
            out[on] = np.exp(4.0 * (np.cos(ang[None, :] - centre[on][:, None]) - 1.0)) * amp[on][:, None]
    return out


@njit(cache=True)
def ou_heading(z, a, s, dt, head):
    """Step 58 exploration heading: om <- a om + s z_i, th <- th + om dt (same operation order as the Python loop)."""
    om, th = 0.0, 0.0
    for i in range(z.size):
        om = a * om + s * z[i]
        th += om * dt
        head[i] = th


@njit(cache=True)
def thin_spikes(u01, rate, g, b, dt, t_axis, out):
    """Spike times t_i with u_i < (g rate_i + b) dt; g, b, dt are passed in the dtype numpy would use for
    (gain * rates + BASE) * DT, so the intensities are the same numbers. Returns the spike count written to out."""
    m = 0
    for i in range(u01.size):
        if u01[i] < (g * rate[i] + b) * dt:
            out[m] = t_axis[i]
            m += 1
    return m
