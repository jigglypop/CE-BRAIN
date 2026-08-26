# Stage 2 multi-animal recovery successor contract

Status: PREREGISTERED / OUTCOME_BLIND

## Question and scope

The predecessor ended at `STAGE2_TRANSFER_TENSION`: one mouse showed a clear
awake/isoflurane waveform difference at 50 and 100 microampere but not at 20
microampere. This successor does not erase or reinterpret that result.

Question: in two different DANDI 000458 mice that each contain awake,
isoflurane and recovery blocks, does the confirmation-set EEG transfer pattern
move away from awake under isoflurane and then return toward the awake pattern
after isoflurane is removed?

This is an L3 perturbational association and a qualitative two-animal
replication. The mice have different fixed currents (70 and 50 microampere), so
absolute response magnitudes are never pooled across animals.

## Frozen observables

For each mouse independently, confirmation trials are converted to the same
artifact-substituted, band-passed, common-average-referenced, baseline-corrected
2--498 ms multichannel waveform used by the predecessor. Every trial waveform
is divided by its own positive L2 norm.

Let `m_A`, `m_I`, and `m_R` be the means of normalized awake, isoflurane and
recovery waveforms. Define:

- `D_AI = ||m_I - m_A||_2`;
- `D_AR = ||m_R - m_A||_2`;
- `Q = D_AR / D_AI`;
- `R_AI`, the relative residual after fitting one nonnegative gain from the raw
  awake mean to the raw isoflurane mean;
- `p_AI`, a frozen one-sided 999-permutation label test of `D_AI`.

Recovery is practically closer only when `Q <= 0.75`; sampling uncertainty is
controlled by a within-state 1,999-bootstrap upper 97.5 percentile for `Q`.

## Frozen decision

- `STAGE2_RECOVERY_REPLICATION_SUPPORTED`: in both mice, `p_AI <= 0.01`,
  `R_AI >= 0.10`, `Q <= 0.75`, and bootstrap `Q_upper_97_5 < 1`.
- `STAGE2_RECOVERY_REPLICATION_TENSION`: both mice satisfy the registered
  awake/isoflurane condition, full support fails, and at least one mouse has
  the directional relation `Q < 1`. This includes a return smaller than the
  practical 25% threshold and a bootstrap interval crossing 1.
- `STAGE2_RECOVERY_NOT_ESTABLISHED`: every other finite valid outcome.
- `STAGE2_SUCCESSOR_APPARATUS_STOP`: any provenance, schema, timing, split,
  preprocessing, finite-value, manifest or independent-recomputation failure.

Support would show recovery-associated reversibility at the registered EEG
resolution. It would not identify anatomical edges, prove a metric manifold,
separate recovery from block order, or establish a consciousness mechanism.
