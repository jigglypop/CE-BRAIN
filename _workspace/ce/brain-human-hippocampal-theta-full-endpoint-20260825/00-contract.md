# 인간 해마 iEEG 교정 전수 endpoint 산출 계약

Status: COMPLETE

Mode: light successor, same-public-data post-hoc full descriptive endpoint

PREDECESSOR: `_workspace/ce/brain-human-hippocampal-theta-author-intended-recheck-20260825`

## 질문과 범위

이 run은 교정된 저자-의도 측정 에뮬레이션을 18개 version-pinned 인간 iEEG 객체
전체에 적용하여, 앞서 고정한 모든 P2P·participant contrast·불확실성·민감도 계산을
끝낸다. 계산 결과의 부호나 크기와 무관하게 전부 기록한다. 동일 공개자료를 이용한
사후 재분석이므로 결과의 형식 지위는 처음부터 `[경험식: SAME_PUBLIC_DATA_POSTHOC]`다.
독립 확인, 원 논문의 exact MATLAB/FieldTrip/`fitlme` 재현 또는 모집단 인과효과로
승격하지 않는다.

선행 run의 `QC_RECHECK1`은 완료된 one-shot 기록이므로 재실행하거나 덮어쓰지 않는다.
이번 run은 그 영수증을 입력 증거로 검증한 뒤 별도 `ENDPOINT_FULL1` 거래만 한 번 연다.

## PREDECESSOR_EVIDENCE

| 선행 증거 | SHA-256 | 상태 | 보존하는 좁은 주장 | 재사용 경계 |
|---|---|---|---|---|
| 계약 | `8a2675fe25199dfe3320bca67046f0777ef738470e9edb105e588a47d4b3eec0` | PASS | 교정 grid, QC, endpoint, estimand, seed와 claim ceiling이 결과 전에 고정됐다. | 수식·window·cohort·reference·seed를 바꾸지 않는다. |
| 경로 선택 | `f23422bd4fcd684d07d9a6474fa1869626d4dcca8b0a4ca048e47687999bc17d` | PASS | `CORRECTED_AVAILABLE_CLEAN`이 선택됐고 MIN10·MIN20 outcome gate는 기각됐다. | count를 보고 새 threshold를 만들지 않는다. |
| 실제 QC receipt | `04edcbe5c290985f6a59c230989f4d13d83323e193767559ec4e15562de9e6e6` | PASS | TS/p17/post `12/25`, PB/p17/pre `24/11`; 두 raw 객체의 source identity와 dual-path QC가 유효하다. | 완료 receipt는 읽기 전용이며 재실행하지 않는다. |
| QC progress | `da9d5d5f77d31632640faef11b3fb8cc7b44068c849c051d0db658938a06d679` | PASS | receipt SHA와 completed rows가 상호 결박된 COMPLETE 거래다. | orphan 또는 변조 receipt를 입력으로 받지 않는다. |
| Stage-Q 감사 | `d2a5ad198b3ae8625de1b393c27e24d8f5b9fa3f216b844144f15651569973d0` | PASS | 실제 QC 재검산의 P0/P1이 닫혔다. | endpoint 승인으로 소급 해석하지 않는다. |
| Stage-Q 검증 | `4649507ffbc4faa66689c0699ff40d2cd230268dcd8604f163108bd6d6af3943` | PASS | 15 focused tests와 실제 two-object 거래가 기록됐다. | 기계 PASS는 생물학적 판정이 아니다. |
| 최종 QC 보고 | `d88393fcb682a8ab7fd8a85ea01eafdcfb0dd4332b6d522ecce85460d061eaa0` | PASS | 시간축 오산이 실제 clinical QC count를 바꿨고 endpoint는 아직 없었다. | 이를 theta 효과로 인용하지 않는다. |
| 교정 executor | `79191826af3a28b174cc793119817e1536e9466f9a162d1dcc05bea724b25c54` | PASS | corrected grid와 dual-path QC 구현이 동결됐다. | hash 불일치 시 실행하지 않는다. |

## 후보 경로

| 경로 | 판정 | 이유 |
|---|---|---|
| R0: 선행 HPC5 result validator로 즉시 실행 | REJECTED | trialwise P2P를 clean trial에서 독립 재구성하지 못하고 bipolar bundle 삭제를 배제하지 못한다. |
| R1: selected-source witness를 저장하고 독립 validator가 전량 재계산 | SELECTED | 모든 QC·P2P·aggregate leaf를 network 재접속 없이 원 selected trace에서 다시 계산할 수 있다. |
| R2: MIN20 또는 관측 count 맞춤 MIN10 | REJECTED | 저자 코드에 없는 gate이거나 outcome tuning이다. |
| R3: literal MATLAB/FieldTrip/`fitlme` parity | BLOCKED | 저자 archive의 호출 결함, FieldTrip 판본 미고정, MATLAB model engine 부재가 남아 있다. |

