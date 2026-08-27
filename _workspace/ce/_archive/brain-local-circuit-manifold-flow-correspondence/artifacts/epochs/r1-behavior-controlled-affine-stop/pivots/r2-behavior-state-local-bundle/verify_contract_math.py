"""Deterministic checks for the R2 contract identities; not neural evidence."""

from __future__ import annotations

import json

import numpy as np


def main() -> None:
    rng = np.random.default_rng(1702)
    n, d = 11, 3
    tangent, _ = np.linalg.qr(rng.normal(size=(n, d)))
    projector = np.eye(n) - tangent @ tangent.T
    diagonal = np.linspace(-0.83, 0.91, n)
    restricted = projector @ np.diag(diagonal) @ projector
    q_exact = float(np.linalg.norm(restricted, 2))
    q_upper = float(np.max(np.abs(diagonal)))

    assert np.allclose(projector @ projector, projector, atol=1e-12)
    assert np.allclose(projector, projector.T, atol=1e-12)
    assert q_exact <= q_upper + 1e-12

    other, _ = np.linalg.qr(rng.normal(size=(n, d)))
    chordal = float(
        np.linalg.norm(tangent @ tangent.T - other @ other.T, "fro")
        / np.sqrt(2.0 * d)
    )
    assert 0.0 <= chordal <= 1.0 + 1e-12

    units = 295
    full_var_penalized_predictors = units + 6
    full_var_parameters_per_output = full_var_penalized_predictors + 1
    minimum_rows = units + 8  # strict n_i > N + 7
    assert minimum_rows > full_var_parameters_per_output
    assert minimum_rows * units > full_var_parameters_per_output * units

    print(
        json.dumps(
            {
                "status": "PASS_CONTRACT_IDENTITIES_ONLY",
                "q_exact": q_exact,
                "q_upper": q_upper,
                "projector_chordal": chordal,
                "full_var_parameters_per_output": full_var_parameters_per_output,
                "minimum_chart_rows": minimum_rows,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
