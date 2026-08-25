# L0 spot-check execution record

Status: COMPLETE

Validation verdict: **POWERSHELL_L0_PASS / PYTHON_NUMPY_PARITY_PASS**

## Historical unavailable-interpreter attempt

The first attempted Python command was:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-riemannian-conscious-subspace-strengthening-20260825\artifacts\spot_checks.py
```

Observed result on 2026-08-25:

```text
CE Python harness: no policy-allowed system Python >=3.10 was found.
Set CE_PYTHON to an approved system interpreter; do not bypass Application Control.
```

No alternative Python interpreter or policy bypass was used for that failed attempt.

## Policy-allowed deterministic fallback

The same finite L0 invariants were also encoded without third-party numerical
dependencies in `spot_checks.ps1`.  The script uses exact finite formulas where
available and a documented symmetric operator-norm upper bound for the edge
quadratic-form inequality.

Executed twice:

```powershell
& .\_workspace\ce\brain-riemannian-conscious-subspace-strengthening-20260825\artifacts\spot_checks.ps1
```

Both executions exited with code `0` and returned the same values:

```json
{
  "status": "PASS",
  "evidence_level": "L0_DETERMINISTIC_ALGEBRA",
  "baseline_min_eigenvalue": 1.0,
  "perturbation_operator_norm_upper_bound": 1.8,
  "normalized_edge_bound": 1.8,
  "local_squared_length_difference": 0.247,
  "local_bound_holds": true,
  "baseline_free_kernel_witness": [0.0, 0.0],
  "skew_drift_work": 1.0,
  "riesz_rank_before": 2,
  "riesz_rank_after": 2,
  "riesz_projector_difference_norm": 0.014285714285714285,
  "oblique_retired_concentration": 1.5,
  "orthogonal_corrected_concentration": 0.5,
  "effective_dimension_lambda_1": 1.5
}
```

## Policy-allowed Python/NumPy parity rerun

After a policy-allowed Python 3.14.2 became available, the same NumPy fixture
was executed twice:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-riemannian-conscious-subspace-strengthening-20260825\artifacts\spot_checks.py
```

Both runs exited with code `0` and returned identical JSON:

```json
{
  "baseline_min_eigenvalue": 1.0,
  "baseline_free_min_eigenvalue": 0.0,
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

The PowerShell fixture's perturbation value 1.8 is a documented rigorous upper
bound, while the NumPy result is the actual spectral norm; the two are
consistent. This closes the Python/NumPy fixture execution prerequisite. It
does not make a SymPy registry test pass and is not a mathematical proof or an
empirical brain result; those evidence levels remain separate.
