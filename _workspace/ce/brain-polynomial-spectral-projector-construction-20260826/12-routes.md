# Routes and counterexamples

Status: COMPLETE

## Implemented factor-to-witness route

Factor coefficients are normalized to monic form.  Extended gcd, Bézout identity,
product annihilation, matrix-polynomial evaluation, projector, complement, and
exterior inverse are all exact rational operations.

## Refusal cases

- Constant/malformed and noncoprime factors are rejected.
- A factor product that does not annihilate the matrix emits no projector.
- A center eigenvalue in the complement prevents exterior inverse construction.
- Swapped inside/outside labels fail the final strict norm gate.

## Open successors

Automatic exact characteristic/minimal polynomial construction, irreducible
factorization, inside/outside factor classification, interval factor witnesses,
and empirical coverage remain separate.
