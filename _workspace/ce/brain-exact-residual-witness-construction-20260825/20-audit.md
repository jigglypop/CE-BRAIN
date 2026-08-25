# Stable-snapshot audit

Status: COMPLETE

Gate: PASS

| ID | Status | Preconditions | Conclusion | Exclusion |
|---|---|---|---|---|
| CE-WITNESS-001 | [정리] | Exact rational normalized node matrix and successful deterministic pivots | Exact $B_k=A_{0k}^{-1}$ exists and both inverse identities hold in $\mathbb Q(i)$. | No float-rounding guarantee. |
| CE-WITNESS-002 | [정리] | Four successful CE-WITNESS-001 nodes | Generated witnesses may be composed with the unchanged residual-family theorem; nominal residuals are zero. | Construction success alone is not robust-family success. |
| CE-WITNESS-003 | [정리: 반례] | A singular sampled node or radius-one scalar uncertainty | Singular node blocks construction; large uncertainty can block family contraction even with exact inverses. | Failure is not silently converted to contour/family certification. |

Implementation is authorized only for the exact rational constructor, its receipt, and a convenience composition with the predecessor certificate. Weighted norms and approximate solver rounding are excluded.

