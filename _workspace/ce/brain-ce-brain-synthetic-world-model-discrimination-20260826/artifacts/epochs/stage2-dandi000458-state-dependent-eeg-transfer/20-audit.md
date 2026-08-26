# Stage 2 pre-execution math audit

Status: COMPLETE / REVISED / OUTCOME_BLIND

Independent read-only audit disposition: `REVISE`, with no P0, three P1 items
and one P2 item. All were resolved before manifest sealing:

1. Added strict positive finite state-mean norm gates so `alpha` and `R` have
   defined denominators.
2. Reduced `D` from a claimed pure waveform-direction/global-gain falsifier to
   a trial-normalized waveform-difference statistic, explicitly retaining
   resultant-length and additive-noise/SNR limitations.
3. Renamed non-rejection from `GLOBAL_GAIN_SUFFICIENT` to
   `GLOBAL_GAIN_COMPATIBLE_AT_REGISTERED_RESOLUTION`.
4. Corrected “exact permutation” to a 999-draw Monte Carlo permutation test.

The audit verified the constrained least-squares gain formula, the 4,233
dimensional waveform (`17*249`), time indexing, p-value arithmetic and the
mutually exclusive/exhaustive decision partition after apparatus failures are
removed.
