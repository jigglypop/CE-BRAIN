# Routes and counterexamples

Status: COMPLETE

## Implemented route

The positive affine-linear radial family is implemented.  It includes genuine
nonelliptic star-shaped curves, rotations, anisotropic axes, and shears while
retaining exact rational contour nodes.

## Boundary and refusal cases

- `r0-||p||_2<=0` loses the strict positive-radius certificate.
- `det(L)=0` destroys regular affine geometry; `det(L)<0` reverses orientation.
- A singular mapped node refuses the residual certificate.
- A four-node mesh may fail even though every node is invertible; an exact
  eight-node refinement can pass the same contour.
- Inexact geometry without a declared provenance route is refused.

## Open successors

Higher-order positive radial polynomials and splines require new positivity,
regularity, injectivity, and derivative-norm certificates.  Numeric smooth rank
and projector quadrature require a verified radial-to-polygon homotopy.  Contour
placement optimization and empirical matrix coverage are separate tasks.
