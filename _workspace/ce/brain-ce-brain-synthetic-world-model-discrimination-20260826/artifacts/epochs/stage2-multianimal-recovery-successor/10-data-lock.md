# Stage 2 successor data lock

Status: PREREGISTERED / SCHEMA_OPEN / EEG_OUTCOME_BLIND

Official source: DANDI `000458`, frozen published version `0.230317.0039`.

## Locked assets

1. Subject `543393`, session `20200820`, asset
   `73689194-02e4-40c5-9936-5c6ed7cfb99d`, path
   `sub-543393/sub-543393_ses-20200820_behavior+ecephys.nwb`, 527,509,576 bytes,
   SHA-256 `78e4809d903aea2261c302799b3ee03b899f01183ccbf434af8671afc6fba332`.
2. Subject `543394`, session `20200827`, asset
   `f00ff515-1833-4f4f-bd9e-9c7dbf353397`, path
   `sub-543394/sub-543394_ses-20200827_behavior+ecephys.nwb`, 589,190,292 bytes,
   SHA-256 `3d9b703e2c96428cad82af4ff13f8f4d1f4c7302c758fad4243220854dbb4c1c`.

The official per-version API supplies the identifiers, paths, byte sizes and
digests. `schema-543393.json` and `schema-543394.json` record the pre-outcome
remote NWB schema probes.

## Registered schema

- Both assets contain one 30-column int16 `ElectricalSeriesEEG` at nominal
  2,500 Hz with conversion `1.9499999284744263e-07` volts/count.
- Both contain 300 trials per state in `{awake,isoflurane,recovery}`.
- Subject 543393 has 900 valid 70-microampere MOs biphasic trials.
- Subject 543394 has 898 valid 50-microampere MOs biphasic trials: 300 awake,
  300 isoflurane, 298 recovery.
- The common registered series columns are
  `[0,1,2,3,4,5,6,7,8,9,10,16,21,22,23,24,25,26,27,28,29]` (21 channels).
- Timestamps are finite, strictly increasing and gap-free. Registered maximum
  relative jitter is at most `2.1e-5`; inferred rate must be within 0.01 Hz of
  2,500 Hz.

Even trial IDs are development and odd IDs are sealed confirmation. Registered
confirmation counts are 150 per state for 543393 and 150 awake, 150
isoflurane, 149 recovery for 543394.

