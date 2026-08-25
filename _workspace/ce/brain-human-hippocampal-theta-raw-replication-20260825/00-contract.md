# BA-OBS-HPC1 연구 계약 — 실제 인간 해마 폐루프 자극의 raw-derived 재현

Status: COMPLETE

PREDECESSOR:

- brain-human-ccep-restricted-active-response-20260824 (BA-OBS-ID3): 단일 피험자
  CCEP magnitude reciprocity proxy가 clinical/A-CAR와 local bipolar 사이에서
  REFERENCE_SENSITIVE_OR_INCONCLUSIVE였다. 이번 run의 reference 강건성 게이트를
  동기화하지만 그 endpoint나 split은 재사용하지 않는다.
- brain-human-ccep-multisubject-precision-retry-20260825 (BA-OBS-DISC2R): 74명
  human SPES CCEP에서 단순 유클리드 거리 감쇠의 제한된 held-out 예측 이득을 확인했다.
  이번 run은 독립 dataset과 다른 intervention/endpoint를 사용한다.
- brain-human-ccep-reference-robust-replication-20260825: source-admission 단계에서
  ds004457을 조사했지만 voltage endpoint는 열지 않았다. MEF3 reader 장벽과 인과
  대조의 강도를 비교한 뒤, phase-blind control을 가진 ds006065를 우선 경로로 골랐다.
  이 선택은 ds006065 전압과 Nature source-data file을 열기 전에 이루어졌다.

## 0. 목적과 지위

OpenNeuro ds006065 v1.0.0의 실제 인간 intracranial EEG에서 다음 공개 결과의
raw-derived 재현 가능성을 시험한다.

> lateral temporal cortex 자극을 해마 theta trough에 동기화한 뒤에는,
> phase-blind protocol 뒤보다 해마 late stimulation-evoked potential(SEP)의
> pre/post 변화가 더 크다.

이 결과는 Kragel et al. (2025)에 이미 발표되었다. 그러므로 이번 run은 outcome-blind
독립 확인이나 새 임상시험이 아니다. 공개 논문의 측정 정의를 별도 구현으로 raw
BrainVision object에 다시 적용하는 재현성 검증이며, 추가 CE delta는 reference 변경과
matched negative control에 대한 same-data robustness reanalysis다.

가능한 최강 문장은 일곱 epilepsy surgery participant의 이 공개 측정사슬에서
history-conditioned observed cortico-hippocampal response 차이를 재현했다는 것이다.
건강한 인구, 기억 행동, 축삭 경로, 뇌 전체 계량, 의식, 자아 또는 AGI로 일반화하지
않는다.

## 1. BIO_STARTING_MECHANISM과 CE_DELTA

### BIO_STARTING_MECHANISM

출발 기전은 state-dependent cortico-hippocampal communication이다. 해마 theta phase를
실시간 측정하고 lateral temporal cortex(LTC)에 5 mA charge-balanced biphasic pulse를
theta trough에 맞추는 30분 theta-synchronized(TS) protocol을, 거의 같은 속도이되 theta
phase에 맞추지 않은 phase-blind(PB) protocol과 비교한다. 연결성 readout은 intervention
전후 LTC single-pulse electrical stimulation에 대한 해마 SEP다.

논문이 고정한 physiological interpretation은 다음 정도까지만 채택한다.

- early 15–50 ms SEP는 더 직접적인 경로 성분에 가깝다.
- late 50–250 ms SEP는 multi-node propagation을 더 많이 포함할 수 있다.
- SEP는 effective-connectivity proxy이지 해부학적 edge weight 자체가 아니다.

### CE_DELTA

CE의 최소 추가 질문은 고정 scalar 연결 대신 intervention history와 measurement
reference를 인자로 갖는 제한된 관측 response operator로 읽었을 때 방향이 유지되는가다.

$$
y^{(r)}(t\mid \mathcal H,c)
= C_r\bigl(h_{\mathcal H,c} * u\bigr)(t)+a^{(r)}(t)+\eta^{(r)}(t),
$$

