# BA-OBS-HPC2 implementation

Status: SKIPPED — raw build authorization blocked after revision 2/2; static record retained below

Pre-raw implementation only. The author-order QC uses the frozen `(k,z,a)=(5,5,500)`
axiom, contract-defined OLS/Butterworth operations (not exact MATLAB parity), first-999
author grid, and artifact decisions before baseline. No raw EEG request has been made.

Header-only source lock was generated for all 18 files, including p20 D9/C1/C'1 QC
indices, channel order/scales, annex and version/header receipts. Its frozen SHA-256 is
`66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810`; the frozen
author-code static receipt SHA-256 is also code-bound. Raw mode is implemented but
audit-gated and has not been invoked.

The static `ATTEMPT1` transaction is mock-injectable: it scans all 18 files for QC
after a QC failure, stops immediately for loader/source failure, writes only integrity
and clinical/local QC clean-count/reason receipts during scanning, and writes
`QC_STOP_MIN20` without endpoint fields if any reference has fewer than 20 trials.
On all-pass mocks it keeps endpoint arrays in memory, writes result before terminal
`RAW_COMPLETE` progress, and rejects any pre-existing transaction receipt.

All-pass aggregation now computes clinical/local participant pre/post deltas and
participant-equal TS(4)-PB(5) D for early/late/prestim, deterministic 65,536-draw
PCG64 shared-participant bootstrap intervals, seven LOO contrasts, p17/p19 paired
sensitivity, model-unavailable/discordance ceiling, and the frozen status lattice.
These fields are created only after the complete scan passes; QC/source-stop receipts
contain no endpoint summary.

Revision 2 additionally binds CLI execution to frozen source-lock bytes and the static
receipt hash, provides a version-pinned full-object default loader with GET
version/ETag/size/SHA checks and little-endian multiplexed scaling, and routes its
endpoint through the first identically preprocessed QC channel. The raw CLI path is
implemented but has not been invoked.

The default loader retains at most one full locked object (largest locked object about
109 MB) plus selected arrays, verifies version/ETag/content length/full SHA-256, then
copies selected arrays and releases the raw byte/blob buffers before the next file.

`run_raw_cli` performs prior-receipt rejection and frozen source/static receipt
verification before constructing a loader, then dispatches the sole ATTEMPT1 through
the existing result-first transaction. It is injection-tested only and was never run
against a network object.

Final revision seals preprocessing and aggregate exceptions as `IMPLEMENTATION_STOP`
after progress exists, with no endpoint artifacts. Bipolar scaling is channel-wise,
nonfinite trials are excluded from finite z statistics, and early control does not
downgrade the late/prestim/paired/LOO status gate.
