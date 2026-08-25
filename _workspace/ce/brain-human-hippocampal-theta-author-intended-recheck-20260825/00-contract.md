# 인간 해마 iEEG 시간축 교정 및 available-clean 사후 재검산 계약

Status: COMPLETE

Mode: full, post-hoc measurement-correction successor

PREDECESSOR: `_workspace/ce/brain-human-hippocampal-theta-receipt-validator-20260825`

## 질문과 형식 지위

이 run은 두 질문만 다룬다. 첫째, 선행 HPC4에서 p17의 clean-trial 수가 낮게
나온 원인이 자료 손상인지, 시간축·필터·마스크 구현 오산인지 재검산한다. 둘째,
교정된 저자-의도 측정 에뮬레이션에서 계산 가능한 clean trial을 모두 사용했을 때
고정된 기술적 endpoint가 어떤 값을 갖는지 산출한다. 두 번째 질문은 HPC4 count를
본 뒤 선택되었으므로 처음부터 `[경험식: 동일 공개자료 사후탐색]`이다. 독립 확인,
원 논문의 정확한 MATLAB 재현, 인과효과 또는 모집단 추론으로 승격하지 않는다.

## PREDECESSOR_EVIDENCE

| 선행 결과 | 증거와 SHA-256 | 상태 | 보존하는 좁은 주장 | 재사용·재시도 경계 |
|---|---|---|---|---|
| 18개 OpenNeuro 객체의 수신 무결성 | HPC4 `raw_progress.json` `5b350ac0b568888ac6a8416f0084f04fad83242500ffbfd40451bb605e065e87`; `qc_result.json` `5f9ce77000613de4761d24519a6b7c1309fbea55d465739aafbc2a7189038e17` | PASS | 18/18 객체, 723,560,000 bytes의 SHA-256·크기·version ID·ETag가 잠긴 목록과 일치했다. | HPC4 ATTEMPT1은 재실행하지 않는다. 객체 정체성만 읽기 전용으로 상속한다. |
| HPC4 clean count와 MIN20 중단 | 같은 두 receipt; 최종 보고 `9c75306a3c95c8dd3091dfbc7d4bb8f6024920f9a1c4cc7e4bbd57a18030bd9d` | APPARATUS_INVALID | HPC4가 자체 고정한 잘못된 시간축 아래 TS p17 post clinical 11, PB p17 pre bipolar 11을 산출하고 endpoint 없이 멈췄다는 거래 사실만 보존한다. | 이 수치를 저자 QC 재현 또는 생물학적 음성 결과로 사용하지 않는다. |
| 시간축 반례 | HPC2/HPC4 `AUTHOR_TIME=j/999*(1000/499.5)-0.5`; 저자 `linspace(0,1000/500,1000)-0.5` 및 BrainVision `SamplingInterval=2002.002002 us` | APPARATUS_INVALID | 올바른 표본 시간은 $t_j=j/499.5-0.5$ s이다. 선행식은 retained sample 998에서 약 2 ms 늦고 DFT 기저를 틀리게 만든다. | 선행 mask·DFT·count는 교정 endpoint에 재사용하지 않는다. 원 artifact는 반례 기록으로 보존한다. |
| HPC4 생물학적 endpoint | `raw_result.json` 부재 | STOP | 효과 크기, bootstrap, LOO, paired sensitivity 또는 생물학 판정이 생성되지 않았다. | 부재를 음성 결과로 해석하지 않는다. |
| 저자 공개 코드 정적 감사 | `author-code-static-receipt.md` `20008069771a37a7e7669e996d0bb799cabed1ad09e0e010c6c1f0ec33b93496` | PASS | 전역 의도 threshold는 `(k,z,a)=(5,5,500)`이고 artifact 판정은 baseline보다 먼저다. 저자 코드에는 MIN20/all-cell gate가 없다. | p17/p19 PB 호출의 kurtosis 인자 누락과 FieldTrip 판본 미고정 때문에 literal-script parity를 주장하지 않는다. |

## 후보 경로와 선택

