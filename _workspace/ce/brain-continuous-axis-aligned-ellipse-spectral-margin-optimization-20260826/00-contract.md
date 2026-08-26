# Contract: continuous fixed-orientation ellipse spectral-margin optimization

Status: COMPLETE

## Objective

Replace the fixed-ellipse-only and finite-menu routes by a certified continuous
optimization of center and two independent semiaxes over one exact compact box,
while keeping a rational orientation, spectral labels, and exact diagonalization
witness frozen before search.

## Acceptance conditions

1. Verify an invertible exact Gaussian-rational witness `UV=V Lambda`.
2. Require one exact rational unit orientation and strictly positive axis boxes.
3. Use a dimensionless quartic ellipse score whose positivity exactly realizes
   every frozen inside/outside label.
4. Enclose every score on every real cell by exact interval arithmetic.
5. Certify `global_upper-incumbent <= eta4` or fail on the cell budget.
6. Require positive margin and emit the exact commuting oblique projector/rank.
7. Preserve circle reduction, scale covariance, and explicit empirical ceilings.

## Ceiling

Continuous orientation, general affine axes, spline knots, defective/no-witness
ellipses, empirical objective selection, consciousness, and dimension 4--6 remain
outside this theorem.
