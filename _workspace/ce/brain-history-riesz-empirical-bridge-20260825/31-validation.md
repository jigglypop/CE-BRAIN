# M2 float64 contour-estimate validation

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-history-riesz-empirical-bridge-20260825`

## Focused validation

```powershell
.codex\hooks\python.cmd pytest tests/test_finite_contour_bounds.py
```

Observed on 2026-08-25:

```text
14 passed in 0.15s
```

Coverage includes a diagonal dense-circle fixture, scaled-unit invariance,
nonpositive coarse `delta_hat_estimate`, a nonnormal pseudospectral adverse
case, annulus-spectrum suppression, a clean diagonal strip fixture, and
invalid-input rejection. Revision coverage adds central-circle error comparison
(inner/outer remain M-only), boundary-eigenvalue suppression, empty-matrix
rejection, and extreme-strip exponent preflight rejection.

The strip-fixture comparison is a test-fixture observation only: it does not
turn the float64 `quadrature_error_estimate` into a verified error bound. No
outward rounding, all-contour enclosure, arithmetic certificate, biological
data validation, or empirical bridge result was executed.
