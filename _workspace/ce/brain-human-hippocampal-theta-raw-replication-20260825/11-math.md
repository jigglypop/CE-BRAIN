# BA-OBS-HPC1 mathematics verification

Status: COMPLETE

Scope: independent checks of the frozen contract only. This lane opened no raw object,
no Nature source-data outcome, and no participant voltage. `F_bio` is the contract's
state-dependent cortico-hippocampal communication mechanism; `H` is the BrainVision,
reference, nuisance-regression, optional p17 filter, baseline, artifact and P2P chain;
`Delta F_CE` is only its claimed history/reference robustness restriction. The raw
measurement can support neither an anatomical metric nor an intrinsic edge weight.

## Recomputed definitions and fixtures

For 499.5 Hz, `dt = 1/499.5 s = 2.002002002 ms`. Thus `t_j=j*dt-500 ms`, `j=0..999`,
equals `linspace(0,2,1000)-0.5` seconds: the epoch is -500 through +1500 ms, with the
last sample exactly +1500 ms. With closed endpoint masks, the integer memberships are:

| window | indices | actual first/last time (ms) | samples |
|---|---:|---:|---:|
| early [15, 50] | 258..274 | 16.5165..48.5485 | 17 |
| late [50, 250] | 275..374 | 50.5506..248.7487 | 100 |
| prestimulus [-300, -100] | 100..199 | -299.7998..-101.6016 | 100 |

So the early and late masks are disjoint, but neither nominal boundary is sampled. This is
correct under the frozen `>=`/`<=` rule; recording these indices prevents an otherwise
silent `linspace`/sample-rate convention change.

`artifacts/math_fixture.py` constructs only synthetic 1000-sample traces. It verifies the
grid and masks; least-squares removal of the 60/120/180-Hz sine/cosine design; a defined
10th-order, 80-Hz zero-phase p17 filter at 499.5 Hz; selected-contact minus second-contact
bipolar algebra; and the nonlinearity `P2P(mean waveform) != mean(trial P2P)`. The latter
is material: the primary participant-equal estimate is P2P of each clean-trial mean
waveform, while the published-model lane's trial P2P is an explicitly different estimand.

The fixture's toy values independently give `D = 2.9` and paired `D_pair = 3.0`; it draws
65,536 PCG64/20260825 coupled bootstrap replicates without reading data.

## Estimand, bootstrap, and exchangeability checks

The stated primary value is dimensionally sound: `A=max(xbar)-min(xbar)`,
`Delta=Apost-Apre`, and `D=mean_TS(Delta)-mean_PB(Delta)` all have voltage units (reported
microvolts). `t`, windows, and cutoff carry time/frequency units; the DFT sine/cosine
arguments, z score, kurtosis, and bootstrap weights are dimensionless. Under the current
contract convention, `u` is an area-one normalized ideal pulse and `y=C_r(h*u)+a+eta` uses
only the statement that `h*u` has voltage units; `y,a,eta` are voltage and `C_r` is a fixed,
dimensionless linear reference operator. No physical units, anatomical transfer function, or
intrinsic connectivity interpretation is inferred for `h`. The prior dimensional P1 gap is
therefore RESOLVED by this convention, without altering the P2P estimator.

The exponential construction is valid for the advertised descriptive participant-cluster
Bayesian bootstrap: within each protocol arm, independent `Exp(1)` weights normalized by
their arm sum are Dirichlet(1,...,1). Reusing the identical draw for p17 and p19 across
arms gives the required joint dependence, though the two arm distributions are therefore
not independent. The fixture uses one `weights[draw, subject]` table and then normalizes
within TS/PB. The reported interval is a small-cohort weighted-empirical sensitivity band,
not a randomization p-value, population posterior, or causal interval.

The paired p17/p19 contrast is algebraically valid but has two paired participants only.
It is descriptive and cannot establish a crossover effect. The seven leave-one-participant
analyses must omit a unique participant from every arm in which that participant occurs and
renormalize each remaining arm; otherwise p17/p19 are accidentally duplicated.

## Counterexamples and status logic

RESOLVED — `SAME_DATA_REANALYSIS_REFERENCE_ROBUST_SUPPORT` now requires both
`D_late,local-bipolar>0` and its 95% participant-cluster lower bound >0. If either fails,
the reference-robust parent claim is removed and the result is
`REFERENCE_SENSITIVE_OR_UNCERTAIN`.

RESOLVED — the current lattice assigns `ESTIMAND_DISCORDANT` when the frozen clinical
published-model interaction and participant-equal clinical `D_late` have opposite signs.
It declares no combined support and requires the differing population weights and error
models to be reported rather than selecting a favorable estimator.

P1 — P2P is polarity invariant but not linear. The stated p16/p19 polarity correction is
therefore harmless for P2P only; it would change any signed waveform/area route and cannot
be silently reused there.

P2 — the trialwise kurtosis/z exclusions use the trial axis and require the locked minimum
20 clean trials. They are not independent observations after the participant mean is formed;
treating retained trials as independent would be pseudoreplication.

No P0 contradiction was found in the time grid, filter specification, closed windows,
participant-equal arithmetic, or overlap-preserving bootstrap definition.

## Reproduction

```powershell
.codex/hooks/python.cmd python _workspace/ce/brain-human-hippocampal-theta-raw-replication-20260825/artifacts/math_fixture.py
```

Expected invariant receipt: early `258..274/17`, late `275..374/100`, prestimulus
`100..199/100`, and `no_real_voltage_read: true`.
