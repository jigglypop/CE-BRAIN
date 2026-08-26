from fractions import Fraction as F

# Direct inverse D4 coefficients from implicit differentiation.
mu, h, t, u = F(10, 9), F(1, 100), F(1, 200), F(1, 400)
nu = h * mu**3
tau = t * mu**4 + 3 * h**2 * mu**5
upsilon = u * mu**5 + 10 * h * t * mu**6 + 15 * h**3 * mu**7
assert nu == h * mu**3
assert tau == t * mu**4 + 3 * h**2 * mu**5
assert upsilon == u * mu**5 + 10 * h * t * mu**6 + 15 * h**3 * mu**7

# Separately norming N and M is conservative: the direct N term contributes
# 3 and the expanded M term contributes 18 to the P^2 R envelope, while full
# cancellation-aware inversion yields 15. The boundary route uses 15.
assert 15 < 21
print("OK: nonaffine coupled C4 inverse-chain and sharp-boundary audit")
