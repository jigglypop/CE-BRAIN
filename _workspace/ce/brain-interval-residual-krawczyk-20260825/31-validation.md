# Componentwise residual validation

Status: COMPLETE

Focused command:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.codex\hooks\python.cmd pytest tests/test_verified_interval_residual.py -vv -s --tb=short
```

Result: **14 passed in 0.11 s**.

Coverage includes the structured global-fail/residual-pass witness, exact and
inexact inverse witnesses, strict contraction equality, node-pass/chord-fail,
witness count/shape/type adversaries, exact unit invariance, nonnormal optional
projector composition, invalid nominal strip, invalid uncertainty, and mesh
rejection.

Four-stage adjacent command over nominal, global interval, induced tightening,
and residual modules returned **53 passed in 0.35 s**.

Dimensionless gate: `tests/test_dimensionless.py`, **23 passed in 0.10 s**.
The added check verifies raw inverse-witness times spectral node matrix is
dimensionless and all normalized residual contractions/inverse bounds remain
dimensionless.

Exact theorem fixture returned
`PASS: componentwise residual/Krawczyk contour spot checks`.
No full suite, data action, or assertion relaxation occurred.
