# BA-OBS-ID4 route ledger — successors to the open P1 proxy

Status: COMPLETE

## Why routes are required

P1 is an explicit model-selection proxy, not a derived theorem, and BA-OBS-ID3 ended `REFERENCE_SENSITIVE_OR_INCONCLUSIVE`.  This run may replicate or refute only its prespecified observed proxy.  It cannot convert either result into a latent-transfer or metric claim.  The following are structurally distinct, outcome-blind successor routes.  They are not authorized changes to this run, and none may reuse its confirmation signals as new confirmation.

| Route | Target-aware status | Distinct mechanism / intervention seam | Pre-data requirement | Primary falsifier / kill condition | Ceiling if it passes |
|---|---|---|---|---|---|
| R1 — signed impulse-transfer route | **TARGET-AWARE; OPEN EMPIRICAL PROXY** | Replace magnitude compression with a sign-preserving, artifact-masked early impulse-response coefficient in a fixed stimulation-current basis.  This tests a linear-response reciprocity proxy, not peak-magnitude reciprocity. | Independent dataset/epoch; source-locked current polarity and scale; predeclared artifact mask, signed coefficient, reference basis, and patient split. | Kill as `SIGNED_TRANSFER_APPARATUS_STOP` if polarity/current basis or artifact-free linear-response interval cannot be source-locked.  Otherwise a reproducible bipolar failure of the fixed signed reciprocal criterion rejects only this signed proxy. | Finite observed signed-transfer comparison; no identification of $H$, conductance, or metric. |
| R2 — reference-equivalence route | **TARGET-AWARE; OPEN MEASUREMENT-MODEL TEST** | Treat admissible rereferencing transforms as a nuisance equivalence class and test whether a fixed directional statistic is stable on that class, rather than choosing CAR75 versus bipolar as the privileged readout. | Independent multichannel CCEP data with sufficient retained contacts; preregister admissible transform family, rank/conditioning floor, statistic, and negative common-component injection control. | Kill as `REFERENCE_QUOTIENT_UNIDENTIFIED_STOP` if the statistic changes across admissible transforms, or transforms are rank-deficient/ill-conditioned on retained channels.  A stable quotient statistic is still not a latent transfer identity. | Reference-robustness of one observed statistic only. |
| R3 — current-dose / polarity intervention route | **TARGET-AWARE; OPEN EMPIRICAL PROXY** | Use deliberately varied, source-locked current amplitudes and polarities to estimate a local input-output slope before comparing reciprocal slopes.  This changes the intervention seam, rather than only the decoder/reference. | A new protocol/dataset with repeated doses and both polarities per retained canonical node; randomization record; preregister linearity range, slope estimator, saturation exclusion, and patient-disjoint confirmation. | Kill as `DOSE_RESPONSE_NONLINEAR_OR_POLARITY_CONFOUNDED_STOP` if slope is not stable in the preregistered range or polarity cannot be balanced.  Failure of reciprocal slopes then rejects only the dose-calibrated proxy. | Local finite interventional response comparison; no global connectivity/metric claim. |

## Route safeguards

1. Routes R1--R3 differ respectively in observable (signed kernel), measurement-model nuisance treatment (reference quotient), and intervention (dose/polarity).  They are not threshold, seed, endpoint, decoder-only, or resampling-only variants.
2. All target-aware design choices must be frozen before opening their outcome data.  Any route selected because it favors the current run's observed label is discovery only and needs a fresh independent confirmation dataset/epoch.
3. Each route needs matched controls: null/non-evoked or prestimulus control, synthetic common-reference/artifact control appropriate to its measurement model, and patient-disjoint confirmation.  A simulator pass remains apparatus evidence only.
4. If no route can meet its pre-data requirement, record the named kill condition rather than relax P1, borrow the present confirmation labels, or infer a metric from finite CCEP matrices.

## Preserved no-go boundaries

BA-OBS-NOGO1 remains binding: finite passive/observed CCEP matrices do not identify an ambient or infinite-dimensional metric or dimension.  BA-OBS-ID3 remains consumed, reference-sensitive evidence; its window, thresholds, split, readouts, and confirmation result cannot be retuned.  This run's outcome, if produced, has the same finite five-subject observed-reciprocity/reference-comparison ceiling.
