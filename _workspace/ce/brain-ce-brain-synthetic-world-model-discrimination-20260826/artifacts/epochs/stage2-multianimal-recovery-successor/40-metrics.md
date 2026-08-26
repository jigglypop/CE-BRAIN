# Stage 2 successor metrics

Status: PREREGISTERED / OUTCOME_BLIND

For each animal report:

1. exact eligible development and confirmation counts;
2. `D_AI`, `D_AR`, and dimensionless recovery ratio `Q=D_AR/D_AI`;
3. nonnegative awake-to-isoflurane gain and dimensionless residual `R_AI`;
4. exactly 999 label permutations using `PCG64(20260828 + subject_number)` and
   `p_AI=(1+count(D_perm >= D_AI))/1000`;
5. exactly 1,999 within-state bootstrap resamples using
   `PCG64(20261828 + subject_number)` and the 97.5 percentile of finite `Q`;
6. waveform shape, norm and finite checks.

The bootstrap is a precision interval conditional on the recorded blocks; it
does not make the block labels exchangeable in time. Channelwise amplitudes and
latencies may be reported descriptively but cannot change the decision.