여기서 $\mathcal H\in\{\mathrm{pre},\mathrm{post}\}$,
$c\in\{\mathrm{TS},\mathrm{PB}\}$, $r$은 clinical 또는 local bipolar reference다.
$u$는 면적이 1로 정규화된 이상적 자극 펄스로 두며, 이 계약은
$h_{\mathcal H,c}*u$가 전압 단위를 갖는다는 것만 사용한다. $h$ 자체의 물리 단위나
해부학적 전달함수는 이 자료로 식별했다고 주장하지 않는다.
이번 자료가 직접 식별하는 것은 $h$나 해부학적 연결 자체가 아니라 frozen P2P
contrast뿐이다. CE-specific 승격 조건은 participant-equal late contrast가 두 reference에서
같은 양의 방향이고, prestimulus control이 같은 positive signal을 만들지 않는 것이다.

## 2. DATA_PROVENANCE

### 2.1 Dataset lock

- OpenNeuro dataset: ds006065, snapshot 1.0.0.
- DOI: 10.18112/openneuro.ds006065.v1.0.0.
- GitHub release commit: 14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4.
- Git tree: 615b6b5caf83776094a4fdfb7ffc168993d80ade.
- BIDS DatasetType=raw, BIDSVersion=1.8, license CC0.
- Converter metadata: FieldTrip 7018a7700, data2bids.
- Subject labels: p16, p17, p18, p19, p20, UC004, UC005.
- Signal: BrainVision IEEE_FLOAT_32, little-endian multiplexed, muV, header 499.5 Hz.

Git annex가 선언한 각 .eeg object의 SHA-256와 byte size, S3 object version ID, ETag,
Content-Length, Accept-Ranges를 raw request 전에 source manifest에 고정한다. 어느
하나라도 release pointer와 다르면 endpoint를 계산하지 않고 STOP_SOURCE_IDENTITY다.

### 2.2 Primary paper and author code

- Kragel et al., Closed-loop control of theta oscillations enhances human hippocampal
  network connectivity, Nature Communications 16, 4061 (2025), DOI
  10.1038/s41467-025-59417-7.
- Author analysis archive: Zenodo 10.5281/zenodo.14735080, record 14735080,
  TSS-main.tar.gz, 51,379 bytes, MD5 6feba89b7c49fd661b39b589e8d9624a.

공개 MATLAB code는 원 Neuralynx event index, phase/stimulation contact, windows,
artifact threshold, filter, polarity note를 고정하는 provenance다. 공개 code에는 BIDS
BrainVision reader가 없고 일부 call-signature 불일치가 있으므로, 이번 run은 그 code가
그대로 실행됐다는 주장이 아니라 공개 measurement grammar의 독립 Python 구현이다.

Nature article의 figure source-data file은 outcome을 담으므로 raw result receipt가 먼저
직렬화될 때까지 열지 않는다. 이후 published aggregate cross-check에만 쓰며 threshold,
reference, window 또는 inclusion을 바꾸는 데 쓰지 않는다.

## 3. DATA_SPLIT와 cohort lock

### DATA_SPLIT

NO_DISCOVERY_SPLIT / PUBLISHED_RESULT_REPRODUCTION_ONLY.

모델 선택이나 coefficient 학습이 없고 논문 outcome이 알려져 있으므로 discovery와
confirmation으로 가장하지 않는다. 모든 eligible pre/post EP file을 한 번의 frozen raw
evaluation에서 연다. raw 전에는 metadata, annex pointer, header, channel table, 공개
code만 볼 수 있다.

각 EP binary는 공개 code의 한 event epoch마다 1000 sample을 이어 붙인 구조다. Annex
byte size / (4 bytes × channel count)가 아래 block 수 × 1000과 정확히 같아야 한다.

