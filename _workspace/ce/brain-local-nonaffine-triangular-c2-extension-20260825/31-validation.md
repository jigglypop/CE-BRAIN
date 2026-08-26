# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused local nonaffine triangular C2 certificate and controls: 31/31 passed;
- local/global nonaffine C2, triangular C1/C2, and dimensionless adjacency:
  133/133 passed;
- graph/C1/C2/local/dimensionless integration: 228/228 passed.

Controls cover exact expanding-sine bounds, strict fixture values, coverage
equality and failure, predecessor failure ordering, exact predecessor
arithmetic identity, contracting-base coverage failure, expanding-base
forward-overflow counterexample, simultaneous recurrence, base-scale
covariance, dimensions $1,4,5,6,100$, and invalid exact inputs.

The target modules are standard-library-only. No full repository suite,
benchmark, package build, remote call, empirical data operation, dependency
installation, or execution-policy change was performed.

