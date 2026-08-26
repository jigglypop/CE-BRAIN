# Twin confirmation hypotheses

Status: COMPLETE

H1: fresh train/validation selection recovers `A:R`, `B:G`, `C:F`, `D:S`,
`E:O`, `F:O`, `G:O`.

H2: the validation-selected class predicts held-out matched twin contrasts within
the frozen NRMSE gate without confirmation-based reselection.

H3: in D/E, the selected model associates each observed state/history with its
own intervention contrast, producing a positive pairing advantage and
$p\le0.01$ under blockwise permutations. In A/B/C/F/G the contrast is exactly
twin-independent and is a negative-control identity, not a pairing endpoint.

Falsifier: failure of any frozen per-world conjunction in `contract.md`.
Protocol-mean calibration alone is not evidence because it cannot identify a
twin within an exact intervention block.
