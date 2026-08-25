# BA-OBS-HPC3 transaction-route audit

Status: COMPLETE

Scope: routes concern receipt authority only. They do not inspect voltage, QC counts,
waveforms, P2P values, or outcomes, and none creates a second raw attempt.

| route | authority rule | status | falsifier / consequence |
|---|---|---|---|
| T1 `ATOMIC_RESULT_AUTHORITATIVE_SEAL` | build the inherited endpoint entirely in memory after all 18 source and dual-`MIN20` gates; atomically replace `raw_result.json`; resolve a valid result first even if progress finalization then fails | selected | any source, processing, construction, or serialization failure before replacement produces only the appropriate endpoint-free terminal receipt; invalid result receipt is not authoritative |
| T0 `PREDECESSOR_AMBIGUOUS_CATCH` | allow endpoint construction or a result-first failure to fall through an ambiguous terminal implementation state | prohibited | repeats the recorded HPC2 P1; no raw authorization |
| T2 `RERUN_AFTER_JOURNAL_OR_INFRASTRUCTURE_FAILURE` | treat incomplete/failed journal handling as a new raw budget | prohibited | violates exact one audited `ATTEMPT1`; resolver remains terminal or incomplete with no retry |
| T3 `QC_OR_THRESHOLD_REOPENING` | change threshold, cohort, contact, aperture, or endpoint after a stop | prohibited | outcome/count tuning; scientific contract is inherited unchanged |

T1 is the only route because it distinguishes a valid irreversible result commit from
non-authoritative progress bookkeeping. Its resolver precedence is fixed:
`raw_result.json`, then endpoint-free `qc_result.json`, then terminal progress, then
incomplete one-shot. This removes the predecessor's ambiguous catch without introducing
a second estimator, a result-selection degree of freedom, or a result-dependent branch.

The transaction stays outcome-blind: before the selected atomic commit, only integrity
and QC receipts may exist; after it, the already fixed computation is authoritative and
cannot be overwritten by journal finalization. Exactly one audited attempt remains
available, irrespective of infrastructure, QC, processing, or serialization failure.
