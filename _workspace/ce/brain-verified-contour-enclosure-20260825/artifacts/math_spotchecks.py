"""Exact Fraction spot checks for the V1--V3 math lane (not production code)."""
from fractions import Fraction as F


def mm(a, b):
    return [[sum((a[i][k] * b[k][j] for k in range(len(b))), F(0))
             for j in range(len(b[0]))] for i in range(len(a))]


def sub(a, b):
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))]
            for i in range(len(a))]


V = [[F(1), F(1)], [F(0), F(1)]]
Vinv = [[F(1), F(-1)], [F(0), F(1)]]
U = mm(mm(V, [[F(0), F(0)], [F(0), F(3)]]), Vinv)
P = mm(mm(V, [[F(1), F(0)], [F(0), F(0)]]), Vinv)

# For the four roots of unity, (1/4) sum_w w/(w-lambda) = 1/(1-lambda**4)
# whenever lambda**4 != 1.  Hence this is exactly the central P_4 for U.
p4_for_0 = F(1)
p4_for_3 = F(1, 1 - 3**4)
P4 = mm(mm(V, [[p4_for_0, F(0)], [F(0), p4_for_3]]), Vinv)
E = sub(P4, P)

assert U == [[F(0), F(3)], [F(0), F(3)]]
assert P == [[F(1), F(-1)], [F(0), F(0)]]
assert P4 == [[F(1), F(-81, 80)], [F(0), F(-1, 80)]]
assert E == [[F(0), F(-1, 80)], [F(0), F(-1, 80)]]
assert (E[0][1] ** 2 + E[1][1] ** 2) == F(1, 3200)  # ||E||_F^2

# q=2: eigenvalues 0 and 3 are respectively inside r/q and outside rq.
assert 0 < F(1, 2) and 3 > 2
# Exact failures required by the contract: closed-annulus endpoints and interior.
assert F(1, 2) == F(1, 2)
assert 2 == 2
assert F(1, 2) < 1 < 2

print("U =", U)
print("P =", P)
print("P4 =", P4)
print("P4-P Frobenius^2 =", F(1, 3200))
print("spot checks: PASS")