| 경로 | 판정 | 이유 |
|---|---|---|
| R0: HPC4 시간축과 all-cell MIN20 유지 | RETIRED | 시간축 반례가 완전하며 endpoint도 열리지 않는다. |
| R1: 교정 시간축, 이중 QC 구현, available-clean 기술통계 | SELECTED | 자료/계산 오산을 직접 가르고 저자 코드에 없는 MIN20을 생물학 판정으로 오용하지 않는다. |
| R2: 관측된 11에 맞춰 MIN10으로 하향 | REJECTED | 결과를 본 뒤 임계값을 맞추는 outcome tuning이다. |
| R3: 공개 MATLAB 스크립트를 문자 그대로 실행 | BLOCKED | p17/p19 PB 호출의 필수 인자 누락, FieldTrip 판본 미고정, MATLAB engine 부재가 있다. |
| R4: 원 논문의 trial-level `fitlme`를 정확히 복제 | BLOCKED | MATLAB/FieldTrip 실행환경과 완전한 판본 영수증이 없다. 대체 엔진을 exact parity라 부르지 않는다. |

R1은 긍정적 endpoint를 얻기 위해 선택한 경로가 아니다. 원자료를 다시 열기 전에
소스의 시간 정의가 선행 구현을 반박했고, 임계값을 숫자 20에서 10으로 바꾸지 않고
계산 가능성의 정의역만 분리한다. 선행 MIN20 결과는 낮은 정밀도의 경고로 함께
보고하지만 endpoint 생성 권한을 좌우하지 않는다.

## 뇌 연구 admission fields

`BIO_STARTING_MECHANISM`: 해마 인접 자극이 유발한 iEEG 전위에서 자극 후
15--50 ms와 50--250 ms peak-to-peak 진폭을 측정한다. 이 측정량은 유발반응의
기술적 readout이지 기억·의식의 기전식이 아니다.

`CE_DELTA`: `NONE`. 이 run은 CE 추가항, CE 상수 또는 새로운 뇌 알고리즘을
적합하지 않는다.

`MEASUREMENT_MODEL`: version-locked BrainVision multiplexed little-endian float32를
채널별 resolution/unit으로 microvolt 변환하고, 첫 999표본에 60/120/180 Hz DFT
성분 제거를 적용한다. p17만 10차 80 Hz Butterworth 양방향 저역통과를 거친다.
교정 시간축과 저자 순서의 artifact QC를 적용한 뒤 clean trial만 baseline 보정하고
trialwise P2P와 clean-trial mean-waveform P2P를 모두 산출한다.

`DATA_PROVENANCE`: OpenNeuro `ds006065` v1.0.0, git commit
`14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4`; 18-object identity lock SHA-256
`66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810`;
Kragel et al. 2025 DOI `10.1038/s41467-025-59417-7`; author code Zenodo
record `14735080`, archive MD5 `6feba89b7c49fd661b39b589e8d9624a`.

`DATA_SPLIT`: 동일 공개자료의 사후 재분석이며 독립 holdout은 없다. Stage Q는
TS p17 post와 PB p17 pre 두 객체에서 QC mask만 재검산하고 endpoint를 만들지
않는다. Stage E는 Stage Q의 구현·정체성 gate가 통과했을 때만 고정 18객체 전체를
한 번 읽어 endpoint를 산출한다. Stage Q count는 Stage E의 threshold, cohort,
contact, window 또는 estimator를 바꾸는 데 쓰지 않는다.

`OBSERVABLES`: 객체 identity, 두 독립 구현의 clinical/bipolar clean mask SHA-256,
clean count와 중복가능 exclusion reason count, trial별 amplitude maximum과
500-microvolt threshold까지의 margin,
participant별 pre/post trial-mean P2P와 mean-waveform P2P, TS 4명과 PB 5명의
participant-equal 변화 차이 $D$, shared-participant bootstrap, 7개 LOO와 p17/p19
paired sensitivity이다.

`RESIDUAL_RULE`: 두 구현의 mask가 한 trial이라도 다르거나 corrected DFT/LPF
파형 차이가 허용오차를 넘으면 `QC_IMPLEMENTATION_DISAGREEMENT`이며 endpoint를
열지 않는다. 교정 count와 HPC4 count의 차이는 오류 증거로 그대로 기록하되
endpoint 선택에 사용하지 않는다.

