# Implementation

Status: COMPLETE

`verified_algebraic_riesz_projector.py` provides:

- exact normalization and shape parsing;
- idempotence, transition/centered commutation, complement, support, and two-sided
  inverse identities;
- outward magnitude, Frobenius, induced, and selected 2-norm certificates for the
  inside operator and exterior inverse;
- strict inside and reciprocal exterior margins;
- exact trace/rank, status/failure vector, and explicit no-diagonalization and
  no-empirical-provenance flags.

The verifier returns all failed mathematical gates together while using the first
as its fail-closed status.
