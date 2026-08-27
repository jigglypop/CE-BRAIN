# Real-data contract: DANDI 001701 development session

Status: COMPLETE

Mode: light empirical successor

## Objective

Test the frozen affine contracting-fiber model on a real biological neural
population recording. Synthetic fixtures are excluded from scientific scoring.
The first endpoint is development evidence only; independent confirmation data
remain unopened.

## Outcome-blind source lock

| field | frozen value |
|---|---|
| repository | DANDI Archive |
| Dandiset | `001701` |
| immutable version | `0.260120.0303` |
| DOI | `10.48324/dandi.001701/0.260120.0303` |
| license/access | CC-BY-4.0 / OpenAccess |
| subject/session | male C57BL/6 mouse `BaggySweatpants`; X-maze `DY15-g1`; 2022-03-04 |
| asset path | `sub-BaggySweatpants/sub-BaggySweatpants_ses-BaggySweatpants-DY15-g1_behavior+ecephys.nwb` |
| asset UUID | `3f3d0b16-9b3e-42ac-a5e6-327829df1116` |
| byte size | `12,967,760` |
| SHA-256 | `5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3` |
| selection rule | smallest asset by official `contentSize`; selected without opening neural values |
| sealed confirmation | DANDI `001695`, version `0.260319.2023`; no assets or outcomes opened in this epoch |

## Required brain-research fields

| field | frozen declaration |
|---|---|
| `BIO_STARTING_MECHANISM` | Extracellularly sorted spike events are treated as point events emitted by a time-varying neural population rate. The empirical baseline is a first-order ridge linear population predictor on variance-stabilized binned counts; it is a predictive baseline, not a cellular mechanism claim. |
| `CE_DELTA` | The tested additional structure is a train-only low-rank split $x_t=(z_t,y_t)$ with $z_{t+1}=Bz_t+d$ and $y_{t+1}=Ay_t+Cz_t+e$, together with the strict contraction/bunching certificates $\|A\|_2<1$ and $\|A\|_2\|B^{-1}\|_2<1$. |
| `MEASUREMENT_MODEL` | NWB `units/spike_times` point events are counted in non-overlapping 100 ms bins. Retain units with at least 0.1 Hz computed only over the chronological train interval `[0,train_end)`, then freeze that same unit set for development and test. Apply $r_{it}=\sqrt{n_{it}+3/8}$, then center and scale each unit using train data only. No LFP or position enters the primary neural predictor. |
| `DATA_PROVENANCE` | Exact immutable DANDI asset, byte count and SHA-256 above. The acquisition contains real mouse Neuropixels electrophysiology, behavior, position and head direction. |
| `DATA_SPLIT` | For $T$ complete bins, train is `[0,floor(.5T))`, development is `[floor(.5T),floor(.75T))`, and test is the remainder. One-step rows are formed separately inside each half-open block, so no input/target crosses a boundary. Unit retention, Anscombe transform parameters, centering/scaling and every PCA basis $U_d,V_d$ use train values only. Only $d,\lambda$ are selected on development. The immutable NWB is downloaded whole, and HDF5 may decode a unit's stored spike vector only to apply the frozen time mask; before `model_selected=True`, no event at or after the test boundary may enter returned count arrays, retained-unit statistics, preprocessing, fitting or selection. The implementation must assert the maximum admitted prefix event time and prefix count shape. `UNOPENED` means no test-derived array/statistic is admitted before selection; DANDI 001695 remains physically unopened. |
| `OBSERVABLES` | Primary: held-out one-step NMSE and paired improvement over persistence and full VAR, including deterministic 10-second-block bootstrap intervals. Structural: $q=\|A\|_2$, $\kappa=\|B^{-1}\|_2$, $q\kappa$, secondary invariant-graph residual, and multi-step error at horizons 1, 2, 5, 10 bins. Report retained units, effective duration, valid bin/row counts after boundary purging, variance denominators and detected timestamp gaps. |
| `RESIDUAL_RULE` | All primary errors use identical held-out rows and the train variance denominator. A positive bridge requires at least 1% lower NMSE than each of persistence and independently tuned full VAR, and the 95% moving-block-bootstrap interval of each paired per-bin squared-error improvement must have lower bound above zero (2,000 resamples, block 100 bins, seed 1701). It also requires $q<1$ and $q\kappa<1$ without coefficient clipping. |
| `FALSIFIER` | Failure of either strict certificate; failure of either held-out effect/uncertainty rule; residual growth across horizons; or a 100-bin (10-second) shifted-alignment control matching/exceeding the real model kills the positive empirical bridge for this session. |
| `MATCHED_CONTROLS` | Persistence $x_{t+1}=x_t$; train-mean predictor; full ridge VAR(1); base-only fiber model $A=0$; circular time shift by 10 seconds applied before fitting with the same dimensions and penalties. |
| `MODEL_SELECTION` | Candidate latent dimensions $d\in\{2,4,8\}$ subject to $d<\min(9,N)$ and ridge $\lambda\in\{10^{-4},10^{-3},10^{-2},10^{-1},1,10\}$. Select the fiber candidate by lowest development NMSE, breaking exact ties by smaller $d$, then larger $\lambda$. Full VAR independently selects its $\lambda$ on the same train/development rows and grid, with identical intercept and denominator, breaking ties by larger $\lambda$. Other controls use the same eligible rows. No test-driven reselection. |
| `REVISION_TRIGGER` | D/I/P/C/B defects may repair decoding without changing endpoint. A valid empirical failure opens a new epoch only for a structurally different model; bin width, split, threshold or endpoint may not be tuned to rescue the result. |
| `CLAIM_CEILING` | At most L2 single-session observational model adequacy. It cannot prove biological global affine fibers, causal attraction, an autonomous generator, a neural metric, consciousness, self or AGI. Independent DANDI 001695 confirmation is required for L3 replication. |

## Resource and persistence rule

The 12.97 MB NWB asset may be downloaded to an owned temporary directory,
verified by SHA-256, decoded, and deleted in the same command. Only the source
receipt, aggregate endpoints and code remain in the repository.

The 100-bin shifted control is constructed separately within each split: its
predictor at index $t$ is the real predictor at $t-100$, its target remains the
real $t+1$ target, and the first 100 eligible rows of every split are discarded.
No circular wraparound is admitted. The real candidate and all controls are
rescored on this same reduced row set for the shifted-control comparison. The
shift exceeds the maximum 10-bin forecast horizon.

Acquisition coverage is read from the NWB ElectricalSeries timestamps, or from
its declared `starting_time` and `rate` when timestamps are implicit. Any
discontinuity longer than 150 ms starts a new segment; one-step and multi-step
rows crossing a segment boundary are dropped. Missing coverage metadata is a
fail-closed `COVERAGE_UNAVAILABLE` result. Bootstrap inference requires at least
300 held-out rows and three non-overlapping 100-bin blocks; otherwise it reports
`INSUFFICIENT_TEST_BLOCKS` and no positive bridge.

For the shifted falsifier, every shifted candidate/control is refit on the
reduced, 100-row-purged train block and selected on the analogously reduced
development block. The already selected real-alignment models are only rescored
on the same reduced held-out targets. Shifted fitting never accesses primary
held-out values.
