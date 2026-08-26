# Validation

Status: COMPLETE

## Focused command

```text
.codex\hooks\python.cmd pytest tests/test_verified_interval_similarity_residual.py -q
```

Result: `8 passed`.

Covered cases: zero-radius reduction, small nonzero interval pass, equality
failure, exact sampled transformed-box containment, exact sampled inverse
containment, raw-scale covariance, invalid-input refusal, and provenance flags.

## Adjacent and dimensional checks

The interval/fixed-dense/dense-menu/base-residual/dimensionless combined command
passes 119/119.  After the interval-similarity dimensional audit was added, the
standalone dimensionless suite passes 65/65.  Source compilation passes and the
exact eight-file research gate reports `OK final`.
