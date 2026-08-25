from fractions import Fraction as F


def frobenius_squared(c):
    return sum((value * value for row in c for value in row), F(0))


def induced_squared(c):
    n = len(c)
    one = max(sum(c[i][j] for i in range(n)) for j in range(n))
    infinity = max(sum(row) for row in c)
    return one * infinity


def main() -> None:
    diagonal = [[F(1), F(0)], [F(0), F(1)]]
    assert frobenius_squared(diagonal) == 2
    assert induced_squared(diagonal) == 1

    frobenius_wins = [[F(1), F(1)], [F(1), F(0)]]
    assert frobenius_squared(frobenius_wins) == 3
    assert induced_squared(frobenius_wins) == 4

    scalar = [[F(3, 5)]]
    assert frobenius_squared(scalar) == induced_squared(scalar) == F(9, 25)

    # Abstract margin window: sqrt(2)*c > delta but c < delta,
    # checked without irrational arithmetic by squaring.
    c, delta = F(1, 5), F(1, 4)
    assert c < delta
    assert 2 * c * c > delta * delta

    # Common unit rescaling cancels after normalization.
    scale = F(7)
    raw = F(3, 10)
    assert (scale * raw) / scale == raw
    print("PASS: induced 1/infinity interval tightening spot checks")


if __name__ == "__main__":
    main()
