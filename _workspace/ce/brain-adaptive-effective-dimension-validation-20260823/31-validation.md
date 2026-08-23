# BA-SRM6 검증 기록

Status: SKIPPED (REAL_ENDPOINT_UNOPENED)

Date: 2026-08-23

## 실행된 범위

실행한 검증은 preregistered input audit뿐이다.

```powershell
.codex\hooks\python.cmd python `_workspace\ce\brain-adaptive-effective-dimension-validation-20260823\artifacts\input_audit.py` --output `_workspace\ce\brain-adaptive-effective-dimension-validation-20260823\artifacts\input-audit.json`
```

Python entry point는 repository의 policy-safe `.codex/hooks/python.cmd`를 사용했다.
영수증 SHA-256은
`52e804ff910bcee5dfb431dc193016c014bf6262a0055d7960795da1c74e7caf`다.

## 결과

| gate | 결과 |
|---|---|
| 세 archive bytes + SHA-256 | PASS |
| 22 MAT schema | PASS |
| recording split membership | PASS |
| clockㆍgapㆍ$h=6$ availability | PASS |
| primary `Ratio2` unit viability | **FAIL** |
| 전체 input gate | **FAIL** |

실패 기록은 train의 `BrainScanner20200130_105254`와 validation의
`BrainScanner20200310_141211`이다. 양쪽 모두 first-60% `Ratio2` finite fraction
0.75를 만족하는 neuron이 0개였다.

## 실행하지 않은 검증

Gate가 열리지 않았으므로 L0-A property test, L0-B synthetic recovery, L0-C
semi-synthetic injection, real GCaMP model fit, validation selection, held-out scoring을
실행하지 않았다. 따라서 recovery correlation, normalized MAE, false-alarm rate,
$R^2$, RMSE, $\Delta R^2$ 값은 존재하지 않는다. 이를 0이나 FAIL score로 대체하지
않는다.

검증 판정: `INPUT_CONTRACT_STOP / REAL_ENDPOINT_UNOPENED`.
