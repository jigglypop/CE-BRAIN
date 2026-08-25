# E1 metadata provenance lock and local receipt

Status: COMPLETE

Date: 2026-08-25

## Abstract

This run repairs the stale predecessor E1 metadata specification and closes
the network-free receipt apparatus. The active boundary is AllenSDK v2.16.2,
commit `a9b5c685396126d9748f1ccecf7c00f440569f69`, manifest `0.3.0`, and the
pinned warehouse method `EcephysProjectWarehouseApi.get_sessions(...)`.
The released cache-level `get_session_table` route is retired because it can
open hidden unit/channel/probe metadata. A dependency-free local module now
canonicalizes already-materialised session mappings and emits separately
hashed table and specimen-split assignment streams. Its focused test passes
18 cases. No live Allen response, signal, scientific endpoint, brain geometry,
consciousness result, or 4--6-dimensional identification was opened or found.

## 1. Frozen source boundary

The accepted source is AllenSDK v2.16.2 with wheel SHA-256
`ecbcac94b720a2909319a741425f8325db9f0c15a9df0db8ceae64345d67fccc`.
The pinned warehouse implementation has raw-source SHA-256
`c486110439af08e88ffc80a6abaa688dd7ae9768f77aef86d3ec0a3061186b0b`.
Its admitted method is:

```text
EcephysProjectWarehouseApi.get_sessions(
    session_ids=None,
    has_eye_tracking=None,
    stimulus_names=None,
)
```

The single RMA response inseparably includes specimen/donor-age and
well-known-file relationship metadata. That file-presence metadata may be
discarded while retaining only the four core fields; separate file queries,
links, downloads, units, channels, probes, NWB, LFP, spikes, and metrics are
forbidden. The live response schema and nullability remain unverified because
this run did not execute the remote method.

## 2. Canonical receipt definition

Each admitted row contains built-in non-Boolean nonnegative integer
`ecephys_session_id` and `specimen_id`, a nonempty NFC/control-free and
UTF-8-encodable `session_type`, and a strict offset-aware RFC3339
`date_of_acquisition`. Time is normalized to UTC microseconds. The table keeps
exactly these four sorted keys, uses compact UTF-8 JSONL with LF terminators,
and sorts sessions by integer ID.

Canonically byte-identical repeated sessions are counted and deduplicated.
Any changed core value for the same session fails with
`E1_INCONSISTENT_DUPLICATE_SESSION`. Optional response columns are discarded.
An assignment JSONL containing exactly session ID, specimen ID, and split is
hashed separately from the table.

For canonical specimen bytes `ASCII10(g)`, define

$$
H(g)=\operatorname{uint64}_{\rm BE}\!\left(
\operatorname{SHA256}(\texttt{CE-E1-NEUROPIXELS-V1:}\Vert
\operatorname{ASCII10}(g))[0{:}8]\right).
$$

The exact integer allocation is calibration for $H<2^{63}$, development for
$2^{63}\le H<3\cdot2^{62}$, and held-out otherwise. Equal specimen IDs have
identical hash input and therefore cannot cross splits. This proves only the
determinism of the apparatus, not biological independence or sample adequacy.

## 3. Implementation and validation

`reality_stone/python/reality_stone/clarus/e1_metadata_receipt.py` is a pure
local core with standard-library imports only. It accepts already-materialised
mappings and has no AllenSDK, HTTP, filesystem, dataframe, cache, or scientific
resource access path. Invalid types, missing fields, unknown timezone
semantics, non-UTF-8 surrogate labels, and conflicting duplicate sessions fail
closed with named errors.

Focused reproduction:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.codex\hooks\python.cmd pytest tests/test_e1_metadata_receipt.py -vv -s --tb=short
```

Result: **18 passed in 0.07 s** under Python 3.14.2 and pytest 9.0.3. External
pytest plugin auto-loading was disabled after the default host path produced a
pre-collection `MemoryError`; the repository hook, interpreter, assertions,
and test scope were otherwise unchanged. The static audit found no network or
forbidden-resource path in the local core.

## 4. Result and strict ceiling

The achieved result is a source-locked, deterministic, fail-closed local
metadata receipt apparatus. It has not produced a remote receipt: there are no
server response bytes, session IDs, specimen counts, actual split counts, or
runtime schema observations. Executing the pinned remote method requires a
separate explicit authorization and a runtime receipt proving the exact
wheel/interpreter/host/query boundary and absence of forbidden follow-up calls.

Even a successful future metadata receipt would establish provenance and a
frozen split only. It would not validate neural dynamics, edge strength,
Riemannian curvature, a low-rank conscious moment, consciousness itself, or a
preferred dimension. In particular, 4, 5, and 6 remain only members of the
predeclared candidate menu.

## Reproducibility record

- Contract and boundary: `00-contract.md`
- Official-source lock: `10-sources.md` and `artifacts/v2.16.2-warehouse-source-lock.md`
- Canonicalization and split proof: `11-math.md`
- Alternative/failure routes: `12-routes.md`
- Independent pre-implementation status audit: `20-audit.md`
- Implementation: `30-implementation.md`
- Focused execution: `31-validation.md`
- Final static audit: `artifacts/implementation-static-audit.md`
