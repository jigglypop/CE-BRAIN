# Stage 2 models

Status: COMPLETE / OUTCOME_BLIND

## M0: global-gain transfer

For each current, `T_I = alpha T_A + epsilon`, with one fitted nonnegative
scalar `alpha`. This model preserves the complete awake channel-time relation
and permits only global amplitude change.

## M1: trial-normalized state waveform

Each trial waveform is mapped to the unit sphere. The state statistic is the
Euclidean distance between state-specific mean unit waveforms. The registered
999-draw Monte Carlo label-permutation procedure provides the finite-sample
reference distribution under label exchangeability.

M1 has no trained weights and no endpoint-dependent hyperparameters. Channelwise
integrated absolute response, peak amplitude and peak latency may be emitted as
descriptive receipts only; they cannot enter the decision.

The statistic is sensitive to both mean direction and resultant-length
(within-state directional concentration) differences. Under additive noise, a
pure signal gain can also change SNR after normalization. It is therefore a
trial-normalized waveform-difference test, not an identified mechanistic test
of pure gain versus geometry.
