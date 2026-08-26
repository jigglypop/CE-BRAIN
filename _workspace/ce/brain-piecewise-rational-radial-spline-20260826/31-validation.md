# Validation

Status: COMPLETE

## Focused commands

```text
.codex\hooks\python.cmd pytest tests/test_verified_piecewise_rational_radial_contour_residual.py -q
.codex\hooks\python.cmd pytest tests/test_verified_piecewise_rational_radial_polygon_rank_bridge.py -q
```

Results: residual `9 passed`; rank bridge `11 passed`.

## Adjacent and document checks

The rational-spline/polynomial-spline/global-radial/ellipse/adaptive-quadrature/
polygon/mesh/residual/contour dependency chain passes 190/190.  Adding
dimensionless and canonical-ledger suites passes 269/269; the dimensionless suite
itself is 75/75.  Both sources compile and the exact eight-file gate reports
`OK final`.
