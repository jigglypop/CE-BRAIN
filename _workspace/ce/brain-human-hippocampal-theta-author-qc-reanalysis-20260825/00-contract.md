# BA-OBS-HPC2 연구 계약 — 저자 순서 QC와 endpoint 봉인을 분리한 실제 인간 해마 iEEG 재분석

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-human-hippocampal-theta-raw-replication-20260825`

Mode: light successor. 선행 run의 dataset/source/mechanism 결론은 재유도하지 않고,
측정 aperture와 QC transaction만 새로 고정한다.

## 0. PREDECESSOR_EVIDENCE와 새 질문

| evidence | receipt / hash | status | 보존 주장 | 재사용 금지 |
|---|---|---|---|---|
| HPC1 final | predecessor `40-final-report.md`; `check final = OK` | `STOP_MEASUREMENT_APERTURE` | p16 eppre 실제 raw 60,480,000 bytes의 full SHA-256 일치 | 같은 contract의 raw retry, cohort/threshold 사후 변경 금지 |
| HPC1 source lock | `0b3d92f998f626ed37f68d0dfb1188a777afb287975916beec1f623d10d3fc58` | metadata 18/18 locked | object/header/channel/version identity | 새 endpoint 결과로 간주 금지 |
| HPC1 attempt 1 | `raw_progress.json` SHA-256 `ce502e77ff83186359259e6129b06d6580c07187740a945a14c7310687a76934` | one completed object, next file aperture stop | endpoint·clean count·biological verdict 없음 | 실패 count를 추정해 threshold 선택 금지 |

선행 계약은 baseline 뒤 artifact rule을 적용하고 `20 trials AND 50%`를 요구했다.
공개 저자 코드 `run_ep_preproc.m`은 artifact rule을 baseline 전에 적용하고 50% 비율
게이트를 두지 않는다. 이 source-defined 순서 차이는 raw endpoint가 아니라 정적 코드에서
확인됐다. successor의 질문은 다음과 같다.

> 공개 코드가 정한 artifact-before-baseline 순서와 outcome-blind QC seal을 사용하면,
> 모든 고정 pre/post file에서 최소 20 clean trials를 확보한 뒤에만 동일한 late SEP
> participant-equal endpoint를 열 수 있는가?

이 run도 published outcome이 알려진 same-data reanalysis다. 독립 confirmation이 아니다.

## 1. BIO_STARTING_MECHANISM과 CE_DELTA

### BIO_STARTING_MECHANISM

출발 기전은 predecessor와 같은 state-dependent cortico-hippocampal communication이다.
해마 theta trough에 동기화한 LTC stimulation(TS)과 phase-blind stimulation(PB)의 전후
해마 stimulation-evoked potential을 비교한다. early 15–50 ms와 late 50–250 ms는 각각
더 직접적인 성분과 multi-node propagation을 포함할 수 있는 관측 proxy이지 해부학적
edge weight가 아니다.

### CE_DELTA

$$
y^{(r)}(t\mid\mathcal H,c)=C_r(h_{\mathcal H,c}*u)(t)+a^{(r)}(t)+\eta^{(r)}(t)
$$

에서 $u$는 area-one normalized ideal pulse이고, 직접 식별하는 것은 $h$가 아니라
frozen P2P contrast다. CE 추가 조건은 history-conditioned late contrast가 clinical과
local bipolar reference에서 함께 양의 participant-level 불확실성 하한을 갖고,
prestimulus control이 같은 signal을 만들지 않는지다.

## 2. DATA_PROVENANCE와 source lock

- OpenNeuro `ds006065` v1.0.0, DOI `10.18112/openneuro.ds006065.v1.0.0`.
- release commit `14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4`, tree
  `615b6b5caf83776094a4fdfb7ffc168993d80ade`.
- Author code archive Zenodo `14735080`, archive MD5
  `6feba89b7c49fd661b39b589e8d9624a`.
- `run_ep_preproc.m` SHA-256
  `626a7467f803c28302ad712b24b891752b013fc471fec7f0057d529fc7ff0729`.
- `run_group_ep.m` SHA-256
  `d4a0ad2cee828c60fb87f91fc63a9c81b3588c974335350ed5fce10f2ac38da4`.
- `compare_p2p.m` SHA-256
  `c6ab8439b109b0b9cf1c046a8045c9fe2be3df72222921a7450c5515cf8d486c`.

18-object cohort, blocks, primary contact, local bipolar pair는 predecessor 표와 동일하다.
p20 clinical QC만 공개 `run_group_ep.m`의 ordered selection `D9,C1,C'1`을 모두 읽고,
endpoint는 사전 고정 첫 채널 D9만 쓴다. local bipolar endpoint/QC는 D9-D10이다.
새 source lock은 extra p20 QC indices, unit scaling, full header/channel order, annex SHA/size,
S3 version/ETag를 포함하고 raw 전에 exact byte hash로 동결한다.

