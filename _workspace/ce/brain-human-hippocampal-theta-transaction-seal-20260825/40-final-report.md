# BA-OBS-HPC3 final report

Status: COMPLETE

## Disposition

`BLOCKED_RECEIPT_VALIDATOR / NO_RAW_ATTEMPT / NO_ENDPOINT`.

HPC3 closed the predecessor's transaction-path, CLI, source-classification, and
commit-order defects. Focused inherited and transaction tests reached 18 passing tests.
The final independent adversarial audit nevertheless found two remaining validator
defects after revision 2/2: nonnumeric or finitely tampered endpoint/analysis values can
be accepted without recomputation, and valid p20 three-channel exclusion-reason totals
can exceed the incorrectly single-channel bound.

No `.eeg` request or range request occurred in HPC3. No progress, QC, or raw-result
receipt was created, so no clean count or biological endpoint is known. The exact
cohort, source lock, channel order, QC thresholds, endpoint, time windows, estimator,
bootstrap, LOO, paired sensitivity, and status lattice remain frozen and reusable.

## Successor condition

A light successor may change only numeric receipt typing, endpoint-derived analysis
recomputation/tolerance, and channel-aware exclusion-reason bounds. It must retain the
single unused ATTEMPT1 and pass a new stable adversarial audit before raw access.
