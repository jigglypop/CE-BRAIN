# 구조 피벗 결과: direct-sample-index-cross-library

Status: ABANDONED (official minimal-block adverse control failed)

Stage A: PASS. Synthetic cross-library capability only; official decoder STOP is
still active. Independent verification found no P0 and required explicit scope
fields plus the bounded official Stage B check defined in this pivot contract.

Stage B: FAILED CLOSED. The pymef direct `[0,2048)` call returned the expected
cardinality and values but inspected the next block at the exact boundary. With
only the contracted first block present it emitted `CRC data block failure
detected, 1 blocks skipped`. The transient source bytes were deleted and no PASS
receipt was persisted. A dtype-dependent raw-byte hash mismatch was also found;
future comparisons must canonicalize equal numeric values before hashing.

Preserved result: Stage A synthetic direct sample-index semantics remain valid.
Rejected result: a single official physical block is not a warning-free executable
closure for this pymef boundary call, so this route does not clear the official
decoder STOP.

Metadata-only diagnostic: the first official TIDX row has RED flag 1 at segment
sample 0; the second row is contiguous at sample 2,048 with flag 0. No `.tdat`
range was requested before this fail-closed diagnostic. The contract now records
this initial-boundary behavior explicitly.
