# BA-SELF3-L3 alternative-route lane: channelwise affine-invariant QC

Status: COMPLETE  
Contract SHA-256: `765c54ee2b20006619b3059c68ec3a5d1a3f007381f6d89593c597015ac41fce`  
Sources SHA-256: `a4be903d20a0f6e1391cde907c7f727b8804b62cd6ace02ab9be1fd9572012a7`  
Math SHA-256: `87778e0738961a7c8b49004b01684f55b92e35368fb06c6a457625094232ec02`

## Decision

This run executes **R2 only**: the frozen channelwise affine-invariant window QC

$$
Q_A^{\rm ch}=\max_{t,c}\left|\frac{X_{tc}-\operatorname{med}_u X_{uc}}{1.4826\operatorname{med}_v|X_{vc}-\operatorname{med}_u X_{uc}|}\right|,
$$

$$
Q_D^{\rm ch}=\max_{t,c}\left|\frac{X_{t+1,c}-X_{tc}}{1.4826\operatorname{med}_v|\Delta X_{vc}-\operatorname{med}_u\Delta X_{uc}|}\right|.
$$

For each channel, both quantities are invariant under $X'_{tc}=a_cX_{tc}+b_c$ for every finite $a_c\ne0$ and offset $b_c$. This makes the gate insensitive to fixed channel-specific units, gain, and offset. It is a measurement QC definition only: it does not establish a neural invariant, remove time-varying gain, montage mixing, clipping, or broad artifacts.

The A2 set fixes each cutoff as the calibration median plus six unscaled MADs across its 64 windows. Nonfinite data or a nonpositive/nonfinite per-channel robust scale rejects the window. Task or rest rejection rejects its whole pair. Cutoffs, split, target, quotient, path feature, model menu, and success thresholds are not changed after B1.

## Competing routes and disposition

| Route | Disposition before B1 | Reason |
|---|---|---|
| R1: absolute-amplitude QC | KILLED | BA-SELF1 rejected all 32 cross-subject D1 pairs under absolute scale; it is not transferable across recordings. It remains a diagnostic, not a selectable gate. |
| R2: channelwise affine-invariant $Q_A^{\rm ch},Q_D^{\rm ch}$ | SELECTED | It directly tests the remaining measurement seam: fixed gain/offset may differ by channel as well as recording. The invariance proof and limits are in `11-math.md`. |
| R2b: robust quantile score instead of maximum | NOT SELECTED | It would answer a different outlier-severity question. Choosing a quantile after observing B1 acceptance would be cutoff/endpoint shopping, so it is a successor-run route only if R2 fails. |
| R3: low-frequency or spectral QC | DEFERRED | It changes the measurement mechanism and introduces frequency-band/estimator choices. It cannot be introduced as an R2 rescue after B1. |
| R4: another dataset | DEFERRED | A distinct recording/dataset is required for biological replication, not for tuning this within-dataset apparatus gate. It is the next external route after a fully closed R2 run. |
| R5: direct state-versus-path ontology | KILLED AS AN EMPIRICAL ENDPOINT | Finite history features can be made instantaneous functions of an augmented state. Scalp EEG identifies an observation quotient, so no finite result decides whether self is ontologically a state or path. |

Thus R2 does not assert that the self is a trajectory. It tests only whether ordered past adds held-out predictive information beyond the matched observed-current-state baseline, after a declared measurement gate.

## Signal-blind B1 and independence boundary

B1 is allocated from the previously sealed D2 pool without signal values: within each `sub-02` session, sort `SHA256(UTF8("BA-SELF3-B1-v1:" || trial_hash))` together with the trial hash and assign the first 16 pairs to B1. This yields 32 B1 pairs (16 per session); the remaining 100 are D2-M (57/43). The allocation receipt must record every trial hash, old and new split, ordering key, session, and word coverage before any signal download.

B1 may open only R2 window acceptance and its pair/session counts. It may not compute $z$, targets, features, loss, fitted coefficients, model selection, or any biological endpoint. B1 is therefore a held-out-window apparatus transfer check, not an independent subject, recording, population, or mechanism replication. Its `sub-02` recording was already exposed to predecessor D1 **QC only**; D1 remains burned and is excluded. The 32 B1 pairs (64 windows) are nonindependent of the 100 D2-M pairs (200 windows) at recording level, and this limitation is retained in every later claim.

`sub-03` C1/C2/C3 remains sealed. No B1 result may alter D2-M selection or any confirmation rule. The 32 B1 pairs (64 windows) are not a source of post-hoc route selection.

## Kill and resume rules

The B1 apparatus gate passes only with at least 24/32 retained pairs and at least 12/16 in each session. The B1 receipt must explicitly state `model_outcome_opened=false`.

| Condition | Immediate disposition | Permitted resume |
|---|---|---|
| Allocation receipt is incomplete, word coverage fails, or its arithmetic differs from 16/16 B1 and 57/43 D2-M | `APPARATUS_INVALID_DESIGN` | New run with a corrected, signal-blind allocation; do not inspect model outcomes. |
| A2 cutoff scale is zero/nonfinite, parser/range/ETag integrity fails, or B1 fails 24/32 or 12/session | `APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER` | Close this run. A successor may preregister one materially different QC mechanism (R2b or R3), with a new apparatus allocation; no in-run cutoff or route switch. |
| B1 passes but either D2-M session retains fewer than 30 pairs, so $2N\le59$ for the $d=4$ M1 guard | `APPARATUS_INVALID_D2_DESIGN` | Close this run; a successor must alter the sampling/design before modelling. |
| D2-M fails the frozen robust-gain or ordered-history gate | `STOP_NO_ROBUST_DEVELOPMENT_GAIN` or `STOP_NO_ORDERED_HISTORY_GAIN` | Close the route. It is not permission to change formula, dimension, cutoff, or decoder on the same data. |
| Confirmation fails its frozen gate or adverse controls contradict orientation | `STOP_CONFOUND_OR_NONREPLICATION` | Close the route; external replication/different measurement is required for a new biological claim. |

If B1 passes, it opens only the predeclared D2-M development route. A development result, whether positive or negative, remains within-dataset. Only the already sealed sub-03 stages can perform C1/C2 futility and C3 final confirmation; neither can be opened early.

## Claim ceiling

R2 can at most support a **within-dataset scalp-EEG observation-quotient temporal-prediction pilot** conditional on the stated preprocessing and QC. It cannot identify neuron-level edge strength, an infinite-dimensional Riemannian state space, hippocampal hashing, consciousness, self ontology, or population generalization. Any apparent history gain remains compatible with an unobserved augmented state.

## Required receipts

P0/A0 must preserve source/header lock, exact HTTP range integrity, parser/filter hashes, synthetic affine-invariance and adverse-artifact checks. A1/A2 must preserve all window scores and frozen cutoffs. B1 must preserve allocation, acceptance, session/word counts, and the unopened-model flag. D2-M and confirmation receipts must separately preserve their QC counts, design guards, losses, controls, and sealed-stage provenance.
