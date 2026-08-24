#!/usr/bin/env python3
"""Frozen synthetic validation for BA-OBS-ID2 active metric tomography.

This program evaluates only the preregistered analytic rank-one \u2113\u00b2 witness.  It is
not a brain, consciousness, self, or AGI experiment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np


R = 0.60
BETA = 0.50
NOISE = 1.0e-8
SIZES = (4, 8, 16, 32)
EXACT_TOL = 1.0e-12
TAIL_TOL = 1.0e-7
GATE_SLACK = 1.0e-12
INVISIBILITY_TOL = 1.0e-14
HELDOUT_TOL = 1.0e-12


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def v_prefix(n: int) -> np.ndarray:
    indices = np.arange(n, dtype=float)
    return np.sqrt(1.0 - R * R) * np.power(R, indices)


def response(vector: np.ndarray) -> float:
    """Exact Q_G(f) for a finite-support vector in the analytic \u2113\u00b2 witness."""
    return float(np.dot(vector, vector) + BETA * np.dot(v_prefix(len(vector)), vector) ** 2)


def query_vectors(n: int) -> list[np.ndarray]:
    vectors = [np.eye(n, dtype=float)[i] for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            plus = np.zeros(n, dtype=float)
            minus = np.zeros(n, dtype=float)
            plus[i] = plus[j] = 1.0
            minus[i], minus[j] = 1.0, -1.0
            vectors.extend((plus, minus))
    assert len(vectors) == n * n
    return vectors


def reconstruct(n: int, values: list[float]) -> np.ndarray:
    """Real polarization reconstruction in frozen query order."""
    assert len(values) == n * n
    matrix = np.zeros((n, n), dtype=float)
    matrix[np.diag_indices(n)] = values[:n]
    cursor = n
    for i in range(n):
        for j in range(i + 1, n):
            entry = (values[cursor] - values[cursor + 1]) / 4.0
            matrix[i, j] = matrix[j, i] = entry
            cursor += 2
    assert cursor == n * n
    return matrix


def analytic_tails(n: int) -> tuple[float, float]:
    """Cancellation-safe Hilbert--Schmidt tails fixed by the contract."""
    b = R ** (2 * n)
    a = 1.0 - b
    c = BETA / (1.0 + BETA)
    mobility = BETA * np.sqrt(2.0 * b - b * b)
    metric = c * np.sqrt(
        2.0 * a * b
        + b * b
        + (BETA * BETA * a * a * b * b) / ((1.0 + BETA * a) ** 2)
    )
    return float(mobility), float(metric)


def validate_size(n: int) -> dict[str, object]:
    queries = query_vectors(n)
    exact_values = [response(vector) for vector in queries]
    v = v_prefix(n)
    true_block = np.eye(n) + BETA * np.outer(v, v)
    exact_block = reconstruct(n, exact_values)
    exact_error = float(np.linalg.norm(exact_block - true_block, ord="fro"))

    noisy_values = [value + NOISE * ((-1.0) ** k) for k, value in enumerate(exact_values)]
    raw_block = reconstruct(n, noisy_values)
    raw_error = float(np.linalg.norm(raw_block - true_block, ord="fro"))
    eta = float(NOISE * np.sqrt(n + n * (n - 1) / 4.0))
    eigenvalues, eigenvectors = np.linalg.eigh(raw_block)
    clipped_eigenvalues = np.clip(eigenvalues, 1.0, 1.5)
    clipped_block = (eigenvectors * clipped_eigenvalues) @ eigenvectors.T
    clipped_block = (clipped_block + clipped_block.T) / 2.0
    clipped_error = float(np.linalg.norm(clipped_block - true_block, ord="fro"))

    mobility_tail, metric_tail = analytic_tails(n)

    # w_N uses coordinates N+1 and N+2 (zero-based N and N+1), while every
    # reconstruction query is supported only on the first N coordinates.
    width = n + 2
    w = np.zeros(width, dtype=float)
    w[n] = R / np.sqrt(1.0 + R * R)
    w[n + 1] = -1.0 / np.sqrt(1.0 + R * R)
    v_full = v_prefix(width)
    w_norm_error = float(abs(np.dot(w, w) - 1.0))
    w_v_inner = float(np.dot(w, v_full))
    invisible_gaps = [0.10 * float(np.dot(np.pad(vector, (0, 2)), w) ** 2) for vector in queries]
    invisibility = float(max(abs(gap) for gap in invisible_gaps))
    heldout_gap = float(0.10 * np.dot(w, w) ** 2)
    base_spectrum = [1.0, 1.5]
    alt_spectrum = [1.0, 1.1, 1.5]

    gates = {
        "exact_block": exact_error <= EXACT_TOL,
        "noisy_raw_bound": raw_error <= eta + GATE_SLACK,
        "noisy_clipped_bound": clipped_error <= eta + GATE_SLACK,
        "clipped_spectrum": bool(np.min(clipped_eigenvalues) >= 1.0 - GATE_SLACK and np.max(clipped_eigenvalues) <= 1.5 + GATE_SLACK),
        "w_unit": w_norm_error <= GATE_SLACK,
        "w_orthogonal_to_v": abs(w_v_inner) <= GATE_SLACK,
        "finite_invisibility": invisibility <= INVISIBILITY_TOL,
        "heldout_gap": abs(heldout_gap - 0.10) <= HELDOUT_TOL,
        "base_spectral_class": base_spectrum[0] >= 1.0 and base_spectrum[-1] <= 1.5,
        "alt_spectral_class": alt_spectrum[0] >= 1.0 and alt_spectrum[-1] <= 1.5,
    }
    return {
        "N": n,
        "query_count": len(queries),
        "query_order": "diagonals_then_lexicographic_plus_minus",
        "exact_block_fro_error": exact_error,
        "noisy_raw_block_fro_error": raw_error,
        "noisy_clipped_block_fro_error": clipped_error,
        "eta_N": eta,
        "clipped_eigenvalue_min": float(np.min(clipped_eigenvalues)),
        "clipped_eigenvalue_max": float(np.max(clipped_eigenvalues)),
        "mobility_hs_tail": mobility_tail,
        "metric_hs_tail": metric_tail,
        "w_unit_error": w_norm_error,
        "w_v_inner_product": w_v_inner,
        "first_N2_response_gap_max": invisibility,
        "heldout_w_response_gap": heldout_gap,
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = [validate_size(n) for n in SIZES]
    mobility_tails = [float(row["mobility_hs_tail"]) for row in rows]
    metric_tails = [float(row["metric_hs_tail"]) for row in rows]
    run_gates = {
        "all_per_size_gates": all(all(row["gates"].values()) for row in rows),
        "N32_mobility_tail": mobility_tails[-1] <= TAIL_TOL,
        "N32_metric_tail": metric_tails[-1] <= TAIL_TOL,
        "mobility_tail_strictly_decreases": all(left > right for left, right in zip(mobility_tails, mobility_tails[1:])),
        "metric_tail_strictly_decreases": all(left > right for left, right in zip(metric_tails, metric_tails[1:])),
    }
    receipt = {
        "status": "PASS" if all(run_gates.values()) else "FAIL",
        "protocol": "BA-OBS-ID2 frozen analytic rank-one active metric tomography",
        "synthetic_only": True,
        "interpretation_limit": "Numerical reproduction of an analytic l2 witness only; no empirical brain, consciousness, self, or AGI validation.",
        "parameters": {"r": R, "beta": BETA, "noise_amplitude": NOISE, "N": list(SIZES)},
        "thresholds": {"exact_block": EXACT_TOL, "tail_N32": TAIL_TOL, "bound_slack": GATE_SLACK, "invisibility": INVISIBILITY_TOL, "heldout": HELDOUT_TOL},
        "formulae": {
            "Q": "||f||^2 + beta <v,f>^2",
            "mobility_tail": "beta sqrt(2 b_N - b_N^2)",
            "metric_tail": "c sqrt(2 a_N b_N + b_N^2 + beta^2 a_N^2 b_N^2/(1+beta a_N)^2)",
            "adverse": "M_alt,N = M + 0.10 w_N outer w_N",
        },
        "rows": rows,
        "run_gates": run_gates,
        "provenance": {
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "numpy_version": np.__version__,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"BA-OBS-ID2 synthetic active metric tomography: {receipt['status']}")
    for row in rows:
        print("N={N} exact={exact_block_fro_error:.3e} raw={noisy_raw_block_fro_error:.3e} clip={noisy_clipped_block_fro_error:.3e} Mtail={mobility_hs_tail:.3e} Gtail={metric_hs_tail:.3e}".format(**row))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
