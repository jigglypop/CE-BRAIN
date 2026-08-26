# Routes and counterexamples

Status: COMPLETE

## Implemented polynomial-spline route

Every patch has an exact base and normalized finite polynomial terms.  All
periodic knot derivatives through the declared order are recomputed rather than
trusted.  The test family
`1+epsilon_k(1-u.u_k)(1-u.u_{k+1})` gives distinct quadratic C1 patches.

## Refusal cases

- Value or derivative mismatches fail at their exact knot and order.
- The distinct C1 bump family refuses false C2 promotion.
- `q<1`, the wrong patch count, and nonpositive patch margins fail closed.
- Singular knots, nonpositive covers, and exhausted quadrature budgets emit no
  rank.

## Open successors

Piecewise rational functions require denominator lower bounds, pole exclusion,
quotient derivative compatibility, and rational Lipschitz bounds.  Knot/contour
optimization, exact projector discovery, and empirical coverage remain separate.
