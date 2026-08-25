# Interval bridge pre-implementation audit

Status: COMPLETE

Audit scope: stable `00-contract.md`, `10-sources.md`, `11-math.md`,
`12-routes.md`, predecessor exact-circle/strip API, and the exact spot-check
fixture. No empirical matrix, network source, or endpoint was used.

## P0 / P1 findings

None.

## Proof audit

- I0 follows entry by entry and then from the standard finite-matrix
  inequality `operator norm <= Frobenius norm`; it covers irrational family
  members despite rational endpoints.
- I1 uses a certified lower bound, not sampled eigenvalue distance. Subtracting
  the common operator error upper is valid uniformly over the entire contour.
- The strict inequality cannot be weakened: the scalar unit-circle control
  reaches a singular contour point at equality.
- I2's homotopy remains inside the same uncertainty ball. Continuity of the
  Riesz projector plus integer-valued finite rank proves rank constancy.
- The resolvent identity sign and order are correct:
  `R(U)-R(U0) = R(U) Delta R(U0)`. Circle length produces exactly the factor
  `r`, so the projector bound is dimensionless.
- I3 is a direct triangle inequality and keeps nominal quadrature and unknown
  matrix perturbation errors separate.
- Normalize-first dyadic enclosure is necessary and sufficient for the stated
  exact unit-rescaling invariance.

## Apparatus admission conditions

Implementation is admitted only as a new module layered on the predecessor.
It must not relabel or modify float64 APIs or weaken predecessor exact-circle
conditions. It must parse rectangular radii fail-closed, shape-match the
nominal matrix, normalize before square-root enclosure, expose every bracket
and squared self-check, and return a positive status only under the strict
margin test.

The optional projector bridge must require an actually passing predecessor
strip certificate. A passing central circle alone is insufficient to provide
the nominal `P4-to-P` term.

## Focused evidence

Command:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-interval-measured-matrix-bridge-20260825\artifacts\math_interval_spotchecks.py
```

Result: `PASS: interval contour/projector exact theorem spot checks`.

## Gate and ceiling

Gate: PASS

This admits implementation of I1--I3 for declared exact interval endpoints.
It does not validate how a real experiment constructs the intervals, establish
simultaneous statistical coverage, open neural data, select a rank, or support
brain-geometry, consciousness, or dimension 4--6 claims.

## Post-implementation stable-snapshot audit

The final module preserves the admitted route. Its only non-standard import is
the frozen predecessor exact-contour module. Rectangular bounds are parsed
before status construction, normalized before the dyadic grid, and included
as both the exact squared radius and a checked lower/upper square-root bracket.
The strict branch is implemented as `robust_delta <= 0` returning a
non-certificate. Positive output derives raw quantities only after normalized
checks and explicitly marks whole-family rank preservation.

The projector route returns a total bound only when both the interval circle
and nominal strip have positive validation levels. Its total is exactly the
sum of the separately exposed uncertainty and quadrature terms. The final
focused and adjacent results are 15/15 and 26/26. The dimensionless gate is
21/21 and separately confirms the spectral-unit and dimensionless-projector
bookkeeping. No P0/P1 implementation or status-label mismatch remains in the
audited snapshot.
