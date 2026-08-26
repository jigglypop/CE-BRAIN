# Mathematics

Status: COMPLETE

## GA.1 — complete QR coordinates for affine ellipses

Let `Q(t)=[p(t),p_perp(t)] in SO(2)` be the stereographic frame and

```text
R(a,b,s) = [[a,s],[0,b]],  a>0, b>0.
L = Q R.
```

Then `det(L)=ab>0`.  Conversely every real 2x2 matrix with positive determinant
has a positive-diagonal QR factorization of this form.  The simultaneous sign of
both disk-image axes is geometrically redundant, so the stereographic undirected
orientation convention is sufficient.  The certificate applies to the supplied
compact coordinate box, not an unbounded parameter space.

## GA.2 — exact shear margin

In rotated coordinates `(xi,eta)=Q^T(lambda-c)`, triangular inversion gives

```text
L^-1(lambda-c) = ((b xi-s eta)/(ab), eta/b).
```

Therefore

```text
g_aff = a^2 b^2 - (b xi-s eta)^2 - a^2 eta^2
```

is positive exactly inside the affine ellipse and negative exactly outside.  At
`s=0` it reduces coefficientwise to the orthogonal-axis margin.  Positive frozen
label margin excludes the contour spectrum and exact diagonalization yields the
oblique Riesz projector.

## GA.3 — six-variable outward enclosure

Using stereographic numerator coordinates, the invariant score is

```text
[d^2 a^2 b^2-(b xi_hat-s eta_hat)^2-a^2 eta_hat^2]/d^2.
```

On a center/axes/shear/orientation cell, four-endpoint signed multiplication,
sign-aware squaring, subtraction, and positive denominator division form an
outward enclosure.  It need not be the minimal range.  The rational natural
extension converges on compact cells because `d^2>=1`.  The incumbent/global
upper sandwich and exact six-axis bisection therefore certify `eta`-global
optimality when the requested gap is reached; budget exhaustion refuses.

## GA.4 — dimensions and selected geometry

Center, `a,b,s`, and eigenvalues share one spectral unit and are normalized by the
same positive reference scale.  `t`, normalized axes/shear, determinant, inverse
coordinates, margin and tolerance are dimensionless.  The selected exact axes
are emitted and their determinant is checked equal to `ab>0`.
