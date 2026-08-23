# BA-SRM4 implementation validation

Status: COMPLETE

Focused command:

` .codex\hooks\python.cmd pytest _workspace\ce\brain-self-trajectory-human-eeg-robust-qc4-l3-20260824\artifacts\test_srm4_real_eeg.py -q `

Result: `12 passed in 1.03s` on Python 3.11.9 with no network access.

The checks cover sealed 10/20/70 allocation, exact all-increment-pair area,
finite transform, nonfinite/zero-scale fail-closed behavior, future-target
sentinel, common-affine loss equivalence, and synthetic Markov-null versus
injected-area identifiability. The regenerated P0 receipt SHA-256 is
`f536116fdde50ae824e6cd91528a5cfb8e59f616351d15fdfc1eb2a462145a5c`.
It reports Markov gain `-0.11255076006434242`, injected-area gain
`0.6473575066316293`, and twenty injected controls, each with oriented loss at
least 0.01 below its refitted constrained shuffle.

Mock R0 checks prove exactly twenty R0 window requests, train-only transform
invariance to held-out future perturbation, positive-baseline pass, tampered
provenance stop before reader access, offline preflight with zero access, and a
truthful partial-fetch failure receipt. A directional gate regression also
proves that one negative LOSO task gain cannot pass behind a positive pooled
gain. Independent pre-execution re-audit returned GO and independently obtained
`12 passed in 1.00s`. R0 offline preflight returned
`R0-SMALL_PREFLIGHT_NOT_EXECUTED`, all endpoint flags false, with R1/R2/C sealed.

The one authorized real R0 execution then opened 10 pairs and 20 exact byte
range windows. Every request returned HTTP 206 and 768,256 bytes; finite,
nonflat, conditioning, provenance, and sample guards completed. The receipt
SHA-256 is
`3bd9db6c2c2519075437bdd142c742f361a6efabc68376a7c786fd9d6f9dd61b`.
Task baseline gain was `-3.6460501404125005` for held-out `ses-01`,
`0.0025103259988423846` for held-out `ses-02`, and
`-0.40260785355519274` pooled. The frozen R0 gate therefore returned
`APPARATUS_INVALID_OR_BASELINE_UNRESOLVED`. Path area, ordered-history gain,
word effect, R1, R2, and C1/C2/C3 remained unopened. No full suite was run.
