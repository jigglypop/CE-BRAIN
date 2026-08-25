# BA-OBS-HPC4 research contract — numeric receipt validator

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-human-hippocampal-theta-transaction-seal-20260825`

Mode: light implementation successor. HPC3 ended
`BLOCKED_RECEIPT_VALIDATOR / NO_RAW_ATTEMPT / NO_ENDPOINT`; therefore no clean count,
waveform, or biological outcome informed this successor.

## Frozen inheritance

HPC4 inherits without change the OpenNeuro release and 18-object lock, author-code
receipt, cohort, p20 `D9,C1,C'1` joint QC, D9 endpoint, D9-D10 bipolar, author-order
preprocessing, thresholds `(5,5,500)`, MIN20 aperture, masks/windows, participant
contrast, PCG64 seed 20260825 and 65,536 draws, LOO, paired sensitivity, status lattice,
single authoritative raw/QC commits, resolver precedence, and the one unused ATTEMPT1.
The inherited hashes remain
`66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810` and
`20008069771a37a7e7669e996d0bb799cabed1ad09e0e010c6c1f0ec33b93496`.

## Sole validator delta

1. Every waveform, P2P, delta, $D$, bootstrap bound/probability, LOO, paired value,
   count, and reason count must be a finite JSON number; strings, booleans, nulls,
   NaN, and infinities are invalid.
2. Each stored mean P2P must equal the P2P recomputed from its committed 599-sample mean
   waveform on the frozen early/late/prestim masks within tolerance
   `rtol=1e-12, atol=1e-12` microvolts.
3. The full stored clinical/local analysis, including deltas, $D$, deterministic
   bootstrap, seven LOO, paired sensitivity, and status lattice, must equal a fresh
   `aggregate(files)` recomputation within the same numeric tolerance and exact
   categorical equality.
4. Clinical exclusion-reason counts are channel-trial counts bounded by
   `blocks * len(qc_indices)`; bipolar reason counts are bounded by `blocks`. This
   explicitly admits p20 values through `3 * blocks`.

No threshold, signal, endpoint, or status is changed. A stable audit must replay the
HPC3 string, finite-tamper, empty-file/analysis, and p20 `3*blocks` counterexamples.
Any remaining P0/P1 blocks raw. Exactly one real ATTEMPT1 may run only after PASS.

## Claim ceiling

Even a successful commit is a same-public-data reanalysis in seven epilepsy-surgery
participants. It is not independent confirmation, healthy generalization, memory or
consciousness proof, or AGI evidence.
