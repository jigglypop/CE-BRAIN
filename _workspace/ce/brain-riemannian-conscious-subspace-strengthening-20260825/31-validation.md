# Focused implementation validation

Status: COMPLETE

Validation result: **POWERSHELL_L0_PASS / PYTHON_NUMPY_L0_2X_PASS / HISTORY_EDGE_17_PASS / DIMENSIONLESS_20_PASS_SYNTAX_MANUAL_HEURISTIC / PACKAGE_DOCTOR_TORCH_PREREQUISITE**

CE_RUN: `_workspace/ce/brain-riemannian-conscious-subspace-strengthening-20260825`

## Dimensionless focused test

```powershell
.codex\hooks\python.cmd pytest tests/test_dimensionless.py
```

Observed on 2026-08-25 through the policy-allowed discovered system Python
`C:\Python314\python.exe` (Python 3.14.2):

```text
20 passed in 0.08s
```

The command used `-rs` and produced no skips. No SymPy was installed. Every
registry-focused test ran through the explicit
`stdlib.ast.parse.syntax_only` backend, which establishes parser-safe syntax
and evaluates the existing manual heuristic only; it is not a symbolic
dimensional proof. Formula results expose
`validation_level: SYNTAX_ONLY_HEURISTIC` and the distinct
`PASS_SYNTAX_ONLY` status whenever the heuristic succeeds.

## History-edge subspace focused test

```powershell
.codex\hooks\python.cmd pytest tests/test_history_edge_subspace.py
```

Observed on 2026-08-25 through the same hook:

```text
17 passed in 0.15s
```

An earlier direct history-test attempt encountered
`OpenBLAS error: Memory allocation still failed after 10 retries` while the
default numerical worker count was allowed. The harness now deterministically
sets `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, and
`NUMEXPR_NUM_THREADS` to `1` for child processes. No caller environment
override was supplied for the recovered runs above. This constrains resource
usage only; it does not alter test fixtures, assertions, or the model.

This standalone-import test does not load the optional torch-backed package
facade. It covers coercivity and the
baseline-free counterexample; small and full-deletion perturbation certificates
with the sufficient `eta < 1` flag; separate topology input; gapped orthogonal
spectral subspaces (including simple and repeated real-normal conjugate pairs)
with normality/invariance residual certificates and near-nonnormal rejection;
canonical symmetric/PSD roundoff projection and material-negative rejection;
certificate-bearing orthogonal concentration with near-projector
canonicalization and oblique/material-idempotence rejection; effective dimension versus positive-spectrum and
thresholded numerical rank; and mobility scale.

## Package doctor boundary

```powershell
.codex\hooks\python.cmd doctor
```

This broader package-facade diagnostic remains blocked, separately from both
focused source tests:

```text
ModuleNotFoundError: No module named 'torch'
```

No torch installation was attempted. This failure concerns
`reality_stone.__init__` importing the optional package facade; it does not
invalidate the standalone history-edge result or the non-SymPy dimensionless
checks.

## Finite nonnormal contour focused test

```powershell
.codex\hooks\python.cmd pytest tests/test_finite_riesz.py
```

Observed after the resource-deterministic harness retry:

```text
6 passed in 0.15s
```

The test covers the audited oblique 3x3 fixture, scaled transition/contour
normalization invariance (including scaling `spectral_reference_scale`), contour crossing/non-real-center rejection, coarse
rank-guard rejection with a separate residual witness, a real rotation pair,
and a nonnormal pseudospectral adversary. The adversary has a positive finite
numerical eigenvalue margin together with a large sampled resolvent norm; this
remains finite a-posteriori evidence only, with `quadrature_error_bound: None`.
Raw sampled separation carries spectral units, while raw sampled resolvent norm
carries reciprocal spectral units; strict decisions use only the certificate's
normalized quantities.

An earlier allocation interruption reported `OpenBLAS error: Memory allocation
still failed after 10 retries`; the final rerun above completed under the same
single-thread child harness without caller overrides. This is not an analytic
contour proof or a rank-stability claim.

## Deterministic L0 algebra fixture

The Python/Numpy fixture executed twice through the policy-allowed hook:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-riemannian-conscious-subspace-strengthening-20260825\artifacts\spot_checks.py
```

Both invocations exited `0` and returned identical JSON:

```json
{
  "baseline_free_min_eigenvalue": 0.0,
  "baseline_min_eigenvalue": 1.0,
  "effective_dimension_lambda_1": 1.5,
  "local_bound_holds": true,
  "local_squared_length_difference": 0.24700000000000003,
  "oblique_contract_concentration": 1.5,
  "on_min_eigenvalue": 1.2554396639452299,
  "orthogonal_corrected_concentration": 0.5,
  "perturbation_norm": 1.5244997998398395,
  "riesz_projector_difference_norm": 0.014285714285714284,
  "riesz_rank_after": 2,
  "riesz_rank_before": 2
}
```

A dependency-free PowerShell counterpart was also executed twice:

```powershell
& .\_workspace\ce\brain-riemannian-conscious-subspace-strengthening-20260825\artifacts\spot_checks.ps1
```

Both runs exited `0` with identical JSON and `status: PASS`.  Covered L0
invariants are the edge quadratic-form bound, the baseline-free kernel, the
non-zero skew-drift work counterexample, rank-2 Riesz stability for the frozen
block-triangular fixture, oblique concentration `1.5`, corrected orthogonal
concentration `0.5`, and effective dimension `1.5`.  The exact output is frozen
in `artifacts/spot-check-attempt.md`.

This is deterministic algebra/software evidence only. It neither supplies a
symbolic dimensional proof nor validates a biological metric, a consciousness
mechanism, or a preferred dimension.