| protocol | subject | pre task / blocks | post task / blocks | published readout | local bipolar |
|---|---|---:|---:|---|---|
| TS | p16 | eppre / 90 | eppost / 60 | RB1 | RB1-RB2 |
| TS | p17 | eppre / 63 | eppost / 59 | D1 | D1-D2 |
| TS | p18 | eppre / 60 | eppost / 60 | AH2 | AH2-AH3 |
| TS | p19 | eppre / 60 | eppost / 60 | D1 | D1-D2 |
| PB | p17 | epcontrolpre / 60 | epcontrolpost / 60 | D1 | D1-D2 |
| PB | p19 | epcontrolpre / 60 | epcontrolpost / 60 | D1 | D1-D2 |
| PB | p20 | epcontrolpre / 151 | epcontrolpost / 149 | D9 | D9-D10 |
| PB | UC004 | epcontrolpre / 40 | epcontrolpost / 40 | RHH1 | RHH1-RHH2 |
| PB | UC005 | epcontrolpre / 40 | epcontrolpost / 40 | RHB1 | RHB1-RHB2 |

p20의 D9는 public run_group_ep.m이 P2P에 전달한 ordered channel list의 첫 채널을 따른다.
endpoint를 본 뒤 다른 hippocampal contact를 고르지 않는다. p16 pre와 p19 pre/post의
공개 polarity correction은 평균 waveform diagnostic에 적용하지만 P2P에는 수학적으로
영향이 없다.

## 4. MEASUREMENT_MODEL과 OBSERVABLES

### MEASUREMENT_MODEL

한 trial block의 index를 $j=0,\ldots,999$라 하고 BIDS header가 선언한 간격을
$\delta t=2.002002002\,\mathrm{ms}$로 둔다.

$$
t_j=j\delta t-500\,\mathrm{ms}.
$$

이 convention은 공개 MATLAB epoched2dat의 linspace(0,2,1000)-0.5와 같은 grid다.
각 reference trace는 다음과 같다.

- clinical: 표에 지정한 published readout contact의 voltage.
- local bipolar: 표의 첫 contact minus 두 번째 contact.

각 trial/reference에 다음 순서를 고정한다.

1. 60, 120, 180 Hz sine/cosine nuisance를 trial별 least-squares DFT regression으로
   제거한다.
2. p17만 public code에 따라 10차 Butterworth 80 Hz low-pass를 zero-phase로 적용한다.
3. [-50,-10] ms 평균을 뺀다.
4. early [15,50] ms, late [50,250] ms, prestimulus [-300,-100] ms를 고정한다.

Window membership은 위 $t_j$에 대해 양 끝을 포함한다. 구현은 floating ambiguity를
피하도록 계산된 integer mask를 receipt에 기록한다.

### OBSERVABLES

- raw multiplexed voltage muV와 full-object SHA-256.
- protocol/participant/time/reference별 clean trial count.
- clean-trial mean waveform과 trial-level early/late/prestimulus P2P.
- participant-protocol pre/post waveform P2P 변화.
- participant-equal TS-minus-PB contrast, participant-cluster uncertainty,
  leave-one-participant-out와 p17/p19 paired sensitivity.
- published clinical reference와 local bipolar 방향 concordance.

관측하지 않는 것: spike, single-neuron activity, axonal path, synaptic weight, anatomical
geodesic, Riemannian metric, memory behavior, conscious report.

## 5. RESIDUAL_RULE과 inclusion lock

### RESIDUAL_RULE

필터·baseline 뒤 trial trace를 $x_{sct}^{(r)}(t)$라 한다. Public code에 대응하는 fixed
artifact rule은 reference별·file별로 다음을 모두 만족하는 trial만 남긴다.

1. $|t|>50\,\mathrm{ms}$에서 $\max|x|<500\,\mu\mathrm V$.
2. $t>50\,\mathrm{ms}$ sample의 Pearson kurtosis < 5.
3. 같은 file의 trial 축에서 sample별 z-score를 만들고 어느 sample에서도 |z| > 5가
   없음. 표준편차 0인 sample의 z는 0으로 둔다.
