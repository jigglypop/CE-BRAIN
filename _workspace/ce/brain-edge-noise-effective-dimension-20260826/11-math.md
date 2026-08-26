# Mathematics

Status: COMPLETE

## EN.1 — fixed-forcing response candidate

For fixed `Q>=0`, define `C_Q(b)=A(b)^-1 Q A(b)^-1`,
`G_Q=M C_Q M^T`, and the usual ridge trace `d_{lambda,Q}`.

## EN.2 — commuting theorem

If `A0,Q,H_1,...,H_E` are pairwise commuting real symmetric matrices, simultaneous
diagonalization gives `C_Q=Q A^-2`. Coordinatewise edge strengthening therefore
decreases `C_Q`, `G_Q`, and ridge dimension. For edge `e`,

`partial_e d = -2 lambda ||(QH_e)^(1/2) A^(-3/2) M^T (G_Q+lambda I)^-1||_HS^2 <= 0`.

The entire edge box lies in `[4,6]` iff its strengthened endpoint is at least four
and its weakened endpoint is at most six.

## EN.3 — noncommuting complete counterexample

Use `A0=diag(2,1)`, `H=diag(1,0)`,
`Q=[[1,-9/10],[-9/10,1]]`, and `M=[1,1]`. Although `H>=0`, `QH!=HQ` and edge
strengthening `b:0->1` gives `G_Q:7/20->23/45`. At `lambda=1`, ridge dimension
increases `7/27->23/68` by `145/1836`; the initial derivative is `80/729>0`.
Thus unconditional arbitrary-noise monotonicity is false.
