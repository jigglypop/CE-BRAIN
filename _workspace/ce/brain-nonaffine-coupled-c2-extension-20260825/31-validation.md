# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

- focused nonaffine coupled C2 certificate and controls: 29/29 passed;
- nonaffine/affine coupled C1/C2 and dimensionless adjacency: 139/139 passed;
- complete graph/C1/C2/local/matched/dimensionless integration: 322/322
  passed.

Controls cover the exact sine witness, the separate $T_\phi$ increments,
full affine coefficient reduction, graph-independent nonaffine triangular
reduction, conditional $\Xi$ bypass, class and bunching equality rejection,
predecessor failure ordering, exact iteration, scale covariance, dimensions
$1,4,5,6,100$, normalized units, and invalid exact inputs.

The target module is standard-library-only. No full repository suite,
benchmark, package build, remote call, empirical operation, dependency
installation, or execution-policy change was performed.
