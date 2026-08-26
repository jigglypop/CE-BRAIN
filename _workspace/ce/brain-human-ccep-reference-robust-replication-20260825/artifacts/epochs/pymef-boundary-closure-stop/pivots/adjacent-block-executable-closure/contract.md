# 구조 피벗 계약: adjacent-block-executable-closure

Status: COMPLETE

## Frozen bounded execution

This capability-only route is limited to official `ds004457 v1.0.2`, commit
`1bbd3a0696c56b7dfd87020bc61092644a702d0a`, `sub-1/LV1`. It may transiently
acquire the complete `.tmet` (16,384 bytes), complete `.tidx` (196,016 bytes),
TDAT bytes `0-2959` (universal header plus target block), and TDAT bytes
`2960-4887` (the single boundary-neighbor block): 217,288 payload bytes total.
No later byte, BIDS trial, CCEP window, reference, edge, endpoint, sub-5 signal,
or confirmation signal is authorized. All source bytes must be deleted before a
compact receipt is retained; persistent raw bytes must equal zero.

The direct pymef `[0,2048)` output must have exactly 2,048 finite numeric values,
emit no warning, and equal mef3io's target-block raw counts after both arrays are
canonicalized to float64 for hashing. Source pointers/full hashes, S3
ETag/version/Content-Range for both ranges, first/second TIDX rows, canonical
hashes, warning list, byte counts, and cleanup are mandatory. Any failure keeps
`APPARATUS_MEF3_SAMPLE_INDEX_STOP` active with no uUTC fallback.

Both readers are inside one warnings-as-errors observation scope. Sampling rate
must equal 2048 Hz and units must equal `microvolts`. A second HEAD after both
ranges must reproduce the same Content-Length, ETag, and VersionId as the first
HEAD. `217,288` is network payload, while the transient TDAT has the source's
6,998,008-byte logical length; the latter is deleted before receipt retention.

반례 식별자: `pymef-boundary-closure-stop`

구조 지문: `target-plus-boundary-neighbor-closure-v1`

구조 변경 종류: `measurement`

바뀌는 항: physical acquisition closure operator

판별 예측: adding only the immediately inspected second compressed block removes every decoder warning while preserving the exact first-block cardinality and canonical value hash

중단 조건: any warning, target value/cardinality mismatch, source identity mismatch, cleanup failure, or access beyond two physical blocks
