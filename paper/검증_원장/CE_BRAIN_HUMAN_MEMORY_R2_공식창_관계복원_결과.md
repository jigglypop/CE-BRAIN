# CE-BRAIN Human Memory R2 공식창 관계복원 결과

Status: `HUMAN_RELATIONAL_RETRIEVAL_R2_NOT_ESTABLISHED_REPLICATED`

기준일: 2026-08-31

## 판정

공식 old/new 기억신호가 재현된 `+0.2~+1.7초`·correct-trial 조건을 사용해, 관계 endpoint가 미개봉이던 P11HMH와 P48CS를 순서대로 실행했다. 두 subjects 모두 완전 200 trials, exact-old 50, unit·행동·category coverage 문을 통과했다.

두 subjects 모두 동일항목, 관계거리, confidence, correct–incorrect, 시간순서 문턱을 통과하지 못했다.

**[판정]** `HUMAN_RELATIONAL_RETRIEVAL_R2_NOT_ESTABLISHED_REPLICATED`.

## 결과

| 지표 | P11HMH | P48CS | 문턱 |
|---|---:|---:|---:|
| 유효 units | 25 | 36 | ≥10 |
| correct / incorrect old | 35 / 15 | 42 / 8 | ≥20 / ≥5 |
| matched cosine 이득 | 0.00718, p=0.3175 | -0.01224, p=0.8334 | ≥0.05, p≤0.01 |
| 관계거리 Spearman | 0.09731, p=0.3085 | 0.02448, p=0.2763 | rho≥0.20, p≤0.01 |
| confidence Spearman | 0.20537, p=0.0254 | 0.08019, p=0.0478 | rho≥0.20, p≤0.01 |
| correct–incorrect cosine | 0.02779, CI [-0.04065, 0.08784] | 0.01131, CI [-0.03419, 0.05556] | ≥0.05, 하한>0 |
| 시간순서–역순 | 0.00263, CI [-0.03836, 0.04851] | -0.00638, CI [-0.03816, 0.02553] | ≥0.03, 하한>0 |

## 쉬운 해석

이 데이터에서는 뉴런이 “전에 본 것인가, 새것인가”를 구별하는 신호는 공식 방법으로 검출된다. 하지만 같은 그림을 다시 볼 때 학습 당시 항목들의 상대적인 거리 지도가 되살아난다는 신호는 검출되지 않았다. 시간창을 공식 기억신호 구간으로 옮기고 정답 trial만 보아도 마찬가지였다.

따라서 `old/new·confidence signal`과 `exact-item relational geometry restoration`은 같은 주장이 아니다. 전자는 자료에서 살아 있고, 후자는 현재 고정 표현에서 반복 미확립이다.

## 계보 판정

- P19/P16 R1과 P11/P48 R2, 총 네 human development subjects에서 관계복원 미통과
- R1 `[0,1.0]`초와 R2 `[0.2,1.7]`초 두 family 모두 미통과
- calibration 14명과 confirmation 9명은 열지 않음
- 로드맵 Phase 8의 관계복원은 미확립
- Phase 9 recurrent capacity와 Phase 10 correction은 계속 미허가

이 결과는 인간 기억에 어떤 관계형 표현도 없다는 증명이 아니다. 현재 시험한 unit×time-bin cosine·거리행렬 family를 더 이상 같은 데이터에서 구제하지 않는다는 STOP 판정이다.

코드: `examples/brain/ce_brain_human_memory_relational_r2.py`

검증: `tests/test_ce_brain_human_memory_relational_r2.py`
