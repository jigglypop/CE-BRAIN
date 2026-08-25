# Tight interval routes and falsifiers

Status: COMPLETE

## Admitted T1/T2 route

Compute both Frobenius and induced bounds on every invocation, then apply the
frozen minimum and tie policy. Expose all intermediate brackets so a tighter
status cannot be attributed to a hidden change in the uncertainty family.

## Precision route

The fixed precision is an explicit input. A higher-precision rerun is a new
apparatus invocation, not permission to alter radii or the nominal matrix.
Because every dyadic is outward, low precision may cause a false negative but
not a false positive.

## Residual route remains separate

T1 is still a global norm-ball certificate. Structure-aware approximate
inverse or invariant-subspace residuals may be sharper, but require a distinct
contract with verified residual and conditioning bounds.

## Falsifiers

- computing entry magnitudes before normalization;
- using lower rather than upper square-root endpoints;
- swapping row and column definitions inconsistently;
- choosing the smaller of a rigorous and a nonrigorous candidate;
- changing the tie policy or computing only one candidate after seeing data;
- allowing `epsilon == delta` to pass;
- interpreting a tighter deterministic result as statistical coverage.
