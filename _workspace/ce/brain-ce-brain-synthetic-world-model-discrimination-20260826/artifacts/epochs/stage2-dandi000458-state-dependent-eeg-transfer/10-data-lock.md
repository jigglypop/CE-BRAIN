# Stage 2 data lock

Status: COMPLETE / OUTCOME_BLIND

- Dandiset: `000458`
- frozen version: `0.230317.0039`
- subject/session: `521885` / `20200709`
- asset ID: `6ab37be4-adfe-4bea-a031-eb1a2b0782a8`
- path: `sub-521885/sub-521885_ses-20200709_behavior+ecephys.nwb`
- byte size: `312139546`
- SHA-256: `b80cd3a375ead36c05c451f562e92947573cd0679a30ffd573a04e44339b0171`
- DANDI ETag: `8b2490771d34b124e46a251075f98f8b-5`
- blob ID: `a367d440-e803-4476-aac4-31b78904f5fe`

Read-only remote schema probing, before any EEG value endpoint was opened,
established:

- `ElectricalSeriesEEG/data`: shape `(6217728,30)`, int16, chunks `(48576,1)`,
  conversion `1.9499999284744263e-07` volt/count;
- explicit timestamps: 6,217,728 values, approximately 2,500 Hz;
- trial table: 360 rows, 180 awake and 180 isoflurane, all biphasic MOs target;
- currents: 20, 50 and 100 microamperes, 120 trials each;
- `is_valid`: 354 true, 6 false;
- 17 valid electrode rows fixed in `00-contract.md`.

Local outcome-blind schema execution found one timestamp interval twice the
nominal duration after index 125,307. It occurs 133.43695 seconds before the
first trial. The initial uniformity gate stopped before any EEG sample value was
opened. The exact fail-closed successor is frozen in
`timestamp-gap-apparatus-amendment.md`; it is part of the manifest.

The executable schema map is frozen to:

- `/acquisition/ElectricalSeriesEEG/{data,timestamps}`;
- `/general/extracellular_ephys/electrodes/{id,is_data_valid}`;
- `/intervals/trials/{id,start_time,behavioral_epoch,estim_current,estim_target_region,stimulus_description,is_valid}`.

String-valued trial columns are UTF-8 decoded, `estim_current` must convert
exactly to integer microamperes, and trial origin is the unique nearest EEG
timestamp within half a sample.

Registered valid-trial split counts (`development=even ID`,
`confirmation=odd ID`) are:

| state | current (microampere) | development | confirmation |
|---|---:|---:|---:|
| awake | 20 | 30 | 30 |
| awake | 50 | 33 | 27 |
| awake | 100 | 27 | 33 |
| isoflurane | 20 | 30 | 30 |
| isoflurane | 50 | 32 | 27 |
| isoflurane | 100 | 24 | 31 |

The raw file must be copied outside the repository to a unique owned temporary
directory and its byte size and SHA-256 verified before execution. The result
must record the exact local identity but must not copy raw EEG into the repo.

Outcome-blind remote metadata receipt: `schema-receipt.json`, SHA-256
`20ab09f8d8afdab69b828fc50e98ae4fc890234e3b3248b6f34a1e1a89e1e79c`.
