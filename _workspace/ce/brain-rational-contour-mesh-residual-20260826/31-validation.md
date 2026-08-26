# Validation

Status: COMPLETE

- focused rational-mesh tests: 15/15 passed;
- mesh/dense/predeclared/weighted/binary64/residual/witness/contour and
  dimensionless adjacency: 214/214 passed;
- dimensionless suite: 62/62 passed;
- source compilation: passed;
- exact eight-file run shape: passed;
- final gate: `OK final`.

Negative fixtures cover too few/off-circle/duplicate/reversed directions, multiple
windings, singular nodes, witness-count mismatch, and inexact witnesses.  Positive
fixtures cover exact four-node reduction, eight-node strict improvement, spectral
unit covariance, and stored honesty flags.