4. 모든 sample이 finite이고 block 길이가 정확히 1000이다.

각 pre/post file은 최소 20 trial과 원 block의 50% 이상을 남겨야 한다. 아홉
protocol-participant pair 중 하나라도 pre 또는 post에서 이 aperture를 못 채우면 cohort를
줄여 계속하지 않고 STOP_MEASUREMENT_APERTURE다.

Clean trial 평균 파형은

$$
\bar x_{sc\mathcal H}^{(r)}(t)
=\frac{1}{N_{sc\mathcal H}^{(r)}}\sum_k x_{sck\mathcal H}^{(r)}(t)
$$

이고, 주 P2P는 이 평균 파형의 window 내 max-minus-min이다. Trial-level P2P 잔차

$$
e_{sck\mathcal H}^{(r)}
=P_{sck\mathcal H}^{(r)}
-\operatorname{mean}_{k}P_{sck\mathcal H}^{(r)}
$$

는 published-model reproduction과 distribution diagnostic에만 쓰며, 수백 trial을
독립 participant처럼 세지 않는다.

## 6. Primary estimand, uncertainty, MODEL_SELECTION

### 6.1 Participant-equal same-data reanalysis

Window $W$의 평균 파형 P2P를

$$
A^{W}_{sc\mathcal H,r}
=\max_{t\in W}\bar x_{sc\mathcal H}^{(r)}(t)
-\min_{t\in W}\bar x_{sc\mathcal H}^{(r)}(t)
$$

로 두고,

$$
\Delta^{W}_{sc,r}
=A^{W}_{sc,\mathrm{post},r}-A^{W}_{sc,\mathrm{pre},r},
$$

$$
D^{W}_r
=\frac{1}{4}\sum_{s\in TS}\Delta^{W}_{s,TS,r}
-\frac{1}{5}\sum_{s\in PB}\Delta^{W}_{s,PB,r}.
$$

Primary는 $W=[50,250]$ ms의 $D^{late}_r$다. Trial 수가 큰 p20에 더 큰 가중치를
주지 않는다. 단위는 muV이며 participant가 inference unit다.

### 6.2 Participant-cluster uncertainty

Subject overlap(p17, p19)을 보존하기 위해 일곱 participant에 한 번씩
$w_s\sim\mathrm{Exp}(1)$ weight를 부여하고, 같은 participant의 TS/PB observation에 같은
weight를 쓴다. 각 protocol 안에서 weight를 정규화한다. 이는
Dirichlet(1,...,1) participant-cluster Bayesian bootstrap과 같다.

- draws: 65,536.
- PRNG: NumPy PCG64.
- seed: 20260825.
- interval: equal-tail [2.5%, 97.5%].
- 함께 보고할 값: $\Pr(D^{late}_r>0)$, 일곱 leave-one-participant-out contrasts.

이 interval은 empirical-distribution model 아래의 작은-cohort sensitivity다.
빈도주의 p-value, treatment randomization 또는 population causal posterior로 부르지 않는다.

두 protocol을 모두 받은 p17과 p19만으로

$$
D_{\mathrm{pair},r}^{late}
=\frac{1}{2}\sum_{s\in\{p17,p19\}}
\left(\Delta^{late}_{s,TS,r}-\Delta^{late}_{s,PB,r}\right)
$$

를 descriptive sensitivity로 보고하고 두 individual difference도 숨기지 않는다.
$n=2$이므로 유의성 검정이나 crossover causal effect로 승격하지 않는다.

### 6.3 Published-result reproduction lane

별도로 public compare_p2p.m처럼 clean trial 각각의 early/late P2P를 계산해 long table을
만든다. Archived code의 fixed model은 p2p ~ protocol*time이고 participant random
intercept와 protocol/time slope를 둔다. Article text의 더 큰 random interaction 구조는
sensitivity로 분리한다. Software가 Satterthwaite df를 재현하지 못하면 p-value를
근사하지 않고 PUBLISHED_MODEL_ENGINE_UNAVAILABLE로 명시한다.

