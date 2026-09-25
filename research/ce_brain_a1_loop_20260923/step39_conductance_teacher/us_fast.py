"""Compiled (numba) version of the training loop of us_network: the authors' fly_rec.network equations in the same
order, arbitrary HD/HR sizes and HD angles, teacher 'current' (authors' vis_in + exc) or 'conductance'
(Urbanczik & Senn 2014: g0 (U* - u)), soma step 'euler' (authors) or 'exp' (exact step of the linear somatic ODE).
Checked against the numpy version (us_network) before use.
"""
from __future__ import annotations

import numba
import numpy as np


@numba.njit(cache=True)
def _logistic(x, x0, beta, fmax):
    return fmax / (1.0 + np.exp(-beta * (x - x0)))


@numba.njit(cache=True)
def train_kernel(w, w_rot, sign, ang_rad, theta0_deg, kind, M, sigma, g0, EE, EI, soma_exp, train,
                 dt_s, tau_s, tau_d, tau_l, gD, gL, inh, inh_rot, x0, beta, fmax, eta, exc, k_vest,
                 f, f_rot, u, Iden, V, Delta, PSP, I_PSP, x, n_snap):
    n = f.size
    m = f_rot.size
    nm = n + m
    dt = dt_s * 1e3
    steps = theta0_deg.size - 1
    block = max(steps // n_snap, 1)
    snaps = np.zeros((n_snap, n, nm))
    err_hist = np.zeros(n_snap)
    f_all = np.empty(nm)
    x_rot = np.empty(n)
    f_new = np.empty(n)
    f_new_rot = np.empty(m)
    err = np.empty(n)
    r0 = -exc - 1.0
    gt = g0 if kind == 1 else 0.0
    a = gL + gD + gt
    decay = np.exp(-a * dt)
    h = (n + 1) // 2
    acc = 0.0
    cnt = 0
    k = 0
    for i in range(steps):
        v_ang = -(theta0_deg[i + 1] - theta0_deg[i]) / dt_s
        th0 = theta0_deg[i] * np.pi / 180.0
        for j in range(m):
            f_all[j] = f_rot[j]
        for j in range(n):
            f_all[m + j] = f[j]
        for p in range(n):
            s = 0.0
            for q in range(nm):
                s += w[p, q] * f_all[q]
            Iden[p] += (-Iden[p] + s + inh) * dt / tau_s
        for p in range(n):
            V[p] += (-V[p] + Iden[p]) * dt / tau_l
        for q in range(nm):
            I_PSP[q] += (-I_PSP[q] + f_all[q]) * dt / tau_s
            PSP[q] += (-PSP[q] + I_PSP[q]) * dt / tau_l
        for p in range(n):
            x[p] += (f[p] - x[p]) / tau_s
        for p in range(h):
            x_rot[p] = x[2 * p]
        for p in range(n // 2):
            x_rot[h + p] = x[2 * p + 1]
        for j in range(m):
            s = 0.0
            for p in range(n):
                s += w_rot[j, p] * x_rot[p]
            f_new_rot[j] = _logistic(s + sign[j] * k_vest * v_ang + inh_rot, x0, beta, fmax)
        for p in range(n):
            g = np.exp(-np.sin((ang_rad[p] + th0) / 2.0) ** 2 / (2.0 * sigma * sigma))
            if kind == 0:
                r = M * g + r0
                e = exc
                us_ = 0.0
            else:
                r = 0.0
                e = 0.0
                us_ = EI + (EE - EI) * g
            if soma_exp:
                u_inf = (gD * V[p] + r + e + gt * us_) / a
                u[p] = u_inf + (u[p] - u_inf) * decay
            else:
                u[p] += (-gL * u[p] + gD * (V[p] - u[p]) + r + e + gt * (us_ - u[p])) * dt
            f_new[p] = _logistic(u[p], x0, beta, fmax)
            err[p] = f_new[p] - _logistic(V[p] * gD / (gD + gL), x0, beta, fmax)
        if train:
            for p in range(n):
                for q in range(nm):
                    Delta[p, q] += (err[p] * PSP[q] - Delta[p, q]) * dt / tau_d
                    w[p, q] += eta * Delta[p, q] * dt
        s = 0.0
        for p in range(n):
            s += abs(err[p])
        acc += s / n
        cnt += 1
        for p in range(n):
            f[p] = f_new[p]
        for j in range(m):
            f_rot[j] = f_new_rot[j]
        if (i + 1) % block == 0 and k < n_snap:
            snaps[k] = w
            err_hist[k] = 1e3 * acc / cnt
            acc = 0.0
            cnt = 0
            k += 1
    return w, snaps, err_hist


def train_fast(w0, theta0, teacher, P, ang_deg, w_rot_code, sign, soma="euler", n_snap=100, state=None, train=True):
    """Same interface idea as us_network.train; w_rot_code is applied to x[::2] ++ x[1::2] as in the authors' code."""
    n, m = w0.shape[0], w_rot_code.shape[0]
    st = state if state is not None else {"f": np.zeros(n), "f_rot": np.zeros(m), "u": np.zeros(n), "Iden": np.zeros(n), "V": np.zeros(n),
                                           "Delta": np.zeros((n, n + m)), "PSP": np.zeros(n + m), "I_PSP": np.zeros(n + m), "x": np.zeros(n)}
    kind = 0 if teacher.kind == "current" else 1
    w, snaps, err = train_kernel(np.array(w0, float), np.ascontiguousarray(w_rot_code, float), np.asarray(sign, float),
                                 np.radians(np.asarray(ang_deg, float)), np.asarray(theta0, float), kind, float(teacher.M),
                                 float(teacher.sigma), float(teacher.g0), float(teacher.EE), float(teacher.EI), soma == "exp", train,
                                 float(P["dt"]), float(P["tau_s"]), float(P["tau_d"]), 10.0, float(P["gD"]), float(P["gL"]),
                                 float(P["inh"]), float(P["inh_rot"]), float(P["x0"]), float(P["beta"]), float(P["fmax"]),
                                 float(P["eta"]), float(P["exc"]), float(P["v0"] / P["v_max"]),
                                 st["f"], st["f_rot"], st["u"], st["Iden"], st["V"], st["Delta"], st["PSP"], st["I_PSP"], st["x"], n_snap)
    return w, snaps, err
