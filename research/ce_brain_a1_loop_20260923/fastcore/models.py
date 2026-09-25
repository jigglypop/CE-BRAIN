"""Session simulators for the A1 sleep models on the compiled kernels, with the SAME random-number call order as the
original Python loops (step 58 sleep_equation.schedule / simulate, step 61 stp_trace.simulate, step 62
upstream_pull.simulate, step 63 wandering_upstream.simulate), so a given seed gives the same session up to
floating-point rounding (checked by check_equivalence.py).

Use from a step script (import by name, so numba finds its disk cache from any folder and batch workers can import):
    sys.path.insert(0, str(LOOP / "fastcore")); import models as fm
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import ring_kernels as rk  # noqa: E402  (after the path insert)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


se = _load("sleep_equation", LOOP / "step58_sleep_equation/sleep_equation.py")
CH = 10000
ANG = se.ANG
K = se.DT / se.TAU


def schedule(rng):
    """Step 58 schedule with the same draws and the same arrays; the exploration heading walk runs compiled."""
    n_ex, n_home = int(se.EXPLORE_S / se.DT), int(se.HOME_S / se.DT)
    n = n_ex + n_home
    c = np.ones(n)
    head = np.full(n, np.nan)
    a = np.exp(-se.DT / 0.5)
    rk.ou_heading(rng.standard_normal(n_ex), a, np.radians(90.0) * np.sqrt(1 - a * a), se.DT, head[:n_ex])
    states, t, wake = [("wake", 0.0, se.EXPLORE_S)], se.EXPLORE_S, True
    while t < se.EXPLORE_S + se.HOME_S:
        d = min(rng.uniform(*se.BLOCK), se.EXPLORE_S + se.HOME_S - t)
        states.append(("wake" if wake else "nrem", t, t + d))
        if not wake:
            i, j = int(round(t / se.DT)), int(round((t + d) / se.DT))
            while i < j:
                u, dn = int(rng.uniform(*se.UP) / se.DT), int(rng.uniform(*se.DOWN) / se.DT)
                c[i:min(i + u, j)] = se.C_UP
                c[min(i + u, j):min(i + u + dn, j)] = np.nan               # marks down; value set per variant
                i += u + dn
        t += d
        wake = not wake
    return c, head, states


def _noise(rng, sigma, buf, m):
    """sigma * rng.standard_normal((m, 16)) in a reused buffer: the same draws and the same products."""
    z = rng.standard_normal(out=buf[:m])
    z *= sigma
    return z


def nrem_mask(sched):
    c, head, states = sched
    t = np.arange(c.size) * se.DT
    m = np.zeros(c.size, bool)
    for s, a0, b0 in states:
        if s == "nrem":
            m |= (t >= a0) & (t < b0)
    return m


def sim_base(sigma, c_down, rng, sched, W=None):
    """Step 58: ring + drive on/off; exploration cue at the head direction."""
    W = se.W if W is None else W
    c, head, states = sched
    c = np.where(np.isnan(c), c_down, c)
    n = c.size
    r = np.zeros(16)
    rates = np.empty((n, 16), dtype=np.float32, order="F")       # unit-major: rates[:, u] is contiguous for the spikes
    zb, eb = np.empty((CH, 16)), np.empty((CH, 16))                 # reused noise / input buffers
    for i0 in range(0, n, CH):
        m = min(CH, n - i0)
        noise = _noise(rng, sigma, zb, m)
        ext = rk.von_mises_input(ANG, head[i0:i0 + m], 1.0, eb[:m])
        r = rk.ring_chunk(W, r, c[i0:i0 + m], noise, ext, K, rates[i0:i0 + m])
    return rates


def sim_stp(sigma, rng, sched, gE, gain, E, R, U0=0.2, tau_d=0.2, tau_f=1.5, c_down=None):
    """Step 61: ring with Mongillo short-term plasticity on the neighbour excitation."""
    c, head, states = sched
    c = np.where(np.isnan(c), se.C_DOWN_PRIMARY if c_down is None else c_down, c)
    n = c.size
    r, u, x = np.zeros(16), np.full(16, U0), np.ones(16)
    rates = np.empty((n, 16), dtype=np.float32, order="F")       # unit-major: rates[:, u] is contiguous for the spikes
    zb, eb = np.empty((CH, 16)), np.empty((CH, 16))                 # reused noise / input buffers
    for i0 in range(0, n, CH):
        m = min(CH, n - i0)
        noise = _noise(rng, sigma, zb, m)
        ext = rk.von_mises_input(ANG, head[i0:i0 + m], 1.0, eb[:m])
        r, u, x = rk.ring_stp_chunk(E, R, gE, r, u, x, c[i0:i0 + m], noise, ext, K, se.DT, gain, U0, tau_d, tau_f,
                                    rates[i0:i0 + m])
    return rates


@njit(cache=True)
def _wander_chunk(theta, head, nrem, down, z, sd_w, sd_n, a_nrem, th_out, a_out):
    for j in range(z.size):
        if not np.isnan(head[j]):
            theta = head[j]
            a = 1.0
        elif nrem[j]:
            theta += sd_n * z[j]
            a = 0.0 if down[j] else a_nrem
        else:
            theta += sd_w * z[j]
            a = 1.0
        th_out[j] = theta
        a_out[j] = a
    return theta


def sim_wander(sigma, rng, sched, a_nrem, d_nrem, d_wake):
    """Step 63: NREM generator = random walk (D_NREM), relay gain a_nrem in up states, 0 in down states."""
    c, head, states = sched
    down = np.isnan(c)
    c = np.where(down, se.C_DOWN_PRIMARY, c)
    nrem = nrem_mask(sched)
    n = c.size
    r = np.zeros(16)
    rates = np.empty((n, 16), dtype=np.float32, order="F")       # unit-major: rates[:, u] is contiguous for the spikes
    zb, eb = np.empty((CH, 16)), np.empty((CH, 16))                 # reused noise / input buffers
    theta = 0.0
    sd_w, sd_n = np.sqrt(2 * d_wake * se.DT), np.sqrt(2 * d_nrem * se.DT)
    for i0 in range(0, n, CH):
        m = min(CH, n - i0)
        noise = _noise(rng, sigma, zb, m)
        z = rng.standard_normal(m)
        th, a = np.empty(m), np.empty(m)
        theta = _wander_chunk(theta, head[i0:i0 + m], nrem[i0:i0 + m], down[i0:i0 + m], z, sd_w, sd_n, a_nrem, th, a)
        ext = rk.von_mises_input(ANG, th, a, eb[:m])
        r = rk.ring_chunk(se.W, r, c[i0:i0 + m], noise, ext, K, rates[i0:i0 + m])
    return rates


@njit(cache=True)
def _pull_chunk(theta, eta, head, nrem, down, z1, z2, sd_w, s_rad, ea, a_nrem, psi_out, a_out):
    for j in range(z1.size):
        if not np.isnan(head[j]):
            theta = head[j]
        elif not nrem[j]:
            theta += sd_w * z1[j]
        if nrem[j]:
            eta = ea * eta + s_rad * np.sqrt(1 - ea * ea) * z2[j]
            a = 0.0 if down[j] else a_nrem
        else:
            eta = 0.0
            a = 1.0
        psi_out[j] = theta + eta
        a_out[j] = a
    return theta, eta


def sim_pull(sigma, rng, sched, a_nrem, s_nrem_deg, d_wake, tau_eta=0.1):
    """Step 62: held NREM generator, relayed heading jittered by an OU process (sd s_nrem), gain a_nrem."""
    c, head, states = sched
    down = np.isnan(c)
    c = np.where(down, se.C_DOWN_PRIMARY, c)
    nrem = nrem_mask(sched)
    n = c.size
    r = np.zeros(16)
    rates = np.empty((n, 16), dtype=np.float32, order="F")       # unit-major: rates[:, u] is contiguous for the spikes
    zb, eb = np.empty((CH, 16)), np.empty((CH, 16))                 # reused noise / input buffers
    theta, eta = 0.0, 0.0
    sd_w, s_rad, ea = np.sqrt(2 * d_wake * se.DT), np.radians(s_nrem_deg), np.exp(-se.DT / tau_eta)
    for i0 in range(0, n, CH):
        m = min(CH, n - i0)
        noise = _noise(rng, sigma, zb, m)
        z1, z2 = rng.standard_normal(m), rng.standard_normal(m)
        psi, a = np.empty(m), np.empty(m)
        theta, eta = _pull_chunk(theta, eta, head[i0:i0 + m], nrem[i0:i0 + m], down[i0:i0 + m], z1, z2, sd_w, s_rad, ea, a_nrem, psi, a)
        ext = rk.von_mises_input(ANG, psi, a, eb[:m])
        r = rk.ring_chunk(se.W, r, c[i0:i0 + m], noise, ext, K, rates[i0:i0 + m])
    return rates
