# Mathematics

Status: COMPLETE

## KO.1 — automatic moving-knot Cq family

For directed unit knots `u_k`, nonnegative amplitudes `eps_k`, and `m=q+1`, set

```text
rho_k(u)=1+eps_k(1-u dot u_k)^m(1-u dot u_(k+1))^m.
```

Since `1-cos(h)` has a zero of exact order two, each endpoint factor has order
`2m`; all angular derivatives through `2m-1=2q+1` vanish.  Every left/right patch
therefore shares endpoint jet `(1,0,...,0)` through q for all knot locations.
Nonnegative amplitudes give `rho>=1`.

## KO.2 — exact cyclic knot domain

Fix the anchor `(-1,0)` and parameterize remaining knots by
`u(t)=((1-t^2)/(1+t^2),2t/(1+t^2))`.  Pairwise-disjoint increasing boxes, a
negative first box, positive last box, and positive lower enclosure of every
adjacent determinant preserve directed cyclic order and make every arc shorter
than pi throughout the box.

## KO.3 — global minimax chord spacing

For adjacent knots define `S_k=2+2 u_k dot u_(k+1)` and `Phi=min_k S_k`.
Because endpoint chord squared is `4-S_k`, maximizing Phi minimizes the worst
endpoint chord.  Exact rational dot-product intervals give
`sup_C Phi <= min_k upper(S_k(C))`.  Positive stereographic denominators and
strict compact order make the natural extension convergent.  Branch-and-bound
with `U-L<=eta` certifies an eta-global spacing optimum; budget exhaustion refuses.

## KO.4 — radial and cover bounds

On the unit disk both factors lie in `[0,2]` and have gradient norm at most one.
For `eps=max eps_k`,

```text
1 <= rho <= 1+eps 2^(2m),
|grad rho| <= eps m 2^(2m),
C_spl <= 1+eps(1+m)2^(2m).
```

Every point of a strict minor arc is within the full endpoint chord of an endpoint.
Thus `C_spl` times an outward square root of the selected worst chord squared is a
valid contour-node cover.  This is a geometry theorem and does not establish a
resolvent or Riesz rank.
