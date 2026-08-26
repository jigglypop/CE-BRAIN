# Alternative routes lane

Status: COMPLETE

## Route A: leave C0 external

The derivative recurrence can preserve `Delta_0` as an external input.  That
is correct for a conditional jet solver but incomplete for a full transform:
it cannot express convergence of the value component.

## Route B: infer approximate contacts

Allowing tolerances between two independently supplied certificates would
require a new perturbation theorem and error budget.  Treating near equality
as identity is rejected.

## Selected route

Require exact normalized contacts and expose them as non-robust equalities.
Use the C0 contraction only in row zero and the already-proved triangular jet
rows above it, all synchronously.  Reuse the audited local and matched
wrappers by exact certificate identity rather than recomputing their claims.
