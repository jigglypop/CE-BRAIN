# Stable-snapshot audit

Status: COMPLETE

Gate: PASS

| ID | Status | Preconditions | Conclusion | Exclusion |
|---|---|---|---|---|
| CE-CGRAPH-001 | [정리] | Affine invertible base, global Lipschitz constants, (C3)--(C6) | Unique invariant coupled-base Lipschitz graph family with supplied base dimension. | No $C^{r-1}$ or local-boundary claim. |
| CE-CGRAPH-002 | [정리] | CE-CGRAPH-001 | Exact margins and transform contraction factor $Q$ are computable after normalization. | Constants are supplied, not estimated from brain data. |
| CE-CGRAPH-003 | [정리: 반례] | $\alpha=0$ or $Q=1$ | Base inversion or uniqueness can fail at the boundaries. | Equality cannot pass. |

Implement only the exact rational constant certificate and controls specified in the contract. Do not add empirical values, nonaffine/smooth claims, or dimension selection.

