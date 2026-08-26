# Sources

Status: COMPLETE

## Internal dependencies

1. `verified_algebraic_riesz_projector.py` — final exact projector, exterior
   inverse, and strict inside/outside norm verification.
2. `verified_rational_contour.py` — exact Q(i) matrices and inversion.

The new proof uses exact rational polynomial Euclidean division, Bézout/Chinese
remainder projectors, polynomial evaluation by matrix Horner, and an augmented
complement inverse.  No external data is used.
