from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"
sys.path.insert(0, str(MODULE_DIR))

import verified_rational_contour as R
import verified_weighted_interval_residual as W


def inverses(matrix):
    u = R._matrix(matrix, "matrix")
    directions = (R.ONE, R.QComplex(0, 1), R.QComplex(-1), R.QComplex(0, -1))
    result = []
    for direction in directions:
        a = tuple(
            tuple((direction if i == j else R.ZERO) - u[i][j] for j in range(2))
            for i in range(2)
        )
        inverse = R._inverse(a)
        if inverse is None:
            return None
        result.append(inverse)
    return result


for offdiag in (F(i, 2) for i in range(1, 17)):
    matrix = [[0, offdiag], [0, 10]]
    witnesses = inverses(matrix)
    assert witnesses is not None
    for uncertainty in (F(i, 20) for i in range(1, 81)):
        radii = [[(0, 0), (0, 0)], [(0, 0), (uncertainty, 0)]]
        for weight in (F(i, 4) for i in range(5, 65)):
            result = W.verified_weighted_componentwise_residual_circle(
                matrix,
                uncertainty_radii=radii,
                approximate_inverses=witnesses,
                diagonal_weights=[weight, 1],
                center=0,
                radius=1,
                spectral_reference_scale=1,
                sqrt_precision=24,
            )
            if result.base_circle.validation_level is None and result.validation_level is not None:
                print(
                    "FOUND",
                    offdiag,
                    uncertainty,
                    weight,
                    result.base_circle.status,
                    result.normalized_robust_delta_lower,
                )
                raise SystemExit(0)

print("NO_FULL_CIRCLE_IMPROVEMENT_IN_DECLARED_GRID")
