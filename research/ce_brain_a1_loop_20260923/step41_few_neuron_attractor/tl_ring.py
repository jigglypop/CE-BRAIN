"""Threshold-linear ring on the fly lattice (N = 16 directions, 22.5 deg): Kim et al. 2017 (Science) local and global
models, Noorman et al. 2024 (Nat Neurosci) few-neuron continuous-attractor condition.

tau dr/dt = -r + [ W r + v A r + c + I_ext(t) ]_+          (tau = 1, Euler dt = 0.02)
  cosine (Kim 'global' / Noorman): W_jk = J_E cos(th_j - th_k) - J_I
  local  (Kim 'local', eq. 9):     W = (alpha - 2D) I + D (S + S^T) - beta 1 1^T
velocity: two fast linear side rings (PEN-like) with gains (1 + v) and (1 - v) that project back with W shifted by
+-1 lattice step: input = (W_+ + W_-)/2 r + v (W_+ - W_-)/2 r, i.e. the symmetric part is W, the generator A = (W_+ - W_-)/2.
"""
from __future__ import annotations

import numpy as np

N = 16
DTH = 360.0 / N
ANG = np.arange(N) * DTH
DT = 0.02


def wrapd(a):
    return (np.asarray(a) + 180.0) % 360.0 - 180.0


def cosine_ring(JE, JI):
    d = np.radians(ANG[:, None] - ANG[None, :])
    return JE * np.cos(d) - JI


def local_ring(alpha, D, beta):
    S = np.roll(np.eye(N), 1, axis=1)
    return (alpha - 2 * D) * np.eye(N) + D * (S + S.T) - beta * np.ones((N, N))


def generator(W):
    return (np.roll(W, 1, axis=1) - np.roll(W, -1, axis=1)) / 2


def com(r):
    return float(np.degrees(np.angle(np.sum(r * np.exp(1j * np.radians(ANG))))) % 360)


def shape(r):
    q = r - r.min()
    if q.max() <= 1e-9:
        return None, 0, 0.0, 0.0
    peaks = int(np.sum((q > np.roll(q, 1)) & (q >= np.roll(q, -1)) & (q > 0.5 * q.max())))
    grid = np.arange(0, 360, 0.25)
    fine = np.interp(grid, np.r_[ANG - 360, ANG, ANG + 360], np.r_[q, q, q])
    return float(np.sum(fine >= fine.max() / 2) * 0.25), peaks, float(q.max() / max(r.max(), 1e-12)), float(r.max())


def cue(c_deg, amp=1.0, kappa=4.0):
    """Visual-like cue (von Mises shape, peak amp)."""
    return amp * np.exp(kappa * (np.cos(np.radians(ANG - c_deg)) - 1))


def wedge(c_deg, amp):
    """22.5 deg optogenetic wedge: amp x overlap of each direction's 22.5 deg sector with the wedge."""
    d = wrapd(ANG - c_deg)
    return amp * np.clip(np.minimum(d + DTH / 2, DTH / 2) - np.maximum(d - DTH / 2, -DTH / 2), 0, None) / DTH


def run(W, c, phases, A=None, every=0, r0=None, cap=1e6):
    """phases: list of (duration in tau, I_ext vector or 0, velocity v). Returns final r and COM trace."""
    r = np.zeros(N) if r0 is None else r0.copy()
    trace = []
    for dur, I, v in phases:
        M = W if (A is None or v == 0) else W + v * A
        for s in range(int(round(dur / DT))):
            r = r + DT * (-r + np.maximum(M @ r + c + I, 0.0))
            if r.max() > cap:
                return r, np.array(trace), True
            if every and s % every == 0:
                trace.append(com(r))
    return r, np.array(trace), False


def drift_profile(W, c, positions=np.arange(0, 22.5, 2.8125), t_cue=20.0, t_free=100.0):
    """Bump created by a cue at each sub-lattice position, then free: final - start position (deg)."""
    out = []
    for p in positions:
        r, _, blow = run(W, c, [(t_cue, cue(p, 1.0), 0.0), (2.0, 0.0, 0.0)])
        start = com(r)
        r2, _, blow2 = run(W, c, [(t_free, 0.0, 0.0)], r0=r)
        w, peaks, contrast, amp = shape(r2)
        out.append({"pos": float(p), "start": start, "drift": float(wrapd(com(r2) - start)), "peaks": peaks, "amp": amp,
                    "n_active": int(np.sum(r2 > 1e-6)), "blow": bool(blow or blow2)})
    return out
