# Mathematics

Status: COMPLETE

## MK.1 — simple moving radial family

For every knot-box member kappa, CE-KOPT gives a periodic Cq function with
`0<rho^-<=rho_kappa(u)<=rho^+`.  The map `u -> rho_kappa(u)u` is injective on
the unit circle because positive radial multiples on distinct rays cannot agree.
An invertible orientation-preserving affine map preserves the simple Jordan
property and its star-shaped interior.

## MK.2 — uniform annulus split

For exact normalized eigenvalue `lambda_j`, center c, and affine axes L, put
`r_j^2=|L^-1(lambda_j-c)|^2`.  Define

```text
m_j = (rho^-)^2-r_j^2 for an inside label,
      r_j^2-(rho^+)^2 for an outside label.
```

If `min_j m_j>0`, every inside eigenvalue is inside every moving contour and
every outside eigenvalue is outside every contour.  Equality is insufficient.
The proof uses the uniform envelope and therefore does not depend on a patch
assignment or finite knot sampling.

## MK.3 — exact common Riesz rank

Exact invertible `V` and `UV=V Lambda` give
`P=V diag(labels)V^-1`.  By MK.2 no family contour intersects the spectrum, and
the same labeled eigenvalues lie inside each one.  Hence every contour has exact
Riesz projector P and rank equal to the inside-label count.  This proves
resolvent existence, not a quantitative operator-norm bound.  It also concerns
the exact nominal matrix, not an interval-valued matrix family.

## MK.4 — dimensions

Matrix, eigenvalues, center, and affine axes share one spectral unit and are
normalized together.  Affine inverse-coordinate squared radii, radial bounds,
signed squared margins, projector entries, and rank are dimensionless.
