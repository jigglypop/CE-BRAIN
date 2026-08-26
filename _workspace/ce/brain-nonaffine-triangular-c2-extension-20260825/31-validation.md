# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused nonaffine triangular C2 certificate and controls: 26/26 passed;
- nonaffine C2, triangular C1/C2, and dimensionless adjacency: 101/101 passed;
- graph/C1/C2/dimensionless integration: 196/196 passed.

Controls cover the exact sine-family bounds, strict baseline values, every
new $\nu$ contribution, exact affine reduction, class equality and failure,
strict bunching equality rejection after C1 passes, predecessor failure
ordering, simultaneous iteration, dimensions $1,4,5,6,100$, and invalid exact
inputs.

The top-level package doctor was not repeated: the predecessor evidence
already records unavailable optional `torch`. The target modules are
standard-library-only, and every scoped test ran successfully through the
required wrapper. No full suite, benchmark, package build, remote call, or
empirical data operation was run.

