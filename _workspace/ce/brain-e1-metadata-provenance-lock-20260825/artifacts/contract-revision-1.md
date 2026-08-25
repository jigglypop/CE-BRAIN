# Contract revision 1 receipt

Status: FROZEN

Revision command record: `revisions/log`, role `contract`, first revision.

Date: 2026-08-25

## Trigger

Pinned AllenSDK v2.16.2 primary source contradicted the predecessor metadata
instruction, and the mathematics lane found underspecified canonical byte
rules. No dataset response or scientific endpoint had been opened.

## Exact retired values

- manifest format `0.2.1`;
- allowed call `EcephysProjectCache.get_session_table(suppress=[])`;
- floating quotient split notation without an executable integer boundary;
- JSONL language without fixed identifier, Unicode, timestamp, duplicate,
  assignment-stream, or deterministic-subset semantics.

## Exact replacement values

- release/tag AllenSDK v2.16.2, commit
  `a9b5c685396126d9748f1ccecf7c00f440569f69`, manifest format `0.3.0`;
- only pinned `EcephysProjectWarehouseApi.get_sessions(session_ids=None,
  published_at=None)` may be considered for the session-only remote action;
- the first eight SHA-256 bytes are compared as a big-endian unsigned integer
  against $2^{63}$ and $3\,2^{62}$;
- exact ASCII10 identifier input, NFC session type, offset-aware RFC 3339 to
  UTC microseconds, compact sorted-key UTF-8 JSONL, byte-identical duplicate
  deduplication, separate assignment JSONL and separate hashes;
- two-run equality applies only to canonical table and assignment byte streams
  for identical pinned response bytes, not invocation timestamps.

## Scope effect

The revision narrows remote access and strengthens reproducibility. It does
not authorize an Allen request, open unit/channel/probe/NWB data, change an E1
endpoint, or promote any biological, metric, dimension, or consciousness
claim.
