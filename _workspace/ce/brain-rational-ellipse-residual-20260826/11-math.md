# Mathematics

Status: COMPLETE

## ELL.1 — smooth Jordan geometry

For exact complex columns `a,b`, let `L=[a b]` as a real 2x2 matrix and require
`d=det(L)>0`.  Then

```text
gamma(u)=c+a*u_1+b*u_2,   ||u||_2=1
```

is the regular injective image of the unit circle and hence a positively oriented
smooth Jordan ellipse.

## ELL.2 — exact operator-norm cover

With `tau=|a|^2+|b|^2` and `Delta=tau^2-4d^2`,

```text
||L||_2 = sqrt((tau+sqrt(Delta))/2).
```

Nested dyadic outward roots give `||L||_2<=S_L+`.  If the rational unit mesh has
maximum nearest-node chord `h+`, every ellipse point is within `S_L+ h+` of a
mapped node.

## ELL.3 — residual and rank

If node residual lowers satisfy

```text
delta_E = min_k ell_k - S_L+ h+ > 0,
```

the entire ellipse is in the resolvent set for every matrix in the certified box.
The connected family therefore preserves the nominal Riesz rank.

## ELL.4 — projector perturbation

Because `length(E)<=2*pi*S_L+`, the resolvent identity gives

```text
||P_E(A)-P_E(A0)||_2 <= S_L+ D2+ (1/delta_E)^2.
```
