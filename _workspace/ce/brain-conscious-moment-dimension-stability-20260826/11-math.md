# Mathematics

Status: COMPLETE

## DS.1 — temporal fractions

For session windows and selected base rank `d*`, compute exact fractions in the
candidate band `{4,5,6}`, exactly at `d*`, and in the matched control band.
Require predeclared band persistence, selected-rank persistence, and a strict
conscious-minus-control separation threshold in every session.  Also require a
maximum adjacent-window rank-transition fraction and a minimum longest
consecutive dwell fraction at `d*`, so rapid alternation cannot mimic persistence.

## DS.2 — block-bootstrap fractions

With frozen session block length and resampled complete-menu winners, compute the
fraction in `{4,5,6}` and exactly at `d*`.  Both must exceed frozen thresholds in
every session.  iid-window resampling is not accepted under the block label.

## DS.3 — conjunction

Support is the conjunction of the validated base certificate, frozen protocol
labels, all temporal gates, all control gaps, and all bootstrap gates.  A single
session failure rejects supplied-summary support.  Passing refers only to neural
signal-rank stability, never consciousness dimension.
