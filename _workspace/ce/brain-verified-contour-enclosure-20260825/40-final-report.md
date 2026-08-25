# Verified rational contour enclosure

Status: COMPLETE

Date: 2026-08-25

## Abstract

The predecessor supplied a correct full-circle theorem but only an unverified
float64 implementation. This light successor closes a deliberately restricted
case with dependency-free exact arithmetic over rational complex matrices.
After exact normalization by a declared spectral scale, four exact contour
nodes yield rigorous singular-value lower bounds and a full-circle resolvent
upper bound. An exact rational diagonalization witness can additionally prove
a spectrum-free annulus and a central four-node Riesz quadrature error bound.
The focused implementation passed 11 tests, but the result remains finite,
rational, four-node, and unrelated to neural or consciousness identification.

## 1. Problem and scope

The earlier function `finite_contour_bounds.py` correctly labels every result
as `FLOAT64_UNVERIFIED`. Sampling a contour with ordinary SVD values cannot by
itself prove that the unsampled contour is resolvent-free because rounding can
overstate the smallest singular value. This run therefore does not rename or
weaken that API. It adds a separate route whose inputs and every intermediate
comparison are exact rational numbers.

The admitted matrix lies in $\mathbb Q(i)^{n\times n}$. Floats, Python complex
values, noncanonical strings, empty matrices, and meshes other than four nodes
are rejected. Exactness concerns this declared rational matrix; it does not
prove that an experimental matrix was measured without uncertainty.

## 2. Normalize before enclosing

Let $s_*>0$ have the same spectral unit as $U$, $c$, and $r$. The executable
calculation first forms

$$
\widetilde U=U/s_*,\qquad
\widetilde c=c/s_*,\qquad
\widetilde r=r/s_*.
$$

All dyadic square-root grids are applied only afterward. This ordering is
necessary: a fixed dyadic grid applied in raw units is safe but changes its
normalized answer when the unit is rescaled. With normalize-first arithmetic,
simultaneously scaling $U,c,r,s_*$ by any positive rational factor leaves the
normalized inputs, branch decisions, and certificate status exactly fixed.

## 3. Full-circle certificate

For the four exact directions $d_k\in\{1,i,-1,-i\}$, set

$$
\widetilde A_k=(\widetilde c+\widetilde r d_k)I-\widetilde U.
$$

Exact Gauss–Jordan elimination either proves a sampled matrix singular or
returns its exact inverse. If $q_k^+$ is a verified rational upper enclosure
of $\|\widetilde A_k^{-1}\|_F$, then

$$
\ell_k=(q_k^+)^{-1}
\le\sigma_{\min}(\widetilde A_k).
$$

The square-root routine returns lower and upper dyadics and rechecks both
squared inequalities with integer arithmetic. The same machinery gives a
rational upper enclosure $\widetilde\chi^+$ for the four-node chord

$$
\widetilde r\sqrt{2-\sqrt2}.
$$

Consequently,

$$
\underline{\widetilde\delta}_4=
\min_k\ell_k-\widetilde\chi^+>0
$$

proves the whole circle resolvent-free and yields

$$
\sup_\Gamma\|(zI-\widetilde U)^{-1}\|_2
\le\underline{\widetilde\delta}_4^{-1}.
$$

The implementation exposes the node brackets, both chord-root brackets, all
exact self-checks, normalized and raw separation, and normalized and raw
resolvent bounds. A singular node or nonpositive conservative difference has
a named failure status and is not interpreted as a contour crossing.

## 4. Restricted analytic-strip certificate

Choose an exact rational expansion factor $q>1$, so the inner and outer radii
are $r/q$ and $rq$. A supplied witness must satisfy

$$
UV=V\Lambda
$$

entry by entry over $\mathbb Q(i)$, with $V$ exactly invertible and $\Lambda$
diagonal. Squared rational distances must place every eigenvalue strictly
inside $r/q$ or strictly outside $rq$. Boundary and annulus eigenvalues,
invalid witnesses, and defective matrices without such a witness fail closed.

When both boundary circles have positive exact certificates, the witness
determines

$$
P=V\operatorname{diag}
\left(1_{|\lambda_j-c|<r}\right)V^{-1}
$$

and the exact central four-node quadrature is

$$
P_4=\frac14\sum_{k=0}^{3}
(z_k-c)(z_kI-U)^{-1}.
$$

The analytic-strip theorem then gives the machine-returned rational upper
bound

$$
\|P_4-P\|_2\le
\frac{2M^+}{q^4-1},\qquad
M^+=\max\left\{
\frac{r/q}{\underline\delta_-},
\frac{rq}{\underline\delta_+}
\right\}.
$$

The factors $(z_k-c)$, $1/4$, and the boundary radii are indispensable. The
bound applies to the central $P_4$, not either boundary quadrature.

## 5. Implementation and validation

The standalone module
`reality_stone/python/reality_stone/clarus/verified_rational_contour.py`
contains no NumPy, Torch, interval-package, or network dependency. It returns
`VERIFIED_RATIONAL_FULL_CIRCLE_ENCLOSURE` or
`VERIFIED_RATIONAL_ANALYTIC_STRIP_ENCLOSURE` only after the corresponding
exact checks succeed.

Focused reproduction:

```powershell
.codex\hooks\python.cmd pytest tests\test_verified_rational_contour.py -vv -s --tb=short
```

The observed result was 11 passing tests. They cover canonical parsing,
dyadic enclosure residuals, exact $P_4$, singular and nonpositive controls,
unsupported inputs, exact unit-rescaling invariance, a nonnormal oblique
witness, three closed-annulus adverse cases, and invalid or defective
witnesses. An independent mathematics re-review and status audit found no P0
or P1 inconsistency in the final snapshot.

## 6. Result, limits, and next falsifiers

The missing verified-arithmetic step is now closed for one precise class:
finite rational complex matrices, four contour nodes, and, for the strip
claim, an exact diagonalization witness. This is stronger than the predecessor
float64 estimate because its positive result is a proof about the declared
rational input.

The result is intentionally incomplete in three directions. Four-node
Frobenius bounds can be too conservative even when the true contour is clear.
Defective matrices and matrices without a rational diagonalization witness do
not enter the strip route. Measured matrices need interval-valued input and a
verified perturbation bridge before this certificate can describe their
unknown exact values.

Nothing in this run selects a subspace rank, executes the E1 neural metadata
receipt, validates a brain metric, or identifies consciousness. In particular,
dimension 4–6 remains only part of the frozen candidate menu. The next
mathematical route is a verified interval-input residual/Krawczyk certificate;
the next empirical route remains the separately frozen metadata-only E1
provenance action.

## Reproducibility record

- Contract and hypotheses: `00-contract.md`
- Proofs and counterexamples: `11-math.md`
- Independent audit: `20-audit.md`
- Implementation record: `30-implementation.md`
- Focused execution record: `31-validation.md`
- Exact Fraction spot checks: `artifacts/math_spotchecks.py`
