# Sources

Status: COMPLETE

## Internal dependencies

1. `verified_rational_ellipse_residual.py` — exact affine geometry and outward
   operator-norm receipt.
2. `verified_rational_mesh_residual.py` — ordered rational unit-circle meshes.
3. `verified_interval_residual.py` — componentwise node-residual theorem.
4. `verified_rational_contour.py` — exact Q(i) arithmetic and nested roots.

The new proof uses positivity of a radial graph, the derivative identity
`D(rho(u)u)=rho(u)I+u p^T`, the mean-value Lipschitz theorem on the convex unit
disk, resolvent continuity, and the standard Riesz-projector resolvent identity.
No external observations or fitted constants are used.
