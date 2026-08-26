# Implementation

Status: COMPLETE

## Module

`reality_stone/python/reality_stone/clarus/verified_rational_polygon_residual.py`

The module implements exact orientation and intersection predicates, signed area,
outward edge lengths, exact nominal node-witness construction, componentwise
residual checks, edge margins, uniform resolvent and projector bounds, raw-scale
translation, and explicit provenance/rank-value flags.

## Tests

`tests/test_verified_rational_polygon_residual.py` covers a square, a concave
polygon, four-to-sixteen node refinement, seven invalid geometries, singular node,
witness-count refusal, inexact witness checking, scale covariance, and honesty
flags.
