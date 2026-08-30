# CE-BRAIN Stage 7 X-미로 선택코드 R1 계약

Status: `PREREGISTERED / NEURAL_ENDPOINT_UNOPENED`

기준일: 2026-08-31

## 1. 목표와 주장 한계

현재 하위 목표는 CRCNS의 `trajectory memory` 미확립 뒤 매뉴얼이 지정한 **다른 memory code 탐색**이다.

주 질문:

> east sample endpoint를 떠나 west choice endpoint로 가는 동안, 중심에 도달하기 전 신경신호가 현재 위치·머리방향·속도·sample arm·직전 선택을 넘어 다음 west arm을 예측하는가?

통과해도 `선택 관련 신경코드 후보`까지만 말한다. NWB에 sample/rule/correct/reward trial table이 없으므로 match-to-sample 기억, 정답, retrieval, correction은 주장하지 않는다.

## 2. 자료 역할

- R1 development: BaggySweatpants, MEC 320 units, east→west 102 transition
- R2 fixed replication: Franklin, hippocampus+MEC 449 units, east→west 101 transition
- 두 파일은 행동 schema가 이미 열렸으므로 confirmation이 아니라 순차 development/replication이다.
- R1 코드·문턱을 결과 확인 뒤 바꾸지 않고 R2에 그대로 적용한다.

## 3. event와 시간 분할

1. 행동 event는 `CE_BRAIN_STAGE7_X미로_다른기억코드_장치계약.md`의 고정 추출기를 사용한다.
2. 각 east→west transition에서 정규화 x가 처음 0.5 이하가 되는 시점을 중심 통과로 둔다.
3. 신경·행동 feature 창은 중심 통과 `[-1.25, -0.25]`초다. 마지막 0.25초를 비워 즉시 팔 진입 운동 누출을 줄인다.
4. 시간순 60% train, 다음 20% validation, 마지막 20% test로 한 번 나눈다. Baggy는 61/20/21, Franklin은 60/20/21이다.
5. 각 split에 north/south가 각각 5개 미만이면 score 전 장치 중단한다.

## 4. feature와 경쟁 모델

### 행동 기준선 B

- sample endpoint의 north/south
- 직전 west choice의 north/south와 첫 시행 표시
- feature 창의 마지막 위치 x/y
- 창 내 평균 head direction의 sine/cosine
- 창 시작→끝의 x/y 속도
- 정규화된 session 진행도

### 신경 정적 모델 S

행동 B와 함께 1초 전체 unit spike count를 사용한다.

### 신경 시간모델 T

행동 B와 함께 0.25초 네 bin의 unit spike count를 순서대로 사용한다.

unit은 전체 session firing rate 0.05 Hz 이상, feature 창 중 nonzero event 비율 5% 이상만 train 정보로 선택한다. 모든 표준화와 PCA는 train에서만 적합한다. 신경 PCA 차원 `{5, 10, 20}`과 ridge penalty `{0.01, 0.1, 1, 10, 100}`는 validation log loss로 선택한다. 행동 B는 같은 penalty grid를 쓴다.

## 5. 주 평가와 문턱

test의 binary log loss를 주 지표로 하고 balanced accuracy를 보조 지표로 둔다.

R1에서 `선택 관련 시간코드 후보`가 되려면 모두 필요하다.

1. `T`가 `B`보다 test log loss를 5% 이상 개선
2. `T`가 `S`보다 test log loss를 3% 이상 개선
3. test balanced accuracy 0.60 이상
4. transition 단위 paired bootstrap 2,000회의 `T-B`, `T-S` 개선율 95% 하한이 모두 0 초과

`S>B`만 통과하면 static choice code로 기록하고 trajectory code라고 부르지 않는다. R1 미통과 시 R2는 강한 확인이 아니라 고정 분석기의 방향 복제로만 실행한다. 두 세션에서 같은 문턱을 통과해야 `replicated development candidate`가 된다.

## 6. 음성·누출 대조

- label permutation 200회에서 실제 `T` balanced accuracy가 95 percentile을 넘어야 한다.
- 신경 event 행을 한 transition씩 circular shift한 모델이 실제 정렬 T보다 나빠야 한다.
- 행동 B가 test에서 완전분리 또는 balanced accuracy 0.90 이상이면 신경 추가 이득은 과제 규칙/운동의 잔차로만 해석하고 기억코드 승격을 중단한다.

## 7. 결과별 다음 분기

- **T 통과, R2 반복:** 선택 관련 시간코드 후보. trial semantics를 가진 새 자료에서 memory-specific 확인 계약.
- **S만 통과:** 정적 선택상태 후보. trajectory memory 연결 폐기.
- **둘 다 미통과:** 현재 X-미로 분석기에서 다른 memory code 미확립. 의미가 있는 trial log 확보가 다음 최소 의무.
- **장치 중단:** 과학 음성으로 세지 않는다.
