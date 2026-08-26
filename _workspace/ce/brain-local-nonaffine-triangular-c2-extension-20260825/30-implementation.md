# Implementation

Status: COMPLETE

The exact local wrapper is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_local_nonaffine_c2_graph_transform.py`.
It composes the final-gated nonaffine C2 certificate and adds raw and
normalized base-domain radii, inverse-image radius, coverage margin, exact
failure ordering, robust-interior status, supplied dimension, and the explicit
invariance label `BACKWARD_COVERED_OVERFLOW_INVARIANT`.

The implementation deliberately reports `forward_retention_certified=False`.
Inverse coverage is sufficient for graph-transform iteration, but the
expanding-base control proves that it cannot certify retention of every input
base point. The analytic helper returns exact inverse derivative, inverse
Hessian, and inverse-image radius bounds for
$\phi_{\lambda,a}(x)=\lambda x+a\sin x$.

The focused seam is
`tests/test_quantitative_local_nonaffine_c2_graph_transform.py`; the normalized
domain-coverage core was added to `tests/test_dimensionless.py`.

