# Verified induced-norm tightening of interval families

Status: COMPLETE

Date: 2026-08-25

## Abstract

The predecessor's rectangular uncertainty bridge used only a Frobenius
radius. This successor computes a second rigorous operator-norm upper from
outward entry magnitudes and induced row/column sums, then uses the frozen
minimum of both. The result is never weaker and can certify diagonal or
structured boxes that the Frobenius route rejects. The predecessor result is
preserved inside the new output. Focused validation passed 13 tests, three-
stage integration 39, and the dimensionless gate 22. This remains deterministic
interval apparatus without empirical coverage or neural data.

## 1. Tight upper

After normalizing every rectangular radius by $s_*$, exact dyadic brackets
give

$$
c_{ij}^+\ge\sqrt{\widetilde a_{ij}^2+\widetilde b_{ij}^2}.
$$

Set

$$
L_1^+=\max_j\sum_i c_{ij}^+,\qquad
L_\infty^+=\max_i\sum_jc_{ij}^+.
$$

For every box member,

$$
\|\widetilde\Delta\|_2
\le\sqrt{\|\widetilde\Delta\|_1
\|\widetilde\Delta\|_\infty}
\le\sqrt{L_1^+L_\infty^+}
\le\widetilde\varepsilon_{1\infty}^+.
$$

With the predecessor Frobenius upper $\widetilde\varepsilon_F^+$, the frozen
apparatus uses

$$
\widetilde\varepsilon_*^+
=\min\{\widetilde\varepsilon_F^+,
\widetilde\varepsilon_{1\infty}^+\}.
$$

Both candidates are always computed; ties select `FROBENIUS`. Therefore this
is one preregistered formula, not a post-failure choice.

## 2. Why both candidates remain

For a diagonal magnitude matrix $C=I_n$, Frobenius gives $\sqrt n$ while the
induced bound gives $1$. Conversely, for
$C=\begin{pmatrix}1&1\\1&0\end{pmatrix}$, Frobenius gives $\sqrt3$ while the
induced candidate gives $2$. Neither dominates, so the exact minimum prevents
regression.

If a nominal contour margin is $\delta$ and a diagonal $n$-entry box has
$\delta/\sqrt n<c<\delta$, the Frobenius bound fails while the induced bound
passes. The focused fixture realizes this behavior with the same nominal
matrix and box and preserves the predecessor non-certificate alongside the
new positive tightened status.

## 3. Propagated conclusions

When $\widetilde\varepsilon_*^+<
\underline{\widetilde\delta}_0$, substitute it into the already-proved family
formulas:

$$
\underline{\widetilde\delta}_*
=\underline{\widetilde\delta}_0-\widetilde\varepsilon_*^+,
\qquad
\overline{\widetilde R}_*=\underline{\widetilde\delta}_*^{-1},
$$

$$
\rho_{P,*}^+=
\frac{\widetilde r\,\widetilde\varepsilon_*^+}
{\underline{\widetilde\delta}_0
(\underline{\widetilde\delta}_0-\widetilde\varepsilon_*^+)}.
$$

The whole family remains contour-free with fixed Riesz rank. A passing nominal
strip additionally gives

$$
\|P(U)-P_4(U_0)\|_2\le\rho_{P,*}^++\eta_4^+.
$$

## 4. Implementation and evidence

`verified_interval_tightening.py` exposes every entry bracket and squared
self-check, $L_1^+$, $L_\infty^+$, the product bracket, both uncertainty
candidates, selected method, raw/normalized robust quantities, rank status,
and optional projector terms. Positive statuses are separate from all
predecessor labels.

- focused: 13/13;
- exact nominal + Frobenius interval + tightening integration: 39/39;
- dimensionless gate: 22/22;
- exact theorem fixture: PASS;
- research final gate: pending this report, checked next.

## 5. Ceiling and next routes

This closes the preregistered induced-norm candidate. Per-entry outward
rounding can still be conservative, and a verified residual/Krawczyk route
remains open. More importantly, no procedure here estimates or calibrates the
box from observations. It gives no Allen metadata result, measured neural
matrix, selected rank, whole-brain metric, consciousness identification, or
dimension 4--6 preference.

## Reproducibility record

- Contract: `00-contract.md`
- Proof and non-domination controls: `11-math.md`
- Routes/falsifiers: `12-routes.md`
- Stable audit: `20-audit.md`
- Implementation: `30-implementation.md`
- Validation: `31-validation.md`
