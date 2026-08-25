# E1 local metadata receipt implementation

Status: COMPLETE

Scope is deliberately local and dependency-free.  Added
`reality_stone/python/reality_stone/clarus/e1_metadata_receipt.py`, which only
accepts already-materialised row mappings and does not import AllenSDK,
network, dataframe, filesystem, NWB, unit, channel, probe, LFP, spike, or
scientific-endpoint code.

Implemented contract mechanisms:

- built-in non-Boolean, nonnegative integer identifiers and exact ASCII
  decimal hashing input;
- NFC/non-control, UTF-8-encodable session labels and strict offset-aware
  RFC3339 conversion to UTC microseconds;
- exactly four canonical table fields, compact sorted-key UTF-8 JSONL, integer
  session ordering, byte-identical canonical deduplication, and conflict
  rejection;
- separate assignment JSONL, SHA-256 hashes, big-endian integer specimen
  allocation, counts, diagnostics, and an explicit negative-access status.

This is a local software apparatus.  It has not opened an Allen response and
does not prove a remote schema, dataset split balance, neural mechanism, CE
term, Riemannian metric, rank, consciousness, or dimension.
