# Componentwise residual/Krawczyk contour mathematics

Status: COMPLETE

## K1 -- uniform residual contraction

At node $k$, write $A=A_{0k}-\widetilde\Delta$ and
$R_k=I-B_kA_{0k}$. Then exactly

$$
I-B_kA=R_k+B_k\widetilde\Delta.
$$

If $D^+$ bounds $|\widetilde\Delta|$ entrywise, outward magnitude arithmetic
gives

$$
|I-B_kA|le |R_k|+|B_k||\widetilde\Delta|
\le |R_k|^+ + |B_k|^+D^+=G_k^+.
$$

Monotonicity of nonnegative row and column sums therefore proves

$$
\|I-B_kA\|_1\le q_{1k}^+:=\|G_k^+\|_1,\qquad
\|I-B_kA\|_\infty\le q_{\infty k}^+:=\|G_k^+\|_\infty.
$$

This is uniform over every matrix in the rectangular box and does not assume
that $B_k$ is an inverse.

## K2 -- Banach inverse and circle theorem

Let $E=I-B_kA$. If $q_p^+<1$ for $p\in\{1,\infty\}$, the Neumann series

$$
(B_kA)^{-1}=(I-E)^{-1}=\sum_{m=0}^{\infty}E^m
$$

converges in the induced $p$-norm and has norm at most $(1-q_p^+)^{-1}$.
Thus $B_kA$ is invertible; in finite square dimension both $B_k$ and $A$ are
invertible. Since $A^{-1}=(B_kA)^{-1}B_k$,

$$
\|A^{-1}\|_p\le\frac{\|B_k\|_p}{1-q_p^+}
\le M_{pk}^+.
$$

Using $\|X\|_2^2\le\|X\|_1\|X\|_\infty$ gives

$$
\|A^{-1}\|_2\le
\sqrt{M_{1k}^+M_{\infty k}^+}\le M_{2k}^+,
\qquad
\sigma_{\min}(A)\ge\ell_k:=(M_{2k}^+)^{-1}.
$$

Every $\ell_k$ is uniform over the family. For an arbitrary point $z$ on the
circle, choose its nearest four-node sample $z_k$. Since smallest singular
value is 1-Lipschitz in the scalar shift,

$$
\sigma_{\min}(zI-\widetilde U)
\ge\ell_k-|z-z_k|
\ge\min_j\ell_j-\widetilde\chi^+.
$$

Therefore a positive
$\underline{\widetilde\delta}_{\rm res}=\min_j\ell_j-
\widetilde\chi^+$ proves the full-circle family certificate and common
resolvent upper. The uncertainty box is convex, so the segment from $U_0$ to
any member remains certified. Continuity and integer-valued Riesz rank imply
one common enclosed rank.

## K3 -- projector perturbation

Let $\overline{\widetilde R}_{\rm res}$ be the uniform family resolvent upper
and $\widetilde\varepsilon_*^+$ any rigorous global operator bound supplied by
the predecessor. Both $U$ and $U_0$ lie in the family, so the resolvent identity
and circle length give

$$
\|P(U)-P(U_0)\|_2
\le\widetilde r\,\widetilde\varepsilon_*^+
\overline{\widetilde R}_{\rm res}^{,2}.
$$

Adding an independent nominal quadrature bound $\eta_4^+$ gives the contract's
total bound by triangle inequality.

## Strictness and complete counterexamples

For scalar $A_0=B=1$ and uncertainty $|\Delta|\le1$, the nominal residual is
zero but $q=1$. The family includes $A=0$, so allowing equality would certify
a singular matrix. Both `q<1` tests are therefore strict.

Passing node contractions does not imply a positive full-circle result. A
coarse node lower can be smaller than the four-node chord; the correct status
is a nonpositive conservative lower, not a spectral crossing.

## Structured improvement witness

Take

$$
U_0=\operatorname{diag}(0,10),\qquad
|\Delta_{22}|\le1,\qquad \Delta_{ij}=0\text{ otherwise},
$$

and the unit circle centered at zero. The global operator uncertainty upper is
one, which exceeds the predecessor nominal four-node margin and forces its
non-certificate. At $z=1$, however,

$$
A_0=\operatorname{diag}(1,-9),\qquad
B=A_0^{-1}=\operatorname{diag}(1,-1/9),\qquad
G^+=\operatorname{diag}(0,1/9).
$$

Thus both contractions are $1/9<1$. The analogous other three exact rational
node inverses contract as well; uncertainty in the distant second eigenvalue
is suppressed by its local inverse factor. The full implementation fixture
checks that the chord-corrected residual route passes on this unchanged box.

## Dimension and scale audit

After normalization, $A,B,R,D,G,q,M$ and node singular bounds are all
dimensionless. In raw units $A$ has spectral unit and an inverse witness has
reciprocal spectral unit; normalization converts their product to
dimensionless form. Raw separation has spectral unit, raw resolvent reciprocal
spectral unit, and $r\varepsilon R^2$ is dimensionless. Normalize-first
outward magnitude brackets preserve exact common-unit rescaling invariance.

## Status audit

- P0/P1: none under the finite exact-witness hypotheses.
- P2: induced row/column contractions can remain conservative; a block or
  weighted norm is a future optimization, not an automatic fallback.
- Statistical coverage and witness construction from experimental estimators
  remain open and cannot inherit K1--K3 status.
