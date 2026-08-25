# BA-OBS-HPC1 alternative-route audit

Status: COMPLETE

All routes are constrained by the contract's `MODEL_SELECTION: NONE`. Their purpose is to
separate estimands and expose free degrees of freedom; no route may replace the frozen
primary result after raw outcome access.

| route | fixed quantity | structural distinction and dof | target-aware / status | falsifier or stop |
|---|---|---|---|---|
| R1 primary | participant-equal P2P of each pre/post mean waveform in late [50,250] ms, then TS-minus-PB | participant is the unit; 4 TS and 5 PB observations; fixed clinical and local-bipolar references; 1 primary window | Frozen before raw endpoint, but it is a same-data reproduction whose published direction is already known: not outcome-blind independent confirmation | clinical `D<=0`; aperture/fixture failure; strict reference claim also needs a predeclared local uncertainty requirement |
| R2 published-model reproduction | trial-level early/late P2P, fixed `protocol*time` mixed model with participant random terms | different non-linear order of operations and trial-level residual model; raw retained trials are clustered, so nominal trial df is not subject df | Outcome-aware as a reproduction target, though not selected by this run's raw results; cannot be used to override R1 | unavailable Satterthwaite engine -> `PUBLISHED_MODEL_ENGINE_UNAVAILABLE`; sign/source aggregate conflict -> implementation audit, not tuning |
| R3 overlap-only paired sensitivity | mean of p17/p19 within-person `Delta_TS-Delta_PB` | two paired differences; eliminates between-person arm composition but discards five unique-participant observations; effective paired n=2 | Fixed descriptive sensitivity, never a causal crossover test or p-value | nonpositive value -> `PAIRED_SENSITIVITY_FAIL`; positive value alone cannot rescue R1 |
| R4 signed late area / peak latency | integral or signed peak timing of mean waveform | adds polarity convention, baseline convention, endpoint selection, and a continuum of possible latency windows | Target-aware if introduced after examining outcome; explicitly not executable under the contract | no execution; requires a successor contract with source-data-independent definition and a fresh confirmation allocation |

The paths are deliberately structurally different: max-minus-min after averaging (R1),
trial-level nonlinear amplitudes and a hierarchical regression (R2), a within-participant
paired contrast (R3), and signed/timing waveform functionals (R4). They cannot be pooled
as independent evidence because R1/R2/R4 share every raw trial and R1/R3 share p17/p19.

## Degrees of freedom and look-elsewhere ledger

R1 has one locked primary time window but two frozen references. The clinical reference is
the main reproduction readout; bipolar is a robustness gate, not a second chance to claim
success. The early and prestimulus windows are controls, not alternative primary endpoints.
R2 has the greatest hidden flexibility (trial exclusions, random-effect structure, df
approximation) and must reproduce the archived model grammar exactly or stop. R3's dof are
small but its inferential power is correspondingly negligible. R4 has unbounded researcher
degrees of freedom unless a signed orientation, latency rule, and validation split are fixed
before access; it is therefore prohibited here.

The seven LOO values are influence diagnostics, not seven hypothesis tests. They should be
computed from unique-participant deletion with arm denominators recomputed: remove p17/p19
from both TS and PB together. A sign change in any LOO value means `PARTICIPANT_SENSITIVE`;
it does not authorize deleting that participant.

## Parent-claim mapping

`F_bio` predicts a state/history-conditioned SEP difference under the two protocols; the
observed chain is `H(F_bio)`, not direct recovery of connectivity. The CE addition is only a
reference-robust observed-response restriction. R1 can support that restricted, same-data
statement if every frozen gate passes. R2 can reproduce a published statistical summary.
R3/R4 cannot identify axonal paths, synaptic weights, memory behavior, a metric,
consciousness, or AGI. No route supplies a randomized population causal estimand because
protocol labels are neither exchangeable nor assumed randomized across the participant set.

