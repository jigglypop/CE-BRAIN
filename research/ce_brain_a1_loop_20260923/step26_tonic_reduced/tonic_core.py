"""Tonic-drive reduced ring (step 26): inhibitory/other populations linear around a tonic operating point are
eliminated; only EPG is thresholded:  tau x_E' = -x_E + [K(g, u) x_E + I0]_+ ,
K(g, u) = g W_EE(u) + g W_Er(u) (I - g W_rr(u))^{-1} g W_rE(u),  W(u) = W + u * Gamma * W (Gamma: +1 left PEN rows, -1 right).
"""
from __future__ import annotations

import numpy as np

DT, T_SETTLE, T_MEASURE = 0.05, 150.0, 150.0


def reduced_kernel(W, epg, g, gamma=None, u=0.0):
    Wu = W if (gamma is None or u == 0) else W + u * gamma[:, None] * W
    n = W.shape[0]
    rest = np.setdiff1d(np.arange(n), epg)
    Wee, Wer, Wre, Wrr = Wu[np.ix_(epg, epg)], Wu[np.ix_(epg, rest)], Wu[np.ix_(rest, epg)], Wu[np.ix_(rest, rest)]
    M = np.eye(len(rest)) - g * Wrr
    if np.max(np.real(np.linalg.eigvals(g * Wrr))) >= 1:
        return None
    return g * Wee + g * Wer @ np.linalg.solve(M, g * Wre)


def simulate(K, ang, I0, cue_deg=0.0, t_settle=T_SETTLE, t_measure=T_MEASURE):
    x = np.maximum(np.cos(ang - np.radians(cue_deg)), 0) * 2.0
    steps_s, steps_m = int(t_settle / DT), int(t_measure / DT)
    phases, amps = [], []
    for s in range(steps_s + steps_m):
        x = x + DT * (-x + np.maximum(K @ x + I0, 0))
        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 1e8:
            return None
        if s >= steps_s and (s - steps_s) % 20 == 0:
            z = np.sum(x * np.exp(1j * ang))
            phases.append(np.angle(z))
            amps.append(abs(z) / max(np.sum(x), 1e-300))
    ph = np.unwrap(phases)
    t = np.arange(len(ph)) * 20 * DT
    vel = float(np.polyfit(t, ph, 1)[0]) if len(ph) > 2 else 0.0
    return {"x": x, "velocity_rad_per_tau": vel, "R_bump": float(np.mean(amps)) if amps else 0.0,
            "active_fraction": float(np.mean(x > 1e-6 * max(x.max(), 1e-300))), "max": float(x.max())}


def profile_fwhm(x, ang, fwhm_fn):
    bins = np.mod(np.round(ang / np.radians(22.5)).astype(int), 16)
    prof = np.array([x[bins == b].mean() if np.any(bins == b) else np.nan for b in range(16)])
    ok = ~np.isnan(prof)
    p = prof[ok]
    if p.max() <= 0:
        return None, 0
    peaks = int(np.sum((p > np.roll(p, 1)) & (p >= np.roll(p, -1)) & (p > 0.5 * p.max())))
    return fwhm_fn(p, np.radians(22.5) * np.arange(16)[ok]), peaks
