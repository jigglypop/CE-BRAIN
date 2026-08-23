# BA-SELF1 A1/A2 validation

Status: COMPLETE

Focused synthetic validation command:

```
.codex\hooks\python.cmd pytest _workspace\ce\brain-self-trajectory-human-fmri-l3-20260824\artifacts\test_brainvision_range.py -p no:cacheprovider
```

Result: `5 passed in 0.77s`.

`artifacts/test_brainvision_range.py` SHA-256:
`08c771d1d383e4b152cac9c6aeacf2c3e2fe7b8928a6dfb7fe39d1615963cfaa`.
The focused tests cover inclusive byte-offset geometry, little-endian
multiplexed float parsing, absence of future leakage from causal filtering,
anchor-aligned decimation, and fail-closed zero-MAD QC scaling.

## Real-data apparatus results

The A1 receipt records 16 exact range responses; A2 records 64. In A2 every
request is `206`, every recorded `Content-Range`/byte count/ETag agrees with
A0, all 64 filtered windows have zero nonfinite values, and none has a
zero-MAD scalp channel. A2 therefore freezes the two declared QC cutoffs.

Five paired task/rest trials are excluded by the frozen amplitude rule. Their
existence does not invalidate A2: the contract requires pair exclusion, not a
post-hoc cutoff change. If either QC metric had a zero MAD, a range/header
receipt mismatched, or an A1 window were nonfinite, the program would instead
have written `APPARATUS_INVALID` and stopped closed.

Receipt-only check result: `A1_A2_RECEIPT_CHECK_PASS`. It confirmed A1=16
windows and A2=64 windows, A2's exact-range and finite/MAD conditions, both
`scientific_endpoint_opened=false` flags, and the unopened split list.

No endpoint/model effect, EEG-path claim, self claim, consciousness claim,
or biological mechanism claim was computed. D1, D2, C1, C2 and C3 are still
unopened, as are all fMRI data.

## D1 draft validation and stop

```
.codex\hooks\python.cmd pytest _workspace\ce\brain-self-trajectory-human-fmri-l3-20260824\artifacts\test_self_trajectory_d1.py -p no:cacheprovider
```

Result after the receipt-only failure-path repair: `6 passed in 0.93s`. The tests cover area reversal/shuffle invariants,
the d=4 feature counts (53/59), fold-local transform behavior, unpenalized
ridge intercept, pair-preserving folds, and preservation of QC diagnostics when
every pair is rejected. The test file SHA-256 is
`a0621b9478f9381090c44f6fe49f18b06bc3f6a440d691a80ba56cb41ebb5061`.

The real D1 execution produced the sealed negative receipt
`D1_FAIL_CLOSED: no QC-accepted D1 pairs`, SHA-256
`d05bd70e013a09cfb47d4ab0cb3bb507bba7839fbb00b98a9988246279da92d2`.
All 64 task/rest windows had exact accepted range receipts. Every window
exceeded the frozen absolute-amplitude cutoff: observed 306.695415322896 to
2884.06387213643 versus 281.5218166091819. None exceeded the first-difference
cutoff: observed 17.4290236704772 to 74.1123038511761 versus
95.39727548778933. Nonfinite and zero-MAD counts were both zero throughout.
Thus the frozen cross-subject absolute-amplitude QC is non-transferable on D1;
this is an apparatus verdict, not an equation result. No d=2/3 outcome
statistic, d=4 diagnostic, future-target loss, or model selection was computed;
D2/C1/C2/C3 and fMRI remain unopened.

The first attempt's missing receipt and the minimal-receipt repair are preserved
under `revisions/`. This disclosure does not turn the repeated QC-only access
into a scientific endpoint.
