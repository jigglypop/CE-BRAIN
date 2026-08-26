# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused affine coupled C2 certificate and controls: 22/22 passed;
- coupled C1/C2, triangular C2, and dimensionless adjacency: 97/97 passed;
- complete graph/C1/C2/scalar-tensor-scale/dimensionless integration: 223/223 passed.

Controls cover every exact intermediate layer, simultaneous recurrence,
missing and equality graph-Hessian modulus gates, the $L_{fy}=0$ bypass,
full zero-coupling equality with the triangular C2 coefficients, strict
second-order bunching equality rejection after C1 passes, predecessor failure
ordering, base/fiber rescaling, dimensions $1,4,5,6,100$, and invalid exact
inputs.

The separate top-level package `doctor` was not repeated: the immediately
preceding final-gated run already recorded that it stops on unavailable
optional `torch`. All target modules are standard-library-only and all scoped
pytest commands ran successfully through the required wrapper. No dependency
was installed or execution policy weakened.

No full repository suite, benchmark, package build, remote call, or empirical
data operation was run. Harness-owned pytest basetemps were removed and no
repository pytest cache was created.
