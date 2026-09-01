# Stx3 보상상대 집단기하 분석계약 v1.2 사전결과 통계보정

Status: `ANALYSIS_CONTRACT_FROZEN_PRE_OUTCOME / BIOLOGICAL_ENDPOINT_NOT_YET_EVALUATED`

보정 계약 ID: `CE_NPF_ALT_BIO_STX3_REWARD_ALIGNMENT_XN_v1_2`

기준 계약 SHA-256: `13bf98597f63fbb397cf86b0aa29404999eeb509a3f3a09e17fb7603d6eb576a`

선행 v1.1 보정 SHA-256: `f7bf144585e19207a1289c85128c6b428a97433d3e355b7e389af0958911aa95`

고정일: 2026-09-02

이 문서는 생물 endpoint를 열기 전 최종 독립 구현감사에서 발견된 조건부
순열의 교환가능성, post-treatment cell 선택, trial identity, 기하 추정량 명칭,
결과 상태 우선순위 문제를 닫는다. v1과 v1.1의 나머지 정의는 그대로 유지한다.
이 보정 시점까지 `G`, `ΔG`, `B`, `ΔB`, 처치군 통계와 결합 통계는 계산하지
않았다.

## 1. 결합 연관의 nuisance-residual 순열

mouse별

\[
x=\operatorname{rank}(\Delta G),\qquad
y=\operatorname{rank}(\Delta B)
\]

를 만들고, primary와 `S_rate`에서는

\[
C=[\mathbf 1,I_{Cre}],
\]

`S_motor`에서는 여기에 `rank(Δspeed)`를 추가한다. Moore--Penrose 역행렬을
써서

\[
M=I-C(C^TC)^+C^T,
\qquad e_x=Mx,
\qquad e_y=My,
\qquad \hat y=(I-M)y
\]

로 둔다. 관측 통계는 `corr(e_x,e_y)`다.

귀무분포는 raw `y`를 섞지 않는다. seed `20260901`로 미리 만든 동일한
99,999개 처치군내 순열행렬 $P_b$를 세 variant에 재사용하되, reduced nuisance
model의 residual만 섞는 Freedman--Lane형 절차를 쓴다.

\[
y_b^*=\hat y+P_be_y,
\qquad e_{y,b}^*=My_b^*,
\qquad T_b=\operatorname{corr}(e_x,e_{y,b}^*).
\]

one-sided Monte Carlo p는 계속

