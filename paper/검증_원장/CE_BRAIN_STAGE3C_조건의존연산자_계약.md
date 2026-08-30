# CE-BRAIN Stage 3C 조건의존 연산자 탐색 계약

Status: `SEALED_EXPLORATORY_PRE_SCORE`

Stage 3B에서 `unc-31` endpoint와 WT→`unc-31` 모델 점수는 이미 공개됐다. Stage 3C는 독립 확인이 아니라 고정 기하 실패 원인을 분해하는 탐색 분석이다. Stage 3C의 조건별 재적합 점수는 이 계약을 봉인하기 전 계산하지 않는다.

`unc-31` subject를 `SHA256("CE-BRAIN-STAGE3C-20260906|subject") mod 10 < 7`이면 development, 아니면 confirmation으로 고정한다. canonical source holdout은 Stage 3B와 동일하게 제외하고, WT와 `unc-31` development 양쪽에 존재한 ordered pair만 confirmation에서 채점한다. development·confirmation 각각 5개체와 8,000·5,000행 이상을 요구한다.

비교 대상은 다음 세 층이다.

1. `W`: WT에서 적합한 고정 구조.
2. `C`: `unc-31` development에서 WT 예측 logit의 절편·기울기만 재보정한 구조. 전체 반응률과 출력척도 변화는 허용하지만 공간구조는 유지한다.
3. `U`: `unc-31` development에서 R/F/S/O/G 구조 자체를 다시 적합한 조건별 표현.

별도 `W_N`, `U_N` 전체 평균을 둔다. confirmation subject cluster bootstrap 1,999회, seed `20260907`을 사용한다. 조건의존 후보는 U가 같은 family의 C보다 3% 이상, U_N보다 5% 이상, 다음 U family보다 3% 이상 개선하고 세 bootstrap 하한이 모두 0보다 클 때만 탐색 지지한다. 구조 후보가 없고 U_N이 W_N보다 3% 이상 안정적으로 나으면 `EXPLORATORY_GENOTYPE_BASE_RATE_SHIFT_ONLY`, 그 밖에는 `CONDITION_DEPENDENT_OPERATOR_NOT_ESTABLISHED`다.

어떤 결과도 Stage 4를 허가하지 않는다. 목적은 새 독립 데이터에서 무엇을 사전등록할지 결정하는 것이다.
