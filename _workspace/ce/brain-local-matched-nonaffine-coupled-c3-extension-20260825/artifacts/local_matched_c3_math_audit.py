from fractions import Fraction as F

a = F(1, 100)
epsilon = F(1, 100)
kappa = F(1, 2)
eta_in = F(1, 10)
core_gap = 1 - 2 * a - epsilon * kappa
collar_gap = 1 + a - 3 * a * (1 + eta_in) ** 2 - epsilon * kappa
eta_out = collar_gap * eta_in / 2
inverse_collar_radius = 1 + eta_in / 2
collar_margin = 1 + eta_in - inverse_collar_radius

assert core_gap == F(39, 40)
assert collar_gap == F(9687, 10000)
assert eta_out == F(9687, 200000)
assert F(1, 1) / collar_gap == F(10000, 9687)
assert inverse_collar_radius == F(21, 20)
assert collar_margin == F(1, 20)
assert 6 * a * (1 + eta_in) == F(33, 500)
assert 6 * a == F(3, 50)
print("OK local/matched nonaffine coupled C3 exact collar audit")
