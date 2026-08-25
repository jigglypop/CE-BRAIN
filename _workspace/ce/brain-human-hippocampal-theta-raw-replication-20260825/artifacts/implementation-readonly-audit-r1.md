# BA-OBS-HPC1 implementation read-only audit — Revision 1

Status: PASS

Scope: independent static comparison of
`examples/brain/ba_obs_hpc1_raw_replication.py` and its focused test against the
frozen contract, source, mathematics, routes, and status audit after attempt 0 was
terminated. No network, `.eeg` voltage, endpoint, or Nature Source Data was opened.

## P0 — must close before attempt 1

1. A clinical late $D\le0$ was incorrectly routed to sensitivity-limited support.
   It must route to `SAME_DATA_REANALYSIS_NOT_SUPPORTED` while the published-model
   direction is unavailable; `RAW_DIRECTION_NOT_REPRODUCED` requires both directions.
2. Full-object hashing was checked transiently but only Boolean values were written.
   Each progress/final file receipt must contain expected and observed SHA-256 and
   byte count, S3 version ID/ETag, header SHA-256, and selected indices; the final
   receipt must also bind the exact source-lock SHA-256.
3. BrainVision `ChN` resolution/unit and endian convention were not parsed. They must
   be receipt-bound and either converted explicitly to microvolts or stopped; the
   IEEE float byte order must be verified before `<f4` decoding.
4. Existing result/progress files did not block another one-shot and success left
   progress at `RAW_IN_PROGRESS`. Attempt 1 must reject pre-existing transaction
   outputs, atomically record failure with the completed-file list, and end in
   `RAW_COMPLETE` exactly once.

## P1 — required closure or explicit ceiling

1. Revalidate the complete source-lock content against the canonical 18-object table,
   commit, sample rate/grid, block/channel/contact fields, unique keys, header sample
   interval, sizes, versions, and indices immediately before raw streaming.
2. Serialize aggregate clean mean waveforms and clean trial-level early/late/prestim
   P2P values as raw-derived summaries. The exact Satterthwaite engine remains
   unavailable; do not manufacture a model coefficient or p-value.
3. If full clinical late $D>0$ but any clinical late leave-one-participant-out contrast
   is nonpositive, add `PARTICIPANT_SENSITIVE`.
4. Do not call the contract-defined sine/cosine least-squares DFT removal or SciPy
   Butterworth implementation exact FieldTrip/MATLAB parity without a parity fixture.
5. Verify the versioned header GET response against HEAD and require its `DataFile`
   link to name the frozen `.eeg` object.

## P2 tests and transaction hygiene

- Write the source lock atomically.
- Add focused negative fixtures for endian/unit-resolution handling, tampered lock,
  observed-hash receipt, existing-run refusal/complete transition, clinical
  non-support, LOO sensitivity, and aggregate waveform/trial-P2P serialization.

The corrected baseline-before-artifact order, trial-axis sample-standard-deviation
z score, 18-file table, multiplex reshape, bipolar sign, integer windows, shared
participant bootstrap, and unique-participant LOO arithmetic were otherwise
consistent at this snapshot.

## Closure re-audit

The stable corrected snapshot was re-read after all items above were implemented.
No open P0, P1, or P2 remained for raw attempt 1. In particular:

- `source_lock.json` SHA-256 is frozen as
  `0b3d92f998f626ed37f68d0dfb1188a777afb287975916beec1f623d10d3fc58`
  and is checked before any raw request;
- BrainVision `DataFile`, resolution, default/declared unit, microvolt conversion,
  FieldTrip little-endian convention, header identity, and selected indices are
  receipt-bound;
- every raw file will record expected and observed digest/size plus version, ETag,
  header hash, and indices;
- aggregate mean waveforms, clean trial P2P, P2P-of-mean, both references, all LOO,
  paired sensitivity, controls, bootstrap, and the non-support/status guards are
  serialized;
- final result atomic commit precedes terminal `RAW_COMPLETE`, and any existing
  transaction artifact blocks another run;
- the documentation makes no exact FieldTrip/MATLAB numerical-parity claim.

The focused fixtures report `4 passed`; the canonical lock/hash check passes. The
re-audit opened no network, `.eeg` voltage, endpoint, or Nature Source Data.
