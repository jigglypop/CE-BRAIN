# Routes and counterexamples

Status: COMPLETE

## Homotopy-transfer route

This implemented route reuses exact rational polygon quadrature and proves that it
computes the same spectral projector as the smooth ellipse.

## Direct ellipse quadrature route

A rational parameterization could be quadratured directly with separate derivative
and chart-pole bounds.  It is not required for the homotopy result and remains an
independent candidate.

## Failure boundaries

- Failed ellipse cover stops before polygon work.
- A singular mapped node stops before residual and quadrature.
- Zero refinement budget can preserve a verified homotopy while leaving rank and
  projector approximation absent.
- Polygon rank cannot be transferred without the swept-sector cover.
