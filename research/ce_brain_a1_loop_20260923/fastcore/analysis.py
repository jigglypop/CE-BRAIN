"""Fast analysis path for simulated sessions: the same spike trains and the same structure measures as the sealed
step 56 / 58 code, without the compressed-file round trip and without the 1000 permutation nulls that models do not
need (checked by check_equivalence.py).

  spikes_and_save(rates, sched, rng, gain, path)   same arrays as step 58 spikes_and_save (same draws), uncompressed
  structure(path)                                   ring coherence C and ring index per state as in step 56 analyse
Sealed readers (step 57 holding_gap.analyse, step 62 upstream_pull.measures, ...) read the uncompressed file as is.
"""
from __future__ import annotations

import numpy as np

import models as fm
import ring_kernels as rk

se = fm.se
s56 = se.s56


SP_CH = 1 << 16                                                     # uniforms per draw (512 kB, stays in cache)


def spikes_and_save(rates, sched, rng, gain, path):
    c, head, states = sched
    n = rates.shape[0]
    t = np.arange(n) * se.DT
    unit = np.repeat(np.arange(16), se.CELLS_PER_UNIT)
    ty = ((gain * rates[:1, 0] + se.BASE_HZ) * se.DT).dtype.type        # numpy's intensity dtype (float32 for a Python gain)
    g, b, dt = ty(gain), ty(se.BASE_HZ), ty(se.DT)
    cols = rates.T if rates.flags.f_contiguous else np.ascontiguousarray(rates.T)   # cols[u] = rates[:, u], contiguous
    ub, buf = np.empty(SP_CH), np.empty(n)
    trains = []
    for u in unit:                                                  # each cell draws its n uniforms in order, in pieces
        k = 0
        for i0 in range(0, n, SP_CH):
            m = min(SP_CH, n - i0)
            rng.random(out=ub[:m])
            k += rk.thin_spikes(ub[:m], cols[u, i0:i0 + m], g, b, dt, t[i0:i0 + m], buf[k:])
        trains.append(buf[:k].copy())
    for _ in range(se.N_OTHER):
        parts = []
        for i0 in range(0, n, SP_CH):
            m = min(SP_CH, n - i0)
            parts.append(t[i0:i0 + m][rng.random(out=ub[:m]) < se.OTHER_HZ * se.DT])
        trains.append(np.concatenate(parts))
    idx = np.cumsum([s.size for s in trains])
    ex = ~np.isnan(head)
    ht = t[ex][::10]
    hd = np.degrees(np.mod(head[ex][::10], 2 * np.pi))
    np.savez(path, spike_times=np.concatenate(trains), spike_times_index=idx,
             unit_id=np.arange(len(trains)), is_head_direction=np.r_[np.ones(unit.size, bool), np.zeros(se.N_OTHER, bool)],
             is_excitatory=np.r_[np.ones(unit.size, bool), np.zeros(se.N_OTHER, bool)],
             is_fast_spiking=np.r_[np.zeros(unit.size, bool), np.ones(se.N_OTHER, bool)],
             ss_start=np.array([s[1] for s in states]), ss_stop=np.array([s[2] for s in states]),
             ss_state=np.array([s[0] for s in states]),
             ep_start=np.array([0.0, se.EXPLORE_S]), ep_stop=np.array([se.EXPLORE_S, se.EXPLORE_S + se.HOME_S]),
             ep_tag=np.array(["wake_square", "home_cage"]), hd_t=ht, hd=hd)


def structure(path):
    """Step 56 ring coherence C and ring index for nrem / rem / wake_home (same bins, cells and state rules)."""
    S = s56.load(path)
    hd_idx = np.flatnonzero(S["hd_flag"])
    th, tracked = s56.preferred(S, [S["spikes"][i] for i in hd_idx])
    T = max(float(np.max(np.concatenate([s for s in S["spikes"] if s.size]))), float(S["ss"][1].max()))
    edges = np.arange(0, T + s56.BIN, s56.BIN)
    centres = (edges[:-1] + edges[1:]) / 2
    N = np.array([np.histogram(S["spikes"][i], edges)[0] for i in hd_idx], dtype=float)
    state, home, opto = s56.labels(centres, S)
    out = {}
    for k in ("nrem", "rem", "wake_home"):
        m = (state == ("wake" if k == "wake_home" else k)) & home
        if (k == "rem" and m.sum() * s56.BIN < s56.MIN_REM) or m.sum() * s56.BIN < 30:
            continue
        out[k] = {"C": s56.coherence(N[:, m], th), "ring_index": s56.ring_index(N[:, m], th)[0]}
    if "nrem" in out and "wake_home" in out and out["wake_home"]["ring_index"]:
        out["ring_ratio"] = out["nrem"]["ring_index"] / out["wake_home"]["ring_index"]
    return out
