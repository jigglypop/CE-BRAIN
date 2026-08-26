# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused coupled-C1 certificate and controls: 21/21 passed;
- coupled Lipschitz, coupled C1, and dimensionless adjacency: 77/77 passed;
- complete graph/C1/scalar-tensor-scale/dimensionless integration: 177/177 passed.

The controls cover a strict interior fixture, exact recurrence at zero and one step,
$C^{1,1}$ class failure separate from derivative bunching, the class-boundary case with
zero second-derivative data, strict bunching equality rejection, predecessor failure
preservation, exact triangular reduction, base/fiber rescaling, dimensions
$1,4,5,6,100$, and invalid exactness inputs.

No full repository test suite, benchmark, package build, remote call, or empirical-data
operation was run.
