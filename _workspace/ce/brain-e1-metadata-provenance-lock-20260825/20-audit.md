# E1 metadata provenance lock — status audit

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-e1-metadata-provenance-lock-20260825`

Audit scope: stable snapshot of `00-contract.md`, `10-sources.md`,
`11-math.md`, `12-routes.md`, both contract-revision receipts, the pinned
v2.16.2 source-lock artifact, and the pure fixture. No Allen response,
network data, scientific endpoint, or Git state was used.

## Findings first

### P0 / P1

None.

The prior source-boundary inconsistency is closed: `10-sources.md` E1-SRC-07
now explicitly says **Historical API documentation — RETIRED, not admissible**
and points active use exclusively to E1-SRC-08A and the byte-locked v2.16.2
warehouse source. The active signature is consistently
`EcephysProjectWarehouseApi.get_sessions(session_ids=None,
has_eye_tracking=None, stimulus_names=None)`.

The prior revision-budget inconsistency is closed: `00-contract.md` §10
explicitly records the two pre-execution repairs, states that the budget is
exhausted, and requires a new contract for any later contradiction.
`contract-revision-1.md`, `contract-revision-2.md`, and `revisions/log` retain
the corresponding before/after values and reasons. Both revisions occurred
before any Allen response was opened and neither broadens data access.

## Verified source and apparatus claims

- AllenSDK v2.16.2 release commit, wheel SHA-256, manifest `0.3.0`, license
  identity, and pinned source paths are recorded.
- The released `get_session_table` call graph is correctly marked unsafe due
  to hidden unit/channel/probe metadata calls.
- The raw v2.16.2 warehouse source is byte-locked with SHA-256
  `c486110439af08e88ffc80a6abaa688dd7ae9768f77aef86d3ec0a3061186b0b`.
  Its single RMA session query and `well_known_files` relationship boundary
  are recorded; download links, separate WellKnownFile queries, NWB, signals,
  and scientific endpoints remain forbidden.
- Core canonicalization fixes are complete: built-in nonnegative integer IDs,
  ASCII decimal serialization, NFC `session_type` with Unicode `Cc`
  rejection, strict offset-aware RFC3339 normalization to UTC microseconds,
  compact sorted-key UTF-8 JSONL, deterministic duplicate policy, and
  optional-field exclusion.
- Separate assignment JSONL, integer session ordering, exact split thresholds,
  two-run byte equality, and separate SHA-256 hashes are exercised by the
  pure fixture.
- The split proof remains conditional apparatus math only: identical specimen
  IDs produce identical salt/hash input and therefore one deterministic split;
  it proves no biological independence or eligible-sample sufficiency.

## Focused validation evidence

Command:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-e1-metadata-provenance-lock-20260825\artifacts\math_metadata_split_fixtures.py
```

Result: `PASS: E1 metadata canonicalization and specimen-split adversarial fixtures`.

This is local fixture evidence only. No remote schema, response rows, split
balance, biological variable, recurrence, metric, geometry, consciousness,
or dimension result was obtained.

## Separate admission decisions

| Item | Decision | Ceiling / condition |
|---|---|---|
| Integer SHA-256 split proof | PASS, conditional apparatus math | Frozen salt, ASCII10 IDs, big-endian prefix, exact integer cutpoints |
| Pure canonicalization/split fixture | PASS, local software evidence | Does not imply a remote receipt |
| Local receipt implementation | **Admitted to proceed under the frozen contract** | Must preserve both hashed streams, negative-access assertions, optional-field exclusion, and fail-closed schema checks; no receipt is claimed by this audit |
| Remote `WarehouseApi.get_sessions` call | **Not admitted** | Requires separate explicit authorization, pinned runtime/wheel/interpreter, exact host/query receipt, runtime schema/nullability checks, and no forbidden follow-up calls |
| Remote metadata receipt | Not present | No Allen response bytes, session IDs, or split counts were opened |
| E1 biological/CE score, recurrence, metric, rank, consciousness, 4–6 dimension | Forbidden / not claimed | Provenance apparatus only; future observational ceiling L3 |

## Gate

Gate: PASS

The source, canonicalization, split, revision, and claim-ceiling gates have
no P0/P1 finding. PASS admits the local implementation route only; it does
not silently authorize the remote call or elevate metadata mechanics to
biological evidence. Any new source/schema contradiction is outside the
exhausted two-revision budget and requires a new contract.

Referee disposition: internal apparatus PASS; not biological or arXiv-level
evidence.
