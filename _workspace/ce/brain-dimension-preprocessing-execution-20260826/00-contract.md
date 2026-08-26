# Contract: development-only exact dimension preprocessing

Status: COMPLETE

## Objective

Remove the precentered-vector assumption by computing session means only from raw
development observations, applying frozen positive reference scales, transforming
both held-out conditions with the unchanged development statistics, and composing
the result with DPCA/DEXEC/DSTAB.

## Acceptance conditions

1. All raw values and reference scales are exact; scales are strictly positive.
2. Means are computed from development observations only.
3. Normalized development coordinate sums are exactly zero.
4. Conscious and control held-out vectors use the same development transform.
5. Held-out statistics are never reestimated.
6. Raw scale covariance and a held-out-shift adversary are verified.
7. External-byte provenance remains false.
