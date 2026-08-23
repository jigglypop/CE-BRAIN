# BA-SELF2-L3 source lane

Status: COMPLETE

Contract SHA-256: `8eb85e4ce7218112c082b84e0f754ae3fa0afb1995374a9675c581164880517f`

## Source lock

The source is frozen to OpenNeuro `ds006033`, version `1.0.1`, DOI
`10.18112/openneuro.ds006033.v1.0.1`, Git tag object
`3af0502b0664b80dacf015e76c436c9ba371527c`, and CC0.  The authoritative
dataset record is [OpenNeuro ds006033](https://openneuro.org/datasets/ds006033/versions/1.0.1);
the public repository is [OpenNeuroDatasets/ds006033](https://github.com/OpenNeuroDatasets/ds006033).
The primary data description is the 2025 Data in Brief paper,
DOI `10.1016/j.dib.2025.112258`, available at
[ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2352340925009795)
and [PubMed](https://pubmed.ncbi.nlm.nih.gov/41362341/).

| ID | Empirical input | Locked value / uncertainty | Evidence and consequence |
|---|---|---|---|
| S2-01 | Participants and recordings | 3 healthy right-handed participants; 5 actual EEG recordings because `sub-01/ses-01` has no EEG. The public paper describes the nominal two-session design; the repository snapshot is the authority for observed files. | A0 metadata receipt from the predecessor run resolved the five recording objects. Statistical dependence is by participant/session, not five independent subjects. |
| S2-02 | Acquisition schema | BrainVision headers: 64 multiplexed little-endian `IEEE_FLOAT_32` columns, 5 kHz (`SamplingInterval=200 us`), ECG at 1-based channel 32 and 63 named scalp channels. | Header names/order and binary content length are authoritative for parsing. Public sidecars sum `EEG64 + ECG1 + Misc1 = 66`, conflicting with the actual 64-column header; this remains a declared metadata defect, not a reason to reinterpret the binary. |
| S2-03 | Correction history | All five headers retain Scanner Artifact Correction and pulse/ECG artifact-correction history, including `Filters ECG 15 Hz`, `Mark R peaks`, and `Pulse Artifact Correction`. | The measurement is corrected scalp EEG, not direct neuronal membrane voltage. No source supports a neuron-wise or whole-brain state claim. |
| S2-04 | Valid events | Frozen event rule yields 539 valid task/rest pairs: `125 + 89 + 75 + 125 + 125 = 539`. Allocation is 32 apparatus, 164 development, 250 confirmation, and 93 sealed unused; predecessor manifest SHA-256 `4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061`. | Counts were sealed before signal access. Subject/session split remains mandatory; nominal paper counts are not substituted for observed events. |
| S2-05 | Prior signal-access result | BA-SELF1 predecessor receipt SHA-256 `d05bd70e013a09cfb47d4ab0cb3bb507bba7839fbb00b98a9988246279da92d2`: all 32 D1 pairs rejected by absolute cross-subject QC; `accepted_pairs=0`, `model_outcome_computed=false`, D2/C1/C2/C3 unopened. | This is an apparatus-transfer failure, not equation falsification. One recorded task window had finite values and zero zero-MAD channels but amplitude 525.02, above the frozen 281.52 cutoff; first difference 22.50 remained below its cutoff 95.40. The evidence is consistent with subject/recording gain or impedance scaling, but does not identify its physical cause. |

## Measurement-method question: absolute versus dimensionless QC

The predecessor's absolute maxima were in the recorded voltage scale. A fixed
cross-recording voltage cutoff therefore conflates signal quality with the
recording's gain, reference, impedance, or other acquisition scale. The source
record and headers do not provide a calibration statement that would justify
assuming those scales are identical across subjects. Accordingly, this run
tests a measurement gate based on within-window robust scale, for example

\[
 Q_A=\frac{\max_{t,c}|X_{tc}-\operatorname{median}_tX_{tc}|}
 {\operatorname{median}_c(1.4826\,\operatorname{MAD}_t X_{tc})},\qquad
 Q_D=\frac{\max_{t,c}|\Delta X_{tc}|}
 {\operatorname{median}_c(1.4826\,\operatorname{MAD}_t\Delta X_{tc})}.
\]

These ratios are dimensionless and invariant to a common nonzero recording
gain and channel-wise additive offsets under the stated preprocessing. That is
a proposed QC/methodological transformation, not evidence for a biological
mechanism, a self variable, consciousness, an infinite-dimensional manifold,
or a hippocampal hash. Its only empirical question is whether a preregistered
apparatus gate transfers across recordings while preserving finite, usable
windows. Thresholds must be frozen from the apparatus split; they may not be
retuned after observing development or confirmation outcomes.

## Source limits and claim ceiling

OpenNeuro's official documentation describes the archive/access model:
[OpenNeuro user guide](https://docs.openneuro.org/user_guide.html). The source
lock supports only an observed scalp-EEG temporal-prediction pilot. It does not
identify the full brain state, distinguish ontological “current self” from a
trajectory, establish consciousness, prove infinite dimension, or support
population generalization. Any later gain is therefore an observed
within-dataset prediction result conditional on this measurement model.

