# Mathematics

Status: COMPLETE

## RBRIDGE.1 — sector homotopy cover

For adjacent directions `u0,u1` with angular gap `theta<=pi`, let `u(t)` be the
intermediate unit-circle arc and `F(u)=rho(u)u`.  Define

```text
H_s(t)=(1-s)F(u(t))+s[(1-t)F(u0)+tF(u1)].
```

If `t<=1/2`, use endpoint `u0`; otherwise use `u1`.  The disk Lipschitz bound
`C_rho+` controls the smooth point.  The chord point is controlled by convexity
and `min(t,1-t)||u1-u0||<=2 sin(theta/4)`.  Hence every `H_s(t)` is within

```text
S_L+ C_rho+ h_k+
```

of the same mapped endpoint.  Positive angularly ordered radial vertices with
gaps at most `pi` form a simple oriented polygon; invertible positive-determinant
affine transport preserves this.

## RBRIDGE.2 — Riesz homotopy invariance

The CE-RAD residual margin subtracts exactly the preceding sector cover.  If it
is positive, every smooth arc, polygon chord, and intermediate contour lies in
the common interval-family resolvent set.  Smooth radial and polygon Riesz
projectors, and therefore their ranks, coincide.

## RBRIDGE.3 — numeric rank and projector transfer

Apply verified adaptive polygon midpoint quadrature to the exact raw mapped
vertices.  If its rank interval contains one integer `d`, then `d` is the smooth
radial nominal and family rank, and its polygon projector approximation/error is
also an approximation/error for the identical smooth-contour Riesz projector.
If the finite refinement budget is exhausted, neither output is emitted.
