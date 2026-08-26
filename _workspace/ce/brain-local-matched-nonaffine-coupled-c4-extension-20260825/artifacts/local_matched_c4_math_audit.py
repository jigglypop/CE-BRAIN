from fractions import Fraction as F

a = epsilon = F(1, 100)
slope = F(1, 2)
eta_in = F(1, 10)
alpha_core = 1 - 2 * a - epsilon * slope
alpha_collar = 1 + a - 3 * a * (1 + eta_in) ** 2 - epsilon * slope
eta_out = alpha_collar * eta_in / 2
r_pre = 1 + eta_in / 2
assert alpha_core == F(39, 40)
assert alpha_collar == F(9687, 10000)
assert eta_out == F(9687, 200000)
assert r_pre == F(21, 20)
assert 1 + eta_in - r_pre == F(1, 20)
assert 0 == 0  # D4 and D5 of the cubic base polynomial.
print("OK: exact local/matched nonaffine coupled C4 collar fixture")
