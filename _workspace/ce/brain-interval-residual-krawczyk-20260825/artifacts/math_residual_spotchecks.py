from fractions import Fraction as F


def main() -> None:
    # Equality is unsafe: A0=B=1 and Delta=1 includes A=0.
    assert abs(1 - 1 * 1) + abs(1) * 1 == 1

    # Structured far-eigenvalue node z=1.
    residual_far = F(0)
    b_far = F(1, 9)
    d_far = F(1)
    q = residual_far + b_far * d_far
    assert q == F(1, 9) < 1
    inverse_infinity_upper = F(1) / (1 - q)
    assert inverse_infinity_upper == F(9, 8)
    assert 1 / inverse_infinity_upper == F(8, 9)

    # Projector perturbation units cancel algebraically under common scaling.
    r, epsilon, resolvent = F(1), F(1, 5), F(3, 2)
    rho = r * epsilon * resolvent * resolvent
    scale = F(7)
    scaled = (scale * r) * (scale * epsilon) * (resolvent / scale) ** 2
    assert rho == scaled == F(9, 20)
    print("PASS: componentwise residual/Krawczyk contour spot checks")


if __name__ == "__main__":
    main()
