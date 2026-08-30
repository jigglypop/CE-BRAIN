# CE-BRAIN Stage 8 DANDI 001371 빠른 교정 R1 계약

Status: `PREREGISTERED / OUTCOME_BLIND`

기준일: 2026-08-31

## 질문

> delay-only trial에서 읽힌 목표 선택축이 switch trial에서는 새 단서 뒤 실제 새 목표 쪽으로 이동하며, 같은 시각 단서가 있지만 목표를 유지하는 stay trial보다 변화량이 큰가?

이 질문은 `다른 memory code 탐색`과 within-trial correction에 직결된다. 장기적인 `v_C`나 READ/WRITE 분리는 아직 묻지 않는다.

## 고정 자료

- development 1: S34-220623
- development replication: S25-210916
- region: CA1, PFC를 분리 분석
- quality가 `good`인 unit만 사용
- `maze_id=4`, duration이 세션 평균의 2배 이하인 trial
- 주 분석은 correct trial; incorrect switch는 방향성 보조대조

## 고정 표현과 시간창

1. 실제 switch trial의 `t_update`에서 `t_choice_made`까지의 세션 중앙값을 `L`로 둔다.
2. delay-only trial의 pseudo-update는 `t_choice_made-L`로 정한다. 이는 neural endpoint를 사용하지 않는다.
3. pre window: 정렬점 기준 `[-1.0,-0.2] s`.
4. post window: `[+0.2,+1.0] s`.
5. 각 unit firing rate에 `log1p`를 적용하고, delay-only train trial의 평균·표준편차로 표준화한다.
6. 목표축 `v_R`은 delay-only correct train trial의 right-minus-left 평균차로 고정한다.

## 검증과 endpoint

- delay-only trial을 시간순 70/30 train/test로 나눈다.
- 장치 양성대조: held-out 목표축 분류 balanced accuracy가 0.60 이상이고 label permutation `p<0.01`.
- 각 switch/stay trial의 pre·post population vector를 `v_R`에 투영하고, 실제 최종 목표가 양수가 되도록 부호 정렬한다.
- 주 endpoint: `DID = mean(post-pre | switch correct) - mean(post-pre | stay correct)`.
- trial-label permutation은 final choice와 시간 절반 strata 안에서 2,000회 수행한다.
- PFC에서 DID>0, permutation `p<0.01`, bootstrap 95% 하한>0을 모두 요구한다.
- CA1은 사전 지정 replication endpoint이며 같은 세 문턱을 별도로 적용한다.
- S34와 S25 둘 다 PFC 문턱을 통과해야 `RAPID_CORRECTION_CODE_ESTABLISHED_REPLICATED`로 한다.

## 실패와 claim ceiling

- 양성대조 실패: `CHOICE_AXIS_SENSITIVITY_NOT_ESTABLISHED`, correction score 금지
- 한 세션만 통과: `RAPID_CORRECTION_CODE_NOT_REPLICATED`
- 둘 다 미통과: `RAPID_CORRECTION_CODE_NOT_ESTABLISHED`
- 어떤 결과도 장기 correction 방향 `v_C`, 지속 geometry 변화, READ/WRITE 분리로 승격하지 않는다.
