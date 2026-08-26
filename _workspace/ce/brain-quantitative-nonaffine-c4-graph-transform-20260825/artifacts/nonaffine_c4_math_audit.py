from fractions import Fraction as F

a = F(1, 10)
gap = 1 - a
mu = 1 / gap
nu = a / gap**3
tau = (a + 4 * a**2) / gap**5
upsilon = a / gap**5 + 10 * a**2 / gap**6 + 15 * a**3 / gap**7
assert (mu, nu, tau, upsilon) == (
    F(10, 9), F(100, 729), F(14000, 59049), F(620000, 1594323)
)

q, r = F(1, 2), F(2)
k2 = k3 = F(1, 16)
k4, k5 = F(1, 64), F(1, 256)
l2, l3, l4 = F(2), F(8), F(100)
s = F(5, 8)
a2 = q * l2 + k2 * r**2
a3 = q * l3 + 3 * k2 * l2 * r + k3 * r**3
a4 = q * l4 + 4 * k2 * l3 * r + 3 * k2 * l2**2 + 6 * k3 * l2 * r**2 + k4 * r**4
out = mu**4 * a4 + 6 * mu**2 * nu * a3 + (3 * nu**2 + 4 * mu * tau) * a2 + upsilon * s
assert out == F(152045000, 1594323)
assert l4 - out == F(7387300, 1594323)
print("OK: exact nonaffine C4 inverse-chain fixture")
