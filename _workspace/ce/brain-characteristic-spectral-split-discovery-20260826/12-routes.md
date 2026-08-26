# Routes and counterexamples

Status: COMPLETE

## Implemented discovery class

Real/Gaussian-rational matrices at arbitrary exact Gaussian-rational circle
centers are shifted to zero and completely factored through a real envelope when
the CE-QFACT and atom-partition searches fit their separate budgets.

## Refusal cases

- Complex-rational entries are refused by this route.
- An eigenvalue on the contour makes every strict partition fail.
- A mixed quartic is exactly split; an irreducible factor that itself straddles
  the contour correctly yields no certified rational primary partition.
- A factor-candidate budget refusal stops before partitions.
- Partition count above the declared budget stops before enumeration.

## Open successors

Interval polynomial factors, direct Q(i)[z] factor output, continuous contour
optimization, and empirical coverage remain separate.
