# Formal status audit — post-revision 1

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-riemannian-conscious-subspace-strengthening-20260825`

Gate: PASS

This audit covers the stable revised snapshot: `00-contract.md`,
`10-sources.md`, `11-math.md`, `12-routes.md`, and the recorded artifact
execution status. Only this audit file was changed.

## Verdict

The four P0 defects identified in the first audit are closed in the active
contract. The contract now conditions the strong metric on a coercive baseline
and norm-summable edge series, gives the full drift energy identity and an
explicit neutrality condition, rejects loop-to-fixed-d inference, and uses the
orthogonal projector `Q` with trace-class assumptions for concentration. The
old oblique-projector expression remains only as a clearly labelled retired
counterexample in `11-math.md`. No active P0 parent claim remains.

## Claim decisions

| Claim ID | Revised location and claim | Decision | Level |
|---|---|---|---|
| CE-METRIC-001 | `00-contract.md` §5.1; `11-math.md` Theorem 1: `A=A0+sum b D*KD` is a strong metric under `A0 >= m0 I`, PSD edge terms, operator-norm summability, and stated smoothness | retain as conditional theorem | P1 |
| CE-METRIC-002 | Baseline-free positive edge/connectivity terms alone imply a strong metric | retired; P0-A is a complete kernel counterexample | P0 closed |
| CE-METRIC-003 | `11-math.md` Theorem 2: small edge-weight changes have operator and length bounds when `epsilon < m0` | retain with its coercivity hypothesis; deletion remains a reachability change, not smooth curvature | P1 |
| CE-DRIFT-001 | `00-contract.md` §5.2: directed/skew transport is automatically energy-neutral | retired; revised text requires `D V(x)[Sx]=0` and states the full energy identity | P0 closed |
| CE-SUBSPACE-001 | `00-contract.md` §5.3; `11-math.md` Theorem 4: an isolated finite algebraic spectral cluster gives a stable rank-d Riesz projector under resolvent perturbation | retain conditionally; nonlinear manifold claims still require dichotomy/normal hyperbolicity | P1 |
| CE-SUBSPACE-002 | Loops/recurrent structure force `d=4` or `4<=d<=6` | retired; revised contract makes the menu a comparison only and keeps P0-C as a no-go | P0 closed |
| CE-CONC-001 | Universal `tr(P C P)/tr(C) in [0,1]` for arbitrary Riesz `P` | retired; P0-D supplies the explicit value `3/2` | P0 closed |
| CE-CONC-002 | `00-contract.md` §5.4; `11-math.md` P0-D repair: `c_d^perp=tr(Q C Q)/tr(C)` with `Q` orthogonal onto `Ran P`, `C>=0` trace class, `tr C>0` | retain conditionally; `Q` must not be conflated with nonorthogonal Riesz `P` | P1 |
| CE-DIM-001 | `11-math.md` Theorem 5: trace-class PSD effective dimension for `lambda>0` | retain as observed effective dimension only, not ambient/manifold/consciousness dimension | P1 |
| CE-IDENT-001 | Passive quotient non-identifiability and lossless finite-dimensional no-go | retain; active routes are narrower finite-family/intervention claims | P1 |
| CE-SCALE-001 | Normalized operators, resolvent, `lambda`, concentration and effective dimension are dimensionless; physical mobility/time scale is missing | retain as formal normalization; physical bridge remains open | P2 |
| CE-DATA-001 | No empirical dataset or confirmation endpoint is opened in this run | retain as scope boundary | P1 |

## Closure checks

The revised active narrative no longer asserts any of the following:

- edge PSD/connectivity without coercivity implies a strong metric;
- skewness alone cancels the drift contribution to `dV/dt`;
- recurrence or loops force a particular consciousness dimension;
- a nonorthogonal Riesz projection yields a `[0,1]` concentration through
  `tr(PCP)/tr(C)`.

The corresponding counterexamples in `11-math.md` are correctly retained as
refutations, not promoted claims. The revised route designs also describe rank
4 as a candidate selected from a predeclared menu, never as a theorem.

## Remaining P1/P2 conditions

P1 conditions are explicit but not yet empirically instantiated: uniform
nonlinear-flow hypotheses, real-versus-complex rank convention, trace-class
conditions, and the exact observation/`F_bio` successor contract. P2 remains
the physical units, mobility and time-scale map. These are open bridges, not
contradictions in the revised mathematics.

## Reproducibility

The initial Python prerequisite failure in `artifacts/spot-check-attempt.md`
is historical. The later policy-allowed Python/NumPy rerun passed twice with
identical output. The remaining unexecuted items are the ten legacy SymPy
checks and the broader optional-torch package doctor. Syntax-only parsing must
not be called a symbolic dimensional proof.

## Gate rationale

`Gate: PASS` is warranted: no active P0 claim remains, every retired parent
claim has an explicit counterexample and replacement, and the remaining
claims carry their hypotheses and epistemic ceiling. The remaining optional
dependencies are reproducibility/package prerequisites, not structural or
mathematical closure blockers.

Publication level: `needs-validation` (not empirical confirmation and not
arXiv-ready until the deterministic L0 fixtures execute under an approved
interpreter and the P1/P2 bridges are documented).

## Post-implementation re-audit

The post-implementation snapshot remains closed at P0 and passes the gate.
`artifacts/spot_checks.ps1` was executed twice with exit code 0 and identical
JSON. Its reported witnesses are consistent with the audited mathematics:

- the coercive baseline is `1.0`; the edge quadratic value is `0.247`, below
  the documented operator-norm upper bound `1.8`;
- the baseline-free kernel witness is `(0,0)` after applying the edge matrix;
- the skew-drift work witness is `1.0`, preserving the warning that skewness
  alone is not energy-neutral;
- the frozen isolated block keeps Riesz rank `2 -> 2`, with projector
  difference `1/70`;
- the retired oblique expression is `1.5`, while the orthogonal correction is
  `0.5`, and the effective-dimension fixture is `1.5`.

These are finite deterministic software/algebra witnesses at evidence level
`L0_DETERMINISTIC_ALGEBRA`. They check the implementation fixtures and do not
constitute proofs of the general operator theorems, empirical validation, or
brain/consciousness evidence. The two L0 implementations do not substitute for
the remaining legacy SymPy registry proof or package doctor.

The implementation and final report preserve the retired status of all P0
parents: no baseline-free strong-metric claim, automatic skew neutrality,
loop-to-4--6 claim, or nonorthogonal `[0,1]` concentration claim was
reactivated. The new dimensionless registry entries are restricted to
`c_d_perp`, `d_eff_mode`, and `eta_edge` with their unit and coercivity
conditions.

Accordingly, `Gate: PASS` remains warranted. The remaining limitation is the
legacy symbolic/package prerequisite and the open physical/empirical bridges;
neither is a P0 contradiction or a reason to downgrade the formal closure
gate.

## Post-formula-strengthening re-audit

The additional mathematics is consistent with the existing closure boundary.
The real/complex rank convention correctly counts a real eigenvalue with its
complex algebraic multiplicity and a nonreal conjugate pair as twice that
multiplicity. It is a bookkeeping convention for a real subspace, not a
dimension claim about consciousness.

The nondimensional mobility calculation is dimensionally correct:
`mu0=X0^2/(V0*t0)` makes the coefficient of `A^{-1} grad(V_tilde)` equal to
one after `x=X0 x_tilde`, `V=V0 V_tilde`, and `t=t0 t_tilde`. It is explicitly
left as dimensional algebra; no biological calibration is claimed.

The conditional slow-manifold theorem is appropriately P1. Its hypotheses
(a `C^r`, `r>=2` flow, invariant stable/center/unstable splitting, uniformly
bounded projections, a uniform exponential-dichotomy/normal-hyperbolicity
gap, and a sufficiently small nonlinear remainder) are the conditions needed
for the stated local graph-transform conclusion. The text expressly says that
Riesz isolation alone is insufficient and asserts no premise for a brain
recording. This does not reactivate a P0 claim.

The expanded R1--R4 routes are specifications, not results. Each now has an
estimand, degrees-of-freedom/gauge accounting, controls, and falsifier. R1 is
limited to a gauge-fixed finite SPD family; R2 uses the real-rank convention
and a complete rank menu; R3 states the blind-tail passive ceiling; R4
separates adjacency indicators from continuous metric weights and records the
`b_e K_e` gauge. None identifies an arbitrary ambient metric, proves a fixed
rank, or calls an empirical outcome a theorem.

The prior post-implementation L0 evidence remains valid and unchanged:
PowerShell and Python/NumPy fixtures passed twice with identical output.
Those results are finite deterministic software/algebra evidence only. They do
not prove the general theorems, validate the slow-manifold hypotheses,
establish any route estimand from data, or provide biological/consciousness
evidence. The ten legacy SymPy registry checks remain the explicit symbolic
prerequisite.

No retired P0 parent was reactivated. Therefore the post-strengthening audit
continues to warrant `Gate: PASS`; the remaining status is conditional formal
theory plus specified future routes, not empirical confirmation.

## Post-code implementation audit

The new finite-array seam in
`reality_stone/python/reality_stone/clarus/history_edge_subspace.py` remains
within the audited claim ceiling:

- `FiniteEdgeMetric` requires a finite symmetric positive-definite baseline and
  PSD edge weights. `perturbation_certificate.small_perturbation` records
  `eta < 1` as a sufficient condition only; it does not claim an iff or infer
  coercivity from edges alone.
- `declared_adjacency` is kept separate from availability-weight metric
  deformation, and `topology_with_deleted_edges` is an explicit topology
  fixture. No deletion is represented as smooth curvature.
- `spectral_subspace` rejects nonnormal transitions. For real symmetric/normal
  finite fixtures it constructs an orthogonal projector after an explicit
  spectral gap check, includes conjugate eigenvalue pairs, and exposes both
  hard rank and conjugation-correct real dimension. It is not a general Riesz
  projector implementation.
- `orthogonal_concentration` enforces a symmetric idempotent projector,
  positive-semidefinite covariance, and positive trace, so the bounded
  `c_d^perp` claim is not extended to arbitrary oblique `P`.
- `effective_dimension` reports the regularized observed quantity separately
  from hard rank, and `mobility_scale` implements only the previously audited
  reference-scale algebra with positive finite inputs.

The focused Python history-edge tests cover these seams and passed 17/17
through the approved interpreter. The twice-executed PowerShell fixture remains
`POWERSHELL_L0_PASS`; it is finite deterministic software/algebra evidence,
not execution of the Python tests, a proof of the general theorems, or
empirical validation of a biological mechanism. The implementation and
validation records state this separation explicitly.

No code path selects a preferred dimension, identifies a brain metric, treats
the effective dimension as ambient/manifold/consciousness dimension, or
reactivates any retired P0 claim. Accordingly, this post-code audit preserves
`Gate: PASS`; the outstanding items are legacy SymPy/package-doctor
prerequisites and the declared physical/empirical bridges, not a closure
defect.

## Independent implementation re-review — superseding decision

The independent math review found implementation-level closure defects that
must be repaired before the gate can remain PASS:

| Claim ID | Defect | Severity | Required action |
|---|---|---|---|
| CE-CODE-METRIC-001 | `_symmetric` accepts an approximately symmetric matrix but stores the original, potentially non-symmetric matrix. `FiniteEdgeMetric` can therefore expose a metric that is not exactly self-adjoint, despite the audited theorem requiring self-adjointness. | P0 | Reject near-asymmetric input unless it is exactly symmetric under the declared numerical contract, or explicitly symmetrize and record the tolerance/error. Add a focused regression proving the stored baseline and edge weight satisfy the promised invariant. |
| CE-CODE-PSD-001 | `_psd` accepts eigenvalues in `[-1e-10,0)` and stores the unchanged matrix. `effective_dimension` can then receive a slightly negative eigenvalue and return a negative mode contribution, violating the claimed PSD/effective-dimension bounds. | P0 | Reject negative eigenvalues, or project/clip with an explicit error budget and validate the resulting matrix. Add a regression that near-negative input cannot produce negative effective dimension. |
| CE-CODE-SPEC-001 | The `allclose` normality branch can accept technically nonnormal input within tolerance, while the returned orthogonal projector is then not an exact spectral/Riesz projector. | P1 | Use an explicit normality residual and declared tolerance; either reject nonzero residual or label the result an approximate finite normal fixture. Verify `Q^2=Q`, `Q^T=Q`, and the invariant-subspace residual before returning. |
| CE-CODE-RANK-001 | `hard_rank` uses an undocumented absolute eigenvalue threshold, so rank is tolerance-dependent but exposed as an unqualified hard rank. | P1 | Expose/store the threshold and label this `numerical_hard_rank`, or define a scale-aware threshold. Document that it is not exact algebraic rank. |
| CE-CODE-CONJ-001 | The conjugate partner is selected by `argmin` without checking residual, uniqueness, or equal algebraic multiplicity. | P1 | Check `|lambda_partner-conj(lambda)|`, multiplicity/uniqueness, and selected-set closure under conjugation; reject ambiguous or failed pairings. |

These defects are not evidence of a biological overclaim, and the retired
theoretical P0 parents remain retired. However, they make the current code
implementation stronger than its actual guarantees: a code-level P0 violation
of the self-adjoint/PSD preconditions is enough to require revision. The
PowerShell L0 fixture does not exercise these near-tolerance adversarial
inputs and therefore cannot close this audit finding; the focused Python tests
are now executed, while legacy SymPy checks and package doctor remain separate
prerequisites.

At the prior pre-fix snapshot the superseding decision was `Gate: REVISE`.
The final post-fix section below evaluates whether the listed actions have
since closed that decision. No other file was modified by this audit.

## Final post-fix re-audit

The implementation revision closes the independent code-level findings. The
canonical `_symmetric` path now stores the symmetrized representative, while
`_psd` rejects material negative spectrum and clips only the declared
roundoff band to the PSD cone. Consequently the finite metric and effective
dimension helpers no longer carry the previously identified self-adjointness
or negative-mode defects.

`SpectralSubspace` now exposes rank tolerance and canonicalization, normality,
and invariance residuals. It rejects residuals beyond the certificate
tolerance, checks near-real ambiguity and conjugate-pair multiplicity, and
returns an explicitly certified orthogonal finite fixture rather than claiming
general nonnormal Riesz calculus. `EffectiveDimension` distinguishes positive
spectrum rank from numerical hard rank. `ConcentrationCertificate` exposes
symmetry/idempotence residuals and the canonical orthogonal projector.

The added focused tests cover each former P0/P1 boundary: tolerance
canonicalization, roundoff-negative PSD projection versus material-negative
rejection, scale-aware normality, near-real rejection, repeated conjugate
pairs, projector certificates, and positive-spectrum versus numerical rank.
The focused tests are executed evidence for the finite source seam, but not
general theorem proof or empirical validation. The independent finite-L0
PowerShell result remains separate evidence.

No retired P0 claim was reactivated, and the physical mobility expression
remains dimensional algebra only with the P2 calibration bridge open.
Therefore the final superseding decision is `Gate: PASS`, conditional on the
declared finite numerical certificates and with legacy symbolic/package
prerequisites and biological/empirical identification still explicitly
outstanding.

## Final closure consistency audit

The canonical paper, claim ledger, final report, and code map are consistent
with the audited ceiling. They all present the result as conditional formal
theorems plus finite L0 witnesses, retain the four retired P0 parents as
counterexamples rather than active claims, and state that 4--6 is only a
predeclared candidate menu. R1--R4 are written as future specifications with
estimands, controls, and falsifiers; no route is reported as having opened
data or selected a winner.

The rank vocabulary is also correctly separated across the documents:

- exact theorem rank is the finite algebraic multiplicity inside an isolated
  contour;
- real dimension applies the real-eigenvalue/conjugate-pair convention;
- `positive_spectrum_rank` is the exact positive-mode count used for the
  finite PSD effective-dimension upper bound;
- `numerical_hard_rank` is the explicitly tolerance-thresholded implementation
  label and is not exact algebraic rank.

The final report and canonical paper describe the code as finite symmetric,
certified real-normal, and separately a finite a-posteriori nonnormal contour
seam—not as general nonnormal Riesz calculus. They
retain the orthogonal `Q` concentration formula and certificate residuals,
the separate adjacency input, the mobility-scale algebra, and the distinction
between PowerShell/Python L0 execution and legacy SymPy tests. The ledger
records the same statuses and does not promote L0 or simulator output to brain,
consciousness, or empirical evidence.

No cross-document P0/P1 contradiction or overclaim was found. `Gate: PASS`
therefore remains warranted for the formal closure snapshot. Remaining open
items are exactly the ledger's legacy symbolic/package prerequisite, physical
mobility calibration, real biological measurement, and future route data—not a defect
in the current claim classification.

## Final validation-status re-audit

The validation record now reflects the discovered policy-allowed
`C:\Python314\python.exe` (Python 3.14.2) and is internally consistent:

- `tests/test_history_edge_subspace.py`: standalone focused execution passed
  `17/17`. This supports the finite implementation boundaries and certificates
  only; it is not a full package or doctor run.
- `tests/test_dimensionless.py`: `20 passed, 0 skipped`. The three new
  registry entries execute via the explicitly named
  `stdlib.ast.parse.syntax_only` fallback. That fallback checks parser-safe
  syntax and preserves declared unit notes; it is not a symbolic dimensional
  proof. The remaining ten checks pass through the available non-SymPy manual
  path rather than a SymPy proof.
- `python.cmd doctor` remains blocked by the optional `torch` facade import.
  This is a package-environment boundary, not evidence against the standalone
  finite module or the focused dimensionless checks.
- The PowerShell L0 fixture remains a separate deterministic algebra result.
  The historical Python/Numpy spot-check attempt was not silently relabelled
  as rerun; its record remains distinct from the newly executed focused
  source tests.

The implementation, final report, canonical paper, and claim ledger all retain
the distinctions among syntax-only parsing, focused source execution, package
doctor health, general mathematical proof, and biological/empirical evidence.
They also continue to mark R1--R4 as candidate routes, not results, and retain
the exact-rank/positive-spectrum-rank/numerical-hard-rank separation.

No retired P0 claim was reactivated. The doctor prerequisite and ten legacy
SymPy skips are reproducibility/package boundaries rather than closure defects
in the audited finite seam. Therefore `Gate: PASS` remains warranted, with the
claim ceiling still limited to conditional mathematics and finite L0 evidence,
not biological identification or a preferred consciousness dimension.

## Final executed-evidence closure

The latest stable records close the prior Python/NumPy execution prerequisite:
`spot_checks.py` ran twice under the policy-allowed Python 3.14.2 hook with
identical JSON and exit code 0. The standalone history-edge focused suite is
`17/17 passed`. The dimensionless focused suite is now `20/20 passed` with no
skips. The three new registry entries report backend
`stdlib.ast.parse.syntax_only`, validation level `SYNTAX_ONLY_HEURISTIC`, and
status `PASS_SYNTAX_ONLY`; the remaining checks use the available non-SymPy
manual path.

The syntax-only backend establishes parser-safe registration and preserves the
declared unit notes. It is not SymPy symbolic dimensional proof. Likewise,
the focused standalone source tests do not establish full package health:
`python.cmd doctor` remains separately blocked by the optional `torch` facade.
The PowerShell and Python/NumPy L0 results are finite algebra/software
reproduction evidence, not general theorem proofs or biological/empirical
validation.

The final report, canonical paper, ledger, implementation record, and code map
use the same statuses and continue to distinguish exact theorem rank,
`positive_spectrum_rank`, and `numerical_hard_rank`. They preserve candidate
status for R1--R4 and explicitly reject the 4--6 consciousness-dimension
overclaim. No stale active claim promotes the old Python prerequisite failure,
syntax-only parsing, focused source execution, or L0 output into symbolic
proof, package-doctor success, or brain evidence. `Gate: PASS` remains
warranted.

## Final-final harness closure addendum

The OpenBLAS allocation failure was reproduced. The harness fix sets BLAS/OMP
numerical thread counts to `1` for child processes only; it does not alter
fixtures, assertions, formulas, or model-selection logic, and recovered runs
required no caller-environment override. This is resource control, not a
scientific or numerical-result adjustment.

The final report, paper, ledger, and completion records now use the same
executed statuses. The optional `torch` package doctor prerequisite and the
empirical bridge remain open. No retired P0 claim, preferred consciousness
dimension, symbolic-proof claim, or biological overclaim was reintroduced.
`Gate: PASS` remains warranted.

## Final finite-Riesz implementation closure addendum

The new `finite_riesz.py` seam and `tests/test_finite_riesz.py` resolve the
R5 implementation scope without exceeding it. The focused suite passed `6/6`
sequentially. It covers the oblique 3x3 fixture, scaled
`spectral_reference_scale` normalization, contour/non-real-center rejection,
coarse quadrature rank guarding, conjugation-closed real rotation, and the
pseudospectral adversary.

The implementation keeps exact and approximate objects distinct: `P_N` and
`P_2N` are finite circular trapezoid approximants, the returned orthogonal
range projector is for concentration, and the certificate explicitly reports
`FINITE_A_POSTERIORI_CONTOUR_APPROXIMATION` with no quadrature error bound.
Sampled separations and resolvent norms retain their raw spectral units, while
strict residual decisions use normalized quantities. The mandatory positive
`spectral_reference_scale` has the transition/center/radius spectral unit, and
the scale-invariance test confirms the normalized decisions are unchanged by
common scaling.

The earlier OpenBLAS allocation interruption is recorded as a historical
parallel/resource failure. The sequential rerun completed under the harness's
single-thread child settings without caller overrides; this changes resource
usage only and does not alter fixtures, assertions, contour formulas, or
certificate labels. It is not evidence of an analytic all-contour bound.

The full-contour resolvent condition, analytic-strip requirement, sampled-gap
warning, coarse-quadrature scalar counterexample, 3x3 oblique fixture, and
pseudospectral adversary remain explicit in `11-math.md`. R5 remains a future
finite numerical/operator certificate route with estimand, DOF, controls, and
falsifier—not an executed brain result. No fixed dimension, biological
mechanism, or consciousness identification was promoted. `Gate: PASS` remains
warranted.

## Nonnormal contour-Riesz closure audit

The new Theorem 10 and R5 material is consistent with the closure gate. The
contour parametrization has the correct factor and sign:
`dz=i r exp(i theta) dtheta`, so
`(2 pi i)^(-1) integral (zI-U)^(-1) dz` becomes
`(2 pi)^(-1) integral r exp(i theta)(zI-U)^(-1) dtheta`, and the periodic
trapezoid is the stated `1/N` sum. The exact projector `P` is explicitly
separated from the sampled approximation `P_N`; only `P` is asserted to be
idempotent and commuting with `U`.

The realification conditions are correctly stated: a real contour and a
conjugation-closed selected cluster give a real range, nonreal eigenvalues
must be paired, and the real dimension follows the earlier conjugate-pair
convention. The orthogonal range projector `Q` is reserved for concentration
and is not substituted for oblique `P` in the Riesz identity.

The evidence labels are appropriately conservative. Sampled separation,
sampled resolvent norms, `N` versus `2N` agreement, idempotence/commutator
residuals, and realification conditioning are finite a-posteriori
certificates; they are not all-contour separation or exact quadrature error
bounds. The analytic-strip inequality is explicitly conditional on a
certified strip and uniform bound, rather than inferred from samples.

The perturbation statement uses the full-contour resolvent
`R_Gamma` and `R_Gamma ||E|| < 1`, which is the required pseudospectral
conditioning hypothesis. It does not replace this by eigenvalue distance.
The explicit 3x3 diagonalizable nonnormal fixture has the stated eigenvalue
enclosure, oblique exact `P`, and orthogonal range `Q`. The upper-triangular
large-coupling adversary and scalar coarse-quadrature example correctly kill
the corresponding overclaims.

R5 is a future candidate route, not an executed result. Its estimands,
contour/mesh/rank/threshold degrees of freedom, conjugation convention,
controls, and `NONNORMAL_RIESZ_NOT_CERTIFIED` falsifier are explicit. It
cannot certify a brain subspace or consciousness dimension. No P0 parent was
reactivated and no P1 condition was silently promoted to evidence; therefore
`Gate: PASS` remains warranted.
