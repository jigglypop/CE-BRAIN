"""Deterministic binary64 witnesses for the conditional correspondence note.

This is a numerical regression harness, not a substitute for the proofs in
11-math.md.  It deliberately uses only Python's standard library and values
that are exactly representable in IEEE-754 binary64 where that is useful.
"""

from __future__ import annotations

import math


TANGENCY_TOLERANCE = 1.0e-12


def require(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def verify_closed_circle_tangency() -> None:
    """F(x, y)=(-y, x) is tangent to S1: x*Fx+y*Fy=0."""
    maximum_residual = 0.0
    for index in range(16):
        angle = 2.0 * math.pi * index / 16.0
        x, y = math.cos(angle), math.sin(angle)
        fx, fy = -y, x
        maximum_residual = max(maximum_residual, abs(x * fx + y * fy))
    require(maximum_residual <= TANGENCY_TOLERANCE, "S1 tangency residual")
    print(f"PASS closed_s1_tangency max_residual={maximum_residual:.1e}")


def verify_open_interval_escape() -> None:
    """For M=(0,1), F=1, x(0)=1/2 reaches the excluded endpoint at t=1/2."""
    initial = 0.5
    time = 0.5
    endpoint = initial + time
    require(0.0 < initial < 1.0, "open interval initial point")
    require(not (0.0 < endpoint < 1.0), "open interval escape")
    print(f"PASS open_interval_escape endpoint={endpoint:.1f} in_M={0.0 < endpoint < 1.0}")


def verify_cusp_two_branches() -> None:
    """Phi(u,0)=(u^2,u^3) has two distinct local branches above every x>0."""
    u = 0.125
    plus = (u * u, u * u * u)
    minus = ((-u) * (-u), (-u) * (-u) * (-u))
    require(plus[0] == minus[0], "cusp equal horizontal coordinate")
    require(plus[1] == -minus[1] and plus[1] != 0.0, "cusp distinct branches")
    print(
        "PASS cusp_two_branches "
        f"x={plus[0]:.9f} y_plus={plus[1]:.9f} y_minus={minus[1]:.9f}"
    )


def verify_discrete_flow_obstructions() -> None:
    """Witness orientation reversal and noninjectivity of discrete updates."""
    # Phi_minus(x)=-x reverses orientation: its (exact) one-dimensional
    # derivative/determinant is -1.
    determinant = -1.0
    require(determinant < 0.0, "orientation reversal")

    # Phi_square(x)=x^2 identifies two distinct points.
    left, right = -0.5, 0.5
    left_image, right_image = left * left, right * right
    require(left != right and left_image == right_image, "noninjective update")
    print(
        "PASS discrete_obstructions "
        f"orientation_det={determinant:.1f} square_images=({left_image:.2f},{right_image:.2f})"
    )


def verify_metric_nonidentifiability() -> None:
    """g1=diag(1,1) and g2=diag(1,2) agree on b=partial_x and grad x."""
    b = (1.0, 0.0)
    g1 = ((1.0, 0.0), (0.0, 1.0))
    g2 = ((1.0, 0.0), (0.0, 2.0))

    def quadratic(metric: tuple[tuple[float, float], tuple[float, float]]) -> float:
        return b[0] * (metric[0][0] * b[0] + metric[0][1] * b[1]) + b[1] * (
            metric[1][0] * b[0] + metric[1][1] * b[1]
        )

    norm1_sq, norm2_sq = quadratic(g1), quadratic(g2)
    grad_x_g1 = (1.0 / g1[0][0], 0.0)
    grad_x_g2 = (1.0 / g2[0][0], 0.0)
    require(norm1_sq == norm2_sq == 1.0, "same drift norm")
    require(grad_x_g1 == grad_x_g2 == b, "same gradient of x")
    require(g1 != g2 and g1[1][1] != g2[1][1], "different transverse metric")
    print(
        "PASS metric_nonidentifiability "
        f"drift_norm_sq=({norm1_sq:.1f},{norm2_sq:.1f}) transverse=({g1[1][1]:.1f},{g2[1][1]:.1f})"
    )


def main() -> None:
    verify_closed_circle_tangency()
    verify_open_interval_escape()
    verify_cusp_two_branches()
    verify_discrete_flow_obstructions()
    verify_metric_nonidentifiability()
    print("PASS all_binary64_witnesses count=5")


if __name__ == "__main__":
    main()
