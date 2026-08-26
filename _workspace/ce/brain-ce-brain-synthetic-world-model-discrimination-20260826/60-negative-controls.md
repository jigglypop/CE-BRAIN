# Stage 0 negative controls

Status: COMPLETE

1. Validation target trajectories are permuted as whole rows with a separately
   derived seed. Already-fitted one-step predictions remain fixed; one-step
   NRMSE plus the ordinary parameter penalty is recomputed for every candidate.
   The original winner advantage must be at most 0.02 in at least 10/12
   replicates of each world. This diagnostic does not refit or change selection.
2. Train-intervention performance is reported beside unseen performance and
   cannot satisfy the unseen gate.
3. Generator identities are asserted directly: A symmetry/SPD, B directional
   asymmetry, C signed-gain gap, D two distinct stable regimes, E polynomial
   nonlinear drive, F hidden count/coupling and full-block stability, G lag-two
   norm and companion stability.
4. Duplicate split hashes, unseen arrays passed to selection, invalid seed,
   unstable transition, nonfinite metric or receipt hash mismatch stops before a
   scientific label.
5. Every trajectory has a SHA-256 identity recorded in the result. A deliberate
   trajectory-overlap fixture and a deliberate unstable-rollout fixture must
   invoke and pass the real fail-closed checks in focused tests.
