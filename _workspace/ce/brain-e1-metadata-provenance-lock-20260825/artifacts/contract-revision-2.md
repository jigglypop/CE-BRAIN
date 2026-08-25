# Contract revision 2 receipt

Status: FROZEN

Revision command record: `revisions/log`, role `contract`, second revision.

Date: 2026-08-25

## Trigger

The raw v2.16.2 warehouse source was fetched from the pinned release commit
after the ordinary source reader reported a cache miss. Its byte hash and
method body showed that revision 1 had copied a stale API signature and had not
disclosed included WellKnownFile relationship metadata.

## Retired revision-1 value

`EcephysProjectWarehouseApi.get_sessions(session_ids=None,
published_at=None)`

## Exact replacement

`EcephysProjectWarehouseApi.get_sessions(session_ids=None,
has_eye_tracking=None, stimulus_names=None)`

The single released RMA query includes `specimen(donor(age))` and
`well_known_files(well_known_file_type)`. The latter is allowed only as
file-presence metadata inseparable from this pinned session response. No
separate WellKnownFile query, download link retention, NWB byte download, or
stream call is authorized.

Evidence: `artifacts/v2.16.2-warehouse-source-lock.md`, raw SHA-256
`c486110439af08e88ffc80a6abaa688dd7ae9768f77aef86d3ec0a3061186b0b`.

## Scope effect

This revision corrects and narrows provenance semantics. It does not execute
the session query or authorize unit, channel, probe, signal, scientific
endpoint, or E1 scoring access.

This is the second and final pre-execution contract repair. The contract now
records the two-step budget explicitly; any later contradiction requires a new
contract rather than another in-place revision.