Raw clinical-reference fixed interaction의 방향이 양수이면
PUBLISHED_DIRECTION_RAW_REPRODUCED, rounded beta 10.3 muV와 5% 안에서 맞고 공개
source-data aggregate와 일치하면 PUBLISHED_MODEL_NUMERICALLY_REPRODUCED다. 이 lane은
동일 자료 재현이며 독립 확인이 아니다.

### MODEL_SELECTION

NONE. Candidate family, hyperparameter, contact, window, filter, artifact threshold, reference,
cohort 또는 outcome label을 결과로 고르지 않는다. Public late window가 primary이고
early와 prestimulus는 controls다. Nature source data는 model selection에 사용할 수 없다.

## 7. MATCHED_CONTROLS와 status lattice

### MATCHED_CONTROLS

1. PB protocol: theta phase에 맞추지 않은 약 1 Hz stimulation의 pre/post EP.
2. Early SEP: 같은 trial의 15–50 ms P2P; late-specificity diagnostic.
3. Prestimulus: 같은 200 ms 길이의 [-300,-100] ms P2P; drift/noise diagnostic.
4. Reference: clinical reference와 사전 지정 local bipolar.
5. Participant influence: seven leave-one-participant-out contrasts.
6. Paired sensitivity: p17과 p19의 within-participant protocol difference.
7. Published aggregate: raw receipt 뒤에만 여는 Nature source data.

TS와 PB label은 일곱 participant 전체에서 교환 가능하거나 무작위 배정됐다고 가정하지
않는다. Condition-label permutation p-value를 계산하지 않는다. EP files 자체는 폐루프
phase concentration을 재검증하지 않으므로 protocol manipulation은 primary paper와 author
code provenance에 의존한다. 따라서 추정 대상은 phase만의 효과가 아니라 관측된 TS
protocol과 PB protocol의 차이다.

Control이 유의하지 않다는 사실을 equivalence로 부르지 않는다. Prestimulus 또는 early
95% lower bound가 0보다 크면 각각 BASELINE_ARTIFACT_CONCERN 또는
EARLY_NONSPECIFICITY_CONCERN을 붙인다. 그렇지 않으면 NO_POSITIVE_CONTROL_SIGNAL이지
null/equivalence 증명이 아니다.

### Status lattice

- PUBLISHED_DIRECTION_RAW_REPRODUCED: frozen clinical raw trial-level interaction 방향이
  공개 결과와 같은 양수.
- SAME_DATA_REANALYSIS_REFERENCE_ROBUST_SUPPORT:
  - clinical $D^{late}>0$이고 95% participant-cluster lower bound > 0;
  - local-bipolar $D^{late}>0$이고 95% participant-cluster lower bound > 0;
  - $D_{\mathrm{pair},clinical}^{late}>0$;
  - prestimulus lower bound가 0보다 크지 않음.
- SAME_DATA_REANALYSIS_SUPPORT_SENSITIVITY_LIMITED: clinical $D^{late}>0$이나 위 조건 중
  일부가 실패. CI_LIMITED, REFERENCE_SENSITIVE_OR_UNCERTAIN, PAIRED_SENSITIVITY_FAIL,
  PARTICIPANT_SENSITIVE, BASELINE_ARTIFACT_CONCERN, EARLY_NONSPECIFICITY_CONCERN을
  병기한다.
- ESTIMAND_DISCORDANT: frozen clinical raw trial-level interaction과 clinical
  participant-equal $D^{late}$ 중 하나만 양수다. 어느 한쪽의 양수만으로 결합 지지를
  선언하지 않고, 두 추정량의 모집단 가중과 오차모형 차이를 명시한다.
- SAME_DATA_REANALYSIS_NOT_SUPPORTED: clinical participant-equal $D^{late}\le0$이고
  published-model 방향은 unavailable이거나 두 추정량을 함께 판정할 수 없다. 이 상태는
  support 또는 sensitivity-limited support가 아니며, same-data descriptive support를
  제거한다.
