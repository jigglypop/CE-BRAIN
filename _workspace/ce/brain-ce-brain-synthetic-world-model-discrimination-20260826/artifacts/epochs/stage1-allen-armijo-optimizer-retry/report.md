# Stage 1 Allen Armijo successor result

Status: COMPLETE

Decision: `STAGE1_HISTORY_SUPPORTED`

The optimizer-only successor preserved the first attempt and every scientific
input while replacing undamped logistic Newton steps with registered monotone
Armijo steps. Both models converged and the one-shot result passed the inherited
history-support gates on the two held-out Noise 2 sweeps.

| Sweep | M0 RMSE (mV) | M1 RMSE (mV) | Voltage improvement | M0 Brier | M1 Brier | Brier improvement |
|---:|---:|---:|---:|---:|---:|---:|
| 61 | 3.3652189884 | 3.0062247299 | 10.66778298% | 0.0032755017 | 0.0020700129 | 36.80317989% |
| 63 | 3.4031114874 | 3.0881825415 | 9.25414718% | 0.0035721015 | 0.0021538122 | 39.70461983% |

M1 also beat voltage persistence on both sweeps (persistence RMSE 3.5071706772
and 3.5617709160 mV). This supports a recent-history representation for 1 ms
prediction in this one recorded mouse neuron. It does not establish a universal
cell-type law, causal memory state, geometry, consciousness or AGI mechanism.

The original post-write generic verifier rejected M0 because JSON did not retain
the original float32 dtype of its mean/scale arrays. The stored numeric arrays
were unchanged: deterministic FIT refitting reproduced both models exactly, and
a separate read-only historical-dtype validator recomputed all 33 sweeps from
raw and matched every metric, data hash and decision. The sealed result was not
rewritten.

## Receipts

- Predecessor apparatus STOP manifest: `190f75971a6e7879e3f2d6825507950d018c954862257b88e0f938b4488a7169`
- Retry manifest: `ccc2299ab21296afdbfe6591b2290f8e490b99870565074f6fd42c93891ed65e`
- Result: `64b48fb80763bd08d08d08a6048ec6bd641e8c0f225c05109e2d50a4a0c6a395`
- Raw-independent validation: `30184462a9415a88e4e60e9a817866a450ea2ff26f0185228144ef46bcf4c946`
- Persistent raw bytes: `0`
- Stage 2 automatically authorized: `false`; a separate Stage 2 contract is required.
