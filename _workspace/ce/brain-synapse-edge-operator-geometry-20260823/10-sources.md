# BA-SRM4 source lane — synapse edge/operator geometry

Status: COMPLETE

Date: 2026-08-23

Scope: source and schema verification only. No pulse-response outcomes, residuals,
validation scores, confirmation scores, rank spectra, or model fits were opened or
aggregated in this lane.

## 1. Pinned provenance and source hierarchy

The pinned input is the medium Allen Synaptic Physiology SQLite database:

| Evidence ID | Source / value | Provenance and uncertainty |
|---|---|---|
| S1 | `C:\Users\dongh\OneDrive\Desktop\Clarus-Equation\data\external\allen-synphys\raw\synphys_r2.1_medium.sqlite`; 11,125,997,568 bytes; SHA-256 `dbf19786f9e0d0d73c26351dc29d69ef8c10a2e67e32e19ac73034a5624d48c5` | Local pinned artifact and predecessor clamp-unit receipt. This fixes the binary input, not a biological claim. |
| S2 | Allen Institute `aisynphys` dataset structure, current-release | Primary repository documentation says the hierarchy is slice → experiment → cell → directed pair → pulse response, and that a pulse response is one presynaptic stimulus, its spikes, and a postsynaptic recording. [Allen dataset structure](https://github.com/AllenInstitute/aisynphys/blob/current-release/doc/source/dataset_structure.rst), accessed 2026-08-23. |
| S3 | Allen Institute schema API | Primary schema documentation identifies SQLite tables/classes for Slice, Experiment, Cell, Pair, Recording, PatchClampRecording, StimPulse, StimSpike, PulseResponse, Synapse, PulseResponseFit, PulseResponseStrength, and Dynamics. [Allen schema API](https://github.com/AllenInstitute/aisynphys/blob/current-release/doc/source/api_schema.rst), current-release, accessed 2026-08-23. |
| S3a | Allen `aisynphys` source code | `Slice.lims_specimen_name` returns the acquisition `.index` field `specimen_ID`; the schema comment calls it the name of a LIMS "slice" specimen. The LIMS helper separately queries `specimens` and joins `donors`, proving specimen and donor are distinct concepts. [slice.py](https://github.com/AllenInstitute/aisynphys/blob/current-release/aisynphys/data/slice.py), [schema/slice.py](https://github.com/AllenInstitute/aisynphys/blob/current-release/aisynphys/database/schema/slice.py), [lims.py](https://github.com/AllenInstitute/aisynphys/blob/current-release/aisynphys/lims.py), accessed 2026-08-23. |
| S4 | Published local clamp audit receipt | SHA-256 `b18d23a4c1d3ef31ba5522724a17d98cedfd71eeef546b14951e608cfd5540b8`; predecessor status says the prior extractor mixed IC and VC command units. It is a QC/provenance fact, not a fit result. |

## 2. Biological meaning fixed by the schema

Read-only SQLite schema inspection confirms the following typed relationships.

| Level / table | Fields relevant to BA-SRM4 | Interpretation licensed by source/schema | Not licensed |
|---|---|---|---|
| `slice` | `id`, `ext_id`, `lims_specimen_name`, species, age, sex, genotype, target metadata | tissue-source and slice identity; `ext_id` is unique DB-row identity, while `lims_specimen_name` names the LIMS "slice" specimen and is the conservative anti-leakage grouping equivalence class | donor/animal identity; the specimen label is not a donor key |
| `experiment` | `id`, `slice_id`, date, target region, temperature, rig | recording session nested within a slice | independent biological replicate across experiments on one slice |
| `cell` | `id`, `experiment_id`, `ext_id`, electrode, cell class/layer | recorded cell and cellular metadata | a synaptic edge by itself |
| `pair` | `id`, `experiment_id`, pre/post cell IDs, synapse flags, distances, test-spike counts | directed candidate edge and its pair-level context | release probability or causal efficacy |
| `recording` + `patch_clamp_recording` | recording ID, sample rate/stimulus metadata; `clamp_mode`, baseline potential/current/noise, `qc_pass` | acquisition channel and clamp-mode typing | treating IC and VC numerical commands as one unitful scalar |
| `stim_pulse` + `stim_spike` | pulse number, cell, onset, amplitude, duration, spike count/timing, `previous_pulse_dt`; spike onset/slope/peak | presynaptic protocol/history and observed spike timing | vesicle release or synaptic efficacy directly |
| `pulse_response` | recording, stimulus, pair, baseline, raw snippet, ex/in QC flags | trial-level stimulus-to-recording observation, with QC state | a guaranteed synaptic event; Allen explicitly allows no detectable postsynaptic response |
| `pulse_response_fit` / `pulse_response_strength` | fitted amplitude, latency, rise/decay, fit error; positive/negative and deconvolved amplitudes/latencies | analysis-derived response features, conditional on fit/QC conventions | molecular mechanism, quantal size, or release probability without intervention/calibration |
| `dynamics` | pair-level STP summaries and variability/correlation fields | precomputed protocol-specific summaries, useful as candidate observables only after provenance/QC review | direct latent state variables; values are not to be treated as ground-truth depletion or facilitation states |

The local schema therefore supports a history-dependent edge observation, but not an
unobserved synaptic state being directly measured.

## 3. Units and clamp-mode contract

The source schema stores numerical fields but does not make all units self-describing
in the column names. BA-SRM4 must retain the source acquisition convention and use
mode-typed channels:

- presynaptic current-clamp (IC) command/stimulus amplitude is a current quantity;
- presynaptic voltage-clamp (VC) command/stimulus amplitude is a voltage quantity;
- postsynaptic response features inherit their recording/clamp mode and source unit;
- latency, rise time, decay time, and inter-pulse interval are time quantities;
- distance fields require an explicit length convention before entering a dimensionless
  kernel or metric.

The predecessor audit found eligible support with postsynaptic recordings IC and
presynaptic recordings in both IC and VC (excitatory and inhibitory strata). This is
the reason the previous operator/rank output is invalidated and cannot be used as a
biological falsifier. Any candidate equation must either use separate typed channels
and reference scales or abstain on a mixed-mode comparison.

## 4. What is observed versus proxy

The following distinction is required before equation discovery:

| Proposed quantity | Dataset status | Safe use |
|---|---|---|
| presynaptic spike count/timing, pulse interval | directly represented in `stim_pulse`/`stim_spike` when populated | history covariates and causal protocol inputs |
| response amplitude, latency, rise/decay | fit/strength outputs derived from pulse-response traces | observed response coordinates, with fit/QC provenance |
| paired-pulse ratio / STP summary | derived summary in `dynamics` | empirical proxy/target, not a mechanistic state |
| release probability $p_r$ | not directly observed in this schema | latent parameter only under an explicitly sourced and identifiable model |
| readily releasable-pool depletion/recovery | not directly observed | mechanistic latent state; protocol response can constrain it but cannot identify it alone |
| facilitation | response-history phenotype/proxy; molecular mechanism not directly measured | candidate state term, labelled empirical unless independently confirmed |
| latency / strength / efficacy | latency and response-strength features are observed or fitted; “efficacy” is an interpretation | use typed response features; do not rename them release probability |

Primary mechanistic sources support the baseline interpretation: short-term
depression is commonly associated with depletion/inactivation of release resources,
recovery with replenishment, and facilitation with residual calcium and related
presynaptic mechanisms. These are source-verified biological hypotheses, not labels
present in each Allen row. See [Zucker & Regehr 2002](https://pubmed.ncbi.nlm.nih.gov/11826273/),
[Regehr 2011, *Short-term forms of presynaptic plasticity*](https://pmc.ncbi.nlm.nih.gov/articles/PMC3599780/),
and [Tsodyks-style model review](https://pmc.ncbi.nlm.nih.gov/articles/PMC3630333/).
The reviews also emphasize multiple mechanisms and synapse heterogeneity, so a
single scalar edge weight is not a source-required representation.

## 5. Fixed 16-coordinate target and split-readiness

The fixed target is 16 coordinates: pulses 8, 9, 10, and 11, each represented by
`{amplitude, latency, rise, decay}`. The schema contains the entities needed to
define this target:
directed `pair_id`, presynaptic `stim_pulse`/`stim_spike` sequence, postsynaptic
`pulse_response`, and fit/strength/QC fields. It does not by itself guarantee that
The schema alone does not guarantee complete pulses 8--11 target support within a
compatible protocol and clamp mode. The fixed 16-coordinate
target is pulses 8, 9, 10, and 11 x `{amplitude, latency, rise, decay}`; it is a target
definition to be frozen after a schema-only receipt,
not a presently verified support count. Same-mode and complete-support status remains
UNVERIFIED; no target outcome was opened here.

Before any outcome aggregation, the following schema-only queries/receipts are
required:

1. enumerate foreign-key paths from `slice → experiment → cell → pair → recording →
   patch_clamp_recording → pulse_response → stim_pulse`, including all IDs and null
   behavior;
2. inspect identity metadata without conflating specimen and donor. Allen source code
   defines `lims_specimen_name` as the acquisition folder's `specimen_ID` and the
   schema calls it the name of a LIMS "slice" specimen. The LIMS helper resolves that
   name to a specimen record which may have a separate `donor_id`, but the medium
   SQLite slice table does not carry that donor relation. In the pinned DB the field
   is non-null for 4,276 slices but has 4,259 distinct values: 16 duplicated names
   cover 33 rows, with a maximum multiplicity of 3. This non-uniqueness is useful for
   leakage control because repeated registrations/acquisitions of one LIMS slice
   specimen should remain together. Use `lims_specimen_name` as the conservative
   slice-specimen grouping key, retaining `slice.ext_id` only as row identity and
   audit metadata. Donor/animal-held-out claims are prohibited unless a separate,
   frozen LIMS donor mapping is supplied;
3. verify that every sequence candidate has a fixed pair, pre/post recording roles,
   clamp-mode tags, pulse order, and the predeclared pulses 8--11 x
   `{amplitude, latency, rise, decay}` window;
4. record only schema/QC/missingness and group membership for split construction;
5. assign the frozen hash bucket from the contract, forcing all groups touched by
   earlier BA-SRM2/3 training into discovery-contaminated status.

The Allen documentation states that experiments can share a slice but are spatially
and temporally isolated, and that connectivity is expected within an experiment, not
between experiments. Thus splitting at pair or recording level is unsafe; the highest
stable anti-leakage key is the non-unique `lims_specimen_name` equivalence class;
only slice-specimen-held-out inference is licensed. The identity status is
`UNRESOLVED_IDENTITY_KEY` for donor-level grouping: the source code establishes
specimen-label semantics, but does not provide a donor mapping in this pinned SQLite
artifact. Any duplicated label is grouped together even if one row appears unusual;
that is the conservative leakage policy, not a claim that labels are donor IDs.

Primary experimental/theoretical evidence includes Tsodyks and Markram's paired
patch-clamp study, which linked depression rate to release probability while showing
variation across neocortical pairs: [PNAS 1997, DOI 10.1073/pnas.94.2.719](https://pubmed.ncbi.nlm.nih.gov/9012851/).
This supports protocol-history and response-dynamics features as a mechanistic
baseline, not treating the Allen `dynamics` columns as direct molecular measurements.
The official Allen `aisynphys` repository is the software/schema evidence for the
relational objects and pulse-response semantics: [dataset structure](https://github.com/AllenInstitute/aisynphys/blob/current-release/doc/source/dataset_structure.rst)
and [schema API](https://github.com/AllenInstitute/aisynphys/blob/current-release/doc/source/api_schema.rst).

## 6. Mechanistic baseline and claim ceiling

The source-verified baseline is a protocol-conditioned, short-term plasticity model
with presynaptic history, a latent resource/release state, and postsynaptic observation:

$$
z_{k+1}=F(z_k,\,\Delta t_k,\,s_k;\theta),
\qquad
y_k=H(z_k,\,\text{clamp mode},\,\text{recording state})+\epsilon_k.
$$

Here $z$ may include depletion/recovery and facilitation components only as latent
model states; the Allen database does not measure them directly. The equation is a
source-aligned baseline template, not a fitted or confirmed law. Any CE addition must
remain an empirical candidate until untouched group confirmation.

Evidence ladder and D→I→P→C→B→T ceiling:

- `D`: Allen schema/provenance and primary STP mechanism sources are fixed.
- `I`: typed history-to-response features may be inferred on discovery groups only.
- `P`: a held-out group prediction is required before any promoted empirical claim.
- `C`: clamp-mode swap, time-order shuffle, missingness, and source-baseline controls
  are required; no intervention is present in this dataset, so causal mechanism is
  not licensed.
- `B`: at most a bounded, mode-aware functional quotient/effective-dimension claim
  for the declared ex vivo mouse-V1 population.
- `T`: status is conditional/empirical; no whole-brain, in-vivo cognition, memory,
  AGI, or infinite-rank claim follows.

Current claim ceiling: source support reaches the biological starting mechanism and
schema readiness (L1/L2 prerequisites), with a possible L3 slice-held-out candidate
only after the contract's untouched split and controls pass. It does not reach L4
intervention or causal release-probability/depletion identification. If donor/specimen
identity, mode-specific units, or complete pulses 8--11 target definition cannot be
fixed, use `STOP_SOURCE`, `BLOCKED_SPLIT_SUPPORT`, or `BLOCKED_TARGET_DEFINITION`.
