# BA-SRM7 검증 기록

Status: SKIPPED (SOURCE_ROOTED_INPUT_STOP / REAL_ENDPOINT_UNOPENED)

Date: 2026-08-23

## 실행한 검증

정책 안전한 repository wrapper만 사용했다.

```powershell
.codex\hooks\python.cmd python `_workspace\ce\brain-adaptive-effective-dimension-validation-v2-20260823\artifacts\math_spotcheck.py`
.codex\hooks\python.cmd pytest tests\test_dimensionless.py -q
.codex\hooks\python.cmd python `_workspace\ce\brain-adaptive-effective-dimension-validation-v2-20260823\artifacts\input_audit.py` --output `_workspace\ce\brain-adaptive-effective-dimension-validation-v2-20260823\artifacts\input-audit.json`
```

focused dimensionless 검사는 `19 passed in 0.37s`였다. math spot check는
$\min\operatorname{eig}G=0.2888557574$, resolvent trace의 $\lambda$ 단조 감소,
orthogonal rechart trace residual $8.88\times10^{-16}$, $A$ condition number
$2.52472$를 확인했다. pairwise-complete adverse matrix의 최소 고유값은 $-0.8$로,
그 방식이 PSD core에 들어가면 안 된다는 반례도 재현했다.

최종 input audit runtime은 60.056초였다. 최종 receipt SHA-256은
`bbb2382ef510a8323ba9b14b1aaa7f653d675fecbe6f34f48d61f3385586c51f`다.

## 결과

| gate | 결과 |
|---|---|
| archive bytes/hashㆍ공개 코드 hash | PASS |
| 22 MAT raw schema | PASS |
| clock monotonicityㆍpositive step | PASS |
| raw/processed prefix | PASS |
| primary/red causal unit eligibility | PASS, all 22 |
| split별 feature-common anchor 최소 100 | **FAIL, 4 recordings** |
| behavior lock | `SKIPPED_NEURAL_LOCK_FAIL` |
| 전체 input gate | **FAIL** |

실패 count는 `214/42/33`, `372/107/48`, `23/8/0`, `555/53/159`다. 상세 recording
mapping과 anchor ID hash는 `20-audit.md`와 `neural-input-lock.json`에 고정했다.

## 실행하지 않은 검증

Gate가 열리지 않았으므로 L0-B synthetic recovery, L0-C behavior-blind semi-synthetic
injection, real GCaMP behavior fit, validation selection, held-out scoring을 실행하지 않았다.
따라서 recovery score, false-alarm rate, $R^2$, RMSE, $\Delta R^2$ 값은 존재하지 않는다.
존재하지 않는 점수를 0 또는 예측 FAIL로 바꾸지 않는다.

검증 판정: `SOURCE_ROOTED_INPUT_STOP / REAL_ENDPOINT_UNOPENED`.
