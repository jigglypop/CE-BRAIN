# Validation

Status: COMPLETE

- focused nonaffine fixture and theorem composition: 10/10 passed;
- nonaffine plus predecessor C1 regression: 30/30 passed;
- complete graph/C1/scalar-tensor-scale/dimensionless integration: 155/155 passed.

Controls cover $a=0$, exact nonaffine $a=1/4$, monotonic inverse bounds, C1 composition, bunching failure despite a valid nonaffine inverse, and $a=1$ or invalid exactness rejection.

The first attempted parallel test launch encountered a Windows helper ACL process-creation error before assertions ran. The same focused files were then run sequentially through the required hook and passed 30/30; no assertion or environment override was changed.

