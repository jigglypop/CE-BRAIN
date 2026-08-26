# Routes and counterexamples

Status: COMPLETE

## Implemented global polynomial route

Repeated monomials are combined exactly and zero coefficients removed.  Linear
terms retain the sharper Euclidean norm receipt; only degree-two-and-higher terms
use coefficient-sum amplitude and degree-weighted gradient bounds.

## Refusal cases

- Positivity equality and negative margins fail closed.
- Constant monomials must be represented by `radial_base`.
- Negative, Boolean, or noninteger exponents and malformed terms are rejected.
- Singular nodes and nonpositive covers stop before rank transfer.
- A finite exhausted quadrature budget never guesses a rank.

## Open successors

Piecewise polynomial or rational splines require explicit knot domains,
value/derivative compatibility, global positivity, and seam regularity.  Contour
optimization, exact projector discovery, and empirical coverage remain separate.
