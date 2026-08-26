# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused local nonaffine coupled C2 certificate and controls: 35/35 passed;
- local/global nonaffine coupled C2, local triangular C2, and dimensionless
  adjacency: 133/133 passed;
- complete graph/C1/C2/local/matched/dimensionless integration: 358/358
  passed.

Controls cover the exact sine-plus-fiber witness, zero coupling, full
differential identity with the global predecessor, strict/equality/failed
coverage, predecessor failure ordering, the $\phi^{-1}$-only counterexample,
overflow non-promotion, exact iteration, base/fiber scale covariance,
dimensions $1,4,5,6,100$, normalized units, and invalid exact inputs.

These numerical checks establish implementation consistency only. No full
repository suite, benchmark, package build, remote call, empirical operation,
dependency installation, or execution-policy change was performed.
