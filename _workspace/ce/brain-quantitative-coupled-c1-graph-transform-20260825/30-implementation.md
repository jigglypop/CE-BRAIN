# Implementation

Status: COMPLETE

The exact certificate is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_coupled_c1_graph_transform.py`.
It composes the predecessor coupled-Lipschitz certificate and reports:

- the normalized Jacobian-Lipschitz inputs $H_f,H_g$ and graph $C^{1,1}$ modulus $\Lambda$;
- the one-graph bounds $C_F,C_Y,\Lambda_{\rm out}$ and the invariant-class margin;
- the two-graph preimage/state couplings $r_x,Z$;
- the derivative factor $\beta_c=Q/\alpha$, cross coefficient $c_c$, and strict bunching margin;
- exact finite iteration of the upper-triangular $(\delta_n,d_n)$ recurrence;
- predecessor-first failure codes and preservation, rather than selection, of the supplied base dimension.

All arithmetic inputs use the predecessor exact-rational parser. Negative derivative bounds,
binary floating-point inputs, non-integral iteration counts, and failed predecessor certificates
are rejected closed.

The focused test seam is
`tests/test_quantitative_coupled_c1_graph_transform.py`; the normalized-core unit audit was
added to `tests/test_dimensionless.py`.
