from fractions import Fraction as F
from math import factorial


def partition_coefficient(k1: int, k2: int, k3: int, k4: int) -> int:
    numerator = factorial(4)
    denominator = (
        factorial(k1)
        * factorial(k2)
        * factorial(k3)
        * factorial(k4)
        * factorial(1) ** k1
        * factorial(2) ** k2
        * factorial(3) ** k3
        * factorial(4) ** k4
    )
    return numerator // denominator


partitions = {
    (0, 0, 0, 1): 1,
    (1, 0, 1, 0): 4,
    (0, 2, 0, 0): 3,
    (2, 1, 0, 0): 6,
    (4, 0, 0, 0): 1,
}
for partition, expected in partitions.items():
    assert sum((index + 1) * count for index, count in enumerate(partition)) == 4
    assert partition_coefficient(*partition) == expected

q = F(1, 2)
mu = F(1)
r = F(2)
k2 = F(1, 16)
k3 = F(1, 16)
k4 = F(1, 64)
k5 = F(1, 256)
lambda2 = F(1)
lambda3 = F(2)
lambda4 = F(6)

output = mu**4 * (
    q * lambda4
    + 4 * k2 * lambda3 * r
    + 3 * k2 * lambda2**2
    + 6 * k3 * lambda2 * r**2
    + k4 * r**4
)
beta4 = q * mu**4
c43 = mu**4 * 4 * k2 * r
c42 = mu**4 * (6 * k2 * lambda2 + 6 * k3 * r**2)
c41 = mu**4 * (
    4 * k2 * lambda3 + 12 * k3 * lambda2 * r + 4 * k4 * r**3
)
c40 = mu**4 * (
    k2 * lambda4
    + 4 * k3 * lambda3 * r
    + 3 * k3 * lambda2**2
    + 6 * k4 * lambda2 * r**2
    + k5 * r**4
)

assert output == F(95, 16)
assert lambda4 - output == F(1, 16)
assert beta4 == F(1, 2)
assert (c43, c42, c41, c40) == (F(1, 2), F(15, 8), F(5, 2), F(2))


def witness(x: F) -> F:
    return x * abs(x) ** 3


for x in (F(-3, 2), F(-1, 3), F(0), F(2, 5), F(7, 4)):
    assert witness(x / 2) == witness(x) / 16

print("OK affine triangular C4 partition, recurrence, and boundary audit")
