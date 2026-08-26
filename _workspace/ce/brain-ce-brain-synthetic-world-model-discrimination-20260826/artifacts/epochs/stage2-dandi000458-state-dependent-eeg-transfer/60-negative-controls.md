# Stage 2 negative controls and limitations

Status: COMPLETE / OUTCOME_BLIND

- Current is stratified; no amplitude pooling can manufacture cross-current
  support.
- Trialwise L2 normalization removes every positive per-trial multiplier before
  the label-permutation test, but it does not remove additive-noise/SNR or
  directional-dispersion differences.
- Invalid trials and invalid EEG channels are excluded only by frozen NWB
  metadata, never by observed endpoint magnitude.
- The global-gain residual and the trial-normalized waveform test must agree
  under the multi-current rule; neither alone supports the disposition.
- Electrode labels are descriptive. Common-average reference creates dependence
  among channels, so results are effective measurement-space relations.
- Awake precedes isoflurane in this session. Condition, elapsed time and order
  are not separable.
- This asset has no recovery state and only one animal. Even a support result is
  a candidate state-dependent transfer signature requiring preregistered
  multi-session/recovery replication.
