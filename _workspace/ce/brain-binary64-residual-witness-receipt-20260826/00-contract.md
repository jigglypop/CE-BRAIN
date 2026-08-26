# Research contract

Status: COMPLETE

PREDECESSORS:

- `_workspace/ce/brain-exact-residual-witness-construction-20260825`
- `_workspace/ce/brain-interval-residual-krawczyk-20260825`

## Objective

Connect stored binary64 approximate inverse witnesses from a numerical solver
to the unchanged exact rational residual certificate without trusting decimal
printing or silently assuming the solver algorithm was exact.

## Frozen claim

Every finite IEEE-754 binary64 bit pattern has an exact rational value.  After
canonical bit decoding, complex witness matrices can enter the existing exact
residual/Krawczyk gate.  A passing residual proves the witness property needed
by that gate regardless of how the solver proposed the bits.

## Claim ceiling

The receipt does not verify the solver algorithm, its operation-by-operation
rounding mode, hardware, BLAS, matrix provenance, or empirical uncertainty.
NaN and infinity are forbidden.

## Validation contract

Normal/subnormal/signed-zero decoding, known exact fractions, special and
noncanonical failures, four-node complex witnesses, bad-witness and interval
failure propagation, deterministic bit hash, normalize-first covariance,
shape checks, dimensionless/adjacent regression, compile, and final gate.
