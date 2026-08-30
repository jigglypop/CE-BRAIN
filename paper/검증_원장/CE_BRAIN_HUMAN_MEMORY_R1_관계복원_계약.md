# CE-BRAIN Human Memory R1 관계복원 계약

Status: `PREREGISTERED / SPIKE_ENDPOINT_UNOPENED`

기준일: 2026-08-31

## 1. 질문과 위치

긴 로드맵 Phase 8의 핵심 문장인 “기억은 좌표를 복제하는 것이 아니라 관계 구조를 복원한다”를 인간 단일 development session에서 시험한다. 동물 Stage 7을 통과시키는 대체물이 아니며 Phase 14 confirmation도 아니다.

질문:

> 학습 때의 항목별 신경관계가 나중 인식 때 보존되며, 그 보존 정도가 실제 기억 응답과 연결되는가?

같은 이미지는 시각 자극 자체 때문에 비슷한 신경반응을 만들 수 있다. 따라서 동일항목 유사도만으로 통과시키지 않고 기억 confidence 및 remembered/forgotten 차이를 함께 요구한다.

## 2. 입력과 의미 고정

- 입력·해시는 `CE_BRAIN_HUMAN_MEMORY_DANDI000004_장치감사.md`를 따른다.
- old는 metadata 숫자가 아니라 학습 이미지와 embedded pixel SHA-256이 같은 인식 trial로 정의한다.
- response 34–36은 `old` 응답(guess/probably/confident), 31–33은 `new` 응답으로 정의한다.
- exact-old 50개 중 response 34–36은 remembered, 31–33은 forgotten이다. score 전 집계는 40/10이다.

## 3. 신경 표현

1. 각 trial의 stimulus onset 전 `[-0.5, 0]`초를 baseline으로 둔다.
2. onset 뒤 `[0, 1.0]`초를 0.25초 네 bin으로 나눈다.
3. 각 unit/bin의 firing rate에서 해당 trial baseline rate를 뺀다.
4. 전체 session rate 0.05 Hz 이상이고 학습+인식 response 창의 5% 이상에서 spike가 있는 unit만 사용한다.
5. 느린 phase drift를 제거하기 위해 unit×bin별로 learning 100개와 recognition 100개 안에서 각각 z-score한다.
6. 4 bin × eligible units를 한 항목의 시간표현 벡터로 둔다.

## 4. 주 통계

### A. 동일항목 pair 보존

remembered 40개에서 encoding 벡터와 같은 이미지 recognition 벡터의 cosine 유사도를 계산한다. recognition 항목을 category 안에서 섞은 5,000회 null과 비교한다.

### B. 관계기하 보존

remembered 항목 사이 encoding 거리행렬과 recognition 거리행렬의 upper triangle Spearman 상관을 계산한다. recognition 항목을 category 안에서 섞은 5,000회 null과 비교한다.

### C. 기억행동 연결

- 50 old 항목에서 pair cosine과 response confidence code 31–36의 Spearman 상관
- remembered 40개와 forgotten 10개의 pair cosine 평균 차이 및 2,000회 bootstrap 95% CI

confidence permutation은 category 안에서 하고, remembered–forgotten bootstrap은 두 집단에서 독립 복원한다.

### D. 시간순서 대조

remembered pair에서 올바른 네 bin 순서의 cosine과 recognition bin을 역순으로 둔 cosine의 항목별 차이를 비교한다. 2,000회 paired bootstrap CI를 사용한다.

## 5. 통과 조건

`RELATIONAL_RETRIEVAL_DEVELOPMENT_CANDIDATE`에는 모두 필요하다.

1. remembered matched cosine이 category-shuffle 평균보다 0.05 이상 높고 one-sided permutation `p≤0.01`
2. encoding–recognition 거리행렬 상관 `rho≥0.20`, `p≤0.01`
3. confidence 상관 `rho≥0.20`, `p≤0.01`
4. remembered–forgotten cosine 차이 0.05 이상이고 bootstrap 95% 하한 >0

위 네 조건에 더해 correct-order가 reversed-order보다 0.03 이상 높고 bootstrap 하한 >0이면 `TEMPORAL_RELATIONAL_RETRIEVAL_DEVELOPMENT_CANDIDATE`다. 시간순서만 실패하면 관계상태 후보까지만 말한다.

어느 하나라도 실패하면 `HUMAN_RELATIONAL_RETRIEVAL_NOT_ESTABLISHED`다. 한 사람 결과이므로 통과해도 독립 subject 확인 전 일반화하지 않는다.

## 6. 금지 주장

- exact-image 유사도만으로 기억을 주장하지 않는다.
- 이 결과로 동물 trajectory memory 실패를 뒤집지 않는다.
- correction, capacity, chemical gating, 인간 최종확증으로 승격하지 않는다.
