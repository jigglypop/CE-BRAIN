# BA-OBS-HPC2 mathematics and measurement audit

Status: COMPLETE

Scope: an independent check of the frozen light-successor contract and its declared
public-code hashes. No raw signal, Nature outcome, or network source was opened. The
predecessor's `STOP_MEASUREMENT_APERTURE` is not treated as an endpoint result. Here
`F_bio` remains the predecessor's state-dependent cortico-hippocampal communication
mechanism, `H` is this contract's author-order QC and P2P measurement, and the CE delta
is only a reference-robust, history-conditioned observed-response restriction.

## Recomputed grid and dimensional checks

The contract fixes

$$
\tau_j=\frac{j}{999}\frac{1000}{499.5}\;\mathrm{s}-0.5\;\mathrm{s},\quad j=0,\ldots,999.
$$

This is **not** the predecessor's simpler `j/499.5 - .5` convention. It has final time
`1.5020020020020022 s`. The preprocessing input excludes original index 999, and the
closed latency mask on the retained indices is `50..648`, 599 samples. Closed masks on
the declared full grid are:

| mask | indices | count | first/last time (ms) |
|---|---:|---:|---:|
| baseline [-50,-10] | 225..244 | 20 | -49.098648, -11.022534 |
| early [15,50] | 257..274 | 18 | 15.029544, 49.097646 |
| late [50,250] | 275..374 | 100 | 51.101652, 249.498247 |
| prestim [-300,-100] | 100..199 | 100 | -299.599399, -101.202804 |

The early/late masks are disjoint. All time-to-frequency products in the 60/120/180-Hz
regression and the 80-Hz cutoff ratio are dimensionless; `y,a,eta` and P2P contrasts
carry voltage units. With the contract's area-one normalized pulse convention, only
`h*u` is asserted to have voltage units. No physical transfer-function or connectivity
unit for `h` follows.

## Measurement order and QC aperture

The frozen order is: first 999 samples, nuisance regression, p17-only filter, latency
restriction, artifact decision, then baseline subtraction. This order is material. A
synthetic constant 600-uV trace fails the pre-baseline amplitude rule but becomes zero
after baseline subtraction; a baseline-first implementation would silently change the
aperture.

For p20, the declared three clinical QC channels are evaluated on an array with axes
`trial x channel x time`, and MATLAB-compatible z-scoring must use the trial axis.
Rejection is the union over every selected channel and time point, not an average over
channels and not D9 alone. The synthetic fixture exhibits an outlier confined to the
third selected channel: trial-axis z exceeds 5 and rejects that trial, whereas a D9-only
check would retain it. The endpoint itself remains frozen to D9; the extra channels are
QC-only.

The contract removes the predecessor's 50% condition and requires at least 20 clean
trials for *both* clinical and local-bipolar references in every one of 18 objects.
This is a source-defined QC successor only if the documented author-code rule and the
`MIN20` aperture are frozen before any endpoint is made visible. It must not be presented
as byte-for-byte execution of the archived MATLAB code.

## Estimand, bootstrap, and lattice

The primary amplitude is P2P of each condition's clean-trial mean waveform, so it is
not equal to mean trial P2P used by the published trial-level model. `Delta` and the
participant-equal TS-minus-PB `D` remain voltage-valued. The participant-cluster
Bayesian bootstrap is coherent as a descriptive sensitivity interval: draw seven shared
PCG64/20260825 exponential weights, normalize within the 4-person TS and 5-person PB
arms, and reuse p17/p19 weights in both arms. It is neither a permutation p-value nor a
population causal interval. LOO must delete p17/p19 from both arms together.

`SAME_DATA_REANALYSIS_REFERENCE_ROBUST_SUPPORT` requires positive clinical and local
late contrasts and positive 95% lower bounds, plus the specified controls. A local
failure becomes `REFERENCE_SENSITIVE_OR_UNCERTAIN`; opposite published-model and
participant-equal clinical directions become `ESTIMAND_DISCORDANT`, not estimator
selection. A clinical `D <= 0` is `SAME_DATA_REANALYSIS_NOT_SUPPORTED`.

## Findings

- P0: none in the stated grid, integer masks, dimensions, ordering, or shared-weight
  bootstrap.
- RESOLVED P1: `artifacts/author-code-static-receipt.md` now binds the archive and all
  three file hashes, the four-argument signature, artifact-before-baseline lines, normal
  `(5,5,500)` calls, the defective p17/p19 omission, and the p20 `D9,C1,C'1` selection.
  The successor explicitly makes `(5,5,500)` a frozen measurement axiom rather than
  calling it literal archived-script execution. Hence no post-QC interpretation remains:
  any hash mismatch is `AUTHOR_QC_CALL_AMBIGUITY` before raw access.
- RESOLVED P1: the same receipt independently supplies the p20 channel-union evidence
  previously unavailable to this lane. The endpoint remains D9 and the additional two
  channels remain QC-only, as the fixed route requires.
- P2: a trial-axis sample z threshold of 5 has finite-sample geometry. With 20 trials a
  single extreme observation cannot exceed 5 (maximum `(n-1)/sqrt(n) ~= 4.25`); this is
  not an error, but `z` cannot be assumed to remove isolated outliers in small files.

## Reproduction

```powershell
.codex/hooks/python.cmd python _workspace/ce/brain-human-hippocampal-theta-author-qc-reanalysis-20260825/artifacts/math_fixture.py
```

Expected receipt includes `no_real_voltage_read: True`, latency `50..648/599`, baseline
`225..244/20`, early `257..274/18`, late `275..374/100`, and 65,536 bootstrap draws.
