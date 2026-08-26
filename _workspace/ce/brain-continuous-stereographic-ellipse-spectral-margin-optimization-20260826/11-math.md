# Mathematics

Status: COMPLETE

## SE.1 — exact continuous orientation chart

For real `t`, set `u=1-t^2`, `v=2t`, and `d=1+t^2>0`.  Then
`u^2+v^2=d^2`, so `p=(u,v)/d` and `p_perp=(-v,u)/d` are an exact positively
oriented orthonormal frame.  Ellipse axes are undirected; the missing limiting
vector `(-1,0)` represents the same axis as `(1,0)` at `t=0`.  Optimization is
nevertheless asserted only over the declared compact finite `t` interval.

## SE.2 — chart-invariant geometric objective

For `delta=lambda-c`, define numerator coordinates

```text
xi_hat  = u Re(delta) + v Im(delta)
eta_hat = -v Re(delta) + u Im(delta).
```

The fixed-frame ellipse margin is exactly

```text
g = (d^2 a^2 b^2 - b^2 xi_hat^2 - a^2 eta_hat^2)/d^2.
```

The denominator is positive, so its numerator has the same sign.  It must not be
used alone as the optimization score: its chart-dependent factor `d^2` changes
objective magnitude with `t`.  Division recovers the same geometric score as
CE-EOPT pointwise.

## SE.3 — five-variable cell enclosure

On `C=Ix x Iy x Ia x Ib x It`, natural exact-rational interval evaluation gives
a numerator enclosure `N_jC` and `D_C` for `d^2`, with `lower(D_C)>=1`.  Taking
the hull of all four endpoint quotients encloses `N_jC/D_C`, including when the
numerator crosses zero.  Label sign and the minimum over eigenvalues yield a
cell upper for every point.  These rational natural extensions are continuous
away from zero denominator, hence converge to point values as all five widths
vanish.  Exact bisection plus `U-L<=eta` certifies tolerance-global optimality;
budget exhaustion produces no claim.

## SE.4 — projector and reductions

Positive selected margin excludes boundary spectrum.  Exact `UV=V Lambda` gives
`P=V diag(labels)V^-1`, checked for idempotence and commutation.  At fixed `t`
the theorem reduces pointwise to CE-EOPT.  When `a=b`, the score reduces to the
orientation-independent circle score.  Spectral values are normalized by one
positive reference scale; `t`, the frame, margin, and tolerance are dimensionless.
