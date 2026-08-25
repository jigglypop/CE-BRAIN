"""Deterministic L0 checks for the mathematical lane only."""
from __future__ import annotations

import json
import numpy as np


def projector(center: float, u: np.ndarray, radius: float, n: int = 4096) -> np.ndarray:
    total = np.zeros_like(u, dtype=complex)
    for k in range(n):
        theta = 2.0 * np.pi * (k + 0.5) / n
        z = center + radius * np.exp(1j * theta)
        dz = 1j * radius * np.exp(1j * theta) * (2.0 * np.pi / n)
        total += np.linalg.inv(z * np.eye(u.shape[0]) - u) * dz
    return total / (2j * np.pi)


def main() -> None:
    a0 = np.diag([1.0, 1.5, 2.0])
    d = np.array([[1.0, -1.0, 0.0], [0.0, 1.0, -1.0]])
    k = np.diag([0.7, 0.2])
    a_on = a0 + d.T @ k @ d
    delta = a_on - a0
    u = np.array([0.3, -0.2, 0.4])
    eps = float(np.linalg.norm(delta, 2))
    local_difference = float(u @ delta @ u)
    m = float(np.linalg.eigvalsh(a0).min())
    singular = np.array([[1.0, -1.0], [-1.0, 1.0]])

    u0 = np.diag([0.95, 0.80, 0.20, 0.10])
    e = np.zeros((4, 4)); e[0, 2] = 0.01; e[1, 3] = -0.01
    p0 = projector(0.875, u0, 0.10)
    p1 = projector(0.875, u0 + e, 0.10)

    p_oblique = np.array([[1.0, 2.0], [0.0, 0.0]])
    c = np.array([[1.0, 1.0], [1.0, 1.0]])
    bad_concentration = float(np.trace(p_oblique @ c @ p_oblique) / np.trace(c))
    q, _ = np.linalg.qr(p_oblique[:, :1])
    q = q @ q.T
    good_concentration = float(np.trace(q @ c @ q) / np.trace(c))
    mu = np.array([4.0, 1.0, 0.25, 0.0])
    deff = float(np.sum(mu / (mu + 1.0)))
    out = {
        "baseline_min_eigenvalue": m,
        "on_min_eigenvalue": float(np.linalg.eigvalsh(a_on).min()),
        "perturbation_norm": eps,
        "local_squared_length_difference": local_difference,
        "local_bound_holds": abs(local_difference) <= eps * float(u @ u) + 1e-12,
        "baseline_free_min_eigenvalue": float(np.linalg.eigvalsh(singular).min()),
        "riesz_rank_before": int(np.linalg.matrix_rank(p0, tol=1e-7)),
        "riesz_rank_after": int(np.linalg.matrix_rank(p1, tol=1e-7)),
        "riesz_projector_difference_norm": float(np.linalg.norm(p1 - p0, 2)),
        "oblique_contract_concentration": bad_concentration,
        "orthogonal_corrected_concentration": good_concentration,
        "effective_dimension_lambda_1": deff,
    }
    assert out["baseline_min_eigenvalue"] > 0
    assert out["on_min_eigenvalue"] >= out["baseline_min_eigenvalue"] - 1e-12
    assert out["local_bound_holds"]
    assert abs(out["baseline_free_min_eigenvalue"]) < 1e-12
    assert out["riesz_rank_before"] == out["riesz_rank_after"] == 2
    assert out["oblique_contract_concentration"] > 1
    assert 0 <= out["orthogonal_corrected_concentration"] <= 1
    assert 0 <= out["effective_dimension_lambda_1"] <= 3
    print(json.dumps(out, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
