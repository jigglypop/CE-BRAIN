# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused matched-domain local nonaffine C2 controls: 32/32 passed;
- matched/overflow/global nonaffine C2, triangular C1/C2, and dimensionless
  adjacency: 166/166 passed;
- graph/C1/C2/local/matched/dimensionless integration: 261/261 passed.

Controls cover the boundary-fixed cubic and identity limit, exact endpoint and
monotonicity samples, inverse/forward strict-contact rejection, both-strict
inconsistency, forward and inverse overruns, overflow-expander non-promotion,
predecessor failure ordering, exact recurrence, base-scale covariance,
dimensions $1,4,5,6,100$, and invalid exact inputs.

The target modules are standard-library-only. No full repository suite,
benchmark, package build, remote call, empirical data operation, dependency
installation, or execution-policy change was performed.

