from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def main() -> None:
    rng = np.random.default_rng(20260823)
    n, window = 12, 60
    z = rng.normal(size=(n, window))
    h = np.eye(window) - np.ones((window, window)) / window
    reliability = np.linspace(0.55, 1.0, n)
    d = np.diag(np.sqrt(reliability))
    g = d @ z @ h @ z.T @ d / (window - 1)
    eigenvalues = np.linalg.eigvalsh(g)
    scale = np.trace(g) / min(n, window - 1)
    g_tilde = g / scale

    def selector(lam: float) -> np.ndarray:
        return g_tilde @ np.linalg.inv(g_tilde + lam * np.eye(n))

    lambdas = (0.1, 0.3, 1.0, 3.0, 10.0)
    selectors = {str(lam): selector(lam) for lam in lambdas}
    effective_dimensions = {
        key: float(np.trace(value)) for key, value in selectors.items()
    }

    q_raw, _ = np.linalg.qr(rng.normal(size=(n, n)))
    g_rotated = q_raw @ g_tilde @ q_raw.T
    s_rotated = g_rotated @ np.linalg.inv(g_rotated + np.eye(n))
    orthogonal_residual = abs(
        float(np.trace(s_rotated)) - effective_dimensions["1.0"]
    )

    epsilon = 1e-3
    a = epsilon * np.eye(n) + (1 - epsilon) * selectors["1.0"]
    a_eigenvalues = np.linalg.eigvalsh(a)

    inconsistent_pairwise = np.asarray(
        [[1.0, 0.9, 0.9], [0.9, 1.0, -0.9], [0.9, -0.9, 1.0]]
    )

    # For tau_h=1, k(s,u)=1 and f_n=e^n 1_[−n−1,−n], the input
    # weighted norm squared tends to (1-e^-2)/2, while the output norm
    # on s in [-1,0] alone grows as e^(2n)(1-e^-2)/2.
    volterra_ratios = {
        str(index): float(np.exp(2 * index)) for index in (2, 4, 6, 8)
    }

    result = {
        "schema": "ce.ba_srm7.math_spotcheck.v1",
        "seed": 20260823,
        "minimum_g_eigenvalue": float(eigenvalues[0]),
        "effective_dimensions": effective_dimensions,
        "monotone_nonincreasing": all(
            effective_dimensions[str(left)] >= effective_dimensions[str(right)]
            for left, right in zip(lambdas, lambdas[1:])
        ),
        "orthogonal_trace_residual": orthogonal_residual,
        "a_minimum_eigenvalue": float(a_eigenvalues[0]),
        "a_condition_number": float(a_eigenvalues[-1] / a_eigenvalues[0]),
        "pairwise_matrix_minimum_eigenvalue": float(
            np.linalg.eigvalsh(inconsistent_pairwise)[0]
        ),
        "unbounded_volterra_output_to_input_lower_bound": volterra_ratios,
    }
    output = Path(__file__).with_name("math-spotcheck.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
