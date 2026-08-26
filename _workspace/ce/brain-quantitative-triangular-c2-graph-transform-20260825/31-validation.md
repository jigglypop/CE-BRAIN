# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused triangular C2 certificate and controls: 22/22 passed;
- triangular C1/C2 and dimensionless adjacency: 73/73 passed;
- complete graph/C1/C2/scalar-tensor-scale/dimensionless integration: 200/200 passed.

The focused controls cover exact class invariance and cross coefficients,
zero/one/two-step simultaneous recurrence, zero Hessian decoupling, class
equality versus class failure, strict second-order bunching equality rejection
after C1 passes, the local $x|x|$ non-C2 witness, predecessor failure ordering,
base/fiber rescaling, dimensions $1,4,5,6,100$, and invalid exactness inputs.

The separate `doctor` command failed before validation because importing the
top-level `reality_stone` package requires unavailable `torch`. The target
module is standard-library-only and all three required pytest commands ran
through the same harness and passed. No dependency was installed or execution
policy weakened.

No full repository suite, benchmark, package build, remote call, or empirical
data operation was run. The harness-owned pytest basetemps were removed by the
wrapper; no repository pytest cache was created.