## 뇌 연구 admission fields

`BIO_STARTING_MECHANISM`: 해마 인접 전기자극 뒤 기록된 iEEG 유발전위의 early
15--50 ms와 late 50--250 ms peak-to-peak amplitude다. 이는 유발반응 readout이며
기억·의식의 완성 기전식이 아니다.

`CE_DELTA`: `NONE`. CE 항·상수·새 뇌 알고리즘을 적합하지 않는다.

`MEASUREMENT_MODEL`: OpenNeuro BrainVision float32를 header resolution/unit에 따라
microvolt로 변환하고 첫 999 samples에서 60/120/180 Hz DFT 성분을 제거한다. p17은
10차 80 Hz Butterworth 양방향 저역통과를 추가한다. 교정 시간은
$t_j=j/499.5-0.5$ s다. artifact QC 뒤 clean trial만 baseline 보정하고 trialwise
P2P와 clean-trial mean-waveform P2P를 계산한다.

`DATA_PROVENANCE`: OpenNeuro `ds006065` v1.0.0, git commit
`14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4`, 18-object identity lock
`66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810`, Kragel et al.
2025 DOI `10.1038/s41467-025-59417-7`, Zenodo `14735080`이다.

`DATA_SPLIT`: 독립 holdout이 없는 동일 공개자료 사후 재분석이다. 18개 객체는 모두
기술통계 산출에 사용하며 확인 표본으로 부르지 않는다. 결과를 본 뒤 participant,
protocol, phase, channel, window 또는 estimator를 제외하지 않는다.

`OBSERVABLES`: 18개 객체의 identity·QC mask/reason/count/margin, 각 clinical과
local-bipolar cell의 clean count, early/late/prestim trialwise P2P 목록과 평균,
mean-waveform P2P, participant별 pre/post 변화, TS 4명과 PB 5명의 participant-equal
contrast $D$, 65,536-draw shared-participant bootstrap, 7개 unique-participant LOO,
p17/p19 paired sensitivity다.

`RESIDUAL_RULE`: producer와 independent validator의 모든 source/QC row, waveform,
trialwise P2P, aggregate leaf가 `rtol=1e-10`, `atol=1e-8 microvolts` 안에서 일치해야
한다. witness hash·shape·dtype·key 또는 predecessor Q row가 다르면 결과를 승인하지
않는다.

`FALSIFIER`: source identity 불일치, dual-path QC mask/파형 불일치, 고정 clinical
cell의 zero clean count, witness/result/progress 결박 실패, 독립 재계산 불일치 중
하나라도 있으면 endpoint-bearing authoritative result 없이 종료한다. 결과가 불리한
것은 실패 조건이 아니다.

`MATCHED_CONTROLS`: PB protocol, local bipolar reference, early와 prestim window,
7-person LOO, 두 arm에 공통인 p17/p19 paired contrast다. bipolar는 분석자 sensitivity며
clinical primary를 veto하지 않는다. 하나의 bipolar cell이라도 zero clean이면 부분
선택 없이 bipolar bundle 전체를 생략한다.

`MODEL_SELECTION`: primary는 clinical trial-mean late P2P의 participant별 post-pre
변화에서 TS mean minus PB mean인 $D$다. clinical mean-waveform late P2P는 선행-compatible
sensitivity다. 두 reference와 두 estimand의 early/late/prestim, bootstrap, LOO, paired를
모두 계산하되 primary를 바꾸지 않는다. published `fitlme`는 계산하지 않는다.

`REVISION_TRIGGER`: raw 거래 시작 뒤 수식, clock, DFT/LPF, QC, baseline, window,
threshold, participant, reference, estimand, seed, draw 수 또는 status를 바꾸지 않는다.
구현 결함이면 이 run을 terminal로 닫고 새 계약에서만 수정한다.

`CLAIM_CEILING`: 7명 epilepsy-surgery participant의 동일 공개자료 사후 기술통계다.
실제 인간 iEEG에서 계산된 관측 비교이지만 독립 확인, exact published-model replication,
건강인·모집단 일반화, causal stimulation effect, 기억 향상, 의식, CE 또는 AGI 증거는
허용하지 않는다.

