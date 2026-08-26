# Structural pivot contract: state reset and immediate challenge

Status: COMPLETE

Mode: outcome-blind independent-seed Stage 0 state-pairing confirmation

Parent counterexample: `twin-prestimulus-state-collapse`

Structural fingerprint: `paired-hadamard-observed-state-reset-immediate-pulse-v2`

## Question and predecessor lock

Does direct intervention from a balanced, fully observed pre-pulse state recover
D/E state-specific response pairing while preserving A/B/C/F/G
twin-independence and all A--G structural classification?

Frozen predecessors remain unchanged:

- Stage 0 result
  `44d059d3b0786b37738782d74a406eac3f77c46ee9286f72f449fc0700c38ab2`,
  `STAGE0_STRUCTURE_DISCRIMINATION_STOP`;
- matched-twin result
  `645a117c1441f8d666b1bba8aded0ffef42b556ac9e471bd5bb222c98a1f7048`,
  `TWIN_STRUCTURE_CONFIRMATION_STOP`;
- state-collapse diagnostic
  `a5290b3553011adcb73a5cfeedc4ca2e0af2b7dd0fc9fcf8f265a8463aaa483f`.

No predecessor threshold, seed, endpoint or label may be retuned. The new
mechanism changes the observed boundary condition and intervention seam.

## State preparation

All parent A--G coefficient laws and R/F/G/O/S candidates remain byte-identical.
Let $H$ be the order-eight Sylvester Hadamard matrix. Select its rows
$0,1,2,4$ as $V$ and form the coordinate-balanced bank

$$
B=\begin{bmatrix}V\\-V\end{bmatrix}.
$$

For protocol block $c$ and twin row $r$,

$$
z_{cr}=0.30\,P_cB_{r,:},
$$

where $P_c$ is a circular coordinate permutation by $c$. Both arms receive

$$
x^{(0)}_{cr,0}=x^{(0)}_{cr,1}
=x^{(1)}_{cr,0}=x^{(1)}_{cr,1}=z_{cr}.
$$

Thus every block has exactly zero coordinate mean and between-twin RMS 0.30,
inside the parent initial support. F receives a shared arm-pair hidden initial
state; every world receives a shared arm-pair innovation schedule. State-bank
row, twin index, permutation label and latent seed are never model features.

Fresh train and validation use the same state bank: trajectory row $q$ uses
$c=q\bmod8$ and
$r=(\lfloor q/8\rfloor+c)\bmod8$. Each bank row therefore occurs 12 times in
train and six times in validation, preventing a reset-support distribution shift.
Only observed $x_0,x_1$ and ordinary inputs enter candidates.

## Immediate held-out intervention

Confirmation retains eight node blocks, eight twins per block and two arms. The
first opposite four-sample pulse occurs at samples `1:5`, so the first scored
state is the direct response to $z_{cr}$. A second opposite pulse remains at
`31:35`. Arm 0 uses `+0.9,-0.45`; arm 1 uses `-0.9,+0.45`.

For D, $z_{cr,0}=\pm0.30$ selects threshold branches. For E, $z_{cr,j}u_j$
directly activates the registered state-input interaction. In linear additive
A/B/C/F/G, arm differences remain independent of $z_{cr}$.

## Fresh seed and split

The root is the first 16 SHA-256 bytes, little-endian, of
`CE-BRAIN-STAGE0-STATE-RESET-CONFIRMATION|v1|26082600`:

`276775390093346278216380119786172003083`.

Digest:
`0b3301db126c273dab5cd9594c0039d0506892f9434a01aba9d7806cdfeb7eca`.

There are 12 fresh replicates per world; train has 96 trajectories, validation
48, and confirmation 8 blocks x 8 twins x 2 arms. Seeds are hash-separated by
world, replicate and purpose. No replicate may be dropped.

## Selection, serialization and metrics

Fresh train/validation select the frozen parent candidates. Winner descriptor and
all candidate hashes are serialized before confirmation construction.

Winner twin NRMSE flattens block, twin, samples 2--63 and node. D/E pairing uses
the same full $S_8^8$ product-group Monte Carlo test as the prior route: 999
uniform Fisher--Yates draws including identity, fixed points and repeats,

$$
p=\frac{1+\#\{L^{(b)}\le L\}}{1000}.
$$

A/B/C/F/G use the registered float64 twin-independence identity instead of a
pairing p-value.

## Frozen gates

Every A--G world must satisfy:

1. expected validation winner in at least 10/12;
2. median selected twin NRMSE at most 0.50;
3. balanced state-bank, exact reset, CRN, finite, hash, split and serialization
   receipts in 12/12;
4. equal-arm zero-prediction identity in 12/12.

D/E additionally require state-identifiable contrasts and $p\le0.01$ in at least
10/12. A/B/C/F/G require twin-independent contrasts in 12/12.

The adverse common-state control sets every twin in a block to $z_{c0}$ and uses
one shared across-twin innovation receipt. Its D/E contrasts must satisfy the
same float64 twin-independence identity in 12/12. This control is never used for
fit or selection.

Any A--E failure gives `STATE_RESET_STRUCTURE_STOP`; F/G-only failure gives
`STATE_RESET_HISTORY_STOP`. Only the full conjunction gives
`STATE_RESET_STAGE0_PASS` and authorizes Stage 1 as a separate successor result.

## Fail-closed and claim ceiling

Parent/source/manifest mismatch, paired-bank balance failure, amplitude or reset mismatch,
pre-serialization confirmation access, repeated main CRN/arm hashes, split-arm
overlap, cross-block permutation, zero scale, nonfinite rollout, adverse signal
or incomplete population stops without success.

This can establish synthetic state-conditioned intervention discrimination only.
It cannot establish real-neuron dynamics, biological geometry, memory,
consciousness or AGI.
