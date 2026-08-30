# CE-BRAIN Human Memory R2 공식창 관계복원 계약

Status: `PREREGISTERED / NEW_DEVELOPMENT_ENDPOINTS_UNOPENED`

기준일: 2026-08-31

## 1. 목적과 변경 근거

R1 P19/P16은 `[0,1.0]`초 전체 old pair에서 관계복원을 확립하지 못했다. 후속 양성대조에서 공개 MATLAB 원코드가 `[0.2,1.7]`초·정답 trial·centered bootstrap으로 알려진 old/new 선택세포 8.75%를 재현한다는 것을 확인했다.

R2는 이미 본 사람을 재채점하지 않는다. 아직 관계 endpoint를 열지 않은 development subjects에 공식 기억신호 시간창을 **결과 전에** 적용한다.

## 2. enrollment

`CE_BRAIN_HUMAN_MEMORY_독립개체_분할계약.md` 순서에서 P19/P16과 양성대조 spike endpoint가 열린 13 subjects를 제외한다. 다음 순서로 완전 200-trial·unit 10개 이상 장치 문을 검사한다.

```text
P11HMH → P48CS → P32CS → P29HMH → P40CS → P27CS → P47CS → ...
```

첫 두 적격 subjects를 R2D1·R2D2로 고정한다. 각 subject는 exact-old 50, correct-old(response 34–36) 20개 이상, incorrect-old 5개 이상, correct-old의 각 visual category 2개 이상이어야 한다. 조건 미달은 score 전 장치 중단이다.

## 3. 표현

- old/new는 embedded image pixel SHA-256 identity로 정의한다.
- stimulus onset `+0.2~+1.7초`를 0.25초 여섯 bin으로 나눈다.
- 공식 방법처럼 baseline subtraction은 하지 않는다.
- 모든 schema units를 사용하되 전체 100 recognition trials에서 spike가 전혀 없는 unit만 제외한다.
- unit×bin을 learning 100개와 recognition 100개에서 각각 z-score한다.
- exact-old 50개의 encoding 벡터와 recognition 벡터를 연결한다.

## 4. 지표와 null

R1과 동일한 네 축을 사용한다.

1. correct-old 동일항목 cosine 대 visual-category 내부 recognition-pair shuffle 5,000회
2. correct-old encoding·recognition 항목 간 거리행렬 upper triangle Spearman 대 같은 shuffle
3. old 50개 pair cosine과 response code 31–36 Spearman, category 내부 confidence permutation
4. correct-old 대 incorrect-old pair cosine 차이, 독립 bootstrap 2,000회

시간순서 대조는 correct-old recognition의 여섯 bin을 역순으로 놓아 paired bootstrap 2,000회로 비교한다.

## 5. 문턱

`RELATIONAL_RETRIEVAL_R2_DEVELOPMENT_CANDIDATE`에는 모두 필요하다.

- matched cosine 이득 ≥0.05, `p≤0.01`
- 거리행렬 `rho≥0.20`, `p≤0.01`
- confidence `rho≥0.20`, `p≤0.01`
- correct–incorrect cosine ≥0.05, 95% CI 하한 >0

여기에 correct-time-order 이득 ≥0.03, CI 하한 >0이면 `TEMPORAL_RELATIONAL_RETRIEVAL_R2_DEVELOPMENT_CANDIDATE`다.

R2D1·R2D2가 모두 관계 후보 이상으로 통과해야 calibration을 열 수 있다. 하나라도 미통과하면 `HUMAN_RELATIONAL_RETRIEVAL_R2_NOT_ESTABLISHED`로 닫고 confirmation은 계속 봉인한다.

## 6. 주장 한계

R2가 통과해도 development 후보일 뿐이다. memory capacity, correction, chemical gating, Phase 14 인간 확인으로 승격하지 않는다.
