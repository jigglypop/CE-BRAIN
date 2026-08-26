# Sources

Status: COMPLETE

## Internal dependencies

1. `verified_polynomial_radial_contour_residual.py` — exact term normalization and
   coefficient-sum positivity/gradient bounds.
2. `verified_polynomial_radial_polygon_rank_bridge.py` — sector homotopy and rank
   transfer.
3. `verified_rational_mesh_residual.py` — periodic ordered rational directions.
4. `verified_adaptive_polygon_riesz.py` — verified numeric rank/projector route.

The new ingredient is exact repeated application of the angular derivative
operator `T=-y*d/dx+x*d/dy` to polynomial patches at every periodic knot.  No
external data is used.
