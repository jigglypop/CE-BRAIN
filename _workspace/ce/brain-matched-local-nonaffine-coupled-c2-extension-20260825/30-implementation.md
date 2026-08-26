# Implementation

Status: COMPLETE

The exact wrapper is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_matched_local_nonaffine_coupled_c2_graph_transform.py`.
It composes the overflow-local nonaffine coupled C2 predecessor with exact
uniform inverse and forward contacts, a zero graph-boundary residual, and a
zero fiber-boundary forcing residual.

The certificate exposes all four inputs independently, raw and normalized
values, contact residuals, failure order, differential/domain robustness
separation, exact full-forward status, supplied dimension, and unchanged
three-level iteration. The analytic helper returns exact base/coupled inverse,
curvature, and domain-contact values for the boundary-anchored cubic witness.

The focused seam is
`tests/test_quantitative_matched_local_nonaffine_coupled_c2_graph_transform.py`;
the normalized boundary-contact core is registered in
`tests/test_dimensionless.py`.
