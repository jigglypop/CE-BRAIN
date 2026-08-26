# Mathematics

Status: COMPLETE

## DC.1 — defective conformal split

Let the contour frame be multiplication by an exact rotation and positive scale
`s`. Let `P^2=P`, `PU=UP`, `Q=I-P`, and let `R_Q` be the complement-supported
two-sided inverse of `Q(U-cI)Q`. Put

```text
g_-=s rho^- - ||(U-cI)P||_2^+,
g_+=1-s rho^+ ||R_Q||_2^+.
```

If both are positive, the P-block spectral radius is below `s rho^-`; the
inverse Q-block spectral radius is below `||R_Q||`, so every Q eigenvalue has
modulus above `s rho^+`. This does not require diagonalization and admits Jordan
blocks. Every moving contour therefore has exact Riesz projector P and rank
`trace(P)`.

## DC.2 — algebraic resolvent

With `p^+=||P||_2^+`, block Neumann series give

```text
sup ||(zI-U)^-1||_2 <= p^+/g_- + ||R_Q||_2^+/g_+.
```

The projector norm is retained because the invariant splitting may be oblique.

## DC.3 — ceiling

The proof uses complex multiplication by a conformal frame. A general real
shear is not a holomorphic scalar map and is not covered. The projector and
inverse are exact supplied witnesses, though eigenvectors are not required.
