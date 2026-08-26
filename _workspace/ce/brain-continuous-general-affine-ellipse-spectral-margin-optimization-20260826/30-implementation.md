# Implementation

Status: COMPLETE

## Module

`reality_stone/python/reality_stone/clarus/verified_continuous_general_affine_ellipse_spectral_margin_optimization.py`

The module parses six exact parameter intervals, normalizes spectral shear,
constructs coupled-coordinate score enclosures, bisects cells deterministically,
and returns selected QR axes/determinant, invariant margin/gap, terminal cells,
and the exact oblique projector/rank.

## Tests

`tests/test_verified_continuous_general_affine_ellipse_spectral_margin_optimization.py`
contains 21 shear, reduction, inverse-coordinate, determinant, containment,
six-variable, scale, oblique, boundary, budget, parser, and claim-ceiling fixtures.
