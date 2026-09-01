<!-- 도메인: ce-brain-bio -->

# CE-NPF 성체 L4 리만접힘 실험계약 v1

Status: `SUPERSEDED_DO_NOT_FREEZE / EXECUTION_NOT_AUTHORIZED / BIO_EVIDENCE_L0`

> 독립감사에서 actuator--state 혼동, 비불변 fold, 비선택적 mediator controller,
> same-contact rescue 부재, power·ITT 모순과 validator 결박 실패가 확인되어 이 판본은
> 동결하지 않는다. 후속 후보는
> [`v2`](CE_NPF_ADULT_L4_리만접힘_실험계약_v2.md)다. 이 표시는 v1의 과거 내용을
> 유효한 실행계약으로 되살리지 않기 위한 폐기 표지다.

계약 작성일: 2026-09-02

정본 규약:
[`실제 뇌 식 기반 발견 루프`](../../.codex/harnesses/real_brain_equation_discovery_loop.md),
[`뇌 생물학 증거 사다리`](../../.codex/harnesses/brain_evidence_ladder.md),
[`성체 최소증거 재설정`](성체_리만접힘_최소증거_재설정.md).

기계 판본:
[`adult_l4_riemann_fold_contract_v1.json`](../6_뇌/국소회로_상태다양체_흐름_대응/repro/adult_l4_riemann_fold_contract_v1.json).

이 문서는 실제 동물실험의 과학 계약이다. 기관 동물실험 승인, 장비 접근,
바이러스·광학 안전검증과 책임 연구자의 서명이 없으므로 **실행을 허가하지
않는다**. 계약·검증기 준비는 생물 endpoint가 아니며 현재 등급은 L0다.

## 0. 목표 정렬

- **최종 목표:** 성체 M1의 동일동물·동일세포·동일 spine 집합에서 시냅스 효능
  변화가 독립 output-likelihood Fisher 계량을 변형하고 별도 운동행동을 매개하는지
  판정한다.
- **이번 하위 목표:** 결과를 보기 전에 생물측정, 두 단계 무작위 개입, raw Fisher,
  인과 estimand, 표본수와 모든 STOP 조건을 실행 가능한 한 계약으로 고정한다.
- **필요한 이유:** 기존 공개자료는 각 구성요소만 보여 주며
  $\Delta\Theta\to\Delta g\to\Delta Y$를 같은 preparation에서 닫지 못한다.
- **목표 이탈 방지:** 청소년기·발달 고정, 물리적 Lorentz 시공간, 해부학적 피질
  주름, AGI 성능은 이 계약의 endpoint가 아니다.
- **다음 gate:** §4의 장치통합 cohort가 endpoint를 보지 않고 전부 통과하고 기관
  승인·책임자 서명이 있어야 confirmation randomization을 열 수 있다.

## 1. 현재 생물학적 근거와 새 통합의 경계

