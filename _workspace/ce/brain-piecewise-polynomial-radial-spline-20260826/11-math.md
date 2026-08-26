# Mathematics

Status: COMPLETE

## SPLRAD.1 — periodic Cq junction theorem

Let patch `rho_k` apply on the arc from rational direction `u_k` to `u_{k+1}`.
For `T=-u_2 partial_1+u_1 partial_2`, require exactly

```text
(T^j rho_{k-1})(u_k)=(T^j rho_k)(u_k),  j=0,...,q,  q>=1.
```

Since `T` is angular differentiation on the unit circle and maps polynomials to
polynomials, these finite rational equalities prove periodic Cq compatibility.
Strict positivity gives injectivity, and the C1 polar derivative cannot vanish.

## SPLRAD.2 — patchwise global cover

For every patch use

```text
C_k+=r0_k+2||p_k||_2^+ + A0_k + A1_k,
```

with the same coefficient/degree sums as the global-polynomial theorem.  Then
`C_spl+=max_k C_k+` bounds every sector map.  The affine knot cover is
`S_L+ C_spl+ h_max+` and the length is at most `2*pi*S_L+*C_spl+`.

## SPLRAD.3 — residual and projector perturbation

If the minimum knot residual lower minus the global cover is positive, every
patch and knot is inside the common interval-family resolvent set.  The family
Riesz rank is preserved and the projector perturbation is at most

```text
S_L+ C_spl+ D2+ R^2.
```

## SPLRAD.4 — numeric rank transfer

On each sector, the smooth patch arc, knot chord, and their convex homotopy share
the same Lipschitz endpoint cover.  Therefore the knot polygon has the identical
Riesz projector.  A verified singleton polygon rank and projector error transfer
unchanged; finite budget exhaustion emits neither.
