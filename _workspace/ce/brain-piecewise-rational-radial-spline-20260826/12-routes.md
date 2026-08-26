# Routes and counterexamples

Status: COMPLETE

## Implemented rational-spline route

Each patch supplies exact numerator and denominator polynomials.  The fixture
`D_k=1+d_k b_k`, `N_k=D_k+e_k b_k`, with endpoint-flat polynomial bumps `b_k`,
has genuinely varying positive denominators and exact C1 quotient junctions.

## Refusal cases

- Zero denominator lower margin fails even if selected samples are nonzero.
- Zero numerator lower margin fails positive radial geometry.
- Quotient value/derivative mismatch and false C2 promotion fail at the exact
  knot/order.
- Wrong patch count, `q<1`, singular knots, nonpositive covers, and exhausted
  budgets fail closed.

## Open successors

Certified contour/knot optimization, automatic exact projector discovery, and
empirical matrix coverage remain independent tasks.