`FALSIFIER`: source identity 불일치, Stage Q 이중 구현 불일치, 또는 고정된
clinical pre/post cell 중 clean trial이 0이면 각각 `SOURCE_IDENTITY_STOP`,
`QC_IMPLEMENTATION_DISAGREEMENT`, `CLINICAL_PAIR_UNAVAILABLE`로 endpoint 없이
종료한다. endpoint가 불리해도 cohort·contact·threshold·window를 고치지 않고
그 값을 보고한다.

`MATCHED_CONTROLS`: PB protocol, local bipolar reference, early와 prestim window,
participant LOO, 양 protocol에 모두 있는 p17/p19 paired contrast를 고정한다.
local bipolar는 분석자 정의 sensitivity이며 clinical primary를 veto하지 않는다.

`MODEL_SELECTION`: primary descriptive estimand는 clinical reference의 participant별
mean trialwise late P2P pre/post 변화에 대한 TS 평균 minus PB 평균이다. 같은
clinical trace의 mean-waveform late P2P는 predecessor-compatible sensitivity다.
Bipolar, early, prestim, LOO, paired 값은 sensitivity/control이다. trial 수로
participant를 가중하지 않는다. 원 논문의 `fitlme`는
`PUBLISHED_MODEL_ENGINE_UNAVAILABLE`로 남긴다.

`REVISION_TRIGGER`: raw Stage Q가 시작된 뒤 시간축, DFT/LPF, QC, baseline,
reference, cohort, threshold, estimator, bootstrap seed/draw 또는 status lattice를
수정하지 않는다. 결함이 발견되면 현재 run을 명시적으로 종료하고 새 계약에서만
수정한다.

`CLAIM_CEILING`: `[경험식: SAME_PUBLIC_DATA_POSTHOC_AUTHOR_INTENDED_EMULATION]`,
7명 epilepsy-surgery participant의 기술통계만 허용한다. 독립 확인, exact MATLAB
replication, 건강인·모집단 일반화, causal stimulation effect, 기억 향상, 의식,
CE 또는 AGI 증거는 허용하지 않는다.

## 교정된 시간·QC 정의

원 sample index를 $j=0,\ldots,999$라 한다. 마지막 sample을 버린 뒤 사용하는
저자/물리 시간은

$$
t_j=\frac{j}{499.5}-0.5\ \mathrm{s},\qquad j=0,\ldots,998.
$$

이는 저자의 `linspace(0,1000/500,1000)-0.5`와 BrainVision sampling interval
$2002.002002\ \mu\mathrm{s}$에 동시에 일치한다. 다음 index를 고정한다.

| 용도 | 조건 또는 FieldTrip 선택 규칙 | index, 개수 |
|---|---|---|
| DFT 입력 | 마지막 표본 제외 | 0..998, 999 |
| QC latency | nearest endpoint `[-0.4,0.8]` | 50..649, 600 |
| amplitude | latency에서 $t<-0.05$ 또는 $t>0.05$ | 50..224 및 275..649, 550 |
| kurtosis | latency에서 $t>0.05$ | 275..649, 375 |
| z-score | 전체 latency, trial 축 표준화 | 50..649, 600 |
| baseline | FieldTrip nearest endpoint `[-0.05,-0.01]` | 225..245, 21 |
| early | 명시적 $0.015\le t\le0.05$ | 258..274, 17 |
| late | 명시적 $0.05\le t\le0.25$ | 275..374, 100 |
| prestim control | $-0.3\le t\le-0.1$ | 100..199, 100 |

각 QC channel에서 amplitude maximum은 $<500\ \mu\mathrm V$, bias-corrected Pearson
kurtosis는 $<5$, trial-axis sample z-score는 $|z|\le5$여야 한다. 여러 QC channel을
쓰는 p20 clinical은 D9/C1/C'1 중 하나라도 실패하면 trial을 제외한다. clinical
endpoint channel은 고정된 첫 QC channel이고 local bipolar는 그 channel minus
고정 인접 channel이다. artifact 판정은 baseline보다 먼저 수행한다.

## 독립 계산과 허용오차

Stage Q와 E는 같은 raw bytes에 대해 두 구현을 실행한다. 구현 A는 실수
sin/cos least-squares projection과 direct-form Butterworth `filtfilt`를 사용한다.
구현 B는 FieldTrip `dftreplace='zero'`에 해당하는 복소 기저 closed-form과
second-order-section `sosfiltfilt`를 사용한다. 999표본에서 60/120/180 Hz가 각각
정수 cycle이므로 두 DFT 표현은 같은 투영을 나타낸다.

