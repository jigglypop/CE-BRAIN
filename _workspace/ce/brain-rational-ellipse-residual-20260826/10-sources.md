# Sources

Status: COMPLETE

## Internal dependencies

1. `verified_rational_mesh_residual.py` — exact ordered rational unit-circle mesh.
2. `verified_interval_residual.py` — componentwise node residual theorem.
3. `verified_rational_contour.py` — exact Q(i) algebra and outward nested roots.

The new route uses injectivity of an invertible affine map, the exact 2x2 singular
value formula, Lipschitz transport of the unit-circle cover, and the ellipse length
bound `length<=2*pi*||L||_2`.  No external data is used.
