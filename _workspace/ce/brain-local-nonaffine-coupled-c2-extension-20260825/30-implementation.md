# Implementation

Status: COMPLETE

The exact wrapper is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_local_nonaffine_coupled_c2_graph_transform.py`.
It composes the final-gated global nonaffine coupled C2 certificate with input
and output base-domain radii and a supplied uniform radius bound for the
actual graph-dependent inverse $F_h^{-1}$.

The wrapper exposes raw and normalized radii, the coverage margin, overflow
invariance kind, failure ordering, supplied dimension, and unchanged exact
three-level recurrence. The analytic helper proves the bound
$R_{\rm pre}=\mu(R_{t+1}+\varepsilon R_y)$ and separately reports the
base and actual coupled inverse-Lipschitz bounds for the scalar
sine-plus-fiber-coupling witness.

The focused seam is
`tests/test_quantitative_local_nonaffine_coupled_c2_graph_transform.py`; its
normalized domain core is registered in `tests/test_dimensionless.py`.
