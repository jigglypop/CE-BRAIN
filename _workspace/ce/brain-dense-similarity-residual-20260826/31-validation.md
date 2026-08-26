# Validation

Status: COMPLETE

- focused dense-similarity tests: 11/11 passed;
- dense/predeclared/diagonal/residual/witness/binary64/contour plus dimensionless
  adjacency: 198/198 passed;
- source compilation: passed;
- dimensionless suite: 61/61 passed;
- exact eight-file run shape: passed;
- final gate: `OK final`.

Fixtures cover identity and diagonal exact reductions, a nontrivial dense-only
positive margin, componentwise uncertainty multiplication, conditioning penalty,
spectral-unit covariance, singular/dimension/inexact-input refusal, and honesty
flags.
