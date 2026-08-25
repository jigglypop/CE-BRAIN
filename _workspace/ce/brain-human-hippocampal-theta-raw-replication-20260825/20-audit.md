# BA-OBS-HPC1 status audit

Status: COMPLETE

Scope: final pre-ATTEMPT1 audit of the patched contract, attempt-0 disposition,
implementation revision, focused validation, and stable source/math/routes lanes.
No raw voltage, network object, or Nature Source Data was opened.

## Gate decision

Gate: PASS

This authorizes exactly one audited ATTEMPT1 raw one-shot. ATTEMPT0 is permanently
invalidated as `ATTEMPT0_IMPLEMENTATION_INVALID_NO_RESULT`, not treated as an
empirical result. Any further failure after ATTEMPT1 closes this contract version as
`BLOCKED`; no additional raw retry or outcome-driven revision is allowed.

## Findings

No open P0, P1, or P2 finding remains in the stable snapshot.

The independent implementation re-audit is `Status: PASS` in
`artifacts/implementation-readonly-audit-r1.md`. Its former P0/P1/P2 checklist is
closed by the registered implementation and the four-pass focused evidence in
`31-validation.md`.

## Attempt-0 disposition

`revisions/01-attempt0-implementation-invalid.md` records that attempt 0 returned
no exit code or result receipt, exposed a baseline-before-artifact-rule defect, and
was terminated before any endpoint, waveform, effect size, status, or biological
verdict was serialized or inspected. No `.eeg` payload or Nature Source Data was
opened. It is therefore a no-result invalidation, not a negative or positive finding.

## Attempt-1 closure checks

- The canonical header-only source lock is frozen at SHA-256
  `0b3d92f998f626ed37f68d0dfb1188a777afb287975916beec1f623d10d3fc58`.
  Raw mode rejects any byte-different lock before an `.eeg` request.
- The source lock covers all 18 objects and binds annex SHA-256/size, version ID,
  ETag, Content-Length, Accept-Ranges, version-pinned header identity, channel order,
  and frozen channel indices. p20 is fixed to D9 index 54 and D10 index 55.
- BrainVision `DataFile`, channel resolution/unit, microvolt conversion, and
  little-endian IEEE-float convention are receipt-bound; incompatible endian or
  unit declarations stop source identity. Header GET identity is checked against
  HEAD and the `DataFile` link must name the frozen `.eeg` object.
- Processing order is fixed: DFT and optional p17 filter, then baseline correction,
  then amplitude/kurtosis/sample-wise trial z-score artifact decisions. The focused
  tests cover the baseline-before-artifact rule.
- Raw streaming is sequential and non-persistent for voltage. Every completed file
  records expected/observed digest and size, version, ETag, header hash, and selected
  indices. Existing progress/result paths are rejected. The final result is atomically
  committed before terminal `RAW_COMPLETE` progress, so interruption or failure
  cannot silently authorize a retry.
- The frozen status lattice includes clinical non-support, reference uncertainty,
  `PARTICIPANT_SENSITIVE`, baseline/early controls, paired sensitivity,
  `ESTIMAND_DISCORDANT`, `SAME_DATA_REANALYSIS_NOT_SUPPORTED`, and
  `RAW_DIRECTION_NOT_REPRODUCED`. Seven unique-participant LOO contrasts are
  serialized with arm denominators recomputed; no LOO result licenses deletion.
- The exact Satterthwaite mixed-model engine is unavailable. The receipt must retain
  `PUBLISHED_MODEL_ENGINE_UNAVAILABLE`; no fabricated p-value or exact published
  connectivity-model claim is permitted. The archive EP lane remains a code-defined
  reanalysis under its stated ceiling.

## Focused evidence

`31-validation.md` records the final four-pass focused test run (`4 passed`, 0.98 s),
including source-lock digest rejection and final transaction ordering. It also records
the canonical source-lock/hash pass and the preceding three-pass validation. These
checks are source/fixture/transaction checks only and contain no real endpoint result.

The contract's normalized-`u` convention, dual-reference participant-cluster lower
bound gate, and `ESTIMAND_DISCORDANT` rule remain reconciled with `11-math.md` and
`12-routes.md`. The claim ceiling remains seven epilepsy-surgery participants with
real human iEEG, direct intervention, and same-data raw-derived robustness reanalysis;
it is not an outcome-blind independent confirmation or a randomized population causal
estimate.

## ATTEMPT1 authorization conditions

Run only the registered ATTEMPT1 transaction with the frozen source lock and no
contact, reference, filter, window, threshold, cohort, bootstrap, seed, or status-rule
change. Stop on any source/header/hash, aperture, implementation, or infrastructure
failure, preserve the atomic STOP receipt, and mark this version `BLOCKED` after that
single audited attempt. Do not open Nature Source Data before the raw receipt and
independent validation stage permits the aggregate cross-check.
