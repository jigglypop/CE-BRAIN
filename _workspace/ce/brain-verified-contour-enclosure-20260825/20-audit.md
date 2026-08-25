# Verified rational contour enclosure - status audit

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-verified-contour-enclosure-20260825`

Gate: PASS

This audit covers the stable contract/source/math/routes snapshot before
implementation. No production code, canonical document, data, or Git state
was changed. The exact Fraction spot check was executed from
`artifacts/math_spotchecks.py` and returned `spot checks: PASS`.

## Verdict and severity

P0: none. P1: none. P2: two bounded limitations remain and are already
disclosed by the contract: V3 is restricted to rational, exactly
diagonalizable fixtures, and the four-node Frobenius enclosure can be
conservative. Neither limitation invalidates the stated conditional claims
or blocks the proposed implementation.

Implementation admission is justified subject to preserving every required
failure-closed condition in `00-contract.md` sections 7-8. No certificate
label is admitted by this audit; that requires the later implementation and
focused tests.

## Claim-by-claim audit

| Claim ID / location | Finding | Status |
|---|---|---|
| V1, `11-math.md` section V1; contract section 4 | Exact Gaussian elimination over \\(\\mathbb Q(i)\\), exact zero-pivot detection, and \\(\\|A^{-1}\\|_F^2\\in\\mathbb Q\\) are valid. The dyadic square-root inequalities imply \\(\\sigma_{\\min}(A)\\ge(q^+)^{-1}\\). | Conditional theorem; PASS |
| V2, `11-math.md` section V2; contract section 5 | The four-node chord is \\(r\\sqrt{2-\\sqrt2}\\); the singular-value 1-Lipschitz step transfers node lower bounds to the whole circle. Positive \\(\\underline{\\widetilde\\delta}_4\\) is sufficient for a resolvent enclosure, while nonpositive output is failure, not crossing evidence. | Conditional theorem; PASS |
| V3, `11-math.md` section V3; contract section 6 | The rational \\(q>1\\) annulus gives exact \\(e^{4a}=q^4\\). The witness checks \\(UV=V\\Lambda\\), invertibility of \\(V\\), and strict exclusion from the closed annulus. These hypotheses imply the stated exact diagonal spectral projector and exclude central-contour poles. | Conditional theorem; PASS |
| V3 proof, `11-math.md` section V3 | The integrand includes the required radius factor \\(r e^{i\\theta}\\); both boundary factors \\(r_-/\\delta_-\\) and \\(r_+/\\delta_+\\) are retained. Two-sided strip analyticity, Fourier decay, and four-node aliasing yield \\(2M^+/(q^4-1)\\) for the central \\(P_4\\), not an inner/outer discrete projector. | Proof dependency complete; PASS |
| Normalization, `00-contract.md` sections 3-5; `12-routes.md` R4 | Normalizing \\(U,c,r\\) by the positive rational reference scale before all elimination and dyadic rounding makes the dimensionless inputs invariant under common positive rational rescaling. Raw \\(\\delta\\) and resolvent bounds transform covariantly afterward. | Control is sufficient; PASS |
| Exact witness, `11-math.md` section V3; `artifacts/math_spotchecks.py` | The oblique fixture \\(V=\\begin{psmallmatrix}1&1\\\\0&1\\end{psmallmatrix}\\), \\(\\Lambda=\\operatorname{diag}(0,3)\\) verifies \\(U\\), \\(P\\), central \\(P_4\\), and \\(\\|P_4-P\\|_F^2=1/3200\\) exactly. The sign and \\(1/4\\) factor are independently spot-checked. | Exact spot check; PASS |
| Failure semantics, `00-contract.md` section 8; `12-routes.md` R1-R4 | Singular nodes, nonpositive lower bounds, invalid witnesses, annulus/boundary eigenvalues, unsupported input/mesh, failed square-root residuals, and changed post-failure choices are all required to fail closed or start a distinct request. | Scope guard; PASS |
| Source lane, `10-sources.md` | Correctly marked SKIPPED: this run introduces no empirical or external-constant claim and inherits the predecessor source/E1 ceiling. | Status consistent; PASS |

## Dependency and limitation notes

- V2 depends on V1 at all four exact nodes and on an independently verified
  chord upper bound; the contract fixes N=4, so no unsupported trigonometric
  mesh is silently admitted.
- V3 depends on positive V2 certificates on both annular boundaries, a valid
  exact diagonalization witness, and strict closed-annulus exclusion. If any
  dependency fails, the V3 label must not be emitted.
- The spot-check script verifies the exact algebraic witness and central
  quadrature identity, but it is not a production parser, interval solver, or
  full adverse-control suite. Those remain implementation-test obligations.
- Exactness is only for the declared rational input. It does not certify an
  unknown measured matrix, a neural observable, consciousness, or a preferred
  rank. These ceilings are explicit in `00-contract.md` sections 1 and 9.

## Gate decision

`Gate: PASS`. The mathematics is internally consistent under the frozen
hypotheses, normalization is applied before dyadic decisions, the exact
diagonalization witness and annulus conditions are adequate, and no P0/P1
issue remains. Proceed to the smallest standalone implementation while
preserving the named failure statuses and the no-promotion ceiling.

## Post-implementation addendum

Math final re-review: PASS. The implementation revision that exposed both
endpoint brackets and exact residual checks for the \(\sqrt2\) and chord
factor enclosures is incorporated in the stable module. The prior P1 concern
about incomplete chord-check visibility is therefore resolved.

### Code, record, and test alignment

| Evidence | Finding | Status |
|---|---|---|
| `reality_stone/python/reality_stone/clarus/verified_rational_contour.py` | Implements exact `QComplex`/`Fraction` parsing, normalize-first arithmetic, exact inverse residual checks, integer-`isqrt` brackets, fixed `nodes=4`, central \(r i^k/4\) quadrature, and the V1-V3 witness/annulus route. | PASS |
| Same module, `VerifiedRationalCircle` fields | Exposes node brackets/checks, \(\sqrt2\) bracket/checks, chord-factor bracket/checks, normalized/raw separation and resolvent values, and named validation levels. | PASS |
| `tests/test_verified_rational_contour.py` | Covers parser and canonical-input rejection, inadequate precision, exact circle/P4, singular and nonpositive controls, unsupported mesh, unit rescaling, oblique witness, invalid/defective witness, and annulus boundary/interior controls. | PASS |
| `31-validation.md` | Focused command reports `11 passed in 0.07s` under the repository Python hook. | PASS |
| `30-implementation.md` | Accurately records the changed implementation scope and preserves the float64/predecessor and empirical ceilings. | PASS |

### Certificate labels and ceilings

- `VERIFIED_RATIONAL_FULL_CIRCLE_ENCLOSURE` is emitted only after all four
  exact node inverses, dyadic inequalities, chord checks, and a positive
  conservative lower separation pass.
- `VERIFIED_RATIONAL_ANALYTIC_STRIP_ENCLOSURE` additionally requires a valid
  exact diagonalization witness, strict closed-annulus exclusion, and positive
  certificates on the central, inner, and outer contours.
- Singular nodes, nonpositive bounds, invalid witnesses, and annulus failures
  remain named non-certificate outcomes. A failed certificate is not evidence
  of contour-spectrum intersection.
- The implementation certifies only the declared finite rational input. It
  does not certify float64 data, measured neural matrices, biological metrics,
  consciousness, or rank 4-6.

### Changed-path and final gate record

The approved changed paths are the standalone module, its focused test, and
the run records `30-implementation.md` and `31-validation.md`. No canonical
CE document, empirical data, or Git publication was changed by this audit.

P0: none. P1: none after the implementation revision. P2 remains limited to
the conservative fixed-four-node bound and the intentionally restricted V3
witness route. Final decision: `Status: COMPLETE`, `Gate: PASS`.
