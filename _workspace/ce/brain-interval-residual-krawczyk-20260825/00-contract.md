# Componentwise residual/Krawczyk interval-contour contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-interval-induced-norm-tightening-20260825`

## 1. Objective

Global uncertainty norms can reject a structured box whose uncertainty lies
in components weakly coupled to the selected contour. This successor uses one
declared exact rational approximate inverse $B_k$ at each of the four contour
nodes and a componentwise interval residual to certify the whole family.

The route is Krawczyk-like/Banach-residual finite matrix analysis. It does not
construct approximate inverses from data, calibrate uncertainty coverage, or
open a neural matrix.

## 2. Frozen inputs

Retain the predecessor exact nominal $U_0\in\mathbb Q(i)^{n\times n}$,
rectangular radii $a,b$, center $c$, radius $r$, scale $s_*$, normalize-first
rule, four exact directions $d_k\in\{1,i,-1,-i\}$, and optional nominal strip
witness.

Supply exactly four nonempty shape-matched matrices
$B_k\in\mathbb Q(i)^{n\times n}$. They are witnesses, not trusted inverses;
every residual is checked. Binary floats, Python complex values, wrong counts,
and shape mismatch are rejected.

For normalized nominal node matrices

$$
A_{0k}=(\widetilde c+\widetilde r d_k)I-\widetilde U_0,
$$

let exact outward entry magnitudes $D_{ij}^+$ satisfy
$|\widetilde\Delta_{ij}|\le D_{ij}^+$ for the whole uncertainty box.

## 3. K1 candidate: componentwise residual contraction

Compute the exact rational-complex residual

$$
R_k=I-B_kA_{0k}.
$$

For any family member $A_k=A_{0k}-\widetilde\Delta$,

$$
I-B_kA_k=R_k+B_k\widetilde\Delta.
$$

Using exact outward magnitude matrices, define

$$
G_k^+=|R_k|^+ + |B_k|^+D^+,
$$

where the product is ordinary nonnegative matrix multiplication. Then

$$
q_{1k}^+=\|G_k^+\|_1,\qquad
q_{\infty k}^+=\|G_k^+\|_\infty.
$$

Only $q_{1k}^+<1$ and $q_{\infty k}^+<1$ may pass. Equality is a
non-certificate.

## 4. K2 candidate: node inverse and full-circle bounds

Let outward induced uppers for $B_k$ be

$$
\beta_{1k}^+=\||B_k|^+\|_1,\qquad
\beta_{\infty k}^+=\||B_k|^+\|_\infty.
$$

Banach's lemma gives uniformly over the family

$$
\|A_k^{-1}\|_1\le
M_{1k}^+:=\frac{\beta_{1k}^+}{1-q_{1k}^+},\qquad
\|A_k^{-1}\|_\infty\le
M_{\infty k}^+:=\frac{\beta_{\infty k}^+}{1-q_{\infty k}^+}.
$$

With an exact dyadic upper
$M_{2k}^+\ge\sqrt{M_{1k}^+M_{\infty k}^+}$,

$$
\sigma_{\min}(A_k)\ge(M_{2k}^+)^{-1}=:\ell_k.
$$

Use the predecessor's exact four-node chord upper
$\widetilde\chi^+\ge\widetilde r\sqrt{2-\sqrt2}$ and require

$$
\underline{\widetilde\delta}_{\rm res}
=\min_k\ell_k-\widetilde\chi^+>0.
$$

Then every matrix in the uncertainty family is resolvent-free on the entire
circle with common upper
$\overline{\widetilde R}_{\rm res}=
\underline{\widetilde\delta}_{\rm res}^{-1}$ and a common enclosed Riesz rank.

## 5. K3 candidate: family projector motion

The predecessor tightening always supplies a rigorous global operator upper
$\widetilde\varepsilon_*^+$, even if its own contour margin failed. Because
both $U$ and $U_0$ are covered by the residual full-circle resolvent bound,

$$
\|P(U)-P(U_0)\|_2
\le\widetilde r\,\widetilde\varepsilon_*^+
\overline{\widetilde R}_{\rm res}^{,2}
=:\rho_{P,\rm res}^+.
$$

If the independent nominal analytic-strip certificate supplies $\eta_4^+$,
then

$$
\|P(U)-P_4(U_0)\|_2
\le\rho_{P,\rm res}^++\eta_4^+.
$$

K3 may be conservative even when K1/K2 are structurally sharp. K1/K2 rank
certification does not depend on K3 being small.

## 6. Required outputs and statuses

Expose the complete predecessor tightening result; normalized uncertainty
entry brackets; every parsed $B_k$; $|B_k|^+$ and $|R_k|^+$ brackets/checks;
$G_k^+$; both $q$ values; both $\beta$ and $M$ values; every inverse-2 bracket
and node lower; chord brackets/checks; robust normalized/raw separation and
resolvent; rank Boolean; K3 bound; optional quadrature and total bound; scale
and precision.

Positive statuses are
`VERIFIED_RATIONAL_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE` and optional
`VERIFIED_RATIONAL_COMPONENTWISE_RESIDUAL_PROJECTOR_BRIDGE`. Named failures
are node contraction unavailable and residual full-circle lower nonpositive.

## 7. Required adverse and improvement controls

- exact inverse witnesses with zero nominal residual;
- inexact rational witnesses with nonzero residual that still pass;
- zero/identity/wrong-shape/wrong-count witness failures;
- $q_1=1$, $q_\infty=1$, and values above one;
- a structured far-eigenvalue uncertainty box where global tightening fails
  but the componentwise residual route passes without changing the box;
- a nonnormal nominal example;
- nonpositive chord-corrected lower despite passing nodes;
- normalize-first exact unit invariance;
- optional projector success and nominal-strip failure;
- all binary-float/Boolean/negative uncertainty adversaries.

## 8. Claim ceiling

K1--K3 may reach conditional finite theorem and exact-apparatus status. They
prove uniform statements for the declared interval family and witnesses only.
They do not prove experimental interval coverage, infer a neural transition,
select a rank from data, validate brain geometry, identify consciousness, or
privilege dimensions 4--6. Failure is inconclusive.

## 9. Execution order

Prove Banach and full-circle steps, audit strict inequalities and structured
controls, implement separately without modifying predecessors, validate one
focused and adjacent chain, then update canonical documents after final gate.