- RAW_DIRECTION_NOT_REPRODUCED: clinical published-model interaction과 participant-equal
  $D^{late}$가 모두 0 이하.
- STOP_SOURCE_IDENTITY, STOP_MEASUREMENT_APERTURE, IMPLEMENTATION_INVALID: source/hash,
  fixed aperture, fixture/validator 실패다. 이 경우 biological verdict를 만들지 않는다.

## 8. FALSIFIER

### FALSIFIER

다음은 해당 부모 주장을 낮추거나 제거한다.

1. Annex SHA-256, S3 version, content length, header/channel order 또는 1000 × trial
   identity가 잠금과 다름: STOP_SOURCE_IDENTITY.
2. 지정 readout/local-bipolar contact가 pre/post에서 같은 index·unit으로 존재하지 않음:
   STOP_MEASUREMENT_APERTURE.
3. Fixed filter/window/exclusion/reference/bootstrap fixture가 analytic expected value를
   재현하지 못함: IMPLEMENTATION_INVALID.
4. Clinical participant-equal late $D\le0$: same-data descriptive support 제거.
   Published-model 방향을 판정할 수 없으면 SAME_DATA_REANALYSIS_NOT_SUPPORTED, 두
   추정량이 모두 0 이하면 RAW_DIRECTION_NOT_REPRODUCED로 기록한다.
5. Clinical lower bound는 양수지만 bipolar의 점추정이 0 이하이거나 lower bound가
   0 이하: reference-robust 부모 삭제, REFERENCE_SENSITIVE_OR_UNCERTAIN만 유지.
6. Prestimulus lower bound > 0: history-conditioned late-response 해석을
   BASELINE_ARTIFACT_CONCERN으로 낮춤.
7. Published-model interaction과 participant-equal clinical $D^{late}$의 부호가 다름:
   ESTIMAND_DISCORDANT로 낮추고 결합 지지를 만들지 않음.
8. Source-data cross-check가 raw receipt와 공개 code로 설명할 수 없는 방향/단위 불일치를
   보임: 결과 승격을 멈추고 implementation audit로 돌림.

이 falsifier는 published paper 전체를 반증하지 않는다. 이번 공개 BIDS 변환과 frozen
measurement chain의 재현·강건성 주장만 판정한다.

## 9. REVISION_TRIGGER와 execution barrier

### REVISION_TRIGGER

- Signal endpoint를 연 뒤 contact, polarity, reference, filter, window, artifact threshold,
  aggregation, seed, bootstrap, label 또는 control을 바꾸지 않는다.
- Source/header mismatch나 fixture failure를 고치려면 current raw result를 폐기하고 새
  version/run에 변경 이유와 predecessor hash를 선언한다.
- 결과가 약하다는 이유로 추가 channel 평균, 다른 hippocampal contact, 다른 window,
  trial exclusion 또는 one-sided p-value를 도입하지 않는다.
- Nature source data를 본 뒤 raw reader를 맞추는 수정은 금지한다.

### Revision 1 — 결과 미생성 implementation abort 뒤의 단일 재실행

2026-08-25의 raw attempt 0은 source lock과 pre-raw Gate PASS 뒤 시작됐지만 실행
인터페이스가 stdout·exit code를 반환하지 않았고, endpoint나 `raw_result.json` 또는
progress receipt를 하나도 만들지 않았다. 그 상태에서 정적 코드 감사가 artifact 판정을
계약과 달리 baseline 보정 전에 적용한 순서 결함을 발견했다. 같은 시각에 시작된 해당
Python child process 두 개만 종료했으며, waveform·효과크기·Nature Source Data는 사람이나
후속 판정에 노출되지 않았다. 이 시도는
`ATTEMPT0_IMPLEMENTATION_INVALID_NO_RESULT`로 폐기하며 생물학적 결과로 세지 않는다.

scientific aperture를 바꾸지 않는 다음 구현 수정만 허용한다.

