# CE-BRAIN Stage 7 R2C 기억궤적 독립 개발 결과

Status: `DEVELOPMENT_REPLICATION_RECOMPUTED`

## 판정

`TRAJECTORY_MEMORY_NOT_ESTABLISHED_REPLICATED`

R1과 다른 topdir `ec016.17/ec016.233`에서 validation-only로 해독기를 선택했지만 test encoding과 replay의 사전 문턱을 넘지 못했다.

## 봉인과 범위

- 실제 cluster에 존재하는 CA1 pyramidal unit 75개
- 왕복 64회: 양방향 각 32회
- train 38·validation 12·test 14회
- manifest SHA-256: `b3bbcce1b046ad0c4f1fa81fb8fb14af39d089b1f6e3b549136f2052a977b56c`
- result SHA-256: `e870e0b049a7141223bc5a1cd4ae59d8eb63871174cdfcba087f1a1243715ebf`
- raw-recompute validation SHA-256: `297eb2a98b2950eb6d7776f323607a39178a0f207e8ef77835a822a52ef3d699`

R2B의 84/84 metadata-cluster 일치 조건은 75/84로 score 전 중단됐다. R2C는 이 중단을 보존하고, 실제 존재 unit 30개 이상이라는 새 장치 정의를 별도 계약으로 고정한 실행이다.

## validation 선택과 test encoding

16개 후보 중 validation median error가 가장 낮은 후보는 spatial sigma 0.5 bin, uniform prior, 0.2초 decode bin이었다.

| 항목 | 결과 | 사전 문턱 | 판정 |
|---|---:|---:|---|
| test 표본 | 1,562 | 100 이상 | 통과 |
| median absolute error | 0.296931 track | 0.15 이하 | 실패 |
| 정적 기준 오차 | 0.421531 track | - | - |
| 정적 기준 대비 개선 | 29.5590% | 20% 이상 | 통과 |

R1과 마찬가지로 population 신호는 정적 위치 기준보다 유용했지만, 실제 위치를 기억 궤적으로 해석할 절대 정확도는 부족했다.

## ripple·trajectory 보조 결과

743개 ripple 후보 중 54개가 활성도 조건을 만족했다. 두 shuffle의 95 percentile을 동시에 넘은 사건은 2/54, 즉 3.704%였고 binomial `p=0.759207`이었다.

| 비교 | median 차이 | bootstrap 95% 하한 |
|---|---:|---:|
| order vs time shuffle | 0.054221 | 0.000000 |
| order vs cell shuffle | 0.024187 | 0.000000 |
| distance vs time shuffle | 0.070286 | -0.031020 |
| distance vs cell shuffle | 0.011811 | -0.036537 |

order는 양의 방향성이 있었으나 사전 효과크기 0.10에 못 미쳤고 하한도 `>0`이 아니었다. distance 하한은 둘 다 음수였다.

## 결론과 다음 의무

**[산출]** 두 독립 development topdir에서 위치 관련 population signal의 정적 기준 대비 개선은 반복됐지만, 사전 정확도와 trajectory-null 게이트를 통과한 기억 궤적은 반복되지 않았다.

**[금지]** Stage 7을 근거로 Stage 8 retrieval·correction을 확인적으로 실행하지 않는다. 같은 hc-3 test를 보고 더 복잡한 decoder를 맞춘 결과는 탐색으로만 표시한다.

**[식별 불가]** 생물학적 replay 부재, place-cell 안정성 변화, 방향별 place field, 단일 ripple channel, 단순 독립 Poisson decoder의 감도 부족은 아직 분리되지 않았다.

**[다음 최소 증명 의무]** trial·epoch 의미가 명시된 새 해마 자료에서 방향별·상태공간 decoder를 train/validation으로만 고정하고 새 test에서 먼저 0.15 encoding 문턱을 통과해야 replay 확인을 재개한다.
