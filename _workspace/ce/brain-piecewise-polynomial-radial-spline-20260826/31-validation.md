# Validation

Status: COMPLETE

## Focused commands

```text
.codex\hooks\python.cmd pytest tests/test_verified_piecewise_polynomial_radial_contour_residual.py -q
.codex\hooks\python.cmd pytest tests/test_verified_piecewise_polynomial_radial_polygon_rank_bridge.py -q
```

Results: residual `10 passed`; rank bridge `11 passed`.

## Adjacent and document checks

The spline/polynomial/radial/ellipse/adaptive-quadrature/polygon/mesh/residual/
contour dependency chain passes 170/170.  Adding dimensionless and
canonical-ledger suites passes 248/248; the dimensionless suite itself is 74/74.
Both sources compile and the exact eight-file gate reports `OK final`.
