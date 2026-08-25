# BA-OBS-HPC4 implementation

Status: COMPLETE

HPC4 binds `raw-one-shot` and read-only `status` to the active receipt-validator run.
It inherits HPC3's single-attempt authority/journal/terminal writer semantics, then
adds strict JSON-number typing, waveform-derived P2P checks, full deterministic
`aggregate(files)` comparison, and p20 three-channel clinical-reason bounds. No raw
object, voltage, or network endpoint was opened.

Revision 1/2 also seals the loader aperture before QC: source-lock block/channel/time
shapes and the endpoint-to-first-QC-channel mirror must match exactly. QC receipts now
reconcile excluded trials against channel-aware reason totals; truncated records cannot
be promoted to either authority.
