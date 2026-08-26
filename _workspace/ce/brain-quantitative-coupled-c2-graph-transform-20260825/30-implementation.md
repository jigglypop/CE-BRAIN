# Implementation

Status: COMPLETE

The exact certificate is implemented in
`reality_stone/python/reality_stone/clarus/quantitative_coupled_c2_graph_transform.py`.
It composes the affine coupled C1 predecessor and exposes every layer used by
the proof:

- map-Hessian moduli $T_f,T_g$ and graph-Hessian modulus $\Xi$;
- one-graph bounds $C_P,C_R,C_T,N,C_N,\Xi_{\rm out}$;
- two-graph coefficients $P_d,P_\delta,R_d,R_\delta,N_d,N_\delta$;
- $\beta_{2,c}=Q/\alpha^2$, both second-order cross coefficients, margins,
  exact simultaneous iteration, robust-interior status, and supplied dimension.

The graph-Hessian modulus gate is conditional on $L_{fy}>0$. At exactly
$L_{fy}=0$, preimages are graph-independent and a negative unused $\Xi$ margin
does not invalidate the certificate. Predecessor failures remain primary,
C2,1 class equality passes as non-robust, and second-order bunching equality
fails closed.

The focused seam is `tests/test_quantitative_coupled_c2_graph_transform.py`;
the normalized core was added to `tests/test_dimensionless.py`.
