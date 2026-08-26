# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused nonaffine coupled C1 certificate and controls: 30/30 passed;
- nonaffine/affine coupled C1, coupled Lipschitz, and dimensionless adjacency:
  113/113 passed;
- complete graph/C1/C2/local/matched/dimensionless integration: 292/292
  passed.

Controls cover the exact sine witness and affine limit, both frozen curvature
increments, full affine coefficient reduction, unchanged diagonal bunching,
curvature-only class failure, equality-boundary rejection, predecessor failure
ordering, exact iteration, zero coupling, scale covariance, dimensions
$1,4,5,6,100$, and invalid exact inputs.

The target module is standard-library-only. No full repository suite,
benchmark, package build, remote call, empirical operation, dependency
installation, or execution-policy change was performed.

