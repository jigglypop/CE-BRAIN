# Candidate routes

Status: COMPLETE

| Route | Decision | Reason |
|---|---|---|
| Positive-diagonal QR with continuous shear | Implemented | Complete coordinates for orientation-preserving affine 2x2 axes. |
| Independent four raw axis entries | Deferred | Needs determinant-sign and singular-value domain subdivision. |
| Orthogonal axes only | Superseded for this branch | Exact predecessor recovered at zero shear. |
| Floating SVD/eigendecomposition | Rejected | Does not supply exact global parameter enclosures. |
| Spline knot family | Deferred | Piecewise geometry and junction constraints differ. |
| Defective algebraic ellipse | Deferred | Requires noncircular exterior-inverse norm gates. |
| Empirical optimization | Deferred | Requires provenance and held-out controls. |
