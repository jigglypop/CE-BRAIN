# Verified interval-valued measured-matrix bridge

Status: COMPLETE

Date: 2026-08-25

## Abstract

The predecessor certified only a declared exact rational matrix. This run
closes the next perturbation layer: an exact rational rectangular uncertainty
box around that nominal matrix now yields a rigorous certificate for every
complex matrix in the box, including irrational members. If the box's
operator-norm upper bound is strictly smaller than the nominal full-circle
separation, the whole family avoids the contour, has one common Riesz rank,
and receives explicit resolvent and projector-motion bounds. An optional route
adds the nominal four-node quadrature error. Focused validation passed 15
tests, adjacent integration 26, and the dimensionless gate 21. No observed
matrix or statistical coverage model was supplied, so this is a measurement-
uncertainty theorem and apparatus, not a neural-data result.

## 1. Interval family and norm enclosure

For exact nonnegative rational radii $a_{ij},b_{ij}$ around a nominal
$U_0\in\mathbb Q(i)^{n\times n}$, define

$$
\mathcal U=\{U_0+\Delta:
|\Re\Delta_{ij}|\le a_{ij},\ |
\Im\Delta_{ij}|\le b_{ij}\}.
$$

With spectral reference scale $s_*>0$, normalize first and form

$$
\widetilde S=\sum_{ij}left[(a_{ij}/s_*)^2+(b_{ij}/s_*)^2\right].
$$

The implementation encloses $\sqrt{\widetilde S}$ by exact dyadic rationals
and rechecks both squared inequalities. Its upper endpoint
$\widetilde\varepsilon^+$ satisfies

$$
\|\widetilde\Delta\|_2\le\|\widetilde\Delta\|_F
\le\sqrt{\widetilde S}\le\widetilde\varepsilon^+
$$

for every box member. Rationality of the unknown member is unnecessary.

## 2. Robust contour and rank theorem

Let the predecessor exact certificate give

$$
\inf_{z\in\Gamma}\sigma_{\min}(zI-\widetilde U_0)
\ge\underline{\widetilde\delta}_0>0.
$$

If $\widetilde\varepsilon^+<
\underline{\widetilde\delta}_0$, singular-value Lipschitz continuity gives

$$
\underline{\widetilde\delta}_{\mathcal U}
=\underline{\widetilde\delta}_0-\widetilde\varepsilon^+>0,
\qquad
\sup_{U\in\mathcal U,z\in\Gamma}
\|(zI-\widetilde U)^{-1}\|_2
\le\underline{\widetilde\delta}_{\mathcal U}^{-1}.
$$

The homotopy $U_t=U_0+t\Delta$ remains contour-free. Its Riesz projector is
continuous, while finite rank is integer-valued, so every member has the same
enclosed spectral rank. Equality cannot pass: for scalar $U_0=0$ on the unit
circle, $\Delta=1$ places an eigenvalue exactly at $z=1$.

## 3. Projector perturbation and total approximation

The resolvent identity integrated around a radius-$r$ circle gives

$$
\|P(U)-P(U_0)\|_2
\le
\rho_P^+
=\frac{\widetilde r\,\widetilde\varepsilon^+}
{\underline{\widetilde\delta}_0
(\underline{\widetilde\delta}_0-\widetilde\varepsilon^+)}.
$$

If the nominal analytic-strip certificate supplies
$\eta_4^+\ge\|P_4(U_0)-P(U_0)\|_2$, then

$$
\|P(U)-P_4(U_0)\|_2\le\rho_P^++\eta_4^+.
$$

This sum visibly separates measurement-box propagation from nominal contour
quadrature. It does not claim that $P_4(U)$ was computed.

## 4. Implementation and verification

`verified_interval_contour.py` layers on the unchanged exact-rational
predecessor. It exposes exact normalized uncertainty squares, dyadic brackets
and self-checks, normalized/raw uncertainty and separation, resolvent bounds,
projector perturbation, explicit family-wide rank preservation, and optional
quadrature/total errors.

Positive statuses are:

- `VERIFIED_RATIONAL_INTERVAL_FAMILY_CONTOUR_BRIDGE`;
- `VERIFIED_RATIONAL_INTERVAL_FAMILY_PROJECTOR_BRIDGE`.

Nominal failure and uncertainty at or above the margin are named
non-certificates. Negative, binary-float, Boolean, malformed, or shape-
mismatched bounds are rejected.

Validation results:

- focused interval behavior: 15/15;
- predecessor plus interval integration: 26/26;
- dimensionless checker: 21/21;
- exact theorem spot checks: PASS;
- research final gate: pending this report, then checked separately.

The dimensionless audit confirms that raw separation has spectral unit, the
raw resolvent has reciprocal spectral unit, and
$r\varepsilon/[\delta_0(\delta_0-\varepsilon)]$ is dimensionless.

## 5. Limits and strengthened candidates

The achieved bridge is deterministic. It proves a statement conditional on
the declared box but cannot establish simultaneous statistical coverage of
that box. A future empirical contract must freeze the estimator, sampling
unit, preprocessing, dependence and missingness model, confidence target, and
held-out policy.

The Frobenius radius can be conservative. A frozen candidate tightening is

$$
\|\Delta\|_2\le\sqrt{\|C\|_1\|C\|_\infty},\qquad
C_{ij}=\sqrt{a_{ij}^2+b_{ij}^2},
$$

using outward-rounded $C_{ij}$ values. A verified residual/Krawczyk route is a
second candidate for local, better-conditioned certificates. Neither may be
chosen after a failed target and reported as the same preregistered route.

Nothing here constructs an observed brain matrix, proves the Allen E1
metadata split, selects a latent rank, validates a global Riemannian brain
metric, identifies consciousness, or privileges dimensions 4--6.

## Reproducibility record

- Contract: `00-contract.md`
- Self-contained proofs and counterexamples: `11-math.md`
- Candidate alternatives and falsifiers: `12-routes.md`
- Stable status audit: `20-audit.md`
- Implementation: `30-implementation.md`
- Focused and adjacent validation: `31-validation.md`
- Exact theorem fixture: `artifacts/math_interval_spotchecks.py`
