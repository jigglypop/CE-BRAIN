# Componentwise residual pre-implementation audit

Status: COMPLETE

Scope: K1--K3 contract, proof, routes, exact fixture, and stable predecessor
APIs. No source/data action occurred.

## P0/P1 findings

None.

## Proof checks

- The sign is correct for $A=A_0-\Delta$:
  $I-BA=(I-BA_0)+B\Delta$.
- Nonnegative matrix multiplication of outward $|B|$ and $D$ bounds every
  component of $B\Delta$ without assuming sign or phase alignment.
- Strict contraction in each induced norm independently yields the stated
  1- and infinity-norm inverse uppers through the Neumann series.
- Combining those uppers with
  $\|X\|_2^2\le\|X\|_1\|X\|_\infty$ gives a valid spectral inverse upper.
- Uniform node singular lowers plus the exact chord yield the whole circle;
  node contraction alone is not silently promoted.
- Convexity of the rectangular family supplies the rank-preserving homotopy.
- K3 uses the uniform residual resolvent for both endpoints and the separately
  rigorous global uncertainty bound; dimensions cancel correctly.
- The scalar equality control proves both contraction comparisons must be
  strict.

## Implementation admission

Implement as a separate module. Preserve all predecessor objects and statuses.
Parse exactly four witnesses; expose magnitude brackets, residuals, interval
products, both contractions, inverse bounds, chord, and status ceiling. A
positive residual status may coexist with a preserved global non-certificate
on the same box, but the output must make that distinction explicit.

Optional total projector error requires a passing independent nominal strip.

Exact fixture result:
`PASS: componentwise residual/Krawczyk contour spot checks`.

Gate: PASS

This admits finite deterministic implementation only, not experimental
coverage, a neural matrix, brain geometry, consciousness, or dimension 4--6.

## Post-implementation stable audit

The final module implements the audited sign, nonnegative component product,
strict two-norm contractions, Banach denominators, spectral inverse enclosure,
and chord gate. It preserves the predecessor global non-certificate while
allowing a separately labelled componentwise pass on the unchanged structured
box. Exact and deliberately inexact witnesses demonstrate that validity comes
from residual checks rather than witness identity.

The optional projector total is emitted only with both a positive residual
circle and positive nominal strip. Focused 14/14, adjacent 53/53,
dimensionless 23/23, and exact fixture PASS leave no P0/P1 or status-ceiling
mismatch in the stable snapshot.
