# CE-BRAIN Stage 10 통합 모델경쟁 게이트 감사

Status: `INTEGRATION_NOT_IDENTIFIABLE`

## 판정

`STAGE10_INTEGRATED_MODEL_NOT_IDENTIFIABLE`

Stage 10은 R·SR·MM·F·G·O를 동일한 held-out state/intervention/animal/counterfactual 자료에서 경쟁시키는 단계다. 현재 각 Stage는 선충 자극, mouse visual coding, rat hippocampus, mouse dopamine learning처럼 서로 다른 종·회로·과제·endpoint를 사용했다. 이 점수들을 한 표에 놓아 최종 승자를 고르는 것은 동일자료 모델 경쟁이 아니다.

## 후보별 현재 지위

| 후보 | 현재 근거 | 지위 |
|---|---|---|
| R: single Riemannian | Stage 3A/B에서 held-out source·genotype 예측 이득이 사실상 0, common/unseen 승자 불일치 | 미통과 |
| SR: state-dependent Riemannian | 개체축·recovery는 재현됐지만 공통축과 기하 예측은 미확립 | 미확립 |
| MM: multiple/stratified manifolds | 국소 patch 생존자가 없어 patch 결합을 식별할 입력이 없음 | 미실행·식별불가 |
| F: directional/Finsler | 일부 분할 1위였으나 null 대비 효과와 일반화 문턱 실패 | 미통과 |
| G: dynamic graph | Stage 3B common pair에서 null보다 악화, 생존 graph 없음 | 미통과 |
| O: general nonlinear operator | 조건별 재학습 이득 0.0813%, 신뢰구간 0 교차 | 미통과 |

## 단계 간 살아 있는 좁은 사실

1. 개체 내부에서는 상태축과 recovery가 재현됐다.
2. 두 visual development subject에서 history와 population mode는 미래 예측에 유용했다.
3. 두 해마 topdir에서 population 신호는 정적 위치 기준보다 유용했지만 정확한 trajectory gate는 실패했다.
4. dopamine 계수 방향은 development 7 animals의 모든 outer fold에서 양수였지만 next-day animal 외삽을 개선하지 못했다.

이 네 사실은 서로 다른 자료에서 얻었으므로 하나의 통합 메커니즘을 자동 구성하지 않는다.

## 다음 최소 통합 의무

하나의 자료계에서 다음이 동시에 필요하다.

- 반복 가능한 state 또는 intervention
- 동일 개체의 history·population dynamics
- 행동 또는 memory update endpoint
- 가능하면 neuromodulator 동시 측정
- animal holdout과 intervention holdout

그 자료에서 R/SR/MM/F/G/O가 같은 입력·출력·자유도 예산을 사용하도록 새 계약을 작성해야 Stage 10을 실행할 수 있다. 현재는 최종 모델 승자를 선언하지 않는다.
