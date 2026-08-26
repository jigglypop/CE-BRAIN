# Stage 1 Armijo retry pre-execution validation

Status: COMPLETE

Gate: PASS

Focused command:

```powershell
.codex\hooks\python.cmd pytest _workspace\ce\brain-ce-brain-synthetic-world-model-discrimination-20260826\artifacts\epochs\stage1-allen-armijo-optimizer-retry\test_stage1_allen_armijo_retry.py -q
```

Stable result: `5 passed in 0.14s`.

The suite is fixture-only and opens no Allen raw, DEV or confirmation value. It
covers quasi-separable full-Newton worsening versus Armijo convergence,
nonfinite/degenerate kills, stationary zero-gradient convergence, gradient/alpha
optimizer-receipt rejection, exact local prereg population, and temporary
result reload rejection for local manifest, decision, model and receipt mutation.

No retry manifest or result existed when this document was written.
