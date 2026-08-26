# Implementation

Status: COMPLETE

## Module

`reality_stone/python/reality_stone/clarus/verified_polynomial_spectral_projector_construction.py`

It emits normalized factors, extended-gcd Bézout coefficients and check,
annihilation check, constructed projector/complement/exterior inverse, the final
algebraic certificate and rank, plus explicit supplied-factor/no-factor-discovery
honesty flags.

## Tests

`tests/test_verified_polynomial_spectral_projector_construction.py` covers
diagonal, defective Jordan, irrational spectrum, rank zero/full, monic and raw
scale covariance, noncoprime/nonannihilating/malformed factors, swapped labels,
center-complement singularity, and honesty flags.
