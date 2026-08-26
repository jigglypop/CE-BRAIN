# Mathematics

Status: COMPLETE

## MKINT.1 — uniform Neumann bridge

Let `||E||_F<=epsilon^+` in normalized spectral units and let MKRES supply
`R^+` on every moving contour. If `nu^+=R^+ epsilon^+<1`, then for every
`t in [0,1]`, contour point, and knot-box member,

```text
zI-(U~+tE) = [I-tE(zI-U~)^-1](zI-U~)
```

is invertible and the perturbed resolvent norm is at most
`R^+/(1-nu^+)`. Frobenius dominates operator norm. Equality is insufficient.

## MKINT.2 — rank preservation

The path `tE` is connected and every supplied contour remains in the resolvent
set along it. Riesz projector rank is integer-valued and continuous, hence is
constant and equals the nominal inside-label count throughout the ball and knot
box.

## MKINT.3 — projector perturbation

The radial map has Lipschitz upper `C_spl^+`; therefore
`length/(2pi)<=||L||_F^+ C_spl^+`. The resolvent identity gives

```text
||P(U~+E)-P(U~)||_2
 <= ||L||_F^+ C_spl^+ epsilon^+ (R^+)^2/(1-nu^+).
```

The affine Frobenius upper is obtained by a self-checked outward dyadic square
root. Every core quantity is dimensionless after the common spectral scaling.
