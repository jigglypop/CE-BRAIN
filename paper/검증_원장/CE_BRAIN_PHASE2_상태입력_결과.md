# CE-BRAIN Phase 2 상태×입력 판별 결과

Status: `COMPLETE / STATE_INPUT_SEPARABLE_RETAINED / STAGE3_NOT_AUTHORIZED`

## 판정

사전 고정한 새 동물·새 전류 동시 holdout에서 M2 상태×전류 방향 상호작용은 지지되지 않았다. 전류가 상태 대비의 크기를 바꿀 수 있지만 대비 방향은 하나라고 두는 rank-1 M1이 세 전류 모두에서 더 작은 예측오차를 냈다.

| 항목 | M1 분리가능 | M2 상호작용 |
|---|---:|---:|
| 20 μA holdout 오차 | 0.076379 | 0.159958 |
| 50 μA holdout 오차 | 0.231320 | 0.239817 |
| 100 μA holdout 오차 | 0.801435 | 0.875162 |
| 세 전류 평균 | 0.369712 | 0.424979 |

M2 상대 개선율은 `-0.149488`이었다. 즉 M2가 개선한 것이 아니라 평균오차가 약 14.95% 커졌다. 1,999회 bootstrap에서 M2 개선율의 중앙값은 `-0.246698`, 95% 구간은 `[-0.551496,-0.124748]`로 전부 0 아래였다. 사전 문턱에 따라 판정은 `STATE_INPUT_SEPARABLE_RETAINED`다.

## 대조 결과

- shape-only: M1 평균오차 `1.350715`, M2 `3.784140`; M2 우위 전류 `0/3`.
- 521886 내부 짝수→홀수 확인: M1 `0.208830`, M2 `0.331173`; M2 상대 개선 `-0.585850`.
- 확인 trial 시간 전반: M2 상대 개선 `-0.135242`; 후반 `-0.132892`. 부호가 유지됐다.
- recovery 비율 `Q=D(awake,recovery)/D(awake,isoflurane)`은 20 μA `0.981081`, 50 μA `0.624197`, 100 μA `0.747017`이었다.

대조들은 주 판정과 같은 방향이다. 다만 recovery의 전류별 차이는 남아 있으므로, 회복 과정 전체가 입력과 무관하다고 말할 수는 없다.

## 쉬운 말 해석

이번 결과는 “상태와 자극이 복잡하게 결합해 매번 전혀 다른 지도를 만든다”는 강한 M2 그림을 약화한다. 현재 자료에는 **같은 상태 변화 방향이 있고, 자극 세기는 그 변화가 얼마나 크게 보이는지를 주로 조절한다**는 단순한 그림이 더 잘 맞았다.

하지만 M1이 M2보다 낫다는 것과 M1이 무신호·global gain보다 낫다는 것은 다른 질문이다. 이 계약은 M1 대 M2만 판별했으므로, 보편적 상태 간선이나 기하를 확립하지 않는다. 다음에는 미개봉 동물에서 `rank-1 상태축 대 0효과/global-gain`을 별도 계약으로 확인해야 한다.

## 증거 영수증

- source-only schema receipt: `d98f1c4c2c0090dfe59f640ebf6fab1a585ba8c502ca1cce3830c671f6cd1618`
- manifest: `7196cdfac1533ee23ac2d960b5e810baa1a8751319fd9a0fddb900ba69084456`
- result: `1cfebe6becb630bb5cf6ed4456a3775fa52b1ce879a66a51be96b254debe1e4f`
- raw recomputation validation: `e1028a30f2d2bb0fac64c082b7790726409987f85aba23f9ff2ef23a174a4456`, `PASS`
- focused test: `11 passed`

## 다음 허용 경로

1. 아직 EEG endpoint를 열지 않은 DANDI 000458 동물의 상태×전류 trial 인벤토리를 만든다.
2. 적격 동물을 고른 뒤 M1 rank-1 상태축이 0효과·global gain·block drift보다 나은지 사전 등록한다.
3. 그 확인을 통과해야만 동일 전달행렬의 metric/graph/operator Stage 3을 연다.

현재 `stage3_authorized=false`다.
