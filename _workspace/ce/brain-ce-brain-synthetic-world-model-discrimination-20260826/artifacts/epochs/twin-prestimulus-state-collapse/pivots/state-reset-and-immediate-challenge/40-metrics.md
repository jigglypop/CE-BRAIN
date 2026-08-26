# State-reset metrics

Status: COMPLETE

Primary metrics: expected validation-winner frequency, selected full-contrast
NRMSE, D/E full-group permutation p-value frequency, A/B/C/F/G twin identity,
paired-bank balance/reset/CRN receipts and common-state adverse identity.

NRMSE and permutation flatten `(block,twin,time=2..63,node)`. Ties count against
pairing. The common-state adverse control is an exact deterministic identity and
does not receive a tuned significance threshold.
