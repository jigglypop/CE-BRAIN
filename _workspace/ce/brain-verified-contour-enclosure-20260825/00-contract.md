# Verified rational contour enclosure contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-history-riesz-empirical-bridge-20260825`

## 1. Objective and exact claim boundary

The predecessor proved a full-circle lower theorem and an analytic-strip
quadrature theorem, but its executable seam deliberately returned ordinary
float64 estimates. This light successor asks whether a dependency-free,
machine-checkable subset can return rigorous enclosures rather than estimates.

The target is finite rational complex linear algebra only. It is not a general
interval eigensolver, an infinite-dimensional Riesz calculus, a neural data
result, a biological metric, or evidence for consciousness or rank 4–6.

## 2. PREDECESSOR_EVIDENCE

| Result | Frozen evidence | Preserved ceiling |
|---|---|---|
| Full-circle theorem | predecessor `11-math.md`, Theorem M2.1; final gate PASS | rigorous only when every node lower bound and the chord upper bound are rigorous enclosures |
| Analytic-strip theorem | predecessor `11-math.md`, annular theorem; final gate PASS | requires a spectrum-free closed annulus in addition to two certified boundaries |
| Float64 implementation | `finite_contour_bounds.py`; focused 14/14 | labels remain `FLOAT64_UNVERIFIED_*`; no relabeling or tolerance inflation |
| Finite Riesz seam | `finite_riesz.py`; focused 6/6 | a-posteriori numerical approximation only |
| Empirical bridge | E1 metadata specification `FROZEN / UNEXECUTED` | no data access or empirical promotion in this run |

## 3. Exact input class

Admit only finite square matrices whose real and imaginary entries are exact
rationals represented by built-in integers, `fractions.Fraction`, or canonical
decimal/fraction strings. Binary floats and Python complex values are rejected
because their intended exact decimal value is ambiguous. The circle center and
radius obey the same rule, with radius positive. All spectral quantities share
one declared unit; a positive rational `spectral_reference_scale` with that
unit is mandatory for normalized output.

Before any elimination or dyadic square-root enclosure, the implementation
must form the exact dimensionless representative

$$
\widetilde U=U/s_*,\qquad \widetilde c=c/s_*,\qquad
\widetilde r=r/s_*,
$$

where $s_*$ is `spectral_reference_scale`.  The fixed fractional-bit grid is
applied only to these normalized rational quantities.  This ordering is part
of the certificate: applying dyadic rounding in raw units and normalizing
afterward is forbidden because it is not invariant under a simultaneous unit
rescaling.

The first verified mesh is fixed at $N=4$ with exact nodes

$$
z_0=c+r,\quad z_1=c+ir,\quad z_2=c-r,\quad z_3=c-ir.
$$

Supporting other $N$ would require a separately verified trigonometric
enclosure and is out of scope. The implementation must reject rather than
silently approximate unsupported meshes.

## 4. V1 candidate: exact sampled inverse bound

For the normalized matrices
$\widetilde A_k=(\widetilde c+\widetilde r d_k)I-\widetilde U$, exact rational Gaussian elimination either proves
singularity or returns the exact inverse. With

$$
\widetilde S_k=\|\widetilde A_k^{-1}\|_F^2\in\mathbb Q_{>0},
$$

let $q_k^+\in\mathbb Q$ be a certified dyadic upper bound on
$\sqrt{\widetilde S_k}$.
Then

$$
\sigma_{\min}(\widetilde A_k)=\|\widetilde A_k^{-1}\|_2^{-1}
\ge \|\widetilde A_k^{-1}\|_F^{-1}
\ge (q_k^+)^{-1}.
$$

The dyadic square-root routine must return both $q^-$ and $q^+$ and verify
internally, with exact rational comparisons,

$$
(q^-)^2\le x\le(q^+)^2.
$$

## 5. V2 candidate: exact four-node chord enclosure

For $N=4$, the nearest-node chord is

$$
2r\sin\frac{\pi}{8}=r\sqrt{2-\sqrt2}.
$$

If $s_2^-\le\sqrt2$ is a certified dyadic lower bound, then a certified upper
bound is

$$
\widetilde\chi^+=\widetilde r\,
\overline{\sqrt{2-s_2^-}}.
$$

