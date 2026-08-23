# BA-ERC1-E2 implementation record

Status: COMPLETE

## 1. Implemented scope

`artifacts/verify_passive_y_crosssolver_e2.py` implements only the frozen E2 synthetic calculation. It contains two separate numerical paths:

1. a cell-centred conservative finite-volume Y-junction operator propagated by classical RK4; and
2. an independently assembled shared-node linear finite-element mass/stiffness pair propagated through a generalized symmetric eigendecomposition.

Both paths are compared first with exact S1/A0/M1 fields and only then with each other. The D0 adverse path replaces the shared junction by three independent sealed centre faces. No predecessor solver code is imported.

## 2. Fail-closed seals

The verifier hard-codes and rechecks the frozen SHA-256 values for current 00/10/11/12/20 inputs and eight predecessor evidence items. It also checks that `artifacts/20-audit-preflight-pass.md` is byte-identical to the frozen PASS audit, and freezes Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1, and disabled bytecode state.

The receipt path must be inside this run's `artifacts` directory and must not already exist. A source, predecessor, environment, archive, finite-value, or D0-discrimination failure receives `APPARATUS_INVALID`. Other frozen numerical failures receive `STOP`. Only an all-gate PASS receives `E2_CROSSSOLVER_MANUFACTURED_ONLY`.

## 3. Pre-build evidence

| item | SHA-256 / result |
|---|---|
| verifier | `a32c833acf740ca9c28764d50230807e391adf247f6790ca593ec183bcbdbb46` |
| current PASS preflight audit/archive | `f076aa9e62449f958db9f94c1d628c9acc149dd6c03902423e1f1391c4b8e2d3` |
| preserved first STOP math | `36e133bf59a428c9658ad82ae3adc59c8cce708c30781a143447f2c161909713` |
| preserved first STOP audit | `91e6dc6797780a5b6f6545152c489111b514b613d449d0b42b7df6ac6a06419d` |
| source-only AST parse | PASS |

The first preflight failure occurred before verifier creation and before numerical execution. Its single correction is recorded as `math-verifier 1/2`; no panel, coefficient, grid, terminal time, solver, metric, threshold, split, or claim ceiling changed.

## 4. Sealed execution command

The following command is authorized exactly once. This section records the command, not its result:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-electrical-riemannian-cable-e2-crosssolver-20260823\artifacts\verify_passive_y_crosssolver_e2.py --output _workspace\ce\brain-electrical-riemannian-cable-e2-crosssolver-20260823\artifacts\e2-receipt.json
```

No real endpoint, biological parameter, behavior, model fit, state-dimension estimator, consciousness variable, hippocampal mechanism, or AGI endpoint is present in the implementation.

## 5. One-shot execution evidence

The sealed command ran once under the recorded system-Python hook and exited zero. It created `artifacts/e2-receipt.json`, SHA-256 `badb1ec5246976b723a257aec4ffb16be1d1e015bb6ebe38afe509b34024ded6`. The receipt records the same verifier hash as the pre-build manifest, all frozen source/predecessor/environment/archive seals match, `failed_checks=[]`, and no numerical apparatus revision was used.

The verifier has not been rerun and the receipt has not been overwritten. Numerical interpretation is delegated to `31-validation.md` and the post-run claim ledger rather than promoted inside this implementation record.
