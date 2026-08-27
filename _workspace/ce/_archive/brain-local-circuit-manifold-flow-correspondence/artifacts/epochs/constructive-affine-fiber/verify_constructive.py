"""Deterministic binary64 witness for the constructive affine-fiber theorem.

This checks one frozen fixture only.  It is a regression witness for the
closed-form construction, not a proof of the general theorems and not
empirical evidence about neural tissue.
"""

from __future__ import annotations

import math


DELTA = 0.25
OMEGA = 0.37
A = (0.2, 0.4)
TERMS = 64
TOL = 5.0e-12


def norm2(vector: tuple[float, float]) -> float:
    return math.hypot(*vector)


def add(left: tuple[float, float], right: tuple[float, float]) -> tuple[float, float]:
    return (left[0] + right[0], left[1] + right[1])


def sub(left: tuple[float, float], right: tuple[float, float]) -> tuple[float, float]:
    return (left[0] - right[0], left[1] - right[1])


def scale_diagonal(diagonal: tuple[float, float], vector: tuple[float, float]) -> tuple[float, float]:
    return (diagonal[0] * vector[0], diagonal[1] * vector[1])


def forcing(theta: float) -> tuple[float, float]:
    return (math.sin(theta), math.cos(2.0 * theta))


def forcing_derivative(theta: float) -> tuple[float, float]:
    return (math.cos(theta), -2.0 * math.sin(2.0 * theta))


def perturbed_forcing(theta: float) -> tuple[float, float]:
    return (
        math.sin(theta) + 0.03 * math.cos(3.0 * theta),
        math.cos(2.0 * theta) - 0.02 * math.sin(theta),
    )


def graph(theta: float, diagonal: tuple[float, float] = A, force=forcing) -> tuple[float, float]:
    value = (0.0, 0.0)
    power = (1.0, 1.0)
    for index in range(1, TERMS + 1):
        value = add(value, scale_diagonal(power, force(theta - index * OMEGA)))
        power = (power[0] * diagonal[0], power[1] * diagonal[1])
    return value


def graph_derivative(theta: float) -> tuple[float, float]:
    value = (0.0, 0.0)
    power = (1.0, 1.0)
    for index in range(1, TERMS + 1):
        value = add(value, scale_diagonal(power, forcing_derivative(theta - index * OMEGA)))
        power = (power[0] * A[0], power[1] * A[1])
    return value


def update(theta: float, y: tuple[float, float]) -> tuple[float, tuple[float, float]]:
    return (theta + OMEGA, add(scale_diagonal(A, y), forcing(theta)))


def maximum(values: list[float]) -> float:
    return max(values) if values else 0.0


def require(name: str, value: float, tolerance: float = TOL) -> None:
    if value > tolerance:
        raise AssertionError(f"{name}: {value:.3e} exceeds {tolerance:.3e}")
    print(f"PASS {name}: {value:.3e} <= {tolerance:.3e}")


def main() -> None:
    angles = [2.0 * math.pi * index / 257.0 for index in range(257)]

    invariance = maximum(
        norm2(sub(graph(theta + OMEGA), add(scale_diagonal(A, graph(theta)), forcing(theta))))
        for theta in angles
    )
    derivative_invariance = maximum(
        norm2(sub(graph_derivative(theta + OMEGA), add(scale_diagonal(A, graph_derivative(theta)), forcing_derivative(theta))))
        for theta in angles
    )
    require("truncated graph invariance", invariance)
    require("truncated derivative invariance", derivative_invariance)

    theta0 = 0.91
    y0 = (1.7, -0.8)
    theta, y = theta0, y0
    attraction_error = 0.0
    for step in range(1, 13):
        theta, y = update(theta, y)
        expected = scale_diagonal((A[0] ** step, A[1] ** step), sub(y0, graph(theta0)))
        attraction_error = max(attraction_error, norm2(sub(sub(y, graph(theta)), expected)))
    require("A^n fiber-attraction identity", attraction_error)

    lambdas = (-math.log(A[0]) / DELTA, -math.log(A[1]) / DELTA)
    lift_error = 0.0
    for theta in angles:
        y = (0.7 * math.sin(theta) - 0.2, -0.3 * math.cos(theta) + 0.5)
        lifted = add(
            graph(theta + OMEGA),
            scale_diagonal((math.exp(-lambdas[0] * DELTA), math.exp(-lambdas[1] * DELTA)), sub(y, graph(theta))),
        )
        lift_error = max(lift_error, norm2(sub(lifted, update(theta, y)[1])))
    require("exact lift time-step parity", lift_error)

    dimensionless_error = maximum(
        [abs(lambdas[index] * DELTA + math.log(A[index])) for index in range(2)]
    )
    require("dimensionless Lambda*Delta exponent", dimensionless_error, 1.0e-15)

    perturbed_a = (0.23, 0.37)
    q_star = 0.4
    delta_a = 0.03
    delta_c = math.hypot(0.03, 0.02)
    ctilde_bound = math.sqrt(2.0) + delta_c
    c5_bound = delta_c / (1.0 - q_star) + ctilde_bound * delta_a / (1.0 - q_star) ** 2
    c5_observed = maximum(
        norm2(sub(graph(theta), graph(theta, perturbed_a, perturbed_forcing))) for theta in angles
    )
    if c5_observed > c5_bound + TOL:
        raise AssertionError(f"C5 sensitivity: observed {c5_observed:.3e} > bound {c5_bound:.3e}")
    print(f"PASS C5 sensitivity: observed {c5_observed:.3e} <= bound {c5_bound:.3e}")

    h_diagonal = (1.0 / (1.0 - A[0] ** 2), 1.0 / (1.0 - A[1] ** 2))
    lyapunov_error = maximum(
        [abs(h_diagonal[index] - A[index] ** 2 * h_diagonal[index] - 1.0) for index in range(2)]
    )
    require("Lyapunov H - A^T H A = I", lyapunov_error, 1.0e-15)

    minimum_metric_ratio = min(
        1.0 + h_diagonal[0] * graph_derivative(theta)[0] ** 2 + h_diagonal[1] * graph_derivative(theta)[1] ** 2
        for theta in angles
    )
    if minimum_metric_ratio < 1.0 - TOL:
        raise AssertionError(f"metric positivity: minimum g(u,u)/u^2 is {minimum_metric_ratio:.16g}")
    print(f"PASS cost-conditioned metric positivity: min g(u,u)/u^2 = {minimum_metric_ratio:.12f}")

    print("RESULT: PASS (deterministic fixture; mathematical and empirical ceilings unchanged)")


if __name__ == "__main__":
    main()
