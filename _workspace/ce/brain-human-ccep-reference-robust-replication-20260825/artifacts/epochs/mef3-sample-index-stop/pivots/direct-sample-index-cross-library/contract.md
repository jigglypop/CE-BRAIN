# 구조 피벗 계약: direct-sample-index-cross-library

Status: IN_PROGRESS

## Staged authorization and claim ceiling

Stage A is signal-free. It must establish exact half-open sample-index cardinality,
TOC identity, and known-value identity across `mef3io==1.1.2` and `pymef==1.4.8`.
Passing Stage A does not clear the official decoder STOP.

Stage B is one bounded **capability fixture**, not development endpoint analysis. It
may access only official `ds004457 v1.0.2`, commit
`1bbd3a0696c56b7dfd87020bc61092644a702d0a`, subject `sub-1`, channel `LV1`:
the complete 16,384-byte `.tmet`, complete 196,016-byte `.tidx`, and `.tdat`
universal header plus the first compressed block (2,960 bytes total). Source
pointers, full-object identities, S3 version/ETag/Content-Range, parsed first TOC
row, decoder cardinality/value hashes, and cleanup must be recorded. All acquired
bytes are OS-temporary and must be deleted before the receipt is written.

The official first row carries RED flag bit 0 because it begins the segment. This
initial-boundary flag is accepted only when the row starts at sample 0 with 2,048
samples and the second row begins exactly at sample 2,048 with discontinuity false.
This source-locked continuity pair replaces the refuted auxiliary assumption that
the first physical row itself must have bit 0 clear.

Stage B may compare only `[0,N)` from the first physical block through the direct
pymef sample API and an independent mef3io read. It may not compute a BIDS trial,
CCEP window, reference, edge, endpoint, or development gate. `sub-5` and every
confirmation subject remain sealed. A Stage B failure retains
`APPARATUS_MEF3_SAMPLE_INDEX_STOP`; no uUTC-grid fallback is allowed.

반례 식별자: `mef3-sample-index-stop`

구조 지문: `pymef-sample-coordinate-cross-library-v1`

구조 변경 종류: `measurement`

바뀌는 항: sample-coordinate access operator

판별 예측: known int32 samples written by mef3io are recovered exactly by pymef for single- and cross-block half-open sample windows

중단 조건: any TOC, cardinality, value-identity, cleanup, or official minimal-block check fails
