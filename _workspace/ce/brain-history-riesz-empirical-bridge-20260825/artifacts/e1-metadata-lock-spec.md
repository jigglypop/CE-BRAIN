# E1 metadata-only lock specification

Status: FROZEN / UNEXECUTED

This specification opens no NWB, spike, unit-level endpoint, covariance,
dimension, model score or scientific result. It defines the only admissible
next provenance action for E1.

## Allowed query

Use an explicitly recorded AllenSDK release and
`EcephysProjectCache.MANIFEST_VERSION == "0.2.1"`. The only permitted remote
call is the project session table, equivalent to
`get_session_table(suppress=[])`. Calls to `get_session_data`, `get_units`,
probe LFP, stimulus templates, analysis metrics or NWB files are forbidden in
this stage.

Record before the query:

- UTC timestamp and API host;
- AllenSDK package version and source commit if available;
- manifest-format version;
- Python version and exact command;
- official data-compatibility generation, including the post-2020-06-11
  AllenSDK 2.0 boundary;
- data-use/license page identity.

## Canonical session-table receipt

Request unsuppressed session metadata.  The following core fields are required
for provenance, grouping, and later source-lock eligibility:

$$
\{
\texttt{ecephys\_session\_id},\texttt{specimen\_id},
\texttt{session\_type},\texttt{date\_of\_acquisition}
\}.
$$

The session ID may be supplied as the official table index, but it must be
materialized under the canonical key `ecephys_session_id` before hashing.
Return `E1_REQUIRED_FIELD_MISSING` if any required field is absent or null;
`E1_SCHEMA_UNSUPPORTED` if the field/index mapping is not the declared schema;
and `E1_FIELD_TYPE_INVALID` if IDs are not integral, session type is not a
nonempty string, or acquisition date cannot be serialized as an explicit UTC
ISO-8601 value.  A naive timestamp must not be assigned a timezone by guess.

The following descriptive fields are optional and are retained only when the
official table supplies them with a supported scalar/list type:

$$
\{
\texttt{published\_at},\texttt{age\_in\_days},
\texttt{sex},\texttt{full\_genotype},\texttt{unit\_count},
\texttt{channel\_count},\texttt{probe\_count},
\texttt{ecephys\_structure\_acronyms},\texttt{has\_nwb}
\}.
$$

Optional fields are not eligibility inputs in this stage.  Record their
presence/absence and return `E1_OPTIONAL_FIELD_TYPE_INVALID` rather than
silently coercing an unsupported value.  Fail closed if a session ID maps to
inconsistent duplicate rows, or if one session is assigned more than one
specimen. Arrays are serialized as lexicographically sorted JSON arrays.
Canonical output is UTF-8 JSON Lines, LF endings, keys sorted, finite JSON
numbers only, rows sorted by integer session ID. Record byte count, row count,
unique specimen count and SHA-256. The receipt stores summaries and IDs only;
it is not committed with authentication tokens or raw signals.

## Split allocation before eligibility

Assign the complete official table by specimen before any scientific inclusion
filter, unit QC, session type, state, covariance or endpoint is inspected.
For fixed salt

```text
CE-E1-NEUROPIXELS-V1
```

define

$$
u(g)=\frac{\operatorname{uint64}_{\rm big}
(\operatorname{SHA256}(\text{salt}\Vert\texttt{:}\Vert g)_{0:8})}{2^{64}},
$$

where $g$ is the decimal `specimen_id`. Allocate all sessions of one specimen
to calibration if $u<0.5$, development if $0.5\le u<0.75$, and held-out if
$u\ge0.75$. The salt, thresholds and group key may not be changed after row
counts are seen. If any eventual source-locked eligible partition has fewer
than two independent specimens, return `E1_SPLIT_APPARATUS_INVALID`; do not
rehash, move a subject or split time bins.

Later source-locked eligibility and default-versus-complete unit filtering are
applied *within* this immutable allocation. Allen's default unit filters
(`presence_ratio`, `isi_violations`, `amplitude_cutoff`) are scientific
measurement choices and cannot be used in this metadata stage.

## Required machine receipt

The future JSON receipt must include:

- `metadata_only: true`;
- `signal_arrays_opened: false`;
- `scientific_endpoint_opened: false`;
- SDK/manifest/release/data-use identities;
- canonical session-table SHA-256 and counts;
- every session/specimen split assignment and split SHA-256;
- missing/duplicate/schema diagnostics;
- required-field and optional-field presence/type diagnostics, including the
  exact canonical mapping from official index/column names;
- explicit confirmation that `get_session_data`, `get_units`, NWB, LFP,
  metrics and endpoint calls were not invoked;
- status `METADATA_LOCK_PASS` or one fail-closed reason.

A passing receipt opens only a new source-locked contract for baseline
reproduction. It does not authorize E1 scoring by itself and supplies no
evidence about recurrence, history geometry, consciousness or dimension.
