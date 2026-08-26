# Implementation

Status: COMPLETE

## Module

`reality_stone/python/reality_stone/clarus/verified_polygon_riesz_quadrature.py`

The module constructs exact midpoint nodes and inverses, the unscaled Q(i)
projector integral sum, edge and total remainder bounds, a Machin pi bracket, the
scaled rational projector approximation, every possible integer rank, and explicit
nominal/family/provenance/adaptivity flags.

## Tests

`tests/test_verified_polygon_riesz_quadrature.py` covers pi enclosure, scalar
inside/outside ranks, a 2x2 rank, interval inheritance, coarse ambiguity,
quadratic frozen refinement, per-edge panels, scale covariance, invalid contracts,
and projector enclosures.
