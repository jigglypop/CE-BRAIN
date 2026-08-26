# Independent routes and counterexamples

Status: COMPLETE

## Route A: componentwise Neumann majorant

This is the implemented route.  It retains entrywise information through `K` and
the three-term transformed uncertainty enclosure.

## Route B: scalar induced-norm inverse bound

The weaker alternative `||T^-1|| <= ||T0^-1||/(1-theta)` also proves
invertibility but loses componentwise structure.  It is retained as an independent
derivation check, not selected for implementation.

## Boundary counterexample

For `T0=I` and an allowed perturbation with `E_11=-1`, the family contains a
singular transform while `|| |T0^-1|E+ ||_infinity=1`.  Therefore `<1` cannot be
weakened to `<=1`.

## Omitted-term audit

If `D=0` but `E` varies and `A0` does not commute with `E`, the transformed
matrix still varies.  Hence transporting only `K D+ T+` is invalid.
