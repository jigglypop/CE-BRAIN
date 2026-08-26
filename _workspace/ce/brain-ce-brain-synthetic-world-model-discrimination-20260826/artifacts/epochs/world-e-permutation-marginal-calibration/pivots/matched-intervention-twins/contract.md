# Structural pivot contract: matched intervention twins

Status: COMPLETE

Mode: outcome-blind, independent-seed Stage 0 confirmation pivot

Parent counterexample: `world-e-permutation-marginal-calibration`

Structural fingerprint:
`common-latent-intervention-twin-contrast-derangement-v1`

## Question and predecessor lock

Can the fixed A--G candidate procedure recover the generating class and predict
held-out intervention-response contrasts, while distinguishing the state-specific
D/E contrasts from the analytically twin-independent A/B/C/F/G contrasts?

The parent run and result remain immutable:

- manifest SHA-256:
  `cadaefa5d746146967c6772a59b1ee5141fbed79b8d804c783b3775c62f9f12a`;
- result SHA-256:
  `44d059d3b0786b37738782d74a406eac3f77c46ee9286f72f449fc0700c38ab2`;
- disposition: `STAGE0_STRUCTURE_DISCRIMINATION_STOP`;
- preserved narrow result: expected class recovery 84/84 and all unseen and
  persistence gates, but World E whole-trajectory permutation only 9/12;
- forbidden retry: no parent seed, threshold, endpoint, candidate or result may
  be changed or relabeled.

## Structural change

For every world, replicate and intervention-pair block, two confirmation arms
share exactly the same simulator-side initial state, hidden initial state and
innovation sequence. They differ only in a frozen intervention waveform. Those
latent quantities are never supplied to a fitted candidate. Candidates receive
the same observed state/history and input variables as in the parent.

For twin $r$ in protocol block $c$,

$$
D_{cr}=Y^{(1)}_{cr}-Y^{(0)}_{cr},
\qquad
\widehat D_{m,cr}=\widehat Y^{(1)}_{m,cr}-\widehat Y^{(0)}_{m,cr}.
$$

For state-interacting Worlds D/E, paired loss is compared with target contrasts
permuted only within their exact intervention-pair block. Protocol means and
model shrinkage cannot by themselves identify the correct twin. For linear
additive Worlds A/B/C/F/G, the contrast is mathematically twin-independent; that
identity is a required negative control and no pairing claim is made.

## Fresh seed and population

The confirmation root is the little-endian integer encoded by the first 16
bytes of
`SHA256("CE-BRAIN-STAGE0-TWIN-CONFIRMATION|v1|26082600")`:

`5230705416521308865218892620027730619`.

Its digest is
`bb1a19f7c19bdc6e39893a28b065ef030cfa9b22d17a9bc7084fd6477bc85139`.
All coefficient, split, twin and randomization seeds are domain-separated hashes
of this root, world, replicate and purpose. There are 12 fresh replicates per
world and none may be dropped.

Train has 96 trajectories and validation has 48 using the frozen parent input
families but fresh coefficients, initial states and noise. Confirmation has eight
exact intervention-pair blocks (one per input node) and eight independent twins
per block. Each pair uses opposite paired-pulse waveforms with amplitudes
`+0.9/-0.45` versus `-0.9/+0.45`, at samples `12:16` and `31:35`.

## Candidates and selection

The frozen parent R/F/G/O/S feature maps, ridge grid, threshold grid, parameter
counts, validation composite and tie-breaks are reused byte-for-byte from the
sealed parent source. Only fresh train and validation data select the model.
The selected descriptor and all candidate hashes are serialized before any twin
confirmation array is generated.

## Confirmation estimands

For every fitted candidate, true twin loss is the closed-loop contrast NRMSE over
samples 2--63 and all observed nodes:

$$
L_m=
\frac{\sqrt{\operatorname{mean}(\widehat D_m-D)^2}}
{\operatorname{std}(D)}.
$$

Only the validation-selected winner is scored; confirmation cannot reselect or
rank models. For D/E, 999 hash-derived draws from the full product of uniform
within-block permutation groups, with fixed points and repeated draws allowed,
give losses $L_m^{(b)}$. Each block permutation uses a frozen Fisher--Yates draw.

$$
p_m=
\frac{1+\#\{b:L_m^{(b)}\le L_m\}}{1000},
\qquad
A_m=\operatorname{mean}_bL_m^{(b)}-L_m.
$$

The NRMSE mean and standard deviation flatten block $c$, twin $r$, sample
$t=2,\ldots,63$, and observed node $j$. A zero or nonfinite scale stops.

## Frozen gates

The pivot passes only if every A--G world satisfies all conditions:

1. expected class is the validation winner in at least 10/12 replicates;
2. the validation winner has median twin NRMSE at most 0.50;
3. in D/E, observed contrasts are twin-identifiable and the winner has Monte
   Carlo randomization $p\le0.01$ in at least 10/12;
4. in A/B/C/F/G, every block is twin-independent to the float64 identity rule
   `max_abs(D-block_mean) <= 1e-12 * max(1,max_abs(D))` in all 12 replicates;
5. equal-arm prediction $\widehat D=0$ has exactly zero pairing advantage and
   $p=1$ in all replicates;
6. all 84 identities, hashes, common-random-number receipts, serialization order
   and finite metrics are valid.

Any A--E failure produces `TWIN_STRUCTURE_CONFIRMATION_STOP`. An F/G-only failure
produces `TWIN_HISTORY_CONFIRMATION_STOP`. Only the complete conjunction produces
`TWIN_STAGE0_CONFIRMATION_PASS` and authorizes Stage 1. A pass does not change the
parent STOP; it is a separate independent confirmation result.

## Leakage and fail-closed rules

- Twin arrays cannot be constructed before model descriptors are serialized.
- Simulator common state/noise receipts are hashes only and cannot become model
  features.
- Randomization permutations are uniform within blocks and never cross blocks.
- D/E pairing is identifiable only if
  `max_abs(D-block_mean) > 1e-8 * max(1,max_abs(D))`; otherwise it stops.
- Parent source hash mismatch, manifest mismatch, reused seed, nonfinite rollout,
  zero contrast scale, split/twin overlap, missing population or adverse-control
  signal stops without a scientific label.
- The manifest binds this contract, route, all preregistration documents,
  implementation and focused tests before the confirmation is generated.

## Claim ceiling

This pivot can establish only synthetic structural discrimination, held-out
intervention-contrast prediction, D/E state-specific pairing, and the declared
linear-world twin-independence identities under these generators.
It cannot establish a biological neuron model, real-brain geometry, memory,
consciousness or AGI.
