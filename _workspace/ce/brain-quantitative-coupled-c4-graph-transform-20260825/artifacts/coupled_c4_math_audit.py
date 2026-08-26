from fractions import Fraction as F


# Independent scalar inverse-series audit.
l, p, u, w = F(13, 10), F(3, 5), F(3, 5), F(0)
k, r, v, z = F(13, 20), F(7, 5), F(3), F(6)
t = k / l
n = r - t * p
m = v - t * u - 3 * n * p / l
o = z - t * w - 4 * n * u / l - 3 * n * (p / l) ** 2 - 6 * m * p / l
modified_identity = o / l**4

a1 = 1 / l
a2 = -(p / 2) * a1**2 / l
a3 = -((p / 2) * 2 * a1 * a2 + (u / 6) * a1**3) / l
a4 = -(
    (p / 2) * (2 * a1 * a3 + a2**2)
    + (u / 6) * 3 * a1**2 * a2
    + (w / 24) * a1**4
) / l
inverse_series = 24 * (
    k * a4
    + (r / 2) * (2 * a1 * a3 + a2**2)
    + (v / 6) * 3 * a1**2 * a2
    + (z / 24) * a1**4
)
assert modified_identity == inverse_series


# Zero-base-coupling coefficient-vector reduction to triangular C4.
q = F(1, 2)
alpha = F(1)
r_graph = F(2)
k2, k3, k4, k5 = F(1, 16), F(1, 16), F(1, 64), F(1, 256)
lambda2, lambda3, lambda4 = F(1), F(2), F(6)
cz = (
    q * lambda4
    + 4 * k2 * lambda3 * r_graph
    + 3 * k2 * lambda2**2
    + 6 * k3 * lambda2 * r_graph**2
    + k4 * r_graph**4
)
assert cz == F(95, 16)
assert q / alpha**4 == F(1, 2)
assert 4 * k2 * r_graph / alpha**4 == F(1, 2)
assert (6 * k2 * lambda2 + 6 * k3 * r_graph**2) / alpha**4 == F(15, 8)
assert (
    4 * k2 * lambda3 + 12 * k3 * lambda2 * r_graph + 4 * k4 * r_graph**3
) / alpha**4 == F(5, 2)
assert (
    k2 * lambda4 + 4 * k3 * lambda3 * r_graph + 3 * k3 * lambda2**2
    + 6 * k4 * lambda2 * r_graph**2 + k5 * r_graph**4
) / alpha**4 == F(2)


def witness(x: F) -> F:
    return x * abs(x) ** 3


for x in (F(-3, 2), F(-1, 3), F(0), F(2, 5), F(7, 4)):
    assert witness(x / 2) == witness(x) / 16

print("OK affine coupled C4 identity, reduction, and boundary audit")
