# Implementation

Status: COMPLETE

## Module

`verified_characteristic_spectral_split_discovery.py` now detects nonzero exact
imaginary entries or a non-real center, shifts the raw/normalized transition by
that center, constructs the exact zero-center realification characteristic source,
checks its polynomial on the working matrix, and retains all downstream
complete-Q-factor and projector gates.

New receipt fields expose whether complex input was processed, whether the center
is conjugation invariant after shift, whether realification envelope discovery
was used, whether center shift was used, the working characteristic center, and
the rank convention `COMPLEX_RANK_OF_ORIGINAL_MATRIX`.

## Tests

`test_verified_characteristic_spectral_split_discovery.py` adds Gaussian-rational
diagonal, defective, raw-scale, complex non-real-center, and real-matrix
non-real-center fixtures.
