# Alternative routes lane

Status: COMPLETE

## Route A: reject every nonsymmetric tensor

Safe for the predecessor but incomplete for directed flow.  It cannot express
energy-neutral rotational or transport components.

## Route B: silently symmetrize and discard the remainder

Rejected.  Symmetrization alone preserves dissipation but loses the actual
velocity.  The skew remainder must be exposed and propagated.

## Route C: treat all nonsymmetry as biological work

Rejected.  Exact skew work is zero in the declared real inner product, whereas
external forcing contributes `g^T u` and can change potential balance.

## Selected route

Normalize first, split uniquely into `S+K`, verify `S` and `S-mI` exactly,
retain both velocity components, and report forcing work separately.  State a
form-level Hilbert theorem but keep its unverified hypotheses outside the
finite certificate.
