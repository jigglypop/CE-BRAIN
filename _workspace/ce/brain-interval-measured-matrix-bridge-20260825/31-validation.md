# Verified interval-family validation

Status: COMPLETE

Focused command:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.codex\hooks\python.cmd pytest tests/test_verified_interval_contour.py -vv -s --tb=short
```

Final result: **15 passed in 0.09 s**, Python 3.14.2, pytest 9.0.3.

Coverage includes zero and positive uncertainty, exact squared Frobenius and
dyadic residual checks, strict margin failure, nominal certificate failure,
shape/type/sign adversaries, exact normalize-first unit invariance, a nonnormal
nominal matrix, optional projector-bridge summation, invalid strip witness,
unsupported mesh, and invalid precision.

Adjacent predecessor integration command:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.codex\hooks\python.cmd pytest tests/test_verified_rational_contour.py tests/test_verified_interval_contour.py -q --tb=short
```

Result: **26 passed in 0.16 s**. No full suite was run and no assertion,
uncertainty radius, precision, or certificate condition was relaxed.

Dimensionless gate:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.codex\hooks\python.cmd pytest tests/test_dimensionless.py -q --tb=short
```

Result: **21 passed in 0.09 s**. The added check verifies equal spectral units
before `delta - epsilon`, dimensionless normalized inputs, reciprocal spectral
unit for the raw resolvent, and zero total dimension for
`r*epsilon/(delta0*(delta0-epsilon))`. Dimensional consistency is not a proof
of the perturbation theorem or of empirical validity.

The independent exact theorem fixture also passed:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-interval-measured-matrix-bridge-20260825\artifacts\math_interval_spotchecks.py
```

This evidence validates the declared finite apparatus only. It supplies no
observed matrix, statistical interval coverage, neural rank, brain geometry,
consciousness result, or preferred dimension.
