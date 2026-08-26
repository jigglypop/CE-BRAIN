# Mathematics

Status: COMPLETE

## CA.1 — algebraic sufficient objective

For fixed exact projector `P`, complement `Q`,

```text
A(c)=(U-cI)P,
R(c)=Q[P+Q(U-cI)Q]^(-1)Q,
Phi_alg(c,r)=min(r^2-||A(c)||_F^2, 1-r^2||R(c)||_F^2).
```

Positive `Phi_alg` implies `||A||_2<r` and `||R||_2<1/r`, hence the strict
algebraic Riesz gates without diagonalization.

## CA.2 — uniform center domain

If every center is within `H` of reference `c0` and
`H ||R(c0)||_F^+ < 1`, Neumann inversion proves the exterior block is invertible
throughout the box.

## CA.3 — cell upper and global optimum

For center displacement `h` from a cell midpoint,

```text
a_lower=max(0, ||A0||_F^- - h||P||_F^+),
Delta_R <= h(b_plus)^2/(1-h b_plus),
b_lower=max(0, b_minus-Delta_R).
```

Thus the cell objective is at most

```text
min(r_upper^2-a_lower^2, 1-r_lower^2 b_lower^2).
```

The same incumbent/global-upper branch proof supplies eta-global optimality.
Singleton cells use exact Frobenius squares.  The selected exact projector is
recomputed and compared coefficientwise with the reference projector.
