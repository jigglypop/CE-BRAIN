# Stage 2 DANDI 000458 state-dependent EEG transfer contract

Status: COMPLETE / OUTCOME_BLIND

## Authorization and question

The predecessor is the independently audited Stage 1 result
`STAGE1_HISTORY_SUPPORTED`, result SHA-256
`64b48fb80763bd08d08d08a6048ec6bd641e8c0f225c05109e2d50a4a0c6a395`.
Stage 1 does not itself prove geometry; this is a separate contract.

Question: in one DANDI 000458 mouse/session, after matching MOs stimulation
current, is the awake-to-isoflurane change in the stimulus-locked 17-channel
EEG transfer waveform compatible with one nonnegative global gain at the
registered resolution, or does a trial-normalized waveform test show a
reproducible state-associated difference beyond the fitted mean-waveform gain?

## Required real-brain fields

- `BIO_STARTING_MECHANISM`: electrical MOs perturbation followed by a
  stimulus-locked multichannel EEG response under awake or isoflurane state.
- `CE_DELTA`: none. The analysis tests a preregistered empirical effective
  transfer relation; it does not insert a CE axiom into biology.
- `MEASUREMENT_MODEL`: NWB `ElectricalSeriesEEG`, 2,500 Hz, int16 samples with
  dataset conversion to volts; valid EEG channels only; trial start time is the
  stimulus origin. All analyzed values are converted to microvolts.
- `DATA_PROVENANCE`: frozen Dandiset `000458`, version `0.230317.0039`, subject
  `521885`, session `20200709`, asset ID
  `6ab37be4-adfe-4bea-a031-eb1a2b0782a8`, path
  `sub-521885/sub-521885_ses-20200709_behavior+ecephys.nwb`, exact byte and hash
  lock in `10-data-lock.md`.
- `DATA_SPLIT`: trials must be valid, biphasic, target MOs, state in
  `{awake,isoflurane}`, current in `{20,50,100}` microampere. Even NWB trial IDs
  are development; odd IDs are sealed confirmation. Development may diagnose
  apparatus only and cannot alter preprocessing, endpoints, thresholds or
  decisions.
- `OBSERVABLES`: per-current optimal global gain, relative gain-fit residual,
  trial-normalized waveform distance and one-sided permutation p-value;
  channelwise integrated absolute evoked response is descriptive only.
- `FALSIFIER`: the odd-ID confirmation set. A state-associated transfer difference requires
  the frozen multi-current rule below. A result compatible with global gain at
  the registered resolution is explicitly dispositioned; intermediate outcomes
  are tension, not support.
- `MATCHED_CONTROLS`: current is never pooled; awake/isoflurane trials at the
  same current use identical channels, samples and preprocessing. Trial-level
  L2 normalization is the registered global-amplitude negative control.
- `REVISION_TRIGGER`: source/schema/unit/timing/filter/nonfinite/norm/manifest
  failure stops as apparatus failure. A scientific miss cannot retune this
  epoch. A recovery-bearing or multi-animal successor needs a new contract.
- `CLAIM_CEILING`: one session, one animal, EEG-only L3 perturbational
  association. No anatomical connectivity, causal edge identity, population
  generality, recovery reversibility, spike mechanism, memory, consciousness or
  AGI claim.

## Frozen preprocessing

Use only electrode table rows whose `is_data_valid` value is true, in NWB table
order. The registered rows are
`[0,1,2,3,4,5,9,19,20,22,23,24,25,26,27,28,29]`. All 17 must be present.
The `ElectricalSeriesEEG/electrodes` DynamicTableRegion must reference
`/general/extracellular_ephys/electrodes`; its 30 row indices must be unique and
in range. Signal columns are selected only by applying table-row validity
through this explicit series-column-to-table-row mapping. For this locked asset,
the resulting signal columns must equal the same registered 17-index sequence.

The EEG timestamps must be finite and strictly increasing; inferred sampling
rate must be within `0.01 Hz` of 2,500 Hz. The outcome-blind apparatus amendment
in `timestamp-gap-apparatus-amendment.md` permits exactly one registered
two-sample interval at index 125,307. All other intervals must have relative
jitter at most `2e-5`. The analysis filters only the post-gap contiguous segment
starting at index 125,308, and every eligible stimulus must be at least 120
seconds after that segment begins.
For each eligible trial, choose the unique sample nearest `start_time`; its
absolute timing error must not exceed `0.5/fs`. Replace the five raw samples at
offsets `[0,5)` with the five at `[-5,0)` channelwise, matching the source
paper's 0--2 ms artifact substitution. Apply this to every eligible trial
before filtering.
An exact nearest-sample tie within an absolute `1e-12` seconds is non-unique and
stops as apparatus failure.

For each valid channel, multiply by the NWB conversion and `1e6`, then apply a
third-order zero-phase Butterworth bandpass of 0.1--100 Hz to the entire
registered post-gap continuous segment. Extract offsets `[-2500,1250)` around
every eligible origin.
At each sample and trial, common-average-reference across the 17 channels.
Subtract each trial/channel mean over raw offsets `[-1250,-25)` (the registered
-500 to -10 ms baseline). The response waveform is offsets `[5,1250)` sampled
every five raw samples, giving exactly 249 time points from 2 to 498 ms and a
flattened vector `x_n` of dimension `17*249`. No additional rejection,
smoothing, clipping or channel weighting is permitted.

Every eligible origin must have the entire extraction window, and every
confirmation state/current cell must contain at least 20 trials. Every waveform
must be finite with strictly positive L2 norm.

## Frozen statistics

For each current independently, let `T_A` and `T_I` be confirmation means of
the raw flattened awake and isoflurane waveforms. Fit only

`alpha = max(0, <T_I,T_A> / <T_A,T_A>)`.

Report

`R = ||T_I-alpha*T_A||_2 / ||T_I||_2`.

Both `||T_A||_2^2` and `||T_I||_2^2` must be finite and strictly positive for
every current; otherwise stop as `STAGE2_APPARATUS_STOP`.

For the trial-normalized test, normalize every confirmation trial
`u_n=x_n/||x_n||_2` and compute

`D = ||mean_I(u)-mean_A(u)||_2`.

Within each current, permute awake/isoflurane labels over the pooled normalized
trial vectors while preserving observed group sizes. Use NumPy
`Generator(PCG64(20260827 + current))`, exactly 999 permutations, and
`p=(1 + count(D_perm >= D_observed))/1000`. No development-derived seed,
threshold or statistic is allowed.

## Frozen decision

- `STAGE2_STATE_ASSOCIATED_TRANSFER_DIFFERENCE`: all three currents have
  `p <= 0.05`, and at least two currents have both `p <= 0.01` and `R >= 0.10`.
- `STAGE2_GLOBAL_GAIN_COMPATIBLE_AT_REGISTERED_RESOLUTION`: all three currents
  have `p > 0.05` and `R < 0.10`.
- `STAGE2_TRANSFER_TENSION`: every other finite valid confirmation outcome.
- `STAGE2_APPARATUS_STOP`: any provenance, manifest, schema, preprocessing,
  timing, count, filtering, finite-value, norm or result-verification failure.

The difference status means only that one animal/session shows a current-robust
trial-normalized EEG waveform difference plus a nontrivial mean-waveform gain
residual between ordered awake and isoflurane blocks. Trial normalization
removes positive per-trial scale but does not remove additive-noise/SNR or
within-state directional-dispersion differences. The result therefore does not
identify a global-gain mechanism, does not establish that anesthesia changed an
anatomical graph, and leaves temporal block order as an explicit alternative.
