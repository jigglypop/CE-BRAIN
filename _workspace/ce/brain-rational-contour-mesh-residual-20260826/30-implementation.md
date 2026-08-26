# Implementation

Status: COMPLETE

`verified_rational_mesh_residual.py` adds:

- `RationalUnitCircleMesh` with exact directions, dot/cross receipts, per-gap chord
  brackets, and the maximum chord factor;
- exact single-winding polar-order and cyclic-gap validation;
- `exact_mesh_nominal_inverse_witnesses` for any admitted mesh;
- arbitrary-node componentwise residual evaluation using predecessor node gates;
- best-of-Frobenius/induced uncertainty size, full-circle delta, resolvent, rank,
  projector perturbation, unit scaling, and honest provenance output.

The legacy four-node implementation is not changed.  Exact reduction tests protect
backward semantics while the successor supplies the larger domain.
