# BA-OBS-HPC3 implementation

Status: COMPLETE

Implemented and audit-gated only; no raw/network invocation. HPC3 inherits exact HPC2
lock/static bytes and commits authoritative result/QC receipts before best-effort journal finalization.

Processing failures before an authoritative replace terminalize the progress receipt as
`IMPLEMENTATION_STOP` without QC/result artifacts. Strict JSON serialization is part of
that boundary; raw result authority survives a later journal-finalization failure.

The inherited HPC2 source lock and author-code static receipt are hash-bound before
loader construction. The inherited version-pinned reader is exercised only with a fake
response in tests; it verifies full-object identity before little-endian decode and
uses ordered QC scaling plus channel-wise bipolar scaling.
