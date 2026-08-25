# Exact residual-witness construction contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-interval-residual-krawczyk-20260825`

## Objective

Close the predecessor's witness-construction gap for exact rational nominal matrices. At the fixed four contour nodes, construct $B_k=A_{0k}^{-1}$ by deterministic exact Gauss--Jordan elimination over $\mathbb Q(i)$, verify both inverse identities, and feed the witnesses into the unchanged componentwise residual certificate.

This does not certify floating-solver rounding, optimize a weighted norm, or provide empirical interval coverage.

## Predecessor evidence

| Result | Evidence | State | Preserved claim | No-retry condition |
|---|---|---|---|---|
| Componentwise residual theorem | predecessor `11-math.md`, K1--K3; final report | PASS | Any supplied exact $B_k$ is checked by strict contractions and a chord-corrected full-circle lower. | Do not bypass the existing residual checks. |
| Supplied-witness apparatus | predecessor focused 14/14 | PASS | Exact/inexact witnesses are parsed and audited. | Construction success alone is not family certification. |
| Witness-generation route | predecessor `12-routes.md` | OPEN | A frozen rule is needed before a generated witness inherits provenance. | Do not use post-hoc floating rounding in this exact route. |

## Frozen construction

Normalize first:

$$
\widetilde U_0=U_0/s_*,\qquad
\widetilde c=c/s_*,\qquad
\widetilde r=r/s_*.
$$

At the ordered directions $(1,i,-1,-i)$, form

$$
A_{0k}=(\widetilde c+\widetilde r d_k)I-\widetilde U_0.
\tag{W1}
$$

Use left-to-right columns and the first nonzero pivot row at or below the diagonal; swap that row into place, normalize the pivot row, and eliminate the column from every other row. Arithmetic is exact in $\mathbb Q(i)$. If no pivot exists, return a named construction non-certificate with the first failing node. Otherwise return $B_k$ only after exact checks

$$
A_{0k}B_k=I,\qquad B_kA_{0k}=I.
\tag{W2}
$$

The convenience bridge must pass these generated witnesses to the predecessor's unchanged family certificate. A construction pass with a residual-family failure remains a family non-certificate.

## Controls and ceiling

Required controls are scalar, diagonal, and nonnormal exact inverses; exact zero nominal residual; deterministic repeat; raw-unit rescaling invariance after normalize-first; a singular-node construction failure; uncertainty contraction failure despite successful construction; malformed/float/Boolean inputs; and adjacent predecessor regression.

The result may be an exact conditional theorem/apparatus for rational nominal nodes. It does not produce approximate rational witnesses from floats, prove a nonsampled arbitrary contour, select weights or blocks, validate statistical coverage, analyze neural data, identify consciousness, or select dimension 4--6.

