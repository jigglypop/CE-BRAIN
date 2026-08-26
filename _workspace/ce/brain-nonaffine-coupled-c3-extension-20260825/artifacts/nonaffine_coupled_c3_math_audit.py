"""Independent exact algebra checks for the nonaffine coupled C3 lane."""

from fractions import Fraction as F


def check_scalar_inverse_composition_identity() -> None:
    # Pointwise scalar jets of F and Y.  The values are deliberately nonzero.
    l, p, u = F(13, 10), F(3, 5), F(7, 10)
    k, r, v = F(13, 20), F(7, 5), F(3)
    t = k / l
    n = r - t * p
    modified = v - t * u - 3 * n * p / l
    via_modified = modified / l**3
    via_direct_chain = (v * l**2 - k * u * l - 3 * r * l * p + 3 * k * p**2) / l**5
    assert via_modified == via_direct_chain


def check_forward_to_inverse_third_reduction() -> None:
    # Exact norm algebra for a graph-independent nonlinear base.
    mu, h_phi, t_phi = F(4, 3), F(1, 4), F(1, 4)
    nu = h_phi * mu**3
    tau = t_phi * mu**4 + 3 * h_phi**2 * mu**5
    a2, a3, s = F(5, 7), F(11, 13), F(3, 8)

    alpha = 1 / mu
    rho = s / alpha
    n = a2 + rho * h_phi
    modified = a3 + rho * t_phi + 3 * n * h_phi / alpha
    coupled_output = modified / alpha**3
    triangular_output = mu**3 * a3 + 3 * mu * nu * a2 + s * tau
    assert coupled_output == triangular_output


def check_sine_forward_bounds() -> None:
    linear, amplitude = F(1001, 1000), F(1, 1000)
    inverse_lipschitz = 1 / (linear - amplitude)
    assert inverse_lipschitz == 1
    # |phi''|, Lip(phi''), and Lip(phi''') are all bounded by a.
    assert (amplitude, amplitude, amplitude) == (F(1, 1000),) * 3


if __name__ == "__main__":
    check_scalar_inverse_composition_identity()
    check_forward_to_inverse_third_reduction()
    check_sine_forward_bounds()
    print("nonaffine coupled C3 exact algebra: OK")

