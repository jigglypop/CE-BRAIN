"""Synthetic multi-population ring used for the pre-freeze check of step 26 (EPG, PEN L/R +-55 deg, Delta7, global inhibitor)."""
import numpy as np


def network():
    N = 16
    ang = np.arange(N) * 2 * np.pi / N
    K = lambda s=0.0, k=3.0: np.exp(k * np.cos(ang[:, None] - ang[None, :] - s))
    n = 4 * N + 1
    E, L, R, D, G = np.arange(N), np.arange(N, 2 * N), np.arange(2 * N, 3 * N), np.arange(3 * N, 4 * N), np.array([4 * N])
    w = np.zeros((n, n))
    w[np.ix_(E, E)] = K(0, 3)
    w[np.ix_(L, E)] = K(0, 4); w[np.ix_(R, E)] = K(0, 4)
    w[np.ix_(E, L)] = 0.5 * K(np.radians(55), 4); w[np.ix_(E, R)] = 0.5 * K(-np.radians(55), 4)
    w[np.ix_(D, E)] = K(0, 1); w[np.ix_(E, D)] = -0.3 * K(np.pi, 1)
    w[np.ix_(G, E)] = 1.0; w[np.ix_(E, G)] = -2.0 * K(0, 3).sum(1)[:, None]
    W = w / np.abs(w).sum(1, keepdims=True).clip(1e-12)
    gamma = np.zeros(n); gamma[L] = 1; gamma[R] = -1
    return W, E, ang, gamma
