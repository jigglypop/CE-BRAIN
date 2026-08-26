# Implementation

Status: COMPLETE

The exact matched-domain wrapper is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_matched_local_nonaffine_c2_graph_transform.py`.
It composes the overflow-local predecessor and adds the output-domain radius,
exact forward-image radius, forward and inverse boundary-contact residuals,
full-forward retention status, differential versus domain robustness, failure
ordering, supplied dimension, and exact recurrence delegation.

The implementation fails closed when either exact image radius is above its
domain radius or strictly below it. Above fails the required inclusion; below
is inconsistent with exact matched compact-ball images. Consequently a
passing certificate has strict differential margins when available but a
necessarily non-robust zero domain-contact margin.

The analytic helper returns exact inverse derivative and Hessian bounds for
the boundary-fixed cubic $\phi_a(x)=x+a x(1-x^2)$ on $[-1,1]$. The focused
seam is `tests/test_quantitative_matched_local_nonaffine_c2_graph_transform.py`;
the boundary-contact dimensional core was added to `tests/test_dimensionless.py`.

