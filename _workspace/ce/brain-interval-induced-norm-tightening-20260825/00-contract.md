# Induced-norm tightening for interval contour families

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-interval-measured-matrix-bridge-20260825`

## 1. Objective

The predecessor uses the exact Frobenius radius of a rectangular uncertainty
box. This successor implements the preregistered alternative
$\sqrt{\|C\|_1\|C\|_\infty}$ and deterministically selects the smaller of the
two rigorous uppers before applying the same contour, rank, resolvent, and
projector theorems.

No observed matrix or statistical coverage model is introduced. This is an
apparatus tightening only.

## 2. Frozen input and normalize-first rule

Use exactly the predecessor nominal matrix, contour, scale, rectangular
radii, parser domain, four-node nominal certificate, and optional strip
witness. For normalized radii define

$$
s_{ij}=\widetilde a_{ij}^2+\widetilde b_{ij}^2,
\qquad
c_{ij}^+\ge\sqrt{s_{ij}}
$$

with exact dyadic brackets and squared self-checks. Every entrywise square root
must be enclosed after normalization. Raw-unit rounding followed by division
is forbidden.

## 3. T1 candidate: induced 1/infinity upper

Let $C^+=(c_{ij}^+)$. Define exact rational sums

$$
L_1^+=\max_j\sum_i c_{ij}^+,\qquad
L_\infty^+=\max_i\sum_j c_{ij}^+.
$$

For every admitted $\Delta$,

$$
\|\widetilde\Delta\|_1\le L_1^+,\qquad
\|\widetilde\Delta\|_\infty\le L_\infty^+,\qquad
\|\widetilde\Delta\|_2
\le\sqrt{L_1^+L_\infty^+}.
$$

Return a checked dyadic upper
$\widetilde\varepsilon_{1\infty}^+\ge
\sqrt{L_1^+L_\infty^+}$.

## 4. T2 candidate: deterministic best-of-two bound

Let $\widetilde\varepsilon_F^+$ be the predecessor Frobenius upper. Freeze

$$
\widetilde\varepsilon_*^+
=\min\{\widetilde\varepsilon_F^+,
\widetilde\varepsilon_{1\infty}^+\}.
$$

Both candidates are unconditional uppers for the same box, so taking their
minimum is rigorous and never weaker. The selection is not data-dependent in
the inferential sense: both are computed for every invocation before the
contour decision. Tie policy is frozen to `FROBENIUS` when
$\widetilde\varepsilon_F^+\le
\widetilde\varepsilon_{1\infty}^+$; otherwise select
`INDUCED_1_INFINITY`.

Substitute $\widetilde\varepsilon_*^+$ for the predecessor uncertainty upper
in its strict margin, robust separation, resolvent, rank-homotopy, projector
perturbation, and optional total $P_4$ error formulas. No theorem formula is
otherwise changed.

## 5. Required outputs

Expose the complete predecessor Frobenius bridge; every entry magnitude
bracket and squared self-check; $L_1^+$, $L_\infty^+$; the product square-root
bracket and self-check; induced normalized/raw upper; selected method and
normalized/raw upper; tightened robust separation/resolvent/projector bound;
rank-preservation Boolean; optional nominal quadrature and total projector
errors; precision and scale.

Positive statuses are
`VERIFIED_RATIONAL_TIGHT_INTERVAL_FAMILY_CONTOUR_BRIDGE` and, with a passing
nominal strip, `VERIFIED_RATIONAL_TIGHT_INTERVAL_FAMILY_PROJECTOR_BRIDGE`.
Nominal failure and selected uncertainty at or above the margin are named
non-certificates.

## 6. Required controls

- diagonal box where induced is strictly smaller than Frobenius;
- dense uniform or scalar tie with frozen `FROBENIUS` selection;
- a case where predecessor Frobenius fails but induced passes;
- zero uncertainty;
- nonnormal nominal matrix;
- strict-margin failure after tightening;
- all predecessor schema/type/sign adversaries;
- normalize-first exact unit invariance;
- optional projector success and strip failure;
- exact comparison against direct matrix norms for finite fixtures.

## 7. Claim ceiling

T1--T2 may become conditional finite theorem/exact apparatus results. They do
not calibrate interval coverage, validate an estimator, access neural data,
select a rank, identify brain geometry or consciousness, or privilege
dimensions 4--6. A certificate failure remains inconclusive.

## 8. Execution order

Prove T1/T2, audit counterexamples and scale invariance, implement without
changing predecessor semantics, run one focused plus adjacent test, and update
the ledger/paper only after the final gate.
