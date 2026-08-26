# Implementation

Status: COMPLETE

## Module

`reality_stone/python/reality_stone/clarus/verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py`

The module parses exact matrix/witness/box data, verifies a rational unit
orientation, normalizes all spectral quantities, constructs exact score ranges,
performs deterministic branch-and-bound, and emits every terminal cell plus the
selected exact oblique projector and rank.  It explicitly reports
`finite_grid_only=False`, `orientation_optimized=False`, and no empirical
provenance.

## Tests

`tests/test_verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py`
contains 18 positive, enclosure, singleton, circle-reduction, rotation, oblique,
scale, boundary, witness, budget, parser, and claim-ceiling fixtures.
