# Routes and counterexamples

Status: COMPLETE

## Passing routes

- diagonal `diag(i,3i)` at real center zero gives envelope
  `(z^2+1)(z^2+9)` and original complex rank one;
- a defective size-two Jordan block at `i` is retained as the primary factor
  `(z^2+1)^2` and gives original complex rank two;
- raw scaling by five preserves normalized envelope, partition, and rank.
- center `i` for `diag(i,3i)` shifts to `diag(0,2i)` and returns rank one;
- real `diag(0,4)` at center `i` uses the same shifted envelope and returns rank one.

## Refusal routes

- factor-candidate and partition budgets retain their independent fail-closed
  behavior;
- interval entries, direct Q(i)[z] factor output, and measured matrices remain outside.

## Rank counterexample prevented

Realification of a complex rank-one projector has real rank two.  Returning that
two as the discovered complex subspace dimension would be a convention error;
the implementation constructs and traces the projector on the original matrix.
