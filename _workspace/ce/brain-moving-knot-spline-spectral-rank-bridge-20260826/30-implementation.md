# Implementation

Status: COMPLETE

## Module

`reality_stone/python/reality_stone/clarus/verified_moving_knot_spline_spectral_rank_bridge.py`

The module composes the knot optimizer, normalizes exact affine geometry,
computes inverse-coordinate squared radii and uniform margins, verifies exact
diagonalization and the common oblique projector, and emits explicit None/false
flags for quantitative resolvent, interval-matrix, and empirical successors.

## Tests

`tests/test_verified_moving_knot_spline_spectral_rank_bridge.py` contains 16
whole-box, margin, affine, oblique, scale, equality, label, witness, budget,
rank-zero/full, geometry, parser, and honesty fixtures.
