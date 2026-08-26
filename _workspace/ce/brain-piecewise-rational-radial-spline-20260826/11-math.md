# Mathematics

Status: COMPLETE

## RSPLRAD.1 — pole exclusion and quotient Cq jets

For `rho_k=N_k/D_k`, coefficient-sum receipts require

```text
0<N_k^-<=N_k<=N_k^+,   0<D_k^-<=D_k<=D_k^+
```

on the whole unit disk.  Thus no patch has a pole and `rho_k>0`.  With angular
derivatives `N_j=T^jN`, `D_j=T^jD`, quotient jets follow exactly from

```text
rho_n=(N_n-sum_{j=1}^n binom(n,j)D_j rho_{n-j})/D_0.
```

Equality of left/right jets through supplied finite `q>=1` proves periodic Cq
compatibility and regular positive radial Jordan geometry.

## RSPLRAD.2 — quotient Lipschitz cover

If `G_N^+,G_D^+` bound the polynomial gradients, then

```text
rho<=N^+/D^-,
||grad rho||<=G_N^+/D^- + N^+G_D^+/(D^-)^2.
```

Their sum `C_rat,k+` bounds `D(rho(u)u)` on each patch.  The maximum over patches
gives affine cover `S_L+ C_rat+ h_max+` and length bound
`2*pi*S_L+*C_rat+`.  Constant denominator one reduces exactly to the polynomial
receipt.

## RSPLRAD.3 — residual, rank, and projector perturbation

A positive knot-residual-minus-global-cover margin places every patch in the
common interval-family resolvent set.  Family rank is preserved and projector
perturbation is at most `S_L+ C_rat+ D2+ R^2`.

## RSPLRAD.4 — numeric rank/projector transfer

Each rational patch has the certified disk Lipschitz bound required by the sector
arc-to-chord homotopy.  The knot polygon therefore has the same Riesz projector.
A singleton adaptive polygon rank and projector error transfer unchanged;
exhaustion emits neither.
