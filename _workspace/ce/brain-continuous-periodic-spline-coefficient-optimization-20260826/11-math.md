# Mathematics

Status: COMPLETE

## CF.1 — coefficient-vector automatic junction

Let `m=q+1`, let the certified base bump satisfy `0<=b_k<=4` and vanish to
order at least `m` at both endpoints, and choose distinct powers `p_r>=m`:

```text
rho_k = 1 + sum_r a_kr b_k^p_r,   a_kr >= 0.
```

Every nonconstant term vanishes through derivative order `q`, so all patches
share endpoint jet `(1,0,...,0)` uniformly over coefficients and moving knots.

## CF.2 — exact continuous box optimum

The sufficient radial constraint is

```text
sum_r 4^p_r a_kr <= rho_cap-1
```

for every patch.  Starting at the lower corner, fill modes in decreasing order
of `w_kr/4^p_r`, clipping the final mode to the remaining capacity.  The standard
exchange argument proves the resulting continuous bounded-knapsack solution is
globally optimal.  Patch separability proves global optimality of their product.

The selected whole subbox has exact rational radial and gradient bounds using
weights `4^p_r` and `p_r 4^p_r`.
