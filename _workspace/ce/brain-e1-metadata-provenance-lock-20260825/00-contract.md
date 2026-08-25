# E1 Neuropixels metadata provenance repair contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-history-riesz-empirical-bridge-20260825`

## 1. Frozen objective

The predecessor froze an E1 metadata-only action before any spike, NWB,
covariance, fitted dimension, or model score was opened. Current official
source inspection exposed two possible defects in that specification:

1. the released AllenSDK 2.16.2 source reports
   `EcephysProjectCache.MANIFEST_VERSION = "0.3.0"`, not the frozen `0.2.1`;
2. `get_session_table(suppress=[])` internally annotates sessions by loading
   unit, channel, and probe metadata, contradicting a literal prohibition on
   unit-level metadata calls.

This run must verify or refute those findings from pinned primary source,
replace the contradictory action with the narrowest official session-only
query, and, only after source/math/audit gates pass, implement a canonical
metadata receipt. It must not open neural signals or scientific endpoints.

## 2. PREDECESSOR_EVIDENCE

| Item | Frozen status | This run may change |
|---|---|---|
| E1 dataset family | Allen Visual Coding Neuropixels, observational | provenance mechanics only |
| Cross-resource separation | `aisynphys` and E1 have distinct dataset families/namespaces | no numeric cross-resource ID comparison |
| Within-E1 split | `UNVERIFIED_PENDING_METADATA` | may become metadata-verified after an authorized receipt |
| E1 scoring | forbidden | remains forbidden |
| 4–6 and consciousness | not identified | remains not identified |
| Previous metadata spec | `FROZEN / UNEXECUTED` | retire or revise if primary source contradicts it |

## 3. BIO_STARTING_MECHANISM and CE_DELTA

The inherited candidate biological baseline remains a state-conditioned
recurrent population model. The sole later CE candidate remains a causal
history readout added to that same baseline. Neither equation is fitted in
this run. Metadata provenance cannot validate recurrence, a Riemannian metric,
or the CE history term.

## 4. MEASUREMENT_MODEL

The future measurement object is sorted extracellular spike data with a
source-locked count/covariance model. This run opens neither spikes nor a
measurement endpoint. Session/specimen identifiers, acquisition date, and
session type are provenance metadata, not neural observations.

## 5. DATA_PROVENANCE candidate

The source lane must pin:

- AllenSDK release/tag, source commit if available, Python compatibility,
  license identity, and wheel/source hashes;
- the exact manifest-format version in that release;
- the implementation and remote call graph of `get_session_table`,
  `_get_sessions`, and the public warehouse API's session-only method;
- the exact official host, query/resource identity, response schema, and
  whether the response can be obtained without unit/channel/probe/NWB calls;
- the Allen data-use/terms page identity and access date.

No claim may rely on the moving `master` branch when a released tag is
available. A release/source mismatch is a stop condition.

The source lane has now pinned AllenSDK v2.16.2, release commit
`a9b5c685396126d9748f1ccecf7c00f440569f69`, wheel SHA-256
`ecbcac94b720a2909319a741425f8325db9f0c15a9df0db8ceae64345d67fccc`,
and manifest format `0.3.0`. The predecessor values `0.2.1` and
`get_session_table(suppress=[])` are retired for this action. The only
admissible remote method is the pinned public
`EcephysProjectWarehouseApi.get_sessions(session_ids=None,
has_eye_tracking=None, stimulus_names=None)` session query against the
recorded Allen API host. Calls
to cache `get_session_table`, units, channels, probes, metrics, NWB, LFP, or
signals are forbidden. Exact server response schema and nullability remain a
runtime assertion, not source evidence.

The pinned method's one session RMA query includes `specimen(donor(age))` and
`well_known_files(well_known_file_type)` relationship metadata to derive donor
fields and `has_nwb`. This relationship metadata is allowed only as an
inseparable part of the pinned session query; download links are discarded and
no separate WellKnownFile query, NWB byte download, or stream call is allowed.
The pinned raw source receipt and hash are in
`artifacts/v2.16.2-warehouse-source-lock.md`.

The exact before/after values and revision reasons are frozen in
`artifacts/contract-revision-1.md` and
`artifacts/contract-revision-2.md`; `revisions/log` records the corresponding
contract revision commands.

## 6. DATA_SPLIT candidate

