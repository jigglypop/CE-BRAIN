"""Deterministic BA-OBS-ID1 metric-identifiability synthetic witness.

This is a trajectory-fitting receipt for the frozen protocol in 00-contract.md.
It is deliberately not a numerical estimate of y''(0), and it is neither a
proof of T3/W1 nor evidence about brains, consciousness, self, or AGI.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RECEIPT = ROOT / "metric_escape_receipt.json"
KAPPA = 0.30
T = 4.0
DT = 0.005
N_STEPS = int(round(T / DT))
THETAS = (-1.20, -0.40, 0.30, 1.10)
GRID = np.linspace(-1.5, 1.5, 241)
H = 1.0e-5
TRAIN_NAMES = ("TRAIN-A", "TRAIN-B")
HOLDOUT_NAME = "HOLDOUT-C"


def schedule(name: str) -> np.ndarray:
    """Return the pre-registered piecewise-constant input at each RK4 step."""
    times = np.arange(N_STEPS, dtype=float) * DT
    u = np.zeros(N_STEPS, dtype=float)
    if name == "TRAIN-A":
        u[(times >= 0.0) & (times < 0.60)] = 1.0
        u[(times >= 1.50) & (times < 2.00)] = -0.30
    elif name == "TRAIN-B":
        u[(times >= 0.30) & (times < 1.00)] = -0.70
        u[(times >= 2.20) & (times < 3.00)] = 0.90
    elif name == "HOLDOUT-C":
        u[(times >= 0.0) & (times < 0.40)] = 0.50
        u[(times >= 1.00) & (times < 1.70)] = -1.00
        u[(times >= 3.00) & (times < 3.50)] = 0.25
    elif name == "NEGATIVE-ZERO":
        pass
    else:
        raise ValueError(f"unknown frozen schedule: {name}")
    return u


INPUTS = {name: schedule(name) for name in (*TRAIN_NAMES, HOLDOUT_NAME, "NEGATIVE-ZERO")}


def rhs(q: np.ndarray, theta: float, u: float) -> np.ndarray:
    """Dimensionless invariant subsystem: x'=z-x, z'=exp(-theta)(x-(1+k)z+u)."""
    x, z = q
    return np.array((z - x, np.exp(-theta) * (x - (1.0 + KAPPA) * z + u)))


def trajectory(theta: float, input_values: np.ndarray) -> np.ndarray:
    """Sample y=x at t=0,...,T using a constant-input RK4 transition per step."""
    q = np.zeros(2, dtype=float)
    y = np.empty(N_STEPS + 1, dtype=float)
    y[0] = q[0]
    for index, u in enumerate(input_values):
        k1 = rhs(q, theta, float(u))
        k2 = rhs(q + 0.5 * DT * k1, theta, float(u))
        k3 = rhs(q + 0.5 * DT * k2, theta, float(u))
        k4 = rhs(q + DT * k3, theta, float(u))
        q = q + (DT / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        y[index + 1] = q[0]
    return y


def train_loss(theta: float, targets: dict[str, np.ndarray]) -> float:
    return float(sum(np.sum((trajectory(theta, INPUTS[name]) - targets[name]) ** 2) for name in TRAIN_NAMES))


def fit_theta(targets: dict[str, np.ndarray]) -> tuple[float, dict[str, float | int]]:
    """Frozen 241 grid, smaller-theta tie, then 80 golden iterations in adjacent cell."""
    losses = np.array([train_loss(float(theta), targets) for theta in GRID])
    minimum = float(np.min(losses))
    # np.flatnonzero preserves the required smaller-theta tie rule.
    best_index = int(np.flatnonzero(losses == minimum)[0])
    left = float(GRID[max(0, best_index - 1)])
    right = float(GRID[min(len(GRID) - 1, best_index + 1)])
    golden = (np.sqrt(5.0) - 1.0) / 2.0
    c = right - golden * (right - left)
    d = left + golden * (right - left)
    fc = train_loss(c, targets)
    fd = train_loss(d, targets)
    for _ in range(80):
        if fc <= fd:  # deterministic smaller-theta choice on an exact tie
            right, d, fd = d, c, fc
            c = right - golden * (right - left)
            fc = train_loss(c, targets)
        else:
            left, c, fc = c, d, fd
            d = left + golden * (right - left)
            fd = train_loss(d, targets)
    estimate = float((left + right) / 2.0)
    return estimate, {
        "grid_best_index": best_index,
        "grid_best_theta": float(GRID[best_index]),
        "grid_best_loss": minimum,
        "refinement_left": left,
        "refinement_right": right,
        "refinement_iterations": 80,
        "refined_train_loss": train_loss(estimate, targets),
    }


def gramian(theta: float, input_names: tuple[str, ...]) -> float:
    total = 0.0
    for name in input_names:
        sensitivity = (trajectory(theta + H, INPUTS[name]) - trajectory(theta - H, INPUTS[name])) / (2.0 * H)
        total += float(np.sum(sensitivity**2) * DT)
    return total


def normalized_holdout_error(theta_hat: float, theta_true: float) -> float:
    target = trajectory(theta_true, INPUTS[HOLDOUT_NAME])
    residual = trajectory(theta_hat, INPUTS[HOLDOUT_NAME]) - target
    return float(np.sum(residual**2) / max(float(np.sum(target**2)), 1.0e-12))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    outcomes: list[dict[str, object]] = []
    for theta_true in THETAS:
        targets = {name: trajectory(theta_true, INPUTS[name]) for name in TRAIN_NAMES}
        theta_hat, fit = fit_theta(targets)
        error = abs(theta_hat - theta_true)
        active_gramian = gramian(theta_true, TRAIN_NAMES)
        holdout_error = normalized_holdout_error(theta_hat, theta_true)
        gates = {
            "parameter_error_le_1e-6": error <= 1.0e-6,
            "holdout_normalized_squared_error_le_1e-10": holdout_error <= 1.0e-10,
            "active_gramian_gt_1e-8": active_gramian > 1.0e-8,
        }
        outcomes.append({
            "theta_true": theta_true,
            "theta_hat": theta_hat,
            "absolute_parameter_error": error,
            "active_train_gramian": active_gramian,
            "holdout_normalized_squared_error": holdout_error,
            "fit": fit,
            "gates": gates,
            "status": "PASS" if all(gates.values()) else "FAIL",
        })

    # The matched negative control changes only the input: evaluate its own
    # zero-input trajectory, not the active TRAIN-A/B schedules.
    zero_target = trajectory(0.0, INPUTS["NEGATIVE-ZERO"])
    zero_losses = np.array([
        np.sum((trajectory(float(theta), INPUTS["NEGATIVE-ZERO"]) - zero_target) ** 2)
        for theta in GRID
    ])
    zero_gramians = [gramian(theta, ("NEGATIVE-ZERO",)) for theta in THETAS]
    zero_gates = {
        "negative_zero_gramian_le_1e-20": max(zero_gramians) <= 1.0e-20,
        "negative_zero_grid_loss_spread_le_1e-20": float(np.max(zero_losses) - np.min(zero_losses)) <= 1.0e-20,
    }
    overall = all(item["status"] == "PASS" for item in outcomes) and all(zero_gates.values())
    receipt = {
        "run": "BA-OBS-ID1",
        "status": "PASS" if overall else "FAIL",
        "claim_ceiling": "DETERMINISTIC_SYNTHETIC_INTERVENTION_WITNESS_ONLY; NOT_THEOREM_PROOF; NOT_BRAIN_CONSCIOUSNESS_SELF_OR_AGI_EVIDENCE",
        "configuration": {
            "dimensionless": True,
            "kappa": KAPPA,
            "T": T,
            "dt": DT,
            "n_steps": N_STEPS,
            "state": "x'=z-x; z'=exp(-theta)*(x-(1+kappa)*z+u); y=x",
            "initial_state": [0.0, 0.0],
            "integrator": "constant-input classical RK4 per step",
            "theta_truths": list(THETAS),
            "fit_grid": {"minimum": -1.5, "maximum": 1.5, "points": 241, "tie_rule": "smaller_theta"},
            "golden_refinement_iterations": 80,
            "sensitivity_central_difference_h": H,
            "schedules": {
                "TRAIN-A": [[0.0, 0.60, 1.0], [1.50, 2.00, -0.30]],
                "TRAIN-B": [[0.30, 1.00, -0.70], [2.20, 3.00, 0.90]],
                "HOLDOUT-C": [[0.0, 0.40, 0.50], [1.00, 1.70, -1.00], [3.00, 3.50, 0.25]],
                "NEGATIVE-ZERO": [],
            },
            "thresholds": {
                "absolute_parameter_error_max": 1.0e-6,
                "holdout_normalized_squared_error_max": 1.0e-10,
                "active_gramian_min_strict": 1.0e-8,
                "negative_zero_gramian_max": 1.0e-20,
                "negative_zero_grid_loss_spread_max": 1.0e-20,
            },
        },
        "per_truth": outcomes,
        "negative_zero_control": {
            "gramian_by_theta": dict(zip((str(theta) for theta in THETAS), zero_gramians, strict=True)),
            "max_gramian": max(zero_gramians),
            "grid_loss_min": float(np.min(zero_losses)),
            "grid_loss_max": float(np.max(zero_losses)),
            "grid_loss_spread": float(np.max(zero_losses) - np.min(zero_losses)),
            "gates": zero_gates,
            "status": "PASS" if all(zero_gates.values()) else "FAIL",
        },
        "environment": {"python": sys.version, "numpy": np.__version__, "platform": platform.platform()},
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt": str(RECEIPT), "sha256": sha256(RECEIPT)}, sort_keys=True))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
