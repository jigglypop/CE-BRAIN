# Alternative routes lane

Status: COMPLETE

## Route A: parse printed decimal output

Rejected as the canonical receipt.  Decimal formatting may discard the stored
bit value or depend on precision and locale.

## Route B: trust the floating inverse because the solver returned success

Rejected.  Solver status is not a proof of inverse quality or interval-family
robustness.

## Route C: require a newly constructed exact inverse

Already available and strongest for small rational nodes, but it does not
audit an independently supplied numerical witness.

## Selected route

Hash canonical raw bits, decode them to exact rationals, and run the unchanged
residual theorem.  Keep solver algorithm, operation rounding, and empirical
matrix provenance as separate unverified fields.
