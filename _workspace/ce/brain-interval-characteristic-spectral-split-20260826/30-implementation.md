# Implementation

Status: COMPLETE

## Module

`reality_stone/python/reality_stone/clarus/verified_interval_characteristic_spectral_split.py`

The wrapper runs nominal characteristic discovery and interval-circle certification
independently, accumulates both failures, and only then emits the nominal exact
projector, common family rank, robust margin, and exact-projector perturbation
bound.  Honesty fields state that interval polynomial factorization, interval root
tracking, and empirical uncertainty provenance are absent/unneeded.

## Tests

`tests/test_verified_interval_characteristic_spectral_split.py` contains ten
success, scale, Gaussian-center, boundary, budget, and parser fixtures.