## 3. DATA_SPLIT와 candidate routing

### DATA_SPLIT

NO_DISCOVERY_SPLIT / SAME_PUBLIC_DATA / PREDECESSOR_ENDPOINT_UNOPENED.

QC count는 endpoint와 분리한다. raw를 한 번 순차 streaming하면서 file integrity와 clean
count만 즉시 atomic receipt에 쓴다. P2P waveform·trial P2P·contrast는 메모리에만 두고,
18개 file의 두 frozen reference가 모두 aperture를 통과한 뒤에만 final endpoint receipt에
직렬화한다. 하나라도 실패하면 QC counts와 source integrity만 남기고 모든 endpoint
summary를 버린다.

후보 경로는 raw 전에 다음처럼 고정한다.

- R1 `AUTHOR_ORDER_QC_SEAL`: 선택. 공개 artifact-before-baseline 순서와 ≥20 count,
  endpoint-sealed transaction.
- R0 `HPC1_BASELINE_FIRST_50_PERCENT`: 퇴역. predecessor에서 terminal STOP.
- R2 `COUNT_TUNED_THRESHOLD`: 금지. predecessor가 실패 count를 남기지 않았고 사후
  threshold 선택은 근거가 없다.
- R3 `SOURCE_DATA_TARGET_MATCH`: 금지. Nature aggregate로 raw reader/QC를 맞추지 않는다.

## 4. MEASUREMENT_MODEL

### 4.1 Author-code time and preprocessing convention

Raw block은 1000 IEEE little-endian float32 multiplexed samples다. 저자 코드의 time vector를
그대로 명시한다.

$$
\tau_j=\frac{j}{999}\frac{1000}{499.5}\ \mathrm{s}-0.5\ \mathrm{s},
\qquad j=0,\ldots,999.
$$

`run_preproc`가 마지막 sample을 제외하므로 preprocessing input은 $j=0,\ldots,998$다.
그 뒤 저자 `ft_timelockanalysis` latency에 대응해 $-0.4\le\tau_j\le0.8$만 사용한다.
math fixture가 고정한 global-index masks는 latency `50..648`(599 samples), baseline
`225..244`(20), early `257..274`(18), late `275..374`(100), prestimulus
`100..199`(100)다.

순서는 다음과 같다.

1. 첫 999 samples에서 contract-defined sine/cosine least-squares로 60/120/180 Hz를
   제거한다. 이는 저자 FieldTrip grammar의 Python analogue이지 exact FieldTrip parity
   주장이 아니다.
2. p17만 10차 80 Hz Butterworth zero-phase low-pass를 적용한다.
3. $[-0.4,0.8]$ s latency를 선택한다.
4. 아래 artifact mask를 **baseline 전에** 계산한다.
5. 통과 trial만 남긴 뒤 $[-0.05,-0.01]$ s mean을 뺀다.
6. early $[0.015,0.05]$, late $[0.05,0.25]$, prestimulus $[-0.3,-0.1]$ s
   closed windows를 계산한다.

### 4.2 Frozen references and artifact masks

- clinical endpoint: 표의 published readout contact. p20 endpoint는 D9.
- clinical QC: 일반 subject는 endpoint contact 하나; p20은 D9,C1,C'1 세 채널이 모두
  artifact criteria를 통과해야 한다.
- local bipolar endpoint/QC: 첫 contact minus 둘째 contact 한 trace.

각 QC trace/채널에서 trial이 다음을 모두 만족해야 한다.

1. $|t|>50$ ms에서 max absolute amplitude $<500\,\mu\mathrm V$.
2. $t>50$ ms Pearson bias-corrected kurtosis $<5$.
3. trial 축 sample-wise MATLAB-compatible sample-SD z score에서 모든 $|z|\le5$.
4. finite이고 원 block 길이가 정확히 1000.

p20의 다채널 z-score는 저자 코드의 의도를 명시적으로 풀어 trial×channel×time 각각을
trial 축으로 표준화하고 모든 selected channel/time을 통과하도록 한다. 공개
`run_group_ep.m`의 p17/p19 control call에는 `k_thr` positional argument가 빠진 signature
결함이 있으므로, 다른 모든 call과 주석이 고정한 intended triple $(k,z,a)=(5,5,500)$을
적용하고 exact script execution이라고 부르지 않는다. 이 해석은 raw 전에
`artifacts/author-code-static-receipt.md`의 archive/file hash와 line-level semantic audit가
일치해야 한다. 불일치하면 `AUTHOR_QC_CALL_AMBIGUITY`로 중단한다.

### 4.3 Aperture

