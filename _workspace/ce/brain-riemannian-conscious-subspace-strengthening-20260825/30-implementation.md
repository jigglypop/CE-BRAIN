# Audit-approved finite L0 implementation

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-riemannian-conscious-subspace-strengthening-20260825`

Gate prerequisite: `20-audit.md` is `Gate: PASS`.

## Scope implemented

Only the audit-approved scalar dimensionless registry entries and their focused
test were added:

| Symbol | Parser-friendly scalar surrogate | Required dimensional condition |
|---|---|---|
| `c_d_perp` | `trace_projected_covariance/trace_covariance` | Numerator and denominator use the same covariance (or precision) unit; the mathematical expression uses an orthogonal `Q_d`, not an arbitrary Riesz `P_d`. |
| `d_eff_mode` | `eigenvalue/(eigenvalue+lambda_reg)` | Parser-safe `lambda_reg` denotes $\lambda$: each spectral eigenvalue and the regularizer have identical operator-eigenvalue units; the full effective dimension is the stated trace/mode sum under its trace-class assumptions. |
| `eta_edge` | `epsilon_A/m0` | The edge perturbation norm and coercive baseline lower bound have the same metric-operator unit; the perturbative theorem additionally requires `epsilon_A < m0`. |

The registry notes preserve the conditions that make each ratio meaningful.
They explicitly do not identify an ambient/manifold/consciousness dimension,
infer a fixed `d`, or implement a biological identification claim.

`dimensionless_checker.py` now has an optional parser backend: when SymPy is
available it uses `sympy.parse_expr`; otherwise the explicitly named
`stdlib.ast.parse.syntax_only` backend applies minimal `^` to `**`
normalization and checks expression syntax only. The fallback does not prove
symbolic dimensional consistency; it merely permits the three parser-safe
scalar registry entries and their documented unit assumptions to be checked
without installing SymPy. Every checker result now exposes `parser_backend`
and `validation_level`; a syntax-only heuristic success is explicitly
`PASS_SYNTAX_ONLY`, not an ordinary symbolic-looking pass. The same fallback
now executes every registry-focused test in `tests/test_dimensionless.py`; it
does not elevate any of those manual/heuristic checks to symbolic dimensional
proof.

## Finite history-edge subspace seam

`history_edge_subspace.py` adds a separate finite-array implementation of the
audited conditional statements. It validates a coercive symmetric baseline and
PSD edge terms, records `eta < 1` only as a sufficient perturbation condition
(not an iff), and leaves declared
adjacency immutable while topology deletion is an explicit separate input.
Tolerance-accepted symmetric inputs are first canonically symmetrized, and PSD
inputs in the accepted negative-roundoff band are explicitly projected to the
PSD cone; material negative eigenvalues are rejected. Its spectral helper
accepts only real symmetric or real-normal finite transitions; the latter is
returned only with scale-aware normality and invariant-subspace residual
certificates; symmetric tolerance acceptance also records an
`input_canonicalization_residual`, and near-real complex eigenvalues inside the
conjugate matching band are rejected as ambiguous. The returned object is an
orthogonal finite spectral projector, not a general Riesz projector. Its
`numerical_rank`/`numerical_hard_rank` labels carry an explicit
`rank_tolerance` and are not exact algebraic-rank claims. Effective dimension
separately exposes `positive_spectrum_rank` (the theorem-style upper bound) and
thresholded `numerical_hard_rank`; it is bounded only by the former. The
remaining helpers enforce the hypotheses for orthogonal concentration and the
positive reference scales in the dimensional mobility expression.

Orthogonal concentration now returns a `ConcentrationCertificate`, not a bare
number. It reports raw-input symmetry and post-symmetrization idempotence
residuals, the certificate tolerance, and an eigenspace-canonical orthogonal
projector. Only projector eigenvalues within tolerance of `0` or `1` are
canonically projected; material non-idempotence or obliqueness is rejected.

No helper identifies a brain mechanism, selects a preferred dimension, or
turns a metric-weight change into a reachability claim.

## Changed paths

- `reality_stone/python/reality_stone/clarus/dimensionless_checker.py`
- `tests/test_dimensionless.py`
- `reality_stone/python/reality_stone/clarus/history_edge_subspace.py`
- `tests/test_history_edge_subspace.py`
- `reality_stone/python/reality_stone/clarus/finite_riesz.py`
- `tests/test_finite_riesz.py`
- `.codex/hooks/python.cmd`
- `.codex/hooks/python_harness.py`

The hook now discovers an already-present all-users system Python at
`%SystemDrive%\Python314\python.exe` through `Python310` only after its prior
explicit and per-user candidates. It performs no installation, environment
creation, policy override, or dependency resolution. The history-edge test
uses a direct file-spec import so its finite NumPy seam does not import the
optional torch-backed package facade.

The Python harness also forces `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`,
`MKL_NUM_THREADS`, and `NUMEXPR_NUM_THREADS` to `1` only in child processes.
This is resource determinism for constrained worker memory, not a test-input,
test-assertion, or mathematical-model alteration.

## Finite nonnormal contour seam

`finite_riesz.py` is independent of `history_edge_subspace.py`. It computes
the finite circular trapezoid approximants `P_N` and `P_2N` and returns a
`FiniteRieszCertificate` labelled
`FINITE_A_POSTERIORI_CONTOUR_APPROXIMATION`. The certificate separates the
generally oblique complex approximant from an orthogonal projector onto its
realified numerical range, reports only sampled resolvent separation/norms and
finite residuals, and leaves `quadrature_error_bound` as `None`. It rejects
ambiguous/crossing eigenvalue classifications, nontrivial-rank failures,
non-conjugation-closed selections, and strict finite residual failures. It
does not claim an all-contour separation proof or analytic-strip quadrature
bound.

`spectral_reference_scale` is mandatory, positive, and has the same units as
`U`, `c`, and `r`. The spectral normalization is
`max(s_ref, ||U||_2, |c|, r, max|eig(U)|)`: raw sampled separation has spectral
units, raw sampled resolvent norm has reciprocal spectral units, and their
certificate counterparts are dimensionless. Strict checks use dimensionless
residuals: refinement is divided by `max(1, ||P_N||_2, ||P_2N||_2)`, imaginary
content by `max(1, ||P_2N||_2)`, idempotence by `max(1, Pscale, Pscale^2)`, and
the commutator by `spectral_scale * Pscale`, where
`Pscale=max(1, ||P_2N||_2)`. The realified rank threshold is relative,
`rank_tolerance * max(1, sigma_max)`, and its effective value/ambiguity band
are exposed in the certificate.

## Post-gate deterministic validation artifact

`artifacts/spot_checks.ps1` is a dependency-free PowerShell counterpart to the
finite L0 fixture. Its exact scope is limited to the frozen algebraic
witnesses: edge quadratic-form bound, baseline-free kernel, skew-drift-work
counterexample, rank-2 Riesz stability, retired oblique concentration,
corrected orthogonal concentration, and effective dimension. It does not run
the Python/SymPy registry test and does not add a biological identification,
fixed-dimension, or empirical validation claim.

The existing `artifacts/spot_checks.py` was not changed. It has now executed
twice under the policy-allowed system Python with identical exit-0 JSON; the
exact Python/Numpy and PowerShell evidence are separately recorded in
`31-validation.md` and `artifacts/spot-check-attempt.md`.