If a session-only table passes schema checks, materialize required fields
`ecephys_session_id`, `specimen_id`, `session_type`, and
`date_of_acquisition`. Allocate the complete table by specimen before any
eligibility rule, using the already frozen salt
`CE-E1-NEUROPIXELS-V1` and the first eight SHA-256 bytes as an unsigned
big-endian integer $H_g$. Use exact integer boundaries: calibration when
$H_g<2^{63}$, development when $2^{63}\le H_g<3\,2^{62}$, and held-out
otherwise. No floating-point quotient enters allocation. Missing
specimen/session IDs, inconsistent duplicates, unknown
timezone semantics, or a source schema that cannot supply the required fields
must fail closed. No rehash or subject movement is allowed.

Identifier hashing uses the ASCII base-10 representation of a nonnegative,
non-Boolean integer, without sign, whitespace, leading zero except `0`, point,
or exponent. The bytes hashed are exactly
`CE-E1-NEUROPIXELS-V1:<ASCII specimen_id>`.

## 7. OBSERVABLES and permitted receipt

The only outputs admitted here are source/version identities, canonical
session rows, row/specimen counts, schema diagnostics, deterministic split
assignments, byte hashes, and explicit negative-access assertions. The receipt
must state that unit/channel/probe tables, NWB, LFP, spike arrays, covariance,
dimension, likelihood, and model-score endpoints were not opened.

If the official session-only response includes descriptive metadata, retain it
only under an audited required/optional schema. Do not derive unit counts or
brain-structure lists by silently opening other tables.

The canonical core table contains exactly the four required keys. IDs are
serialized as canonical ASCII decimal strings. `session_type` is a nonempty
NFC Unicode string without control characters. `date_of_acquisition` must be
an offset-aware RFC 3339 instant and is emitted in UTC as
`YYYY-MM-DDTHH:MM:SS.ffffffZ`; naive or named/unknown timezones fail closed.
Rows are compact UTF-8 JSON objects with sorted keys and one LF terminator,
sorted by integer session ID. Non-finite values and silent coercions are
forbidden.

Byte-identical repeated canonical rows are deduplicated with a recorded count;
any nonidentical repetition of a session ID returns
`E1_INCONSISTENT_DUPLICATE_SESSION`. A separate assignment JSONL contains
exactly session ID, specimen ID, and split, under the same ordering and
serialization rules. Table and assignment bytes receive separate SHA-256
hashes. Two-run determinism means equality of these two byte streams and
hashes for the same pinned response bytes; invocation timestamps and host
diagnostics remain outside the hashed streams.

## 8. RESIDUAL_RULE and FALSIFIERS

Return a named fail-closed status for any of the following:

- release, tag, manifest, host, license, or source hash mismatch;
- hidden unit/channel/probe or signal request in the selected call graph;
- missing or invalid required fields;
- inconsistent duplicate session rows or one session assigned to multiple
  specimens;
- noncanonical serialization or nonreproducible split/hash receipt;
- any scientific endpoint or signal access.

A metadata failure does not permit synthetic replacement, a different release,
or endpoint access in the same run.

## 9. MATCHED_CONTROLS and MODEL_SELECTION

This is a provenance apparatus, not a fitted model. Controls are call-graph
inspection, a synthetic schema fixture, duplicate/missing/type adversaries,
and deterministic two-run byte comparison. There is no model selection,
dimension menu scoring, or biological parameter estimation.

## 10. REVISION_TRIGGER

This repair used two pre-execution contract revisions. Revision 1 retired the
predecessor manifest/call and froze canonical bytes; revision 2 corrected the
API signature and disclosed relationship metadata after the pinned raw source
became available. Both are recorded with exact before/after values in the two
revision artifacts and occurred before any Allen response was opened. The
contract revision budget is now exhausted: any further source/schema
contradiction closes remote execution and requires a new contract. Neither
revision may broaden access to unit, channel, probe, signal, or scientific
endpoint data.

## 11. CLAIM_CEILING

- Source inspection may retire the stale predecessor metadata instruction.
- A deterministic local receipt implementation is software evidence only.
- A remote metadata receipt, if executed, can verify provenance and split
  apparatus only; it does not reach biological evidence L1.
- E1 prediction remains unopened and capped at future observational L3.
- No result identifies recurrence, a metric, a subspace rank, consciousness,
  or dimension 4–6.

## 12. Candidate order

1. Pin release/source/call graph and data-use terms.
2. Audit canonicalization and split mathematics independently.
3. Retire the predecessor instruction if contradicted.
4. Implement a session-only receipt generator after Gate PASS.
5. Execute a remote metadata call only if the pinned source path, environment,
   and access boundary are all satisfied; otherwise stop at a validated local
   apparatus with the exact prerequisite recorded.