## 고정 수학과 endpoint

시간·QC·window 정의는 선행 계약을 byte-hash로 상속한다. index는 first999
`0..998`, latency `50..649`, amplitude `50..224 ∪ 275..649`, kurtosis `275..649`,
baseline `225..245`, early `258..274`, late `275..374`, prestim `100..199`다.
threshold는 Pearson kurtosis 5, trial-axis sample z-score 5, amplitude 500 µV다.

각 clean trial $i$와 window $W$의 P2P는

$$
P_{i,W}=\max_{j\in W}(x_{ij}-\bar x_{i,B})-
        \min_{j\in W}(x_{ij}-\bar x_{i,B})
$$

이고 trial-mean estimand는 $\bar P_W=n^{-1}\sum_iP_{i,W}$다. mean-waveform
sensitivity는 $P_W^{mean}=\operatorname{ptp}_{j\in W}\bar x_j$다. participant $s$의
post-pre 변화 $\Delta_s$를 사용해 primary를

$$
D=\frac14\sum_{s\in TS}\Delta_s-
  \frac15\sum_{s\in PB}\Delta_s
$$

로 계산한다. PCG64 seed `20260825`와 65,536 exponential-weight draws를 사용하고,
p17/p19는 두 arm에서 같은 unique-participant weight를 공유한다. bootstrap interval과
$P(D>0)$은 기술적 요약이지 p-value나 모집단 causal interval이 아니다.

## 독립 authority witness

`source_witness.npz`는 18개 객체 각각의 모든 trial에 대해 raw source에서 추출하고
microvolt로 변환한 selected QC-channel tensor와 local-bipolar tensor를 저장한다.
rejected trial도 포함한다. full 168--175 channel payload는 저장하지 않는다. key order,
dtype, shape, 파일 SHA-256과 size는 result manifest에 고정한다.

clinical endpoint trace는 각 객체의 selected QC tensor에서 고정된 첫 channel
`q[:,0,:]`이다. p20의 나머지 selected channels는 clinical trial의 QC union에만
참여한다. local-bipolar endpoint는 source lock에 고정된 endpoint channel minus 인접
bipolar channel trace다.

producer는 source identity를 확인해 witness를 원자적으로 commit한 뒤, 그 witness에서
endpoint를 계산한다. 별도 validator는 network를 사용하지 않고 witness를 다시 열어
dual-path QC, baseline, 모든 trialwise/mean-waveform P2P와 aggregate를 독립 코드 경로로
전량 재계산한다. 최종 progress는 witness SHA와 result SHA 및 exact completed source
rows를 결박한다. witness가 없거나 hash가 다르면 JSON의 자기일관성만으로 승인하지 않는다.

독립 validator의 시작점은 witness다. full raw object에서 selected trace를 추출하는
단계 자체는 별도 재구성하지 않으며, 그 provenance는 frozen HPC2 loader의 exact
code hash와 각 GET의 expected/observed SHA·size·version ID·ETag 검증에 의존한다.
따라서 witness-backed PASS는 raw-to-witness 추출의 독립 구현 parity를 뜻하지 않는다.

공개 인간 데이터의 selected trace witness는 이 run의 local artifact로만 보존하며 Git
stage·commit·push 대상이 아니다.

## 거래와 완결 조건

attempt ID는 `ENDPOINT_FULL1`이다. prior witness, result 또는 progress가 하나라도 있으면
재실행하지 않는다. HTTP retry는 같은 object/version GET 안에서만 허용한다. clinical
18개 cell 중 하나라도 zero clean이면 `CLINICAL_PAIR_UNAVAILABLE`; source 실패는
`SOURCE_STOP`; 계산·authority 실패는 `IMPLEMENTATION_STOP`으로 terminal journal에
남긴다. bipolar zero는 clinical result를 보존하고 전체 bipolar bundle을
`BIPOLAR_SENSITIVITY_UNAVAILABLE`로 둔다.

완결은 다음을 모두 요구한다.

1. 18/18 source identity와 total bytes가 frozen lock과 일치한다.
2. predecessor Q 두 row가 새 전수 재계산과 exact 일치한다.
3. witness-backed independent validator가 모든 결과 leaf를 재계산한다.
4. result와 progress가 witness/result hash 및 rows로 상호 결박된다.
5. primary, 두 estimand, 두 reference 가능 범위, 세 window, bootstrap, LOO, paired와
   clean-count 표를 결과 방향과 무관하게 논문에 전부 보고한다.
