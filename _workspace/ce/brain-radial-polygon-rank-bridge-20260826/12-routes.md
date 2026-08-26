# Routes and counterexamples

Status: COMPLETE

## Implemented route

The existing global radial Lipschitz receipt controls the complete sector sweep,
so no unsupported smooth quadrature assumption is needed.  Exact polygon nodes
are the raw smooth-contour mesh nodes.

## Refusal cases

- A nonpositive radial residual margin stops before polygon quadrature.
- A singular radial node stops before residual and homotopy claims.
- An exhausted adaptive budget preserves an unresolved status without guessing.
- Invalid positive-radius or affine-orientation geometry is rejected upstream.

## Open successors

Higher-order positive radial polynomials/splines need independent positivity,
regularity, injectivity, and derivative bounds.  Contour optimization, automatic
exact projector discovery, and empirical measurement coverage remain separate.
