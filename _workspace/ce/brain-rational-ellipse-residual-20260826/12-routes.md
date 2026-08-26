# Routes and counterexamples

Status: COMPLETE

## Affine unit-circle route

This is implemented.  It admits rotations, anisotropic axes, and real shears while
retaining exact rational contour nodes.

## General smooth route

Polynomial or spline arcs need separate regularity, injectivity, cover, and
quadrature certificates.  They are not inferred from the affine result.

## Boundary cases

- `det(L)=0` degenerates to a segment.
- `det(L)<0` reverses the required contour orientation.
- Proportional axes fail the same determinant gate.
- A four-node mesh can fail the affine cover although all node inverses exist;
  an exact eight-node refinement passes the same ellipse.
- For `a=r`, `b=ir`, every geometry and residual output reduces to the circle route.