- keep mask, channel×trial exclusion reason mask와 그 trial-union mask는 bitwise
  identical이어야 한다. channel-reason count와 union-trial count를 모두 기록하며,
  HPC4의 reason count와 비교할 때는 같은 channel-reason 의미만 사용한다.
- 동일 channel scaling과 padding을 쓴 모든 block의 selected QC, clinical endpoint,
  bipolar trace에 대해 DFT와 optional LPF 직후, latency/QC/baseline 전 999 samples
  전체의 구현 A/B 최대 절대차가 `1e-6 microvolts` 이하여야 한다.
- endpoint 수치 recomputation은 `rtol=1e-10, atol=1e-8 microvolts`를 사용한다.
- JSON number는 finite여야 하며 boolean/string/null 대체를 허용하지 않는다.
- mask hash는 길이 고정 `uint8` 0/1 배열의 raw bytes에 대한 SHA-256이다.

FieldTrip 판본이 저자 archive에 잠겨 있지 않으므로 이 일치는 두 Python 구현의
수치 일관성이지 저자의 정확한 MATLAB binary 재현 증명은 아니다.

## available-clean 정의와 endpoint

임의의 `MIN10` 또는 `MIN20`을 두지 않는다. clinical primary에서 각 고정
participant/protocol의 pre와 post에 $n_{clean}\ge1$이어야 평균이 정의된다. 하나라도
0이면 participant를 버리지 않고 `CLINICAL_PAIR_UNAVAILABLE`로 끝낸다. bipolar의
고정 pre/post cell 중 하나라도 0이면 primary는 보존하되 late/early/prestim/LOO/
paired를 포함한 bipolar bundle 전체를 계산하지 않고
`BIPOLAR_SENSITIVITY_UNAVAILABLE`로 표시한다. clinical p17/p19 paired는 clinical
gate가 통과하면 정의되며, bipolar paired는 관련 8개 TS/PB pre/post cell이 모두
양수일 때만 bipolar bundle 안에서 계산한다.

각 trial $i$, window $W$에서 baseline-corrected P2P를

$$
P_{i,W}=\max_{j\in W}(x_{ij}-\bar x_{i,B})-
        \min_{j\in W}(x_{ij}-\bar x_{i,B})
$$

로 두고 cell 기술량은 $\bar P_W=n^{-1}\sum_iP_{i,W}$이다. sensitivity로 clean
trial 평균 파형 $\bar x_j$의 $\operatorname{ptp}_{j\in W}\bar x_j$도 계산한다.
participant $s$의 변화는 $\Delta_s=P_{s,post}-P_{s,pre}$이고 primary contrast는

$$
D=\frac{1}{4}\sum_{s\in TS}\Delta_s-
  \frac{1}{5}\sum_{s\in PB}\Delta_s.
$$

PCG64 seed `20260825`, 65,536개의 exponential-weight participant bootstrap을
고정하고 p17/p19의 weight를 두 arm에서 공유한다. interval과 $P(D>0)$은 기술적
불확실성 요약이며 p-value나 population causal interval이 아니다.

## 단계·거래 봉인

1. `QC_RECHECK1`: TS p17 post와 PB p17 pre의 exact version-pinned 객체를 한 번
   다시 내려받아 source identity, 구현 A/B mask·margin·count를 기록한다.
   이 receipt에는 waveform, P2P, $D$, bootstrap 또는 status lattice를 넣지 않는다.
2. valid `QC_RECHECK1`이 있고 clinical clean count가 모두 1 이상이면
   `ENDPOINT1`을 한 번 허용한다. 18객체를 exact version으로 읽고 같은 이중
   계산을 통과한 뒤에만 `raw_result.json`을 원자적으로 commit한다.
3. 각 stage는 prior authoritative receipt가 있으면 재실행하지 않는다. HTTP
   transport retry는 한 stage 내부의 동일 object/version GET에만 허용하며 분석
   attempt를 늘리지 않는다.
4. endpoint의 부호·구간·control이 불리해도 result를 삭제하거나 재선택하지 않는다.

최종 결과에는 HPC4 잘못된-grid count와 corrected-grid count를 나란히 싣고,
차이를 계산 오산으로 분류할지 자료 고유의 낮은 clean count로 분류할지 구분한다.
