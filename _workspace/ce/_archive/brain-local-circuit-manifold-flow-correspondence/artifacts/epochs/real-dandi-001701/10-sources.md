# Real-data source lock

Status: COMPLETE

## Primary repository evidence

| source | locked fact | claim boundary |
|---|---|---|
| DANDI `001701`, version `0.260120.0303`, DOI `10.48324/dandi.001701/0.260120.0303` | 12 mice; Neuropixels medial entorhinal cortex and hippocampus during spatial match-to-sample; spike times, LFP, trials, 2D position and head direction; 218 assets, 6.2 GB; CC-BY-4.0 | Dataset metadata establishes the biological recording and variables, not the CE structure. |
| DANDI REST asset metadata, UUID `3f3d0b16-9b3e-42ac-a5e6-327829df1116` | exact path `sub-BaggySweatpants/sub-BaggySweatpants_ses-BaggySweatpants-DY15-g1_behavior+ecephys.nwb`, 12,967,760 bytes, SHA-256 `5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3`, male C57BL/6 subject, X-maze session; metadata retrieved 2026-08-27 Asia/Seoul | Identity lock only; neural values remained unopened at selection. Whole-file digest must be reverified after retrieval before decoding. |
| DANDI data-access documentation | public read API, per-asset download and anonymous S3/WebDAV access | Access mechanism is not scientific validation. |
| DANDI `001695`, version `0.260319.2023`, DOI `10.48324/dandi.001695/0.260319.2023` | independent mouse high-density hippocampal-cortical recordings across rest/navigation/stimulation | Reserved confirmation source; it is not opened or scored here. |

Official URLs:

- `https://dandiarchive.org/dandiset/001701/0.260120.0303`
- `https://api.dandiarchive.org/api/dandisets/001701/versions/0.260120.0303/assets/3f3d0b16-9b3e-42ac-a5e6-327829df1116/`
- `https://docs.dandiarchive.org/user-guide-using/accessing-data/downloading/`
- `https://dandiarchive.org/dandiset/001695/0.260319.2023`

## Candidate audit

DANDI 001701 is selected for development because its individual NWB assets are
small enough for exact whole-file hashing and contain population spike and
behavior streams. DANDI 001695 is structurally independent and reserved for
confirmation. IBL/DANDI 000409 is a later multi-lab generalization panel; its
49.7 TB total size excludes whole-dataset download, so only asset streaming is
admissible.
