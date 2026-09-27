"""CE-BRAIN 공통 식.

고정 뉴런 i의 상태 x_i와 방향 있는 관계 W[받는, 보내는]로 쓴다.

    ẋ = −L_g x + Σ_k u_k S_k x,    L_g = I − g·W_s
    τ_h ḣ = −h + x                (현재 상태에 남는 과거의 흔적)

W_s = (W + Wᵀ)/2는 계량이다. 유지 비용 xᵀ L_g x가 작은 방향이 기억으로 남는다.
W_a = (W − Wᵀ)/2와 입력 u_k로 조절되는 S_k는 방향, 곧 상태를 옮기는 흐름이다.
"""

from __future__ import annotations

import numpy as np


def normalize(w, sign):
    """Signed input fractions: presynaptic column j times sign_j, each row over its total input."""
    signed = w * sign[None, :]
    total = np.abs(signed).sum(1, keepdims=True)
    return np.divide(signed, total, out=np.zeros_like(signed), where=total > 0)


def split(w):
    """Metric (symmetric) and direction (antisymmetric) parts of a relation matrix."""
    return (w + w.T) / 2, (w - w.T) / 2


def metric(ws, gain):
    """L_g = I − g·W_s; it must be positive definite (g·λ_max(W_s) < 1)."""
    l = np.eye(len(ws)) - gain * ws
    if np.linalg.eigvalsh(l)[0] <= 0:
        raise ValueError("L_g is not positive definite; lower the gain")
    return l


def uniformity(vector, groups):
    """Share of a vector's energy in its per-group means (1 = constant within every group)."""
    groups = np.asarray(groups)
    return sum(np.sum(groups == g) * vector[groups == g].mean() ** 2
               for g in np.unique(groups)) / np.sum(vector ** 2)


def plane(ws, groups, limit=0.5):
    """Least-cost pair of L_g: the two leading eigenvectors of W_s that are not group-uniform."""
    values, vectors = np.linalg.eigh(ws)
    order = [i for i in np.argsort(values)[::-1] if uniformity(vectors[:, i], groups) < limit]
    pair = order[:2]
    return values[pair], vectors[:, pair]


def circle(points):
    """Angle (deg) of 2-D points around the origin and the variation of their radius."""
    radius = np.hypot(points[:, 0], points[:, 1])
    return np.degrees(np.arctan2(points[:, 1], points[:, 0])), radius.std() / radius.mean()


def angle_slope(theta, k):
    """Circular-linear fit θ ≈ s·k + c in degrees: best slope s and resultant length R."""
    slopes = np.arange(-180, 180, 0.25)
    z = np.exp(1j * np.radians(theta[None, :] - slopes[:, None] * k[None, :])).mean(1)
    best = np.argmax(np.abs(z))
    return slopes[best], np.abs(z[best])


def conformal(m):
    """A 2×2 map as scale·rotation: angle ψ (deg), scale, and the conformal share of its energy."""
    a, b = (m[0, 0] + m[1, 1]) / 2, (m[1, 0] - m[0, 1]) / 2
    return np.degrees(np.arctan2(b, a)), np.hypot(a, b), 2 * (a * a + b * b) / np.sum(m * m)
