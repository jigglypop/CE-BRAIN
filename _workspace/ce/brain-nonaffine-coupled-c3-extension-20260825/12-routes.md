# Alternative routes

Status: COMPLETE

목표는 전역 비아핀 결합 기저에서 3차 그래프 반지름과 네 단계 차이 재귀를
동시에 닫는 것이다. 후보는 계산 결과를 보기 전에 계약에 고정했으며 조정
모수나 데이터 적합은 없다.

| Candidate | Decision | Added dof | Target-aware? | Cross-check and killing falsifier |
|---|---|---:|---|---|
| Generic coupled inverse-composition skeleton plus $T_\phi,U_\phi$ | SELECTED | 2 explicit moduli | No | Must reduce exactly to affine coupled $C^3$ and common-inverse nonaffine triangular $C^3$; any unmatched coefficient kills the route. |
| Reuse affine coupled $C^3$ unchanged | REJECTED | 0 | No | $D^3\phi$ contributes the nonzero additive $T_\phi$ term, so the one-graph bound is incomplete. |
| Replace the coupled inverse by only $\mu,\nu,\tau$ | REJECTED | 3 inverse bounds | No | When $L_{fy}>0$, the preimage depends on the graph and the modified-Hessian plus inverse-Jacobian difference terms survive. |
| Keep $T_\phi$ but omit $U_\phi$ | REJECTED | 1 | No | $D^3\phi(x_1)-D^3\phi(x_2)$ is uncontrolled in the $C^{3,1}$ and two-graph comparison. |
| Local/matched-domain nonaffine coupled $C^3$ | DEFERRED | domain radii and contacts | No | It may start only after this global identity passes; failure of inverse-domain coverage kills local composition without changing the global theorem. |

The selected route introduces one third-order base bound already required by
the $C^2$ predecessor and one genuinely new fourth-order modulus.  It is the
only candidate that preserves both independent predecessor reductions without
discarding graph-dependent inverse corrections.

