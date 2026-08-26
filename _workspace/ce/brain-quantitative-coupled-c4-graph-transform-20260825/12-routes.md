# Alternative routes

Status: COMPLETE

| Candidate | Decision | Added dof | Target-aware? | Killing falsifier |
|---|---|---:|---|---|
| Modified tensor plus coefficient-vector composition | SELECTED | $V_f,V_g,\Lambda_4,\Xi_4$ | No | Scalar jet identity or any triangular reduction coefficient fails. |
| Reuse triangular C4 under graph-dependent inverse | REJECTED | 0 | No | Omits $TW$, $N[LU]$, $N[LP,LP]$, $M[LP]$ and inverse-slot changes. |
| Expand every final coefficient manually | REJECTED | 0 | No | Obscures predecessor dependencies and is vulnerable to term loss; vector form is exact and auditable. |
| Omit C4,1 when $L_{fy}>0$ | REJECTED | 1 fewer | No | Different preimages leave $D^4h(x_1)-D^4h(x_2)$ uncontrolled. |
| Nonaffine/local coupled C4 | DEFERRED | base D5 and collar data | No | Must reduce to this affine coupled theorem first. |

The selected route preserves the tensor identity and exposes every difference
source without introducing fitted parameters.
