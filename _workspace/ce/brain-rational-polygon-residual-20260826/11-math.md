# Mathematics

Status: COMPLETE

## RPOLY.1 — exact Jordan geometry

For unique cyclic rational vertices `v_0,...,v_(N-1)`, require positive signed
double area, no intersection or touching between nonadjacent edges, and no
collinear reversal between adjacent edges.  Forward collinear subdivision is
allowed.  These conditions give a positively oriented simple polygonal Jordan
contour.

## RPOLY.2 — edge cover

Let `L_k+` outwardly bound the length of edge `[v_k,v_(k+1)]`.  Every point of
that edge is within `L_k+/2` of its nearer endpoint.  If residual certificates
give endpoint singular-value lowers `ell_k`, define

```text
delta_k = min(ell_k,ell_(k+1)) - L_k+/2,
delta_polygon = min_k delta_k.
```

Strict positivity implies a uniform resolvent bound `R+=1/delta_polygon` on the
entire polygon.

## RPOLY.3 — rank preservation

For every admitted perturbation `D`, the path `A(t)=A0+tD` remains contour-free.
The Riesz projector varies continuously along this path, while its finite rank is
integer-valued.  Hence the rank equals the nominal polygonal Riesz rank throughout
the interval family.

## RPOLY.4 — projector perturbation

With normalized perimeter upper `L+`, selected matrix uncertainty `D2+`, and
uniform resolvent upper `R+`, the resolvent identity yields

```text
||P(A)-P(A0)||_2 <= (L+/(2*pi)) D2+ (R+)^2
                   < (L+/6) D2+ (R+)^2.
```

The final expression is an exact rational-compatible outward bound.
