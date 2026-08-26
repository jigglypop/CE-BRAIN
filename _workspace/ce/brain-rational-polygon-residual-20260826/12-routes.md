# Routes and counterexamples

Status: COMPLETE

## Route A: endpoint half-edge cover

This is the implemented route.  It works for convex and concave simple polygons
and improves monotonically under exact forward edge refinement.

## Route B: direct segment interval arithmetic

Parameterizing each edge and bounding the full matrix pencil is possible but more
expensive and unnecessary for the scalar-shift node matrix.  It remains an
independent alternative, not silently identified with Route A.

## Counterexamples and refusal cases

- A bow-tie has nonzero edge data but is not a Jordan contour.
- A nonadjacent edge touching a vertex invalidates simplicity.
- Reversed vertices give negative winding orientation.
- Collinear backtracking retraces an edge.
- Positive endpoint residuals with nonpositive half-edge margin do not cover the
  edge; a four-corner square fixture demonstrates this failure.
- The same square with 16 exact boundary nodes passes, demonstrating genuine
  refinement rather than a changed contour.
