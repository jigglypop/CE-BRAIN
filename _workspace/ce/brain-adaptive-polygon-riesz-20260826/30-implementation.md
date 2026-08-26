# Implementation

Status: COMPLETE

## Module

`reality_stone/python/reality_stone/clarus/verified_adaptive_polygon_riesz.py`

The module stores every round's panel vector, complete quadrature result, exact set
of refined edges, final rank or exhaustion, and flags for determinism, fixed
geometry, provenance, and contour discovery.

## Tests

`tests/test_verified_adaptive_polygon_riesz.py` covers uniform success, zero-budget
exhaustion, maximum-error scheduling, exact ties, deterministic replay, interval
inheritance, nonbinary multipliers, scale covariance, invalid contracts, and
honesty flags.
