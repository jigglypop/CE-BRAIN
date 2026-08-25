# Induced-norm tightening validation

Status: COMPLETE

Focused command:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.codex\hooks\python.cmd pytest tests/test_verified_interval_tightening.py -vv -s --tb=short
```

Final result: **13 passed in 0.10 s**. The first collection attempt exposed a
test syntax error, and the next run exposed an invalid assertion that an
outward dyadic upper must equal the underlying nondyadic value. The test was
corrected to verify the squared enclosure; no implementation condition was
relaxed.

Coverage includes diagonal strict improvement, a tightened pass with preserved
Frobenius non-certificate, asymmetric Frobenius selection, scalar tie policy,
entry/product residuals, zero and strict failure, schema adversaries, exact
unit invariance, nonnormal optional projector composition, invalid strip, and
unsupported mesh.

Adjacent command over exact nominal, Frobenius interval, and tightening files:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.codex\hooks\python.cmd pytest tests/test_verified_rational_contour.py tests/test_verified_interval_contour.py tests/test_verified_interval_tightening.py -q --tb=short
```

Result: **39 passed in 0.25 s**.

Dimensionless gate: `tests/test_dimensionless.py`, **22 passed in 0.09 s**.
The new check distinguishes raw spectral-unit row/column sums and their
spectral-squared product from the dimensionless normalized core.

Exact theorem fixture: `PASS: induced 1/infinity interval tightening spot checks`.
No full suite or empirical action was run.
