# E1 local receipt static audit

Status: PASS

Snapshot audited: `e1_metadata_receipt.py` and its focused test after the
UTF-8 fail-closed repair.

## Contract-to-code checks

- Imports are Python standard-library only: dataclasses, hashlib, json, re,
  datetime, typing, and unicodedata.
- The module has no AllenSDK, HTTP, socket, dataframe, filesystem, cache,
  unit, channel, probe, NWB, LFP, spike, covariance, model-score, or signal
  access path. It consumes already-materialised mappings only.
- The hashed table retains exactly the four frozen core fields. Optional
  source columns are discarded.
- IDs accept built-in non-Boolean nonnegative integers only and serialize to
  ASCII base-10 without coercion.
- Session labels are NFC, nonempty, Unicode `Cc`-free, and explicitly checked
  for UTF-8 encodability. Invalid surrogates receive the named
  `E1_FIELD_TYPE_INVALID` result.
- Time input uses the frozen offset-aware RFC3339 subset and emits fixed UTC
  microseconds. Naive time receives `E1_TIMEZONE_UNRESOLVED`.
- JSONL is compact, sorted-key, `ensure_ascii=False`, UTF-8, LF-terminated;
  sessions are integer-sorted.
- Canonically byte-identical session repeats are counted and deduplicated;
  same-session conflicts fail with `E1_INCONSISTENT_DUPLICATE_SESSION`.
- Assignment bytes are separate, use the frozen SHA-256 prefix rule and exact
  integer thresholds, and count unique specimens rather than sessions.
- Table and assignment SHA-256 values are separate. Status/diagnostics are
  outside both hashed streams.

## Evidence and ceiling

Focused test: `18 passed in 0.07 s`. This proves the declared local fixture
behavior only. It does not verify the live server schema/nullability, create a
remote metadata receipt, show split sufficiency, or support a brain geometry,
consciousness, or 4--6-dimensional identification claim.