각 18 file에서 clinical QC와 local-bipolar QC가 각각 최소 20 trials를 남겨야 한다.
50% 비율 조건은 공개 코드에 없으므로 사용하지 않는다. 하나라도 20 미만이면 전체
endpoint를 열지 않고 `QC_STOP_MIN20`; cohort를 줄이거나 재실행하지 않는다.

## 5. OBSERVABLES, RESIDUAL_RULE, endpoint

### OBSERVABLES

항상 공개: 18 full-object expected/observed SHA-256·bytes·version/ETag/header/contact indices,
reference별 clean count, exclusion reason counts, source-lock/progress hash.

aperture 전체 통과 때만 공개: clean mean waveform, clean trial early/late/prestim P2P,
participant pre/post change, participant-equal $D$, 65,536-draw participant-cluster interval,
seven LOO, p17/p19 paired sensitivity, status lattice.

### RESIDUAL_RULE

QC mask는 결과와 무관하게 위 threshold로 한 번 계산한다. exclusion reason은 amplitude,
kurtosis, z-score, nonfinite를 중복 가능한 count로 기록한다. endpoint를 본 뒤 trial을
복구하거나 추가 제거하지 않는다.

Primary와 uncertainty는 predecessor와 동일하다.

$$
D_r^W=\frac14\sum_{s\in TS}\Delta_{s,TS,r}^W
-\frac15\sum_{s\in PB}\Delta_{s,PB,r}^W,
$$

primary는 late $W=[50,250]$ ms, participant equal, 단위 $\mu\mathrm V$다. 일곱 participant
shared-weight Bayesian bootstrap은 PCG64 seed 20260825, 65,536 draws, 95% equal-tail이다.
published Satterthwaite engine이 없으면 `PUBLISHED_MODEL_ENGINE_UNAVAILABLE`을 유지한다.

## 6. MATCHED_CONTROLS와 status lattice

PB protocol, early window, equal-duration prestimulus window, local bipolar reference,
seven LOO, p17/p19 paired sensitivity를 유지한다.

- `QC_STOP_MIN20`: 하나 이상의 file/reference가 clean trials <20. Endpoint 없음.
- `SAME_DATA_REANALYSIS_REFERENCE_ROBUST_SUPPORT`: clinical/local late $D>0$ 및 두 95%
  lower bound >0, clinical paired >0, clinical prestim lower bound ≤0, clinical late LOO
  전부 >0.
- `SAME_DATA_REANALYSIS_SUPPORT_SENSITIVITY_LIMITED`: clinical late $D>0$이나 위 조건 일부
  실패. 원인 flag를 모두 기록.
- `SAME_DATA_REANALYSIS_NOT_SUPPORTED`: clinical late $D\le0$이고 published direction
  unavailable.
- `ESTIMAND_DISCORDANT`: published-model direction과 participant-equal direction 불일치.

## 7. FALSIFIER와 REVISION_TRIGGER

1. source lock/header/unit/contact/hash mismatch: `STOP_SOURCE_IDENTITY`, raw 전에 중단.
2. synthetic author-grid/filter/artifact/baseline fixture 실패: `IMPLEMENTATION_INVALID`.
3. any clean count <20: `QC_STOP_MIN20`, endpoint 삭제.
4. clinical late $D\le0$: same-data support 삭제.
5. local late point/LCB 실패: reference-robust 부모 삭제.
6. prestimulus lower bound >0: `BASELINE_ARTIFACT_CONCERN`.
7. any clinical late LOO ≤0: `PARTICIPANT_SENSITIVE`.

raw 뒤 contact, time grid, order, threshold, min count, reference, seed, cohort를 바꾸지 않는다.
한 번의 audited `ATTEMPT1`만 허용한다. infrastructure나 QC failure 뒤 같은 판본 재실행은
없다. Nature Source Data는 endpoint receipt가 atomic commit된 뒤에만 aggregate
cross-check로 열 수 있다.

## 8. CLAIM_CEILING

SEVEN_EPILEPSY_SURGERY_PARTICIPANTS / REAL_HUMAN_IEEG /
DIRECT_ELECTRICAL_INTERVENTION / SAME_PUBLIC_DATA_AUTHOR_ORDER_QC_REANALYSIS /
ENDPOINT_VISIBLE_ONLY_AFTER_ALL_QC_PASS /
NO_OUTCOME_BLIND_INDEPENDENT_CONFIRMATION / NO_RANDOMIZED_POPULATION_CAUSAL_ESTIMATE /
NO_HEALTHY_GENERALIZATION / NO_MEMORY_BEHAVIOR /
NO_ANATOMICAL_GEODESIC_RIEMANNIAN_METRIC_CONSCIOUSNESS_SELF_HIPPOCAMPUS_HASH_OR_AGI.
