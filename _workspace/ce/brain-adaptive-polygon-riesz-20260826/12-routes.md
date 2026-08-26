# Routes and counterexamples

Status: COMPLETE

## Uniform route

All edges are multiplied together.  It gives the simplest exact `a^-2` receipt but
may spend panels on already small-error edges.

## Maximum-error-tie route

Only all exact maximizers are multiplied.  Refining all ties is essential for
determinism and for avoiding input-order bias.

## Refusal cases

- Negative, float, or Boolean budgets fail.
- Multipliers below two, floats, and Booleans fail.
- Unknown strategy names fail.
- Budget zero performs exactly the initial attempt and cannot continue.
- A non-singleton final rank set remains unresolved; nearest-integer selection is
  forbidden.
