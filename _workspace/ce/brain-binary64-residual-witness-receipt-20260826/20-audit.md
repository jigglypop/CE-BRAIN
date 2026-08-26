# Formal status audit

Status: COMPLETE

Gate: PASS

| ID | Status | Claim | Exclusion |
|---|---|---|---|
| CE-B64-001 | [정리] | Every finite canonical binary64 bit pattern decodes to the stated exact rational. | NaN and infinity are excluded. |
| CE-B64-002 | [정리: 조건부] | Decoded complex witnesses inherit the exact residual/Krawczyk theorem. | Solver success is neither assumed nor needed. |
| CE-B64-003 | [산출] | Canonical bit arrays receive deterministic SHA-256 identities and preserve signed-zero diagnostics. | Hash identity is not empirical provenance. |
| CE-B64-004 | [반례/경계] | Bad witnesses and excessive uncertainty fail at the unchanged exact gate. | No float tolerance or silent repair. |
| CE-B64-005 | [미완성: narrowed] | Full solver algorithm/hardware/BLAS/operation-rounding and empirical matrix receipts are known. | Stored-value decoding alone cannot prove them. |

The stored-value bridge passes formal audit without solver or empirical
promotion.
