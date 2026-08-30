# CE-BRAIN Human Memory R1 관계복원 결과

Status: `HUMAN_RELATIONAL_RETRIEVAL_NOT_ESTABLISHED`

기준일: 2026-08-31

## 판정

DANDI 000004의 한 인간 development session에서 exact-image encoding–recognition 50쌍을 구성했다. 15 units 중 14개가 사전 firing/coverage 문턱을 통과했다. 정확히 `old`라고 답한 remembered 40개와 `new`라고 답한 forgotten 10개를 분리했다.

사전 등록한 네 개의 관계복원 문턱 중 어느 것도 통과하지 못했다. 정본 판정은 `HUMAN_RELATIONAL_RETRIEVAL_NOT_ESTABLISHED`다.

## 수치

| 지표 | 결과 | 문턱 | 판정 |
|---|---:|---:|---|
| remembered 동일항목 cosine | 0.03662 | - | - |
| category-shuffle 평균 | 0.02732 | - | - |
| 동일항목 이득 | 0.00930, p=0.3485 | ≥0.05, p≤0.01 | 실패 |
| encoding–recognition 관계거리 Spearman | 0.06376, p=0.2935 | rho≥0.20, p≤0.01 | 실패 |
| pair cosine–confidence Spearman | -0.17789, p=0.9722 | rho≥0.20, p≤0.01 | 실패 |
| remembered–forgotten cosine | -0.07684, 95% CI [-0.20067, 0.04990] | ≥0.05, 하한>0 | 실패 |
| 올바른 시간순서–역순 | 0.03423, 95% CI [-0.02729, 0.09420] | ≥0.03, 하한>0 | 실패 |

## 쉬운 해석

사람이 나중에 같은 그림을 봤을 때 뇌 반응이 학습 때와 아주 조금 비슷해 보였지만, 같은 그림 범주 안에서 짝을 바꿔도 그 정도 차이는 흔히 나왔다. 학습 때 항목들 사이의 “거리 지도”도 인식 때 재현되지 않았다. 잘 기억했다고 답한 그림에서 이 유사성이 더 크지도 않았다.

따라서 이 세션에서는 “기억이 관계 구조를 복원한다”고 말할 수 없다. 반대로 인간 기억 전체에 그런 구조가 없다고 결론낼 수도 없다. 한 사람의 amygdala 계열 14 units로 제한된 개발 결과이기 때문이다.

## 계보 영향

- 동물 Stage 7 trajectory memory 미확립을 구제하지 않는다.
- 긴 로드맵 Phase 8 retrieval은 계속 미확립이다.
- Phase 9 capacity와 Phase 10 correction은 계속 미허가다.
- Phase 14 인간 confirmation은 시작된 것으로 세지 않는다.

## 다음 최소 증명 의무

동일 계약을 다른 subject/영역에 적용하기 전에 subject·unit coverage를 outcome-blind하게 목록화하고 development/calibration/confirmation으로 나눈다. 단일 세션의 음성을 보고 시간창이나 문턱을 바꾸지 않는다.

## 고정 분석기 P16 독립 development 복제

전체 59 subjects를 outcome-blind hash 분할한 뒤, 다음 unopened development subject P16HMH를 고정했다. P19에서 사용한 feature·시간창·null·문턱을 바꾸지 않았다.

| 지표 | P16 결과 | 문턱 | 판정 |
|---|---:|---:|---|
| 유효 units / old pairs | 21 / 50 | ≥10 / 50 | 장치 통과 |
| remembered / forgotten | 28 / 22 | - | - |
| 동일항목 cosine 이득 | 0.02321, p=0.1704 | ≥0.05, p≤0.01 | 실패 |
| 관계거리 Spearman | -0.02231, p=0.1332 | rho≥0.20, p≤0.01 | 실패 |
| confidence Spearman | 0.30991, p=0.0888 | rho≥0.20, p≤0.01 | p 실패 |
| remembered–forgotten | 0.10164, 95% CI [0.01784, 0.18212] | ≥0.05, 하한>0 | 통과 |
| 시간순서–역순 | 0.02805, 95% CI [-0.06125, 0.11491] | ≥0.03, 하한>0 | 실패 |

P16에서는 기억 응답과 연결된 평균 차이 하나는 통과했지만, 동일항목 보존과 관계거리 복원은 통과하지 못했다. 부분 신호 하나로 주 판정을 뒤집지 않는다.

**[복제 판정]** `HUMAN_RELATIONAL_RETRIEVAL_NOT_ESTABLISHED_REPLICATED`.

P19와 P16 두 development subjects에서 관계복원이 미확립이므로 calibration 14명과 confirmation 9명은 열지 않는다. 다음 허용 행동은 이 고정 선형/시간-bin 표현을 계속 구제하는 것이 아니라, 다른 사전등록 표현 family 또는 별도 데이터 family를 개발자료에서 경쟁시키는 것이다.

실행 코드: `examples/brain/ce_brain_human_memory_relational.py`

검증: `tests/test_ce_brain_human_memory_relational.py`
