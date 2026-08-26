# Implementation

Status: COMPLETE

The exact certificate is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_nonaffine_coupled_c1_graph_transform.py`.
It composes the coupled Lipschitz predecessor and exposes the nonaffine base
curvature $H_\phi$, modified one-graph base-Jacobian bound, output C1,1 class,
two-preimage base/fiber value coefficients, bunching and cross coefficients,
margins, supplied dimension, failure ordering, and exact iteration.

The implementation makes both curvature increments explicit. At
$H_\phi=0$, every numerical layer reduces exactly to the affine coupled C1
certificate. The analytic helper returns exact inverse-Lipschitz and base
Hessian bounds for $\phi_{\lambda,a}(x)=\lambda x+a\sin x$.

The focused seam is
`tests/test_quantitative_nonaffine_coupled_c1_graph_transform.py`; the
normalized base-curvature core was added to `tests/test_dimensionless.py`.