| 모듈 | 실제 1차 자료 | 이 계약에 주는 것 | 주지 않는 것 |
|---|---|---|---|
| 과제 관련 spine 선택·삭제·행동 | Hayashi-Takagi et al. 2015, M1 L2/3의 AS-PaRac1 표지 spine 광축소가 획득한 운동과제를 선택적으로 손상시킴: [Nature](https://doi.org/10.1038/nature15257), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4634641/) | 성체 M1, task-tagged spine, 표적·비표적 행동 대조 | 독립 Fisher field와 mediator 개입 |
| 동일 spine 기능·구조 종단 | Rais & Wiegert 2026, 성체 awake CA3→CA1, 929 spines·17 dendrites·5 mice를 16일 추적: [Nature Communications](https://doi.org/10.1038/s41467-026-71332-z) | 반복 EPSCaT·구조 identity의 현실성 | M1 행동·계량·개입 |
| 동일세포 spine 입력과 학습 전후 가중치 | Gonzalez et al. 2025, CA1 12 cells/8 mice·484 spines, control 11 cells/6 mice·370 spines: [Nature](https://doi.org/10.1038/s41586-024-08325-9), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11988941/) | 동일세포 spine input과 유도 전후 광학 기능측정 | 무작위·맹검, 별도 행동 매개 |
| 고정 입력-grid·직접 postsynaptic current | Chen et al. 2025, V1 L2/3의 41 connections/12 mice, 최대 100 presynaptic cells를 약 5분에 탐색: [Nature Neuroscience](https://doi.org/10.1038/s41593-025-02024-y) | 2P holography와 evoked EPSC calibration | awake 종단·행동·Fisher |
| awake 직접 voltage plasticity | Carolan et al. 2025, Purkinje dendrite의 440 Hz GEVI와 입력자극, plasticity 32 cells/4 mice: [Nature Communications](https://doi.org/10.1038/s41467-025-63867-4) | subthreshold voltage efficacy readout | 단일 spine·M1 행동·매개 |
| 성체 M1 조작·행동·구제 선례 | Lai et al. 2025, motor learning 중 spine/dendrite activity와 astrocyte·adenosine 조작: [Nature Neuroscience](https://doi.org/10.1038/s41593-025-02072-4) | 기전 조작, 행동, 부분 rescue의 현실성 | 같은 세포의 독립 계량 rescue |

어느 논문도 이 계약의 통합 사슬을 이미 지지하지 않는다. 이 표는 서로 다른
기술을 한 장치에 통합할 수 있다는 **설계 근거**일 뿐 L4 합성증거가 아니다.

## 2. 좁은 주장과 반증 대상

### 2.1 primary 주장

성체 mouse hindlimb M1 L2/3 pyramidal ensemble에서 과제 A 학습으로 강화된
spine 집합의 기능 효능 $\Theta$를 선택적으로 약화하면, 고정된 2차원 입력 probe에
대한 별도 follower-cell output likelihood의 raw Fisher metric $g$가 사전 방향으로
변형되고 과제 A 행동이 손상된다. $\Theta$를 회복하지 않은 채 output causal state를
복원하면 $g$와 행동이 함께 부분 회복되고, 같은 $\Theta$를 다시 회복하면 두 endpoint가
재회복된다.

이는 명시한 preparation에 한정한 인과 주장이다. 모든 뇌, 모든 기억, 물리적
시공간 또는 신호지연 일반론으로 승격하지 않는다.

### 2.2 경쟁 설명

1. `R0_NO_METRIC`: spine 약화는 행동을 바꾸지만 output Fisher field는 바꾸지 않는다.
2. `R1_DIRECT_ONLY`: $\Theta$와 행동은 변하지만 $g$는 행동 mediator가 아니다.
3. `R2_FINSler`: 방향비대칭 때문에 단일 Riemann tensor보다 Finsler/Randers가 낫다.
4. `R3_STRATIFIED`: rank·support가 바뀌어 하나의 열린 Riemann patch가 아니다.
5. `R4_STIMULATION_DIRECT`: causal-state controller의 행동효과는 metric 복원이 아니라
   빛·발화·각성의 직접효과다.

## 3. preparation과 측정모형

### 3.1 생물단위

- 종·연령: C57BL/6J background, 암수 균형, 첫 baseline 12–20주.
- 영역·세포: hindlimb M1 L2/3 pyramidal neurons와 같은 FOV의 follower ensemble.
- 행동: head-fixed 두 개의 구별되는 lever-sequence 과제 A/B. A가 primary이고 B는
  task-specific off-target 대조다.
- primary 독립단위: animal. spine·cell·trial을 animal 수로 세지 않는다.
- identity: animal→FOV→cell→dendrite→spine의 고정키와 blinded registration.

### 3.2 세 개의 독립 채널

1. `THETA_CHANNEL`: AS-PaRac1 task tag, spine morphology와 고정 upstream probe에
   대한 spine-local postsynaptic voltage transient. 구조만으로 효능을 대신하지 않는다.
2. `OUTPUT_CHANNEL`: 조작 spine 신호를 제외한 동일 FOV follower somatic
   voltage/spike vector $O$; 최소 8개 안정 세포가 필요하다.
3. `BEHAVIOR_CHANNEL`: probe light가 없는 블록의 lever trajectory·sequence success.

세 채널의 raw sensor, ROI와 전처리는 분리한다. 행동값을 $g$ 정의나 controller
training loss에 넣지 않는다.

### 3.3 고정 입력 chart

무차원 좌표 $z=(z_1,z_2)\in[-1,1]^2$를 사용한다. $z_1$은 과제 A와 연결된
사전등록 upstream ensemble의 자극 진폭, $z_2$는 총 광에너지·세포수·공간범위를
맞춘 과제 B/직교 ensemble 진폭이다. 5×5 grid의 각 점에서 세션당 48회 probe를
무작위 순서로 제시하고 24회는 animal calibration, 24회는 봉인 holdout으로 쓴다.
probe는 학습을 유도하지 않는다는 pilot 기준을 먼저 통과해야 한다.

관측모형은

$$
p_\eta(O\mid z,h,c)
=\exp\{\eta(z,h,c)^\top T(O)-A(\eta)\}
$$

형태의 고정 multivariate point-process/exponential-family likelihood다. 구조와
regularization은 development cohort에서만 선택하고 confirmation 전에 hash로 잠근다.

## 4. 장치통합 cohort — 가설결과가 아닌 선행 gate

12마리 이하의 별도 development cohort에서 다음만 판정한다. 효과 방향·행동효과·
primary 임계는 보지 않으며 confirmation 표본에 합치지 않는다.

| gate | PASS | STOP |
|---|---|---|
| 광학 독립성 | 각 채널 cross-talk가 signal SD의 5% 미만, opsin-free light control에서 evoked response 없음 | `SPECTRAL_CROSSTALK_STOP` |
| 광독성 | 세션 전후 baseline voltage·spine survival의 사전 equivalence ±10% | `PHOTOTOXICITY_STOP` |
| 종단 identity | cell ≥90%, task-tagged spine ≥80%를 전 세션 blinded 재등록 | `IDENTITY_STOP` |
| probe 비가소성 | probe-only 전후 $\Theta$와 행동의 equivalence ±10% | `PROBE_PLASTICITY_STOP` |
| 직접 효능 calibration | spine voltage readout과 동시/인접 whole-cell EPSP calibration의 animal-heldout $R^2\ge0.50$ | `THETA_PROXY_STOP` |
| likelihood | holdout calibration, common support와 2D raw-rank 가능성 | `OUTPUT_MODEL_STOP` |
| controller 특이성 | restore와 energy-matched orthogonal state가 분리되고 direct motor endpoint equivalence 통과 | `CONTROLLER_SPECIFICITY_STOP` |

하나라도 실패하면 confirmation을 열지 않는다. 센서·파장·세포형을 바꾸려면 v2
계약이며 이 cohort의 결과를 confirmation으로 재사용하지 않는다.

## 5. confirmation 설계와 표본수

### 5.1 두 단계 무작위화

동물은 sex·litter·surgery batch로 층화해 1:1:1 배정한다.

| arm | $Z_\Theta$ | 목적 |
|---|---|---|
| `TARGET_A` | 과제 A tag spine의 AS-PaRac1 photoactivation | 주 mechanism 개입 |
| `SHAM` | photoactivation-incompetent probe와 동일 빛 | 수술·발현·빛 대조 |
| `OFFTARGET_B` | 동일 동물이 학습한 과제 B tag spine을 같은 수·에너지로 photoactivation | task·spine specificity 대조 |

그 뒤 각 동물은 `STATE_OFF`, `STATE_RESTORE`, `STATE_ORTHOGONAL` controller
세션을 Latin-square 순서로 경험한다. controller는 development cohort에서 고정한
output target만 사용하며, `STATE_RESTORE`는 sham post-learning $p(O\mid z)$를,
`STATE_ORTHOGONAL`은 같은 광량·발화수로 그 접공간의 직교 mode를 겨냥한다.

### 5.2 표본수

- confirmation evaluable N = 28/arm, 총 84 animals.
- 최대 등록 N = 35/arm, 총 105. outcome을 보지 않은 사전 제외만 대체한다.
- one-sided $\alpha=0.05$, standardized SESOI $d=0.8$의 두 독립군 t 근사에서
  N=28/arm은 power 0.9050이다.
- `TARGET_A` 안의 controller paired SESOI $d_z=0.6$에서 N=28은 power 0.9263이다.
- primary는 모든 화살표의 conjunction인 intersection--union test다. 각 필요조건
  $\alpha=0.05$를 통과해야 하므로 한 endpoint 양성으로 전체를 구제하지 않는다.

효과크기는 과거 논문에서 가져온 추정치가 아니라 “그보다 작으면 L4 기전 주장에
충분하지 않다”는 설계 상수다. 더 작은 실제 효과는 유의하더라도 primary PASS가 아니다.

### 5.3 결측·제외

randomization 전 QC 제외만 허용한다. randomization 뒤 animal은 ITT에 남기며,
등록 소실·sensor failure를 outcome에 따라 제외하지 않는다. primary endpoint의
post-randomization 결측이 arm별 10%를 넘거나 differential missingness가 10%p를
넘으면 `MISSINGNESS_STOP`이다. spine/cell 수가 많아도 animal 결측을 대신하지 않는다.

## 6. raw Fisher와 접힘 요약

출력 score와 Fisher는

$$
s_a(O;z)=\partial_{z^a}\log p_\eta(O\mid z,h,c),
\qquad
g_{ab}(z)=\mathbb E[s_a s_b\mid z,h,c]
$$

로 정의한다. ridge를 더한 working metric은 계산 안정화용으로 별도 보고하지만
Riemann PASS에는 **raw $g$만** 쓴다.

`RAW_RIEMANN_PASS`는 중앙 3×3을 포함한 연결 patch에서 다음을 모두 요구한다.

1. common-support probability floor 0.01.
2. simultaneous 95% lower bound $\lambda_{\min}(g)\ge0.02$.
3. condition number $\kappa(g)\le50$인 grid point가 90% 이상.
4. 사전등록 두 좌표변환에서 $g'=J^TgJ$의 relative Frobenius error ≤0.10.
5. Finsler 방향항의 held-out ELPD 이득 <0.01 nat/trial.
6. rank/support-change 또는 discrete graph 대안이 사전 margin으로 우세하지 않음.

하나라도 실패하면 `RAW_FISHER_NOT_RIEMANN`이며 regularization으로 구제하지 않는다.

pre/post 정렬계량의 strain을

$$
E(z)=\frac12\log\!\left[g_{\rm pre}(z)^{-1/2}
g_{\rm post}(z)g_{\rm pre}(z)^{-1/2}\right]
$$

로 두고, 사전 고정한 chart 축 $u_A=(1,0)^T$, $u_B=(0,1)^T$에 대해

$$
m^g=\frac1{|P|}\sum_{z\in P}
\{u_A^TE(z)u_A-u_B^TE(z)u_B\}
$$

를 유일한 primary fold summary로 쓴다. 이는 task-axis 대비 orthogonal-axis의
상대 stretch이고 해부학적 접힘이나 물리 시공간 곡률이 아니다.

## 7. 인과 DAG와 estimand

주 DAG는

$$
Z_\Theta\to\Theta\to m^g\to Y,
\qquad \Theta\to Y,
\qquad Z_m\to m^g\to Y,
\qquad Z_m\to Y
$$

다. 마지막 직접경로는 없다고 선결하지 않고 대조한다. tensor field 자체의
`do(g)`는 쓰지 않는다. $Z_m$은 development에서 검증한 controller로 유한차원
causal state $m^g=s_{\rm pre}(g)$의 분포를 바꾸는 개입이다.

| ID | animal-level estimand | 사전 방향·SESOI |
|---|---|---|
| `E_THETA` | TARGET_A 대 SHAM·OFFTARGET_B의 task-tagged $\Delta\Theta$ | 각각 ≤ −0.8 SD, 직접효능 20% 이상 감소 |
| `E_METRIC` | 같은 두 대비의 $\Delta m^g$ | 각각 ≤ −0.8 SD |
| `E_BEHAVIOR` | probe-free task-A success/trajectory composite의 변화 | 각각 ≤ −0.8 SD; task B와 locomotion은 equivalence ±0.2 SD |
| `E_STATE` | TARGET_A에서 RESTORE 대 ORTHOGONAL의 $m^g$와 $Y$ paired 효과 | 각각 ≥ +0.6 SD, $\Theta$는 equivalence ±10% |
| `E_DIRECT` | $m^g$가 같은 범위로 clamp됐을 때 TARGET_A 대 SHAM의 잔여 행동효과 | equivalence ±0.2 SD |
| `E_UPSTREAM_RESCUE` | 같은 tagged pathway의 사전등록 re-potentiation 뒤 $\Theta,m^g,Y$ | 세 양 모두 baseline equivalence ±10% 또는 예측방향 회복 |

모형은 animal random intercept를 갖되 primary contrast는 animal-level summary에서
재현한다. cell·spine bootstrap은 불확도 분해용이고 animal permutation을 대신하지
않는다.

## 8. L4 PASS의 conjunction

다음 열 개가 모두 PASS일 때만 명시한 preparation에서
`BIO_EVIDENCE_L4_PREPARATION_SPECIFIC_SUPPORT`를 허용한다.

1. `G0_SOURCE_LOCK`: construct·protocol·analysis hash와 기관 승인.
2. `G1_APPARATUS`: §4의 7개 장치 gate 전부.
3. `G2_IDENTITY`: confirmation의 animal/cell/spine identity와 결측 gate.
4. `G3_THETA_FIDELITY`: `E_THETA`, spatial specificity, sham/off-target.
5. `G4_RAW_RIEMANN`: §6의 raw field와 경쟁기하.
6. `G5_MICRO_TO_METRIC`: `E_METRIC`이 두 대조 모두 SESOI를 넘음.
7. `G6_METRIC_TO_BEHAVIOR`: `E_BEHAVIOR`와 task-specific negative endpoints.
8. `G7_MEDIATOR_STATE`: `E_STATE`, $\Theta$ 불변, orthogonal/light direct-path 대조.
9. `G8_SELECTIVE_RESCUE`: `E_UPSTREAM_RESCUE`와 `E_DIRECT`.
10. `G9_HOLDOUT_ASSUMPTIONS`: frozen animal-independent development, confirmation
    holdout, positivity·consistency·confounding·exclusion audit.

양성 p-value만으로는 PASS가 아니다. 방향, SESOI, confidence bound, 조작 충실도,
negative control과 raw metric gate가 모두 필요하다.

## 9. fail-closed 판정

| 상태 | 의미 | 다음 허용 행동 |
|---|---|---|
| `APPARATUS_INTEGRATION_STOP` | §4 실패 | endpoint를 열지 않고 한 구조만 바꾼 v2 |
| `ENDPOINT_NOT_EVALUATED` | 승인·identity·입력 부족 | 생물 양성/음성 금지 |
| `RAW_FISHER_NOT_RIEMANN` | rank/support/SPD/경쟁기하 실패 | Riemann 주장 기각; Finsler/stratified 별도 계약 |
| `MICRO_TO_METRIC_NOT_SUPPORTED` | $\Theta$는 움직였으나 $m^g$가 안 움직임 | 접힘 bridge 비지지 |
| `METRIC_BEHAVIOR_MEDIATION_NOT_SUPPORTED` | metric·행동 또는 state-rescue 사슬 실패 | 상관·직접효과로 축소, L4 금지 |
| `INTERVENTION_EXCLUSION_FAILED` | orthogonal/light/각성 직접경로 대조 실패 | mediator 해석 금지 |
| `RESCUE_NOT_SUPPORTED` | state 또는 upstream rescue 실패 | L4 금지 |
| `CONFIRMATION_NOT_REPRODUCED` | frozen confirmation 방향·SESOI 실패 | 개발 양성으로 구제 금지 |

어떤 상태에서도 “물리적 시공간 접힘이 증명됐다”는 문장을 허용하지 않는다.

## 10. timing/전도속도 arm의 분리

이 v1의 직접 미시변수는 contact efficacy다. 전도속도·지연은 같은 결과에 합치지
않는다. 후속 timing 계약은 같은 identified axon의 3D path length, 두 지점 직접
evoked latency, release/receptor delay 분리, 선택적 myelin/node 또는 excitability
개입과 timing-only rescue를 요구한다. myelin morphology를 속도로 대체하거나
directed latency를 Riemann distance로 쓰지 않는다. timing arm은 v1을 구제하지
않으며, v1과 timing arm이 각각 통과해야만 연결·효능·속도의 복수 기전 일반화를
논의할 수 있다.

## 11. 실행 전 남은 외부 의존성

1. IACUC/기관 승인과 책임 연구자 서명.
2. AS-PaRac1·GEVI·red-shifted opsin의 construct/license·spectral bench 확인.
3. adult M1 chronic window, holography, ≥8-cell high-speed voltage readout 장비.
4. blinded registration과 동물수용량을 감당할 독립 분석팀.
5. development 종료 뒤 고정된 likelihood·controller·분석 코드 hash.

이 다섯 항목이 없으므로 현 상태는 `EXECUTION_NOT_AUTHORIZED`다. 이는 가설의
실패가 아니라 실물실험 선행조건이다.