- DFT와 p17 filter 뒤 baseline을 먼저 적용하고, 그 trace에서 amplitude·kurtosis·z-score를
  판정한다.
- 각 객체의 실제 수신 byte 수와 SHA-256 검증값을 endpoint와 분리된 atomic progress
  receipt에 남기고, 예외도 마지막 완료 객체와 함께 atomic STOP receipt로 남긴다.
- 계약에 이미 고정된 일곱 leave-one-participant-out 값과 status lattice를 빠짐없이
  직렬화한다. Full clinical late $D>0$인데 어느 한 participant를 뺀 clinical late
  contrast가 0 이하가 되면 `PARTICIPANT_SENSITIVE`를 붙인다.

수정 코드의 focused fixture, 독립 read-only implementation audit, 갱신된 status audit가
모두 통과한 뒤 raw attempt 1을 한 번만 실행할 수 있다. contact, reference, filter, window,
threshold, cohort, bootstrap, seed 또는 status 기준은 바꾸지 않는다. attempt 1이 source,
aperture, implementation 또는 infrastructure 이유로 결과 receipt 없이 끝나더라도 이
판본에서 추가 raw retry는 하지 않고 BLOCKED로 닫는다.

### Stages

1. S0_SOURCE_LOCK: metadata/annex/S3 version manifest와 DOI/code hash. No voltage.
2. S1_FIXTURE: synthetic multiplexing, filter, block, window, exclusion, reference,
   bootstrap tests. No real endpoint.
3. S2_AUDIT: source/math/routes independent lanes와 status audit. Auditor GO 전 raw 금지.
4. S3_RAW_ONE_SHOT: Revision 1의 허용 조건을 통과한 attempt 1에서 18 EP objects를
   version-pinned HTTPS로 sequential streaming, full SHA-256 검증, 지정 contact 추출,
   atomic progress와 endpoint/result receipt 직렬화. Raw binary는 repository에 저장하지
   않는다.
5. S4_INDEPENDENT_VALIDATION: receipt 재계산, source-data aggregate cross-check,
   final status audit.

## 10. CLAIM_CEILING

### CLAIM_CEILING

SEVEN_EPILEPSY_SURGERY_PARTICIPANTS / REAL_HUMAN_IEEG /
DIRECT_ELECTRICAL_INTERVENTION / PUBLISHED_DATASET_RAW_DERIVED_REPRODUCTION /
SAME_DATA_PARTICIPANT_EQUAL_ROBUSTNESS_REANALYSIS /
HISTORY_CONDITIONED_OBSERVED_CORTICO_HIPPOCAMPAL_SEP /
REFERENCE_ROBUST_ONLY_IF_BOTH_FROZEN_REFERENCES_PASS /
NO_OUTCOME_BLIND_INDEPENDENT_CONFIRMATION / NO_RANDOMIZED_POPULATION_CAUSAL_ESTIMATE /
NO_HEALTHY_POPULATION_GENERALIZATION / NO_MEMORY_BEHAVIOR_VALIDATION /
NO_AXONAL_GEODESIC_OR_RIEMANNIAN_METRIC_RECOVERY /
NO_INFINITE_DIMENSIONAL_IDENTIFICATION /
NO_CONSCIOUSNESS_SELF_HIPPOCAMPUS_HASH_OR_AGI_VALIDATION.

## 11. Reproducibility environment

- Repository root: C:\dev\ce\ce-agi-runtime.
- Run: _workspace/ce/brain-human-hippocampal-theta-raw-replication-20260825.
- Python entry: .codex/hooks/python.cmd python.
- Frozen interpreter at contract time: system CPython 3.11.9, NumPy 2.4.6, SciPy
  available. Workspace .venv와 uv-managed Python은 사용하지 않는다.
- Raw network execution은 non-interactive, version-pinned streaming receipt를 남긴다.
- 실제 voltage나 Nature source-data outcome은 lanes와 audit를 통과하기 전에 열지 않는다.
