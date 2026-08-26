# Implementation

Status: COMPLETE

The exact certificate is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_nonaffine_coupled_c2_graph_transform.py`.
It composes the nonaffine coupled C1 predecessor and exposes every one-graph
$P,R,N,J$ bound, the conditional C2,1 class gate, every two-graph coefficient,
second bunching, margins, supplied dimension, failure ordering, the analytic
sine witness, and exact three-level iteration.

The implementation propagates both base terms separately: $H_\phi$ changes
the Hessian size and inverse-Jacobian factors, while $T_\phi$ changes both the
one-graph Hessian modulus and the two-preimage value coefficient. Setting both
to zero reproduces every affine coupled C2 layer exactly; setting $f\equiv0$
reproduces the graph-independent nonaffine triangular C2 certificate.

The focused seam is
`tests/test_quantitative_nonaffine_coupled_c2_graph_transform.py`; the
normalized curvature core is registered in `tests/test_dimensionless.py`.
