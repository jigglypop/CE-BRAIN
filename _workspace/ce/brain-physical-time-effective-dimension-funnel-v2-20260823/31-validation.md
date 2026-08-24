# BA-SRM9 F2-C validation

Status: COMPLETE

## Focused command

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-physical-time-effective-dimension-funnel-v2-20260823\artifacts\validate_f2c_receipt.py
```

The read-only validation returned `status=PASS`. It rehashed the F2-A, F2-B,
F2-C, and runner files; checked 20 distinct ordered inputs and 20 candidate
rows; recomputed the conjunction of the two frozen scenario gates; and checked
that all behavior, model, real-endpoint, biological-claim, and downstream flags
are false.

The exact status counts are:

| status | count |
|---|---:|
| `PROMOTE` | 0 |
| `DROPPED_BUDGET` | 0 |
| `FUTILITY_KILL` | 20 |
| `ABSTAIN` | 0 |
| `INVALID_KILL` | 0 |

Across the 20 candidates, ART10 median Spearman recovery ranges from
`0.6136981053328` to `0.7404632890000811`; all 20 are below the frozen `0.80`
gate. BLOCK30 recovery ranges from `0.9284251656475162` to
`0.9788390822185931`, and every candidate's median NMAE in both scenarios is at
most `0.20`. Thus the kills arise from the preregistered ART10 recovery gate,
not from an invalid domain, abstention, cap, or tie-break.

The validator does not rerun F2-C and does not test a brain mechanism. No full
test suite or downstream scientific stage was run.

