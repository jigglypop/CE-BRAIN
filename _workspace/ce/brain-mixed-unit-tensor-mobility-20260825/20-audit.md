# Stable-snapshot audit

Status: COMPLETE

Gate: PASS

| ID | Status | Preconditions | Conclusion | Exclusion |
|---|---|---|---|---|
| CE-TMOB-001 | [정리] | Positive coordinate/energy/time scales and declared tensor units | (T2) is dimensionless and gives (T3). | No biological scale identification. |
| CE-TMOB-002 | [정리] | Exact symmetric rational tensor and all principal minors nonnegative | PSD is preserved by normalization and pure-gradient model potential is nonincreasing. | No metabolic-energy or drift-work claim. |
| CE-TMOB-003 | [정리: 반례] | Negative principal minor or nonsymmetry | Dissipation theorem is unavailable; inputs fail closed. | No tolerance symmetrization. |

Implement only the exact finite tensor scale/PSD/pointwise-output certificate. No empirical defaults or operator/higher-dimensional claims are authorized.

