# Quantitative graph-transform validation

Status: COMPLETE

Focused command:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.codex\hooks\python.cmd pytest tests/test_quantitative_graph_transform.py -vv -s --tb=short
```

Result: **26 passed in 0.08 s**.

Coverage includes strict interior, exact tube/slope boundaries, contraction
equality and above, separate/combined failures, exact tracking, zero coupling,
independent base/fiber rescaling, dimensions 1/4/5/6/100, invalid dimensions,
scales/types/bounds, and canonical rational strings.

Adjacent finite-subspace plus graph-transform validation:
`tests/test_history_edge_subspace.py` and
`tests/test_quantitative_graph_transform.py`: **43 passed in 0.34 s**.

Dimensionless gate: `tests/test_dimensionless.py`, **24 passed in 0.10 s**.
The added check verifies fiber radius/forcing ratios and the cross-slope groups
$L_{x,\rm raw}X_*/Y_*$ and $\kappa_{\rm raw}X_*/Y_*$.

Exact theorem fixture returned
`PASS: quantitative triangular graph-transform spot checks`.
No full suite, data action, tolerance, or theorem condition was changed.
