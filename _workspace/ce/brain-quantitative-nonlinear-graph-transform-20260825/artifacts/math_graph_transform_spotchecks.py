from fractions import Fraction as F


def margins(mu, b, lx, ly, radius, forcing, slope):
    q = b + ly
    return q, 1 - q, radius - (q * radius + forcing), slope - mu * (q * slope + lx)


def main() -> None:
    values = margins(F(1), F(1, 4), F(1, 4), F(1, 4), F(1), F(1, 4), F(1))
    assert values == (F(1, 2), F(1, 2), F(1, 4), F(1, 4))

    boundary = margins(F(1), F(1, 4), F(1, 2), F(1, 4), F(1), F(1, 2), F(1))
    assert boundary == (F(1, 2), F(1, 2), F(0), F(0))

    assert F(1, 2) ** 4 * 3 == F(3, 16)

    # Independent base/fiber rescaling preserves normalized cross-slopes.
    x_scale, y_scale = F(2), F(3)
    lx_raw = F(3, 8)
    assert lx_raw * x_scale / y_scale == F(1, 4)
    lambda_x, lambda_y = F(5), F(7)
    assert (lx_raw * lambda_y / lambda_x) * (x_scale * lambda_x) / (y_scale * lambda_y) == F(1, 4)
    print("PASS: quantitative triangular graph-transform spot checks")


if __name__ == "__main__":
    main()
