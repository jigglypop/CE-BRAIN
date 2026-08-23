# BA-SELF2 scale-free QC apparatus implementation

Status: COMPLETE

The implementation is limited to the apparatus path: it never constructs
quotient coordinates, future targets, path features, losses, or models.

`artifacts/scale_free_qc.py` first checks the SHA-256 of the predecessor
BrainVision parser/range/filter before importing it. It then verifies the
current contract SHA-256 `8eb85e4ce7218112c082b84e0f754ae3fa0afb1995374a9675c581164880517f`,
the sealed predecessor manifest SHA-256
`4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061`, and
the sealed predecessor A0 receipt SHA-256
`5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7` before
any executable stage can request a range.

For a finite post-filter $126\times63$ window, the code implements the frozen
$Q_A,Q_D$ definitions, rejects any nonfinite value, any nonfinite or
nonpositive channel robust scale, or any nonfinite/nonpositive median
denominator, and records no raw payload or decoded window. A2 freezes exactly
`median(Q) + 6 * median(abs(Q - median(Q)))` from 64 windows. D1-QC records
only $Q_A,Q_D$, paired accept/reject reasons, exact range receipts, and the
matched legacy absolute diagnostics; it cannot construct a model outcome. Its
pass condition is at least 24 of 32 paired trials and at least 12 of 16 in each
session.

The CLI defaults to sealed offline preflight. `--execute` is required for an
A1, A2, or D1-QC range stage. The following sealed commands were then run by
the main agent (the manifest, A0 receipt, contract, and predecessor arguments
were the locked inputs named above):

```text
.codex\hooks\python.cmd python artifacts\scale_free_qc.py --stage A1 --execute ... --output artifacts\a1-scale-free-receipt.json
.codex\hooks\python.cmd python artifacts\scale_free_qc.py --stage A2 --execute ... --output artifacts\a2-scale-free-receipt.json
.codex\hooks\python.cmd python artifacts\scale_free_qc.py --stage D1-QC --execute ... --a2-receipt artifacts\a2-scale-free-receipt.json --output artifacts\d1-qc-transfer-receipt.json
```

The three offline seal-preflight receipts have SHA-256 prefixes
`75eaadc6`, `4457e49a`, and `7a2c3348`, respectively. Build completed OK.

The receipt writer is local to this run, so even a predecessor-import,
network, parser, or other ordinary execution exception writes an atomic
fail-closed receipt with its exception type/message and both endpoint flags
false. A1/A2 hard-domain QC errors cannot be returned as pass receipts. D1-QC
uses the production paired transfer gate and exits nonzero when its 24/32 and
12-per-session requirement fails. Stage-specific unopened lists retain D1-QC
as unopened after A1/A2.

## Real apparatus receipts

- A1 receipt `artifacts/a1-scale-free-receipt.json`, SHA-256
  `37f82cea31a36f4d036422dcaea8b92fa2d8198f2d8d62d740f78eb7f2a4a79e`, is
  `A1_APPARATUS_PASS`: 16 exact windows, zero hard-domain rejects,
  $Q_A=5.51530810708829\ldots27.9038068077509$ and
  $Q_D=5.2898306578321\ldots32.7086040321134$. Both endpoint flags are false.
- A2 receipt `artifacts/a2-scale-free-receipt.json`, SHA-256
  `0427207665cd3411ade82fcef157187e199cbaa5923e337f100790db39ed121b`, is
  `A2_APPARATUS_PASS`: 64 exact windows and zero hard-domain rejects. It froze
  $Q_A$ median/MAD/cutoff `8.071297797761897`, `1.5591476116114693`,
  `17.42618346743071`; and $Q_D$ median/MAD/cutoff
  `7.540774258395317`, `1.831687591291058`, `18.530899806141665`. Six of 32
  calibration pairs exceed a frozen cutoff; this is a paired diagnostic, not
  an endpoint.
- D1 receipt `artifacts/d1-qc-transfer-receipt.json`, SHA-256
  `7ea150e088625774b75ce1ceec35b8529e3abae470348fa4f693188e3820d28a`, is
  `APPARATUS_INVALID_CROSS_SUBJECT_SCALE_FREE_QC` (nonzero command exit): 64
  exact windows, 13 accepted and 19 rejected pairs, with session counts
  `ses-01=8` and `ses-02=5`. This fails both the 24/32 total and 12/16
  per-session transfer gates. $Q_A$ ranges from `6.2055476321105` to
  `77.2573686972437` (upper-sample median `15.490390421801653`) and exceeds in
  22/64 windows; $Q_D$ ranges from `5.73470969032329` to
  `29.1100615157984` (upper-sample median `10.166710207972347`) and exceeds in
  4/64. Pair reasons are `Q_A=18`, `Q_D=4` (not disjoint).

D1 opened no scientific endpoint and computed no model outcome. D2 and all
three confirmation splits remain sealed. R1 is therefore killed as an
apparatus-transfer failure, not as a result about the path equation, self,
or consciousness.
