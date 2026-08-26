# Stage 1 Allen source lock

Status: COMPLETE

## Official resources

- Allen Cell Types Database API documentation:
  `https://brain-map.org/support/documentation/cell-types-database-api`
- Allen Cell Types data overview:
  `https://celltypes.brain-map.org/`
- Allen physiology and morphology documentation:
  `https://brain-map.org/support/documentation/cell-types-database-physiology-and-morphology`
- Allen SDK `NwbDataSet` sweep API:
  `https://alleninstitute.github.io/AllenSDK/allensdk.core.nwb_data_set.html`
- Allen citation policy: `https://alleninstitute.org/citation-policy/`
- Official API object query for specimen `320654829` and its sweeps/ephys file.
- Official NWB download:
  `https://api.brain-map.org/api/v2/well_known_file_download/491201608`

The API reports specimen `320654829`, ephys result `320654827`, sampling rate
200,000 Hz and well-known file `491201608`. The server reports 53,057,893 bytes,
ETag `546d9396f5b40`, and filename `320654827_ephys.nwb`.

## Locked sweep identities

- Fit: Long Square 33--54 and 56--59; Ramp 5--6.
- Development: Noise 1 60, 62, 64.
- Confirmation: Noise 2 61, 63.

The official API reports Noise 1/2 duration 18.999995 s, onset 2.02 s, and the
selected specimen has 62/75/85 spikes for Noise 1 and 70/77 spikes for Noise 2
in its database metadata. These counts are provenance/QC metadata already public;
they are not model endpoint scores and cannot be used to alter the contract.

The official SDK documents `get_sweep()` outputs as stimulus A, response V and
sampling rate Hz, with `index_range` excluding the initial test pulse and invalid
tail. Implementation must reproduce those semantics from the file and convert
to pA/mV explicitly. The dataset is used with Allen attribution under its
citation policy; no commercial-use claim is made.

The schema-only smoke verified NWB `NWB-1.0.5`, IVSCC pipeline `1.0`, specimen
`320654829`, session/ephys result `320654827`, response path
`/acquisition/timeseries/Sweep_N/data`, stimulus path
`/stimulus/presentation/Sweep_N/data`, and valid experiment indices at
`/epochs/Experiment_N/{response,stimulus}/{idx_start,count}`. Response/stimulus
units are `Volts`/`Amps`; all selected sweep rates are exactly 200,000 Hz.

Downloaded byte SHA-256:
`fd164a3091fbbb3be358238088afa2e2f08981d49edffa87d55309931a9853ab`.
