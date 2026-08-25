# E1 metadata provenance source lane

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-e1-metadata-provenance-lock-20260825`

Access date: 2026-08-25 (Asia/Seoul)

Scope: primary/official source inspection only. No Allen dataset bytes, remote
session list, NWB, spikes, units, channels, probes, LFP or analysis endpoint
was opened. This lane does not evaluate the mathematical or biological claim.

## Evidence table

| ID | Contract input | Primary evidence | Verified value | Uncertainty / consequence |
|---|---|---|---|---|
| E1-SRC-01 | Released SDK identity | [AllenSDK v2.16.2 release](https://github.com/AllenInstitute/AllenSDK/releases/tag/v2.16.2) | Released 2023-11-30; tag points to commit `a9b5c685396126d9748f1ccecf7c00f440569f69` | Pin this tag/commit; do not use moving `master`. |
| E1-SRC-02 | Wheel and compatibility | [PyPI allensdk 2.16.2](https://pypi.org/project/allensdk/2.16.2/) | `allensdk-2.16.2-py3-none-any.whl`; SHA-256 `ecbcac94b720a2909319a741425f8325db9f0c15a9df0db8ceae64345d67fccc`; PyPI classifiers Python 3.8, 3.9, 3.10, 3.11; upload 2023-11-30 | PyPI lists no source distribution for this release. A future receipt must record the exact wheel hash and interpreter; do not claim source-archive hash. |
| E1-SRC-03 | SDK license identity | [PyPI license metadata](https://pypi.org/project/allensdk/2.16.2/), [Allen Institute Terms](https://alleninstitute.org/terms-of-use/), [Citation Policy](https://alleninstitute.org/citation-policy/) | PyPI identifies `Other/Proprietary License`; Allen Terms permit research/noncommercial use with attribution and restrict commercial use absent permission; citation policy applies | This is not a blanket CC-BY/CC0 assertion. Record Terms URL and access date in the receipt. |
| E1-SRC-04 | Manifest version | [Released v2.16.2 cache source](https://raw.githubusercontent.com/AllenInstitute/AllenSDK/v2.16.2/allensdk/brain_observatory/ecephys/ecephys_project_cache.py) | `EcephysProjectCache.MANIFEST_VERSION = '0.3.0'` | Predecessor frozen `0.2.1` is contradicted and must be retired. Current `master` also reports `0.3.0` ([source](https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/brain_observatory/ecephys/ecephys_project_cache.py)); release/tag remains authoritative. |
| E1-SRC-05 | `get_session_table` graph | [Released cache source](https://raw.githubusercontent.com/AllenInstitute/AllenSDK/v2.16.2/allensdk/brain_observatory/ecephys/ecephys_project_cache.py) | `get_session_table(suppress=...)` calls `_get_sessions`, then `_get_annotated_units`, `_get_annotated_channels`, `_get_annotated_probes`, and grouped channel structures. Those paths invoke `get_units`, `get_channels`, and `get_probes` and therefore load unit/channel/probe tables. | The predecessor literal prohibition plus `get_session_table` is unsafe. `suppress=[]` changes output-column suppression only; it does not prevent those hidden calls. |
| E1-SRC-06 | `_get_sessions` graph | [Released cache source](https://raw.githubusercontent.com/AllenInstitute/AllenSDK/v2.16.2/allensdk/brain_observatory/ecephys/ecephys_project_cache.py) | `_get_sessions` caches `self.fetch_api.get_sessions` into `sessions.csv`, reads with `index_col='id'`, and converts raw `structure_acronyms` with `ast.literal_eval` to `ecephys_structure_acronyms`. | This is the narrow cache layer, but calling the public `get_session_table` continues beyond it. Use the fetch API directly for the metadata-only action. |
| E1-SRC-07 | Historical API documentation — RETIRED, not admissible | [AllenSDK v2.13.2 API reference](https://allensdk.readthedocs.io/en/v2.13.2/allensdk.brain_observatory.ecephys.ecephys_project_api.ecephys_project_api.html), [stable API index](https://app.readthedocs.org/projects/allensdk/downloads/pdf/stable/) | These older/moving documents expose the historical signature `get_sessions(session_ids=None, published_at=None)`. They are retained only for provenance context and must not define the active query boundary. | The active v2.16.2 signature and semantics are exclusively E1-SRC-08A and [the pinned source-lock artifact](artifacts/v2.16.2-warehouse-source-lock.md): `get_sessions(session_ids=None, has_eye_tracking=None, stimulus_names=None)`. |
| E1-SRC-08 | Host and query boundary | [Allen API reference](https://alleninstitute.github.io/AllenSDK/allensdk.api.api.html), [official ecephys access example](https://allenswdb.github.io/physiology/ephys/visual-coding/vcnp-data-access.html) | Default Allen API host is `http://api.brain-map.org`; the warehouse API uses its RMA engine. The documented direct RMA pattern queries `model::EcephysSession`; session NWB is a separate `WellKnownFile` query/download path. | Record the actual scheme/host and query identity before execution. HTTPS availability and exact query serialization must be captured in the receipt; no endpoint was contacted here. |
| E1-SRC-08A | Direct released warehouse source paths | [v2.16.2 cache source](https://raw.githubusercontent.com/AllenInstitute/AllenSDK/a9b5c685396126d9748f1ccecf7c00f440569f69/allensdk/brain_observatory/ecephys/ecephys_project_cache.py), [v2.16.2 warehouse API source](https://raw.githubusercontent.com/AllenInstitute/AllenSDK/a9b5c685396126d9748f1ccecf7c00f440569f69/allensdk/brain_observatory/ecephys/ecephys_project_api/ecephys_project_warehouse_api.py), [source-lock artifact](artifacts/v2.16.2-warehouse-source-lock.md) | Pinned warehouse source bytes: 13,493; SHA-256 `c486110439af08e88ffc80a6abaa688dd7ae9768f77aef86d3ec0a3061186b0b`. Exact signature: `get_sessions(session_ids=None, has_eye_tracking=None, stimulus_names=None)`. Its single `build_and_execute` query uses `criteria=model::EcephysSession`, optional filters, `specimen(donor(age))`, and `well_known_files(well_known_file_type)`; it sets index `id`, derives age/sex/genotype/has_nwb, drops nested relationships, renames `stimulus_name` to `session_type`, and makes no unit/channel/probe/NWB/signal call. | The `well_known_files` relationship is file-presence metadata inside the RMA response, not an NWB download; discard links and make no separate WellKnownFile/stream request. Runtime server response schema/nullability/dtypes and actual rows remain unverified. |
| E1-SRC-09 | Raw session schema | [Official session API docs](https://allensdk.readthedocs.io/en/v1.8.0/_static/examples/nb/ecephys_session.html), [released cache source at pinned commit](https://raw.githubusercontent.com/AllenInstitute/AllenSDK/a9b5c685396126d9748f1ccecf7c00f440569f69/allensdk/brain_observatory/ecephys/ecephys_project_cache.py), [pinned warehouse source lock](artifacts/v2.16.2-warehouse-source-lock.md) | Static source verifies index `id`; derives `age_in_days`, `sex`, `genotype`, `has_nwb`, and renames `stimulus_name` to `session_type`. It returns the remaining RMA session fields (including specimen/date/publication fields when supplied by the server) after dropping nested relationship objects. | Runtime v2.16.2 response columns, required-field presence, nullability and dtypes remain UNVERIFIED. The four required fields remain a schema assertion for the future metadata receipt, not a verified observation. `well_known_files` is relationship metadata only; no file link or NWB bytes may be retained or fetched. |
| E1-SRC-10 | Compatibility generation | [AllenSDK Visual Coding compatibility guide](https://allensdk.readthedocs.io/en/stable/visual_coding_neuropixels.html) | Official guide documents a breaking AllenSDK 2.0/NWB compatibility boundary and warns that Visual Coding Neuropixels NWB files released before 2020-06-11 are not guaranteed with the reorganized 2.0.0 format. | A future receipt must record the dataset/NWB release generation; SDK version plus session IDs alone is insufficient. |

## Corrected call graph and admissible action

The released source gives the following graph:

```text
EcephysProjectCache.get_session_table
  -> _get_sessions
     -> one_file_call_caching(..., fetch_api.get_sessions, ...)
  -> _get_annotated_units -> _get_units -> fetch_api.get_units
  -> _get_annotated_channels -> _get_channels -> fetch_api.get_channels
  -> _get_annotated_probes -> _get_probes -> fetch_api.get_probes
```

Consequently, `get_session_table(suppress=[])` is **not** a metadata-only
boundary. The narrow corrected boundary is:

```text
Pinned v2.16.2 EcephysProjectWarehouseApi.get_sessions(
    session_ids=None, has_eye_tracking=None, stimulus_names=None
)
  -> its RMA session query / tabular response only
```

The method and query are now validated by the byte-locked artifact cited in
Evidence E1-SRC-08A. The runtime receipt must still record the actual server
response schema and must treat `well_known_files` as relationship metadata
only; no download-link follow-up is allowed.

The receipt must instrument or record that no `get_units`, `get_channels`,
`get_probes`, `get_session_data`, `get_probe_lfp_data`, metrics, NWB, or signal
endpoint was invoked. It must also record the exact query/resource identity,
host, SDK wheel hash, commit, manifest `0.3.0`, interpreter, and Terms URL.

## Predecessor defects and narrow repair

Two predecessor instructions are P1 source-contract defects:

1. `MANIFEST_VERSION == "0.2.1"` is false for the pinned released SDK; it is
   `"0.3.0"`.
2. `get_session_table(suppress=[])` is not session-only because it computes
   counts and grouped structures through unit/channel/probe tables.

No P0 source defect was found. The repair is to retire the old call and use
the direct official `EcephysProjectWarehouseApi.get_sessions` method, with a
fail-closed schema/endpoint audit. This does not authorize any scientific or
signal access and does not produce a session list in this lane.

## Source-lane ceiling

This artifact establishes provenance mechanics only. It does not verify the
remote table's actual rows, split balance, data completeness, recurrence,
history geometry, consciousness, or any dimension such as 4--6.
