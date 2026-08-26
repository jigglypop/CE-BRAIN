# Mathematics

Status: COMPLETE

## GD.1 — affine singular sandwich

For real 2x2 L, `sigma_min(L)^2=det(L)^2/sigma_max(L)^2` and
`sigma_max(L)^2<=||L||_F^2`. Thus `det(L)^2/||L||_F^2` is a lower bound for
the minimum squared singular value, while `||L||_F` upper-bounds the operator
norm. Self-checked dyadic square roots give rational `sigma_L^-` and `S_L^+`.

## GD.2 — defective block split and resolvent

If
`sigma_L^- rho^- > ||(U-cI)P||` and
`S_L^+ rho^+ ||R_Q||<1`, the P block lies in the Euclidean disk contained in
every affine contour and the Q block lies outside the disk containing every
contour. Block Neumann series give

```text
||resolvent|| <= ||P||/g_-^aff + ||R_Q||/g_+^aff.
```

No diagonalization or conformality is required.
