# Contract: continuous algebraic circle-margin optimization

Status: COMPLETE

## Objective

Certify tolerance-global continuous circle optimization for defective or otherwise
non-diagonalized rational/Gaussian-rational matrices by optimizing a sufficient
Frobenius algebraic Riesz margin built from an automatically discovered reference
projector and exterior inverse.

## Acceptance conditions

1. Reference CHSPEC must construct an exact projector, complement inverse, and rank.
2. A strict Neumann condition must prove exterior-block invertibility for every
   center in the parameter box.
3. The objective combines exact inside and exterior-inverse Frobenius gates.
4. Every cell has a reverse-triangle/resolvent-identity global upper.
5. Branch-and-bound must meet the declared optimality tolerance before its cell
   budget, and the selected margin must be positive.
6. Selected CHSPEC projector/rank must exactly equal the reference projector/rank.

## Ceiling

Boxes lacking a reference projector or uniform exterior domain, noncircular
shape/knot families, empirical objective selection, consciousness, and dimension
4--6 remain outside.
