# Interval-valued measured-matrix contour bridge contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-verified-contour-enclosure-20260825`

## 1. Objective and scope

The predecessor certifies a declared exact rational nominal matrix but leaves
open the bridge to an unknown matrix known only through entrywise uncertainty.
This run asks for a rigorous finite-dimensional perturbation certificate for
the entire declared rectangular uncertainty family.

The target is finite matrix analysis and exact rational apparatus only. No
experimental matrix, Allen response, neural signal, covariance estimate, or
uncertainty calibration is supplied in this run. A positive result therefore
certifies a user-declared interval family, not the empirical truth of its
bounds and not a brain, consciousness, or dimension claim.

## 2. Frozen predecessor evidence

The nominal input uses the predecessor's exact four-node rational full-circle
certificate. Its normalized lower separation
`nominal.normalized_delta_lower` is denoted
$\underline{\widetilde\delta}_0>0$. Existing float64 estimate APIs and their
labels remain unchanged.

The optional nominal approximation route uses the predecessor's exact
diagonal-witness strip certificate and its central four-node approximation
bound $\eta_4^+\ge\|P_4(U_0)-P(U_0)\|_2$.

## 3. Exact uncertainty input

Let $U_0\in\mathbb Q(i)^{n\times n}$ be the declared nominal matrix and
$s_*>0$ the same spectral reference scale used by the nominal certificate.
For every entry, accept exact nonnegative rational rectangular radii
$a_{ij},b_{ij}$ and define the family

$$
\mathcal U(U_0;a,b)=\left\{U_0+\Delta:
|\Re\Delta_{ij}|\le a_{ij},\quad
|\Im\Delta_{ij}|\le b_{ij}\right\}.
$$

The uncertainty matrix must be nonempty, square, and exactly shape-matched to
$U_0$. Binary floats, Python complex bounds, Booleans, negative values,
missing pairs, and noncanonical strings are rejected. The center and radius
are fixed; uncertainty in the contour itself is out of scope.

Normalize before every dyadic enclosure:

$$
\widetilde a_{ij}=a_{ij}/s_*,\qquad
\widetilde b_{ij}=b_{ij}/s_*,\qquad
\widetilde S=\sum_{ij}(\widetilde a_{ij}^2+\widetilde b_{ij}^2).
$$

An exact dyadic upper enclosure $\widetilde\varepsilon^+$ must satisfy
$(\widetilde\varepsilon^+)^2\ge\widetilde S$. Then every admitted matrix has

$$
\|\widetilde\Delta\|_2\le
\|\widetilde\Delta\|_F\le\sqrt{\widetilde S}le
\widetilde\varepsilon^+.
$$

The raw error upper is derived afterward as
$\varepsilon^+=s_*\widetilde\varepsilon^+$. Simultaneously rescaling
$U_0,c,r,s_*,a,b$ by one positive rational factor must leave normalized
inputs, branch decisions, and dimensionless outputs exactly unchanged.

## 4. I1 candidate: robust full-circle separation

For the fixed circle $\Gamma$ and every $U=U_0+\Delta$ in the family,
Weyl's singular-value Lipschitz inequality gives

$$
\sigma_{\min}(zI-U)
\ge \sigma_{\min}(zI-U_0)-\|\Delta\|_2.
$$

If

$$
\widetilde\varepsilon^+
<\underline{\widetilde\delta}_0,
$$

then the entire family is contour-free with common normalized lower bound

$$
\underline{\widetilde\delta}_{\mathcal U}
=\underline{\widetilde\delta}_0-\widetilde\varepsilon^+>0,
\qquad
\sup_{U\in\mathcal U,z\in\Gamma}
\|(zI-\widetilde U)^{-1}\|_2
\le\underline{\widetilde\delta}_{\mathcal U}^{-1}.
$$

Equality or a larger uncertainty is a named non-certificate result, never
evidence of a contour crossing.

## 5. I2 candidate: rank and exact-projector stability

The path $U_t=U_0+t\Delta$, $0\le t\le1$, remains contour-free under I1.
Continuity and integer-valued rank therefore give

$$
\operatorname{rank}P(U)=\operatorname{rank}P(U_0)
$$

for the exact Riesz projectors defined by $\Gamma$. The resolvent identity and
$|\Gamma|=2\pi r$ yield the dimensionless bound

$$
\|P(U)-P(U_0)\|_2
\le
\frac{\widetilde r\,\widetilde\varepsilon^+}
{\underline{\widetilde\delta}_0
 (\underline{\widetilde\delta}_0-\widetilde\varepsilon^+)}
=:\rho_P^+.
$$

This bound may exceed one and can be conservative; positivity of I1, not a
small projector bound, is the rank-stability condition.

## 6. I3 candidate: measured-family to nominal four-node approximation

If the optional predecessor strip certificate supplies
$\eta_4^+\ge\|P_4(U_0)-P(U_0)\|_2$, then triangle inequality gives, for every
$U$ in the interval family,

$$
\|P(U)-P_4(U_0)\|_2\le\rho_P^++\eta_4^+.
$$

This is an approximation to the exact projector of each admitted unknown
matrix by the computable nominal $P_4$. It does not certify $P_4(U)$ and does
not make the four-node nominal approximation exact.

## 7. Required outputs and statuses

The implementation must expose the predecessor nominal certificate; exact
$\widetilde S$; lower/upper dyadic square-root bracket and squared
self-checks; normalized/raw uncertainty upper; robust normalized/raw
separation; normalized/raw resolvent upper; $\rho_P^+$; optional nominal
quadrature and total projector bounds; scale and precision.

Only all passing I1 prerequisites may return
`VERIFIED_RATIONAL_INTERVAL_FAMILY_CONTOUR_BRIDGE`. The optional I3 route may
return `VERIFIED_RATIONAL_INTERVAL_FAMILY_PROJECTOR_BRIDGE` only when both I1
and the predecessor strip certificate pass.

Named non-certificate states include nominal certificate unavailable and
uncertainty not strictly below the nominal lower separation. Invalid input
raises a validation error before any scientific status is emitted.

## 8. Required adverse controls

- zero uncertainty, including exact zero square-root bracket;
- positive uncertainty strictly below the margin;
- uncertainty exactly equal to and greater than the margin;
- nominal certificate failure;
- shape mismatch, negative/binary-float/Boolean/malformed bounds;
- a nonnormal nominal example;
- simultaneous unit rescaling;
- optional I3 success and unavailable-strip failure;
- exact scalar examples that directly check the singular-value, rank, and
  projector inequalities.

## 9. Claim ceiling

I1--I3 may reach conditional finite-dimensional theorem and exact-apparatus
status. They cover every matrix in the declared componentwise uncertainty box,
including irrational entries, because the proof uses bounds rather than exact
elimination on the unknown member.

They do not prove that a measured estimator lies in the box. Constructing
$a,b$ from finite neural observations needs a separately frozen measurement
and statistical coverage contract. No result selects a rank from data,
validates a whole-brain metric, identifies a conscious moment, or privileges
dimension 4--6.

## 10. Execution order

1. Prove I1--I3 and audit normalization, strict inequalities, and counterexamples.
2. Implement a separate exact interval bridge without weakening predecessor APIs.
3. Run one focused test file and audit the stable snapshot.
4. Promote only claims supported by the final gate.
