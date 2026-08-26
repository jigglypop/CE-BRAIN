# Implementation

Status: COMPLETE

The exact certificate is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_nonaffine_c2_graph_transform.py`.
It composes the global graph-independent nonaffine C1 certificate and exposes
the inverse-base Hessian bound $\nu$, the nonaffine class bound, strict
$q\mu^2$ margin, both lower-order recurrence coefficients, exact simultaneous
iteration, robust-interior status, and the supplied dimension.

The analytic helper returns exact bounds for $\phi_a(x)=x+a\sin x$ and rejects
$a\notin[0,1)$. Predecessor failures remain primary, class equality passes as
non-robust, bunching equality fails closed, and $\nu=0$ reduces exactly to the
affine triangular C2 coefficients.

The focused seam is
`tests/test_quantitative_nonaffine_c2_graph_transform.py`; the normalized
inverse-curvature core was added to `tests/test_dimensionless.py`.

