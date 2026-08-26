# Mathematics

Status: COMPLETE

## EBRIDGE.1 — sector cover

For a unit-circle mesh gap `theta<=pi`, let `u_arc(t)` be angular interpolation and
`u_lin(t)` its chord interpolation.  Choose the left endpoint for `t<=1/2` and the
right endpoint otherwise.  Then

```text
distance(u_arc, endpoint) <= h = 2 sin(theta/4),
distance(u_lin, endpoint) <= sin(theta/2) <= h.
```

Every convex interpolation `u_s=(1-s)u_arc+s u_lin` obeys the same bound.  The
affine ellipse image is therefore within `S_L+ h+` of the mapped endpoint.

## EBRIDGE.2 — contour homotopy

The predecessor ellipse residual margin subtracts exactly the maximum affine
sector cover.  If it is positive, every contour in the ellipse-to-polygon homotopy
is resolvent-free for every admitted matrix.  Homotopy invariance gives equality of
the smooth ellipse and inscribed polygon Riesz projectors and ranks.

## EBRIDGE.3 — numeric rank and projector

If adaptive polygon quadrature isolates rank `r` and returns approximation
`P_hat` with error `E_P+`, the ellipse has the same nominal and family rank and

```text
||P_ellipse(A0)-P_hat||_2 <= E_P+.
```

An exhausted polygon budget leaves the smooth rank unresolved even though the
ellipse residual and sector homotopy may be verified.