\[
p=\frac{1+\#\{b:T_b\ge T_{obs}\}}{100000}
\]

이다. pseudo-response를 다시 rank 변환하지 않는다. residual norm이 0이거나
비유한이면 `STX3_NUMERICAL_BLOCKED`다. primary와 `S_rate`에서는 순열이
처치군 안에서만 일어나므로 이 정의가 기존 group-demeaned rank 순열과
대수적으로 같다.

이 검정은 reduced rank-linear nuisance model이 적절하고, 그 residual이 실제
처치군 안에서 교환가능하다는 조건부 가정에 의존한다. 이 가정을 생물학적
무작위화로 바꾸어 말하지 않는다.

## 2. ROI를 post-treatment 값으로 선별하지 않는 규칙

day0--day5 ROI aligner가 정한 ordered pair 전체를 mouse별 분석집합으로 한 번
고정한다. 이후 firing 값, endpoint 크기, residual variance 부호를 보고 cell을
버리지 않는다.

1. 모든 mapped ROI가 A/B fold의 좌·우 reward window 전체에서 day0과 day5
   finite endpoint를 가져야 한다. 하나라도 아니면 cell 삭제 대신
   `STX3_REGISTRATION_BLOCKED`다.
2. training row는 speed·lick과 **모든 고정 ROI**가 finite인 blocks 0--4의
   `trial × bin`만 남긴다. 세 행 미만이면 `STX3_NUMERICAL_BLOCKED`다.
3. category-demeaned residual variance가 0인 ROI도 버리지 않는다. 전체 variance가
   finite이고 양의 variance가 하나 이상일 때, v1.1의 median-based floor를 적용해
   diagonal precision을 만든다.
4. 고정 mapped ROI가 20개 미만이면 종전대로 `STX3_REGISTRATION_BLOCKED`다.

따라서 분석의 표적은 전체 CA1이 아니라 **두 날 모두 구조적으로 등록 가능하고
필수 표본이 완전한 ROI 집합**이다. Stx3가 등록 가능성 자체에 영향을 주지
않는다는 근거가 없으므로 이 선택집합 밖으로의 인과 일반화는 금지한다. mouse별
mapped ROI 수를 결과에 항상 보고한다.

## 3. trial identity와 기하 추정량의 지위

- v1의 대표 schema 파일명은 `scan0`로 적혔지만 고정된
  `schema_sample_audit.json`이 실제로 감사한 파일은
  `sub-Ctrl-2_ses-ymaze-day3-scan1-novel-arm1_behavior+ophys.nwb`다. 이 표기
  불일치는 schema 탐색 기록에만 해당하며, confirmatory 선택집합은 selection
  receipt에 고정된 day0/day5 `scan0` 32개 파일이다.
- 각 trial의 aligned 및 full-resolution `trial number` 구간은 각각 하나의 유한
  정수여야 하고 두 값이 정확히 같아야 한다. 완성 trial의 번호열은 시작값을
  임의로 허용하되 정확히 1씩 증가해야 한다. 어긋나면 trial ordinal로 대신
  맞추지 않고 `STX3_TRIAL_JOIN_BLOCKED`다.
- A/B는 arm 안의 시간순 trial을 `A,B,H`로 순환 배정한 결정론적 split이다.
  인접 trial 오차의 독립성 또는 교차 fold 무상관성이 설계로 보장되지 않으므로,
  계산되는 \(\delta_A^T W\delta_B/p\)를 이 자료에서 **불편 crossnobis**라고
  주장하지 않는다. 정식 명칭은 **A/B crossvalidated bilinear reward-alignment
  proxy**다.
- 이 proxy 하나는 출력 likelihood의 Fisher tensor도, 열린 이웃에서 추정한
  리만 metric field도, 물리적 시공간 metric도 아니다. 따라서 양성 결과는
  “Stx3 성분과 보상상대 집단표현 proxy의 연관”까지만 말할 수 있으며 뇌의
  리만기하 또는 시공간 접힘의 완전증명이 아니다.

## 4. 처치군 label 검정의 지위

9 Ctrl/7 Cre의 11,440개 label 열거와 p 계산식은 바꾸지 않는다. 그러나 원 연구가
동물의 Stx3 처치를 무작위 배정했다고 보고하지 않았고 wavelength와 batch가
완전히 교차하지 않으므로, 이 값은 실제 표본에서의 **조건부 label-exchangeability
reference p**다. 설계기반 randomization p 또는 Stx3의 인과효과 p가 아니다.
양성 상태도 최대 `L2` 동일동물 관찰 triad와 비무작위 기전조작 연관 성분이며,
`L3` 또는 통합 `L4`로 승격하지 않는다.

### 4.1 결과 상태의 우선순위

v1 §10.3과 §11의 `GLOBAL_RATE_OR_MOTOR_CONFOUND_COMPATIBLE_FAIL`은 민감도
분석의 **신경 `mean ΔG_Ctrl - mean ΔG_Cre <= 0`**에만 적용한다. 행동 또는 결합
연관의 방향 역전만으로 이 신경-confound 상태를 만들지 않는다.

1. primary conjunction이 실패하면 먼저 v1의
   `GEOMETRY_COMPONENT_ONLY` 또는 `COMPONENT_CONJUNCTION_NOT_SUPPORTED`를
   반환한다. 민감도 상태가 primary-null 상태를 덮어쓰지 않는다.
2. primary conjunction이 통과한 뒤에만 두 필수 sensitivity를 판정한다.
3. 그중 하나의 신경 방향이 0 또는 역전이면
   `GLOBAL_RATE_OR_MOTOR_CONFOUND_COMPATIBLE_FAIL`이다.
4. 두 신경 방향은 양수지만 sensitivity conjunction 하나라도 실패하면
   `PRIMARY_ONLY_CONFOUND_SENSITIVE_NO_EVIDENCE_ELEVATION`이다.
5. 세 variant conjunction이 모두 통과해야만 confound-robust supported다.

## 5. 실행 허가 게이트

- runner는 이 문서와 v1.1 문서의 SHA-256을 함께 확인해야 한다.
- 합성시험은 raw-rank 순열과 nuisance-residual 순열이 달라지는 speed-confounded
  fixture, 수동 Freedman--Lane 계산 일치, endpoint cell 삭제 대신 fail-closed,
  zero-variance ROI 보존, aligned/full trial-number 불일치 차단을 포함해야 한다.
- 갱신된 focused test 전부, 32-file preflight, download receipt, 실행환경과 모든
  source hash가 새 execution lock에 일치하기 전에는 one-shot을 허가하지 않는다.
