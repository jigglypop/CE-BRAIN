# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused matched local nonaffine coupled C2 controls: 38/38 passed;
- matched/overflow/global coupled C2, matched triangular C2, and dimensionless
  adjacency: 173/173 passed;
- complete graph/C1/C2/local/matched/dimensionless integration: 397/397
  passed.

Controls cover the nonzero-coupling boundary-anchored cubic, endpoint and
monotonicity samples, zero coupling, exact predecessor identity, all four
independent contact/boundary failures, stable failure ordering, unanchored
base and fiber adverse controls, exact iteration, base/fiber scale covariance,
dimensions $1,4,5,6,100$, normalized units, and invalid exact inputs.

These numerical checks establish implementation consistency only. No full
repository suite, benchmark, package build, remote call, empirical operation,
dependency installation, or execution-policy change was performed.
