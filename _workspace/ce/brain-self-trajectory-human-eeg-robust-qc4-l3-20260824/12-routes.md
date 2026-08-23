# BA-SRM4-L3 route lane

Status: COMPLETE

Contract SHA-256: `04ea2bb2166916120bebf25c546646dd59f4bd20b4c97c4e9ba5de28f70a174d`

## Decision

이 실행은 hard max-QC를 한 번 더 조정하지 않고, bounded measurement transform 뒤에 상태 baseline과 ordered path area를 직접 비교하는 R4를 선택한다. 실제 생물물리 출발식은 cable/current-conservation과 conductance dynamics지만, scalp EEG에서 검정하는 것은 그 식의 neuron parameter가 아니라 “저차 관측상태만으로 충분한가”라는 축약 implication이다.

| route | disposition | 이유 |
|---|---|---|
| R1 absolute/common-scale max-QC | KILLED | BA-SELF1/2에서 0/32와 13/32. recording transfer 실패 |
| R2 channelwise max-QC | KILLED | BA-SELF3 B1에서 17/32, ses-01 10/16, ses-02 7/16. 차분 극값이 14 reject에 관여 |
| R3 smooth tail-occupancy hard gate | NOT SELECTED | max보다 낫더라도 다시 pair를 cutoff 하나로 폐기한다. 이번 질문은 장치 통과율이 아니라 직접 predictive implication이다. |
| R4 bounded observation + state/path comparison | SELECTED | $4\tanh(u/4)$로 유한 artifact 영향을 제한하고, 동일 관측·baseline에 area 하나만 추가한다. |
| R5 neuron-edge/ambient metric inversion | KILLED FOR THIS DATASET | scalp volume conduction과 finite sensors 때문에 ds006033에서 식별 불가능 |
| R6 self/consciousness/hippocampal-hash endpoint | DEFERRED | report·memory·intervention이 없는 inner-speech EEG는 해당 endpoint를 제공하지 않는다. |

## Funnel

SELF3가 signal-blind로 남긴 D2-M 100 pair만 새 hash prefix로 10/20/70에 배정한다. R0-SMALL은 all-finite 10/10과 $p=5$ baseline이 persistence를 이기는지만 본다. R1-MEDIUM은 SMALL과 합친 30 pair에서 $d=2$, $H=0.4$ s, $\Delta=0.1$ s, $\kappa=4$, ridge $\lambda=1$의 고정 식을 최초로 futility 검정한다. R2-LARGE는 앞의 transform·coefficient·outcome을 재사용하지 않고 남은 70 pair에서 독립 development validation을 한다.

각 단계가 실패하면 뒤 signal은 열지 않는다. R1의 양의 gain은 R2를 열 자격일 뿐 최종 증거가 아니다. R2가 고정 threshold와 모든 adverse control을 통과해야만 기존 C1/C2/C3 confirmation을 별도 실행할 수 있다.

## Alternative-control decision

단순 $A\mapsto-A$ reverse는 refit ridge와 정확히 동치여서 성공 gate에서 제거했다. 선택된 control은 마지막 increment를 보존한 20개 deterministic order shuffle이다. 이 control은 모든 $M_0$ feature와 model capacity를 보존하면서 area ordering만 파괴하지만 인과 null이나 p-value는 아니다.

## Kill rules

- allocation count/hash/coverage 불일치: `APPARATUS_INVALID_DESIGN`
- P0 Markov false positive 또는 injected-history miss: `STOP_SYNTHETIC_IDENTIFIABILITY_FAILURE`
- R0 hard-domain·rank·baseline failure: `APPARATUS_INVALID_OR_BASELINE_UNRESOLVED`
- R1 nonpositive directional gain, shuffle 우위 또는 word fragility: `STOP_NO_ORDERED_HISTORY_FEASIBILITY`
- R2 fixed gate failure: `STOP_NO_ORDERED_HISTORY_VALIDATION`
- R2 pass: `PASS_L3_ORDERED_HISTORY_OBSERVATION_QUOTIENT`

## Claim ceiling

R4가 통과해도 “scalp EEG 관측 quotient에서 400 ms 순서정보가 100 ms 미래변화 예측에 추가된다”까지만 말한다. 이 결과는 무한차원 metric, 실제 edge strength, 자아·의식의 차원, hippocampal hash, 인구 일반화 또는 인과기전을 확인하지 않는다.
