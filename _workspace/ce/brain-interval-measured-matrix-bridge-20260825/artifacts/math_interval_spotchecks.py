from fractions import Fraction as F


def main() -> None:
    # Scalar rectangular radius is attained at a + ib.
    a, b = F(3, 10), F(2, 5)
    assert a * a + b * b == F(1, 4)

    # Strictness counterexample: U0=0, unit circle, Delta=1 touches z=1.
    nominal_margin = F(1)
    touching_error = F(1)
    assert nominal_margin - touching_error == 0

    # Exact nonnormal projector movement for [[0,e],[0,2]].
    e = F(1, 10)
    projector_difference_norm_squared = e * e / 4
    assert projector_difference_norm_squared == F(1, 400)

    # One exact abstract I2 bound and its dimensional unit invariance.
    r, delta, epsilon = F(1), F(3, 4), F(1, 10)
    rho = r * epsilon / (delta * (delta - epsilon))
    assert rho == F(8, 39)
    assert e / 2 <= rho
    scale = F(7)
    rescaled = (scale * r) * (scale * epsilon) / (
        (scale * delta) * (scale * delta - scale * epsilon)
    )
    assert rescaled == rho

    # I3 must add independent uncertainty and quadrature contributions.
    eta = F(1, 50)
    assert rho + eta == F(439, 1950)
    print("PASS: interval contour/projector exact theorem spot checks")


if __name__ == "__main__":
    main()
