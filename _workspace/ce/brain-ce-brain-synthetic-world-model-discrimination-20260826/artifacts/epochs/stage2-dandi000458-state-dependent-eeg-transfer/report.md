# Stage 2 DANDI 000458 state-associated EEG transfer report

Status: COMPLETE / `STAGE2_TRANSFER_TENSION`

## Outcome

The frozen one-session, one-animal EEG endpoint completed and independently
recomputed from the raw NWB. Its preregistered multi-current support and
global-gain-compatible branches both failed, leaving the exhaustive third
status `STAGE2_TRANSFER_TENSION`.

| current (microampere) | awake / isoflurane confirmation trials | alpha | R | D | p |
|---:|---:|---:|---:|---:|---:|
| 20 | 30 / 30 | 0.521078 | 0.858568 | 0.245263 | 0.556 |
| 50 | 27 / 27 | 0.382945 | 0.822672 | 0.357731 | 0.015 |
| 100 | 33 / 31 | 0.434684 | 0.769004 | 0.557087 | 0.001 |

The 100-microampere endpoint is strong and the 50-microampere endpoint is
nominally different, but 20 microamperes does not reject the registered
trial-normalized null. The contract required all three currents at `p<=0.05`
and at least two at `p<=0.01` with `R>=0.10`; it therefore cannot be relabeled
as support. Large `R` alone is not sufficient.

## Apparatus history

The first local schema-only attempt stopped before any EEG value was opened
because one timestamp interval was twice nominal. Metadata-only diagnosis found
the gap 133.44 seconds before the first stimulus. The pre-manifest amendment
fixed the exact gap profile and analyzed only the post-gap contiguous segment.
Two independent read-only audits passed the amendment. The original apparatus
stop remains preserved in `timestamp-gap-apparatus-amendment.md`.

## Receipts

- raw SHA-256: `b80cd3a375ead36c05c451f562e92947573cd0679a30ffd573a04e44339b0171`
- schema receipt: `fd22626e9445b86f7a6a6b8885542f3e2d2790a92b3be788bcc567e234b62546`
- manifest: `548cc0977a771768795dd38f14ec15a83aedd6dda3648b835e3d7af6c31f9feb`
- result: `a2b8485ed50a9a32144c890f8f2434d4bb40c44f6f8d5c78a93e2fcfa075af7b`
- raw-recomputation validation receipt:
  `c0629284f355c1172ebc01c22e7db71738474f57b3605be1d7169c191e2feff8`
- final independent status audit: `PASS`, no P0/P1/P2

## Claim and next gate

This is an EEG-only L3 perturbational association in one ordered session. The
trial-normalized statistic can reflect additive-noise/SNR or directional
dispersion, condition is confounded with time/order, and this asset lacks a
recovery block. It does not establish anatomical connectivity or geometry.

`stage3_authorized=false`. The staged strong-geometry branch stops here. Any
continuation requires a new admission contract, preferably multi-animal and
recovery-bearing, and may not retune this result.
