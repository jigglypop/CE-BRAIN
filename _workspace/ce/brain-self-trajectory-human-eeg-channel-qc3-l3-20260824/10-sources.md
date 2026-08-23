# BA-SELF3-L3 source lane

Status: COMPLETE  
Contract SHA-256: `765c54ee2b20006619b3059c68ec3a5d1a3f007381f6d89593c597015ac41fce`

## Source lock and empirical inputs

The source is frozen to OpenNeuro [ds006033 v1.0.1](https://openneuro.org/datasets/ds006033/versions/1.0.1), DOI `10.18112/openneuro.ds006033.v1.0.1`, Git tag object `3af0502b0664b80dacf015e76c436c9ba371527c`, and CC0. The public repository is [OpenNeuroDatasets/ds006033](https://github.com/OpenNeuroDatasets/ds006033). The primary description is the 2025 [Data in Brief paper](https://www.sciencedirect.com/science/article/pii/S2352340925009795), DOI `10.1016/j.dib.2025.112258` (also indexed at [PubMed](https://pubmed.ncbi.nlm.nih.gov/41362341/)).

| ID | Empirical input | Locked value / uncertainty | Consequence |
|---|---|---|---|
| S3-01 | Participants and recordings | 3 healthy right-handed participants; 5 EEG recordings are actually present because `sub-01/ses-01` has no EEG. The paper describes the nominal two-session design; the repository snapshot controls the observed-file count. | These are five recordings from three people, not five independent subjects. |
| S3-02 | Binary schema | BrainVision headers specify 64 multiplexed little-endian `IEEE_FLOAT_32` columns at 5 kHz (`SamplingInterval=200 us`): ECG at 1-based channel 32 and 63 named scalp channels. | Header names/order and binary content length are authoritative for parsing. Sidecar totals (`EEG64 + ECG1 + Misc1 = 66`) conflict with the actual 64-column header and are retained as a metadata defect, not silently repaired. |
| S3-03 | Correction history | Headers retain Scanner Artifact Correction and pulse/ECG correction history, including ECG filtering, R-peak marking, and Pulse Artifact Correction. | This is corrected scalp EEG, not direct membrane voltage or a neuron-wise whole-brain state measurement. |
| S3-04 | Events and allocation | Frozen predecessor manifest: 539 valid task/rest pairs (`125+89+75+125+125`), with 32 apparatus, 164 development, 250 confirmation, and 93 sealed unused. Manifest SHA-256: `4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061`. | Counts and split were sealed before signal access; nominal paper counts are not substituted for observed events. |

## Pinned predecessor evidence

BA-SELF1 used absolute cross-subject voltage cutoffs. Its primary repaired D1 receipt (`d05bd70e013a09cfb47d4ab0cb3bb507bba7839fbb00b98a9988246279da92d2`; A0 receipt `5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7`) records `accepted_pairs=0`, `rejected_pairs=32`, `model_outcome_computed=false`, and unopened D2/C1/C2/C3. The historical minimal receipt (`b9ba7c105f691056c0983749b9b8e0d954bf7c94e0144f948c69957902096d71`) is retained only as an earlier failure artifact and is not used for those fields. A diagnostic D1 window was finite with zero zero-MAD channels, but its maximum amplitude was 525.02 versus the frozen 281.52 cutoff; its maximum first difference was 22.50 versus 95.40. This is an apparatus/measurement-transfer failure, not falsification of the trajectory equation.

BA-SELF2 tested a common-gain/robust-scale variant. Its pinned D1 receipt (`7ea150e088625774b75ce1ceec35b8529e3abae470348fa4f693188e3820d28a`) reports 13/32 D1 pairs retained, with session counts 8/16 and 5/16; therefore 19/32 were rejected. The 24/32 figure was the required pass threshold, not the number rejected. No model endpoint was opened and no biological conclusion was drawn. The current source lane treats both predecessors as apparatus-only evidence.

## Physical interpretation and QC limit

Common reference, channel-specific gain, electrode impedance, montage mixing, nonlinear saturation, and residual artifacts are physically distinct possibilities. A channel-wise affine transformation

\[
X'_{tc}=a_cX_{tc}+b_c,
\]

can absorb channel-specific scale and offset, but it does not prove that the cause was gain or impedance, and it does not remove channel mixing, time-varying artifacts, saturation, or bad electrodes. The proposed per-channel robust normalization is therefore a measurement QC device, not a biological invariant or evidence for a self variable.

Its adverse risk is artifact masking: an artifact that inflates the within-channel robust scale can make its own peak look less extreme, while channel dropout or near-zero scale can create unstable ratios. The implementation must retain explicit nonfinite/zero-scale rejection and report the raw diagnostics; passing dimensionless QC cannot be interpreted as neural or consciousness evidence.

## B1/D2 independence status

The new B1 allocation is hash-fixed from the D2 pool, but it is not an independent subject/recording replication. The same `sub-02` recordings were partially signal-seen during BA-SELF1/SELF2 D1 apparatus checks. In particular, D2 model values remain unopened in this run, but recording-level QC transfer is not pristine held-out replication. B1 can test transfer of the frozen QC gate to held-out windows; it cannot establish population replication or validate a biological mechanism. Confirmation remains restricted to the sealed `sub-03` allocation.

## Claim ceiling

The source lock supports only an observed scalp-EEG, within-dataset temporal-prediction pilot conditional on the declared measurement model. It does not identify the full brain state, decide whether self is an instantaneous state or a trajectory, establish consciousness, prove infinite dimension, validate a hippocampal hash, or support population generalization. Any later model gain must be reported as an observational prediction result with the above apparatus and dependence limits.
