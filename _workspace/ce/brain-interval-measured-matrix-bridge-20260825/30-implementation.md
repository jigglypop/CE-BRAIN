# Verified interval-family contour implementation

Status: COMPLETE

Added `reality_stone/python/reality_stone/clarus/verified_interval_contour.py`
without changing predecessor float64 or exact-rational APIs.

The module:

- parses a square matrix of exact nonnegative `(real_radius, imag_radius)`
  pairs and shape-matches it to the nominal matrix;
- normalizes every radius by the spectral reference scale before constructing
  the exact squared Frobenius radius and dyadic square-root enclosure;
- calls the predecessor exact nominal full-circle certificate;
- returns robust separation, resolvent, projector-perturbation, and explicit
  whole-family rank-preservation outputs only under the strict positive margin;
- retains named nominal-unavailable and uncertainty-not-below-margin
  non-certificate states;
- optionally composes the predecessor analytic-strip error with the uncertainty
  projector error, exposing both terms and their sum.

It imports only Python standard-library components and the local predecessor
module. It has no network, dataframe, interval-package, neural-data, file-I/O,
or scientific-endpoint path. The word `interval` refers to exact declared
rectangular endpoints, not statistically calibrated measurement coverage.
