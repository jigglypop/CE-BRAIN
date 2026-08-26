# Implementation

Status: COMPLETE

The exact certificate is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_c2_graph_transform.py`.
It composes the triangular C1 predecessor and reports the normalized
$K_2,K_3,\Lambda_2$, output Hessian bound, class margin, second-order bunching
factor and margin, both lower-order cross coefficients, robust-interior flag,
and preserved supplied dimension.

`c2_graph_iteration_bound` iterates the value/derivative/Hessian recurrence
simultaneously from the previous step, avoiding an in-place ordering error.
Predecessor failures remain primary. Exact class equality is accepted as
non-robust; second-order bunching equality fails closed. Inputs use the shared
exact-rational parser, so binary floats, Booleans, noncanonical strings, and
negative derivative bounds are rejected.

The focused seam is `tests/test_quantitative_c2_graph_transform.py`; the
normalized Hessian core was added to `tests/test_dimensionless.py`.