Define the exact rational output

$$
\underline{\widetilde\delta}_4=
\min_k(q_k^+)^{-1}-\widetilde\chi^+.
$$

Only $\underline{\widetilde\delta}_4>0$ may return

$$
\overline{\widetilde R}_\Gamma=
\underline{\widetilde\delta}_4^{-1}.
$$

Zero or negative values mean `VERIFIED_LOWER_BOUND_NONPOSITIVE`, not contour
crossing. Raw-unit reports are derived only afterward as
$\underline\delta_4=s_*\underline{\widetilde\delta}_4$ and
$\overline R_\Gamma=\overline{\widetilde R}_\Gamma/s_*$.  Simultaneously
scaling $U,c,r,s_*$ by one positive rational factor therefore leaves all
normalized elimination inputs, dyadic decisions, and certificate status
exactly unchanged.

## 6. V3 candidate: restricted analytic-strip certificate

Let a rational expansion factor $q>1$ replace an approximate strip width:

$$
r_-=r/q,\qquad r_+=rq,\qquad a=\log q.
$$

Then $e^{aN}=q^N$ is exact and the predecessor theorem becomes

$$
M^+=\max\left\{\frac{r_-}{\underline\delta_-},
\frac{r_+}{\underline\delta_+}\right\},\qquad
\|P_4-P\|_2\le\frac{2M^+}{q^4-1}.
$$

The annulus condition may be certified only with a supplied exact rational
diagonalization witness $UV=V\Lambda$: exact multiplication must verify the
identity, exact elimination must verify $V$ invertible, and squared rational
distances must show that no diagonal entry of $\Lambda$ lies in the closed
annulus. The witness also fixes the exact inner spectral projector
$P=V\operatorname{diag}(1_{|\lambda-c|<r})V^{-1}$. Missing, invalid,
boundary, or annulus eigenvalues fail closed. This witness route is restricted
to exactly diagonalizable rational fixtures and makes no claim for defective
or general measured matrices.

## 7. Required executable outputs

The implementation may be admitted only after math audit and must expose:

- exact rational-complex $P_4$ and, when the diagonalization witness is
  supplied, exact rational-complex $P$;
- dyadic square-root enclosure precision and exact enclosure residual checks;
- every node's rational singular lower bound, rational chord upper bound,
  normalized $\underline{\widetilde\delta}_4$, derived raw
  $\underline\delta_4$, and optional normalized/raw resolvent uppers;
- raw spectral-unit values and dimensionless normalized values;
- exact annulus classification and conditional analytic-strip error upper;
- validation levels `VERIFIED_RATIONAL_FULL_CIRCLE_ENCLOSURE` and
  `VERIFIED_RATIONAL_ANALYTIC_STRIP_ENCLOSURE` only when all corresponding
  hypotheses pass.

## 8. Adverse controls and falsifiers

Required controls are: singular sample node; nonpositive conservative lower
bound; oblique but exactly diagonalizable nonnormal matrix; invalid
eigendecomposition; eigenvalue on either annulus boundary; eigenvalue strictly
inside the annulus; binary-float input; unsupported node count; inadequate
square-root precision; and simultaneous unit rescaling.

Any failed exact comparison, singular pivot, unsupported input, nonpositive
lower bound, invalid witness, or annulus violation returns a named failure or
raises a validation error. Threshold, precision, mesh, or witness may not be
changed after observing a failed target and then reported as the same
certificate.

## 9. CLAIM_CEILING

- V1–V3 may reach conditional finite rational theorem/certificate status after
  independent mathematics and status audits.
- Exactness refers to the declared rational input, not an unknown real matrix
  that was rounded to create it.
- The certificate can be conservative and incomplete: failure is not evidence
  that the contour intersects the spectrum.
- No result selects a neural rank, validates the E1 bridge, identifies a brain
  metric, or identifies consciousness or dimension 4–6.

## 10. Candidate ordering

1. Audit V1/V2 algebra and the square-root enclosure first.
2. Audit the rational-expansion reformulation and exact witness conditions.
3. Implement the smallest standalone module without modifying float64
   semantics.
4. Run one focused test file and an independent status audit.
5. Promote only the frozen ledger entries supported by the final gate.
