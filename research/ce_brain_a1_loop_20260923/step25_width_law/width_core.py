"""Width law core (step 25): nonlinear eigenvector of a rotation-invariant threshold-linear ring.

law_profile(J): fixed point of r <- [sum_m J_m P_m r]_+ on a continuous ring (J_1 = 1), where P_m projects on
harmonic m. Homogeneous, so the bump shape depends only on the spectral ratios J_m = lambda_m / lambda_1.
"""
from __future__ import annotations

import numpy as np

GRID = np.linspace(-np.pi, np.pi, 720, endpoint=False)


def law_profile(J, iters=4000):
    r = np.maximum(np.cos(GRID), 0)
    for _ in range(iters):
        h = J.get(0, 0.0) * r.mean() * np.ones_like(r)
        for m, j in J.items():
            if m == 0:
                continue
            c = 2 * np.mean(r * np.cos(m * GRID))
            s = 2 * np.mean(r * np.sin(m * GRID))
            h = h + j * (c * np.cos(m * GRID) + s * np.sin(m * GRID))
        new = np.maximum(h, 0)
        norm = np.linalg.norm(new)
        if norm == 0:
            return None
        new /= norm
        if np.max(np.abs(new - r)) < 1e-12:
            r = new
            break
        r = new
    return r


def fwhm_profile(values, angles):
    """FWHM (deg) of a nonnegative profile sampled at angles (rad), circular linear interpolation, half of max."""
    order = np.argsort(np.mod(angles, 2 * np.pi))
    a = np.mod(angles, 2 * np.pi)[order]
    v = np.asarray(values, float)[order]
    grid = np.radians(np.arange(0, 360, 0.25))
    fine = np.interp(grid, np.r_[a - 2 * np.pi, a, a + 2 * np.pi], np.r_[v, v, v])
    if fine.max() <= 0:
        return None
    return float(np.sum(fine >= fine.max() / 2) * 0.25)


def law_width(J):
    r = law_profile(J)
    return None if r is None else fwhm_profile(r, GRID)
