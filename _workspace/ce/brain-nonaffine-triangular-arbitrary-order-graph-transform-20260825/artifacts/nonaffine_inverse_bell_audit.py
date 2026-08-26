from fractions import Fraction as F

mu = F(10, 9)
h, t, u = F(1, 100), F(1, 200), F(1, 400)
i2 = h * mu**3
i3 = t * mu**4 + 3 * h**2 * mu**5
i4 = u * mu**5 + 10 * h * t * mu**6 + 15 * h**3 * mu**7
assert i2 == F(10, 729)
assert i3 == F(160, 19683)
assert i4 == F(8300, 1594323)
print("OK: exact nonaffine inverse Bell I2--I4 audit")
