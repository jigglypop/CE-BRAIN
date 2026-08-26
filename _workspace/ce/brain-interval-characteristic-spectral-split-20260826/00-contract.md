# Contract: interval-family automatic characteristic split

Status: COMPLETE

## Objective

Combine exact nominal characteristic/envelope factor discovery with the existing
uniform interval-circle perturbation theorem so an automatically discovered
nominal projector rank is certified for every matrix in a supplied rectangular
complex uncertainty box.

## Acceptance conditions

1. Nominal complete-Q/centered-envelope discovery must pass independently.
2. Componentwise exact real/imaginary radii produce an outward dyadic Frobenius
   uncertainty upper bound.
3. The existing full-circle certificate must prove a strict nominal margin, and
   uncertainty must be strictly smaller.
4. The receipt exposes nominal exact projector/rank, robust family margin,
   all-family rank, and exact-projector perturbation upper bound.
5. Nominal factor-budget failure, contour equality, excessive uncertainty, and
   invalid schema all fail closed.

## Ceiling

The run does not calibrate uncertainty coverage from data, optimize a continuous
contour, or emit direct interval-polynomial factors.
