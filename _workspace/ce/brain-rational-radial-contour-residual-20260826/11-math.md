# Mathematics

Status: COMPLETE

## RAD.1 — positive radial Jordan geometry

Let `rho(u)=r0+p.u` on the unit circle and let `p*+` be an outward dyadic upper
bound for `||p||_2`.  If

```text
r0-p*+ > 0,   det(L)>0,
```

then `rho` is strictly positive.  Distinct polar directions cannot map to the
same nonzero radial point.  Moreover

```text
d[rho(u)u]/dtheta = rho'(u)u + rho(u)u_perp,
```

whose orthogonal components cannot vanish simultaneously because `rho>0`.
An invertible orientation-preserving `L` therefore gives an injective, regular,
positively oriented smooth star-shaped Jordan contour.

## RAD.2 — whole-contour Lipschitz cover

Extend `F(u)=rho(u)u` to the closed unit disk.  There

```text
DF(u)=rho(u)I+u p^T,
||DF(u)||_2 <= r0+2||p||_2 <= C_rho+ := r0+2p*+.
```

Because the disk is convex, `F` is `C_rho+`-Lipschitz.  If `S_L+` bounds
`||L||_2` and `h_max+` is the rational mesh chord cover, every smooth contour
point is within

```text
chi_R+ = S_L+ C_rho+ h_max+
```

of a mapped node.

## RAD.3 — residual and rank preservation

For certified node residual lower bounds `ell_k`, require

```text
delta_R = min_k ell_k - chi_R+ > 0.
```

Then every point on the smooth radial contour is in the resolvent set of every
matrix in the connected certified interval family.  The nominal Riesz rank is
therefore constant throughout that family.

## RAD.4 — projector perturbation

The angular speed is at most `S_L+ C_rho+`, so the contour length is at most
`2*pi*S_L+*C_rho+`.  If `D2+` bounds the matrix perturbation and
`R=1/delta_R`, the resolvent identity gives

```text
||P_R(A)-P_R(A0)||_2 <= S_L+ C_rho+ D2+ R^2.
```

For `p=0`, every node and bound reduces exactly to the affine-ellipse route with
axes scaled by `r0`.
