# Stable-snapshot audit

Status: COMPLETE

Gate: PASS

| ID | Status | Preconditions | Conclusion | Exclusion |
|---|---|---|---|---|
| CE-C1GRAPH-001 | [정리] | Passing triangular Lipschitz certificate, affine base, C1 derivative-variation bounds, $q\mu<1$ | The unique invariant Lipschitz graph is C1. | No coupled/nonaffine or higher-smooth claim. |
| CE-C1GRAPH-002 | [정리] | CE-C1GRAPH-001 and initial value/derivative distances | Exact recurrence (D5)--(D6) bounds derivative convergence. | It is an iterate bound, not a measured neural rate. |
| CE-C1GRAPH-003 | [정리: 반례] | $q\mu=1$ local linear map | Invariant Lipschitz $c|x|$ graphs need not be C1. | Equality cannot force smoothness. |

Implement only the exact rational C1 certificate and derivative-iteration bound composed with the predecessor gate. Do not add coupled/nonaffine/higher-order or empirical claims.

