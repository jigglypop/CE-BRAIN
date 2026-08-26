# BA-OBS-ID4 independent status audit

Status: COMPLETE

Gate: PASS

Scope: final stable v4 read-only audit of the lexical-ULP contract revision,
development range planner, acquisition/checkpoint integration, actual `sub-1` and
`sub-5` v4 receipts, tests, and validation narrative. The auditor made no file or
Git change and opened no signal, `.tdat` body, endpoint, or confirmation subject.

## Stable snapshot

| file | SHA-256 |
|---|---|
| `00-contract.md` | `EC594861BDEA42B3A4BB10558C1EF205F76714AEBCCBA94800AD7EEA9FBEA83F` |
| `11-math.md` | `9CB1FEFECC61F272E594C2EEEFC2C70233792659B71974C928947B418781981B` |
| `30-implementation.md` | `E388A7FA0D8651694FABB8BA15DFC33E07685C3C39E73D8F92DB25BAC17CF5A8` |
| `31-validation.md` | `F3B52DAD879AC599800D28659C721478AD4026FDCAA5A2353B95ED24051B889C` |
| `artifacts/id4_development_range_plan.py` | `82296D2A82351C6598BB2E419EF179900C6D2F65BBCA4FAD60DADDEE758814CC` |
| `artifacts/id4_development_index_acquire.py` | `1E1D12438E7962A04A90FBF91094E7C0FE04FE1A1A0822584586CEA3694B51C3` |
| `artifacts/test_id4_development_range_plan.py` | `6F93A6AC5F478916FF6D024EA783A66F18D404EF06EB9861186D498F40789AF7` |
| `artifacts/test_id4_development_index_acquire.py` | `3C36C20D77B4CF255105CB4B5AE53D0C5F0D76EA957CF8242EDEBE12863760DC` |
| `artifacts/development-index-plan-sub-1-v4.json` | `CDB3385FCD936E6835E9E0AC2DD36D8AF6C40F0BE44F5307D5FDF1753D16BE2B` |
| `artifacts/development-index-plan-sub-5-v4.json` | `A32FC05C7EB8868CCAC880B1AEAFEEEFD24EBA4D116D3B4E5B4AFAE28FB84112` |
| `artifacts/development-index-sub-1-checkpoint-v4.json` | `54D6EC62CDA6C5C3014AC2E10B9FBF7216CE8648C73595C5712DFF0119FAAFA6` |
| `artifacts/development-index-sub-5-checkpoint-v4.json` | `26838223BD5A6B8FE46BE04871F0E57DF46AC41286C8A63B5438E0785D24DE33` |

## Findings

1. **P0/P1/P2: none.** The contract, mathematics addendum, planner, and tests
   implement the same exact-Decimal rule: retain an integral product directly;
   otherwise accept only a unique integer in the lexeme-specific half-ULP interval.
   Empty, ambiguous/tied, and duplicate same-site sample mappings fail closed.

2. Precision convention 4 and checkpoint schema 5 are consistent across code,
   tests, receipts, and both COMPLETE checkpoints. `sub-1` covers 154/154 channels
   with 179,221,944 planned `.tdat` bytes; `sub-5` covers 156/156 with 225,625,112.
   Both record persistent raw zero, signal false, development signal false, and
   confirmation false. No raw ranges, `.tidx/.tdat` body, or raw payload is stored.

3. The older v3 `sub-1` receipt/checkpoint is explicitly superseded apparatus
   history and is not used by v4. The v3 `sub-5` onset rejection is recorded as the
   signal-blind P0 that motivated the adopted source-representation revision, not as
   source, neural, or endpoint evidence.

4. Exact sample-index adjacency and RED bit-0 discontinuity checks remain intact.
   `APPARATUS_MEF3_SAMPLE_INDEX_STOP` remains active because the uUTC-only reader
   fixture does not prove returned stored-sample identity. Therefore the completed
   index plans do not authorize development signal or confirmation access.

5. The strict claim ceiling is unchanged: this run has only apparatus and
   source-locked planning evidence. It supplies no biological result, neural metric
   or geodesic identification, population generalization, consciousness/self-memory,
   hash, or AGI evidence.

## Formal status

The final v4 stable snapshot passes the independent status gate with no P0/P1/P2.
This authorizes only the prescribed apparatus progression. It is not biological,
endpoint, metric, or confirmation evidence.
