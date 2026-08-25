# Verified componentwise residual/Krawczyk contour bridge

Status: COMPLETE

Date: 2026-08-25

## Abstract

This successor closes the declared residual/Krawczyk candidate. Four exact
rational approximate-inverse witnesses are checked at the contour nodes using
componentwise interval residuals. Strict Banach contractions give uniform node
inverse bounds for every matrix in the declared uncertainty box; the exact
four-node chord then certifies the whole circle, common Riesz rank, and a
projector-motion bound. A structured box rejected by the global uncertainty
route is certified without changing the box because its large uncertainty lies
in a distant spectral component. Focused validation passed 14 tests, four-stage
integration 53, and the dimensionless gate 23. No empirical interval coverage
or neural matrix is provided.

## 1. Componentwise contraction

At normalized node
$A_{0k}=(\widetilde c+\widetilde r d_k)I-\widetilde U_0$, supply a rational
witness $B_k$ and compute rather than assume

$$
R_k=I-B_kA_{0k}.
$$

For $A_k=A_{0k}-\widetilde\Delta$,

$$
I-B_kA_k=R_k+B_k\widetilde\Delta.
$$

If $D^+$ encloses the uncertainty entry magnitudes, outward arithmetic gives

$$
G_k^+=|R_k|^++|B_k|^+D^+,\qquad
q_{1k}^+=\|G_k^+\|_1,\qquad
q_{\infty k}^+=\|G_k^+\|_\infty.
$$

Only $q_{1k}^+<1$ and $q_{\infty k}^+<1$ pass. Equality is unsafe: scalar
$A_0=B=1$ with radius-one uncertainty contains $A=0$.

## 2. Banach inverse and full circle

The Neumann series for $B_kA_k=I-(I-B_kA_k)$ gives

$$
M_{1k}^+=\frac{\||B_k|^+\|_1}{1-q_{1k}^+},\qquad
M_{\infty k}^+=\frac{\||B_k|^+\|_\infty}{1-q_{\infty k}^+}.
$$

With an outward square-root upper

$$
M_{2k}^+\ge\sqrt{M_{1k}^+M_{\infty k}^+},\qquad
\ell_k=(M_{2k}^+)^{-1},
$$

every family member satisfies
$\sigma_{\min}(A_k)\ge\ell_k$. Consequently

$$
\underline{\widetilde\delta}_{\rm res}
=\min_k\ell_k-\widetilde\chi^+>0
$$

certifies the whole circle and
$\overline{\widetilde R}_{\rm res}=
\underline{\widetilde\delta}_{\rm res}^{-1}$. The convex interval family then
has one common enclosed Riesz rank.

## 3. Structured improvement

For

$$
U_0=\operatorname{diag}(0,10),\qquad |\Delta_{22}|\le1,
$$

on the unit circle, the global operator uncertainty upper is one and exhausts
the predecessor margin. At $z=1$, however,

$$
A_0=\operatorname{diag}(1,-9),\qquad
B=A_0^{-1}=\operatorname{diag}(1,-1/9),\qquad
G^+=\operatorname{diag}(0,1/9).
$$

The distant uncertain component contracts. All four exact rational nodes and
the chord pass in the executable fixture, while the preserved predecessor
result remains a non-certificate. This is structural improvement, not an
altered uncertainty claim.

## 4. Projector bound

Using the predecessor's always-rigorous selected global error upper only in
the resolvent identity gives

$$
\|P(U)-P(U_0)\|_2
\le\widetilde r\,\widetilde\varepsilon_*^+
\overline{\widetilde R}_{\rm res}^{\,2}
=\rho_{P,\rm res}^+.
$$

With a separate passing nominal strip,

$$
\|P(U)-P_4(U_0)\|_2\le\rho_{P,\rm res}^++\eta_4^+.
$$

Rank certification depends on the positive residual circle, not on this
projector bound being numerically small.

## 5. Implementation, evidence, and ceiling

`verified_interval_residual.py` exposes each witness, exact residual,
magnitude brackets and checks, interval residual matrix, both contractions,
Banach inverse bounds, node lowers, chord checks, robust outputs, rank flag,
and optional projector terms. Inexact rational witnesses can pass when their
checked residuals contract; exact identity is not assumed.

- focused residual behavior: 14/14;
- four-stage adjacent integration: 53/53;
- dimensionless gate: 23/23;
- exact theorem fixture: PASS;
- research final gate: pending this report, checked next.

This closes the finite componentwise residual route. Weighted/block norms and
a frozen witness-construction rule are possible optimizations. Experimental
coverage of the interval box, actual neural matrices, Allen metadata, nonlinear
brain dynamics, consciousness, and dimensions 4--6 remain outside the result.

## Reproducibility record

- Contract: `00-contract.md`
- Proofs and counterexamples: `11-math.md`
- Alternative routes/falsifiers: `12-routes.md`
- Stable audit: `20-audit.md`
- Implementation: `30-implementation.md`
- Validation: `31-validation.md`
