# BA-OBS-ID3 연구 계약 — 인간 CCEP의 제한된 능동 응답 대칭성

Status: COMPLETE

Mode: full real-brain interventional validation

PREDECESSOR: `_workspace/ce/brain-complete-active-metric-tomography-20260824`

CE_RUN: `_workspace/ce/brain-human-ccep-restricted-active-response-20260824`

Signal-state at freeze: metadata/schema/stimulation labels opened; derivative iEEG sample values unopened.

## 1. 질문과 주장 상한

BA-OBS-ID2는 실 separable Hilbert 공간에서 모든 countably complete exact quadratic
query가 임의 bounded strong metric을 유일하게 정한다는 수학 정리다. 실제 뇌에서는
그 oracle을 구현할 수 없다. 이번 run은 인간 single-pulse electrical stimulation
(SPES)과 intracranial EEG에서 더 좁은 질문만 검사한다.

> 같은 bipolar electrode-pair 집합을 자극 좌표와 수신 좌표로 맞췄을 때, early CCEP
> magnitude의 finite observed response matrix는 split-half noise가 설명하는 범위에서
> reciprocal한가, 아니면 재현 가능한 방향 비대칭을 보이는가?

이 질문은 $G$ 또는 $M=G^{-1}$ 자체를 복원하지 않는다. 관측 응답의 대칭성이 깨지면
"CCEP magnitude matrix를 BA-OBS-ID2의 self-adjoint mobility block으로 직접 읽는다"는
naive observed proxy를 기각한다. 대칭성이 기각되지 않아도 metric, neuron edge,
consciousness, self, hippocampal hash 또는 AGI가 확인되는 것은 아니다.

## 2. 선행 증거 잠금

| predecessor | evidence / SHA-256 | status | preserved result | retry prohibition |
|---|---|---|---|---|
| BA-OBS-ID2 | `40-final-report.md`, `9d295684bfbdcb3d5e2ec807f3bc48d44f0d35690cd89511af156f77d9ae99f4` | PASS | Countably complete exact quadratic response는 arbitrary strong metric을 전역 유일하게 정한다. 모든 finite query set에는 blind tail이 남는다. | 이번 real run을 full ambient-metric recovery로 쓰지 않는다. |
| BA-SRM4-EEG R0 | `40-final-report.md`, `ea1085ad853bdc63a36f698dfea59730c7ffdc976878206699d451d95c4a2552` | APPARATUS_INVALID_OR_BASELINE_UNRESOLVED | Remote scalp-EEG byte-range apparatus는 작동했으나 frozen 2D linear state baseline이 persistence를 이기지 못했다. | ds006033의 sealed signal이나 같은 baseline을 retune하지 않는다. |
| BA-OBS-NOGO1 | route-ledger frozen entry | PASS theorem | Finite passive observation은 ambient neural metric과 dimension을 식별하지 못한다. | CCEP finite matrix를 ambient metric으로 승격하지 않는다. |

## 3. 실제 생물 입력과 측정모형

**[외부 입력: 확립 자극 프로토콜]** OpenNeuro `ds003708`의 환자 한 명은 병상에서
휴식하는 동안 약 $0.2\,\mathrm{Hz}$로 bipolar single-pulse stimulation을 받았다.
Pulse duration은 $200\,\mu\mathrm{s}$, current는 이번 eligible set에서 모두
$6\,\mathrm{mA}$다. Pulse는 biphasic이다.

자극 site $s$의 물리 입력을 $u_s(t)$라 하고, contact $c$의 관측전압을
$V_{c\leftarrow s,k}(t)$라 한다. 방어 가능한 유한창 측정모형은

$$
V_{c\leftarrow s,k}^{\rm obs}(t)
=C_{\rm ref}R_c[H_s*u_s](t)
+a_{csk}(t)+\eta_{csk}(t),
$$

이다. $H_s$는 causal neural response, $R_c$는 electrode/volume-conduction readout,
$C_{\rm ref}$는 reference transform, $a$는 stimulation artifact, $\eta$는 생리·전자
잡음이다. 이 분해는 $H_s$, $R_c$, $C_{\rm ref}$와 metric을 서로 식별하지 않는다.

**[측정 입력]** Primary signal은 공개 derivative의 adjusted common-average reference
(A-CAR) BrainVision float32 data다. A-CAR는 각 64-channel cable block에서 stimulation
전후 분산이 가장 낮은 75% channel만 common average에 사용한다. Primary readout은
receiver pair의 두 contact를 contact-level magnitude에서 평균한다. Matched reference
control은 같은 두 contact의 bipolar difference다.

**[공리: 시험할 CE proxy P1]** 동일한 24개 bipolar pair를 input과 output coordinate로
맞춘 finite observed response가 하나의 self-adjoint mobility compression을 직접
반영한다면, reference와 gain 차이를 무시한 가장 좁은 예측은 reciprocal symmetry다.

$$
A_{r\leftarrow s}=A_{s\leftarrow r}.
$$

P1은 BA-OBS-ID2에서 자동으로 나오지 않는다. $B^*MB$ 꼴의 aligned input/readout과
짧은창 선형화를 추가 채택한 **[공리: 모델 선택]**이다. 이번 data가 직접 반증할
대상은 P1뿐이다.

## 4. 데이터 provenance와 source lock

- Dataset: OpenNeuro `ds003708`, derivative descriptor DOI
  `10.18112/openneuro.ds003708.v1.0.2`, CC0, BIDS-iEEG.
- Primary paper: Miller, Müller, Hermes (2021), PLoS Computational Biology,
  DOI `10.1371/journal.pcbi.1008710`.
- Subject/session: `sub-01/ses-ieeg01`, one implanted epilepsy patient, one CCEP run.
- Sampling: $2048\,\mathrm{Hz}$; 89 channels; 76 ECoG, 12 SEEG, 1 ECG.
- Frozen S3 object:
  `ds003708/derivatives/preprocessed/sub-01/ses-ieeg01/ieeg/sub-01_ses-ieeg01_task-ccep_run-01_ieeg.eeg`.
- Object identity: `ContentLength=2899637088`,
  `ETag=9832a1868bff527620c3cec91df4bb81-3`,
  `VersionId=ekxCFJH.NE2DhaUDkQ_Nc0iIxeHeLgF4`.
- Frozen metadata hashes:
  - events TSV: `f4767c8d6f25a641e706d5bee7dfc928b9ca4501c54bf33b67e96dc5562a9aab`;
  - channels TSV: `baf23675a6dd235a7a37549ec16ddcd9e0cebd5b7fa26348b0dcb0f5f82a1318`;
  - MNI electrodes TSV: `6606045c8881d7ed1ef15990c9160e2884bec8789b59aeb9bd5dba709a4b6aec`;
  - BrainVision header: `5551a8ca58fe16f489956981ab6437ae65c041891273c08fbea13dfab70cef4a`;
  - BrainVision marker: `a2e09a018d1359aaf1e8d0bdb65586ec0e4f9611ab9455497d83b3b7b7cfca24`;
  - derivative README: `24b59bb2a00971fe9e56a0cef2e9a1368fc86a0a9637e4f395c368e8bae7c908`.

Signal acquisition은 HTTP/S3 byte range만 사용한다. 각 range의 start/end, returned byte
count와 SHA-256을 receipt에 기록한다. ETag, VersionId 또는 metadata hash가 다르면
signal endpoint를 열지 않고 `SOURCE_IDENTITY_STOP`으로 끝낸다.

Raw epoch의 canonical 0-based anchor는 같은 BrainVision export의 `.vmrk` position에서
1을 뺀 값이다. Marker 425개와 events 425개를 행 순서로 one-to-one 대응시켰을 때
`raw_anchor - sample_start`는 $-1$인 event 201개와 $0$인 event 224개여야 한다.
Events의 `sample_start`는 425/425에서 $\operatorname{round}(2048\,t_{\rm onset})$와
일치해야 한다. 이 count나 관계가 다르면 byte decode 전에
`SOURCE_METADATA_ALIGNMENT_STOP`으로 끝낸다. 닫힌 시간창 $[a,b]$의 sample offset은
$\lceil 2048a\rceil\le j\le\lfloor2048b\rfloor$인 정수 $j$만 포함한다($a,b$의 단위는
second). 따라서 epoch acquisition은 anchor 기준 $-1024\le j\le512$를 가져오며
각 endpoint는 이 공통 time grid의 boolean mask로만 정한다.

## 5. Metadata-only eligibility와 split

Signal 값과 무관하게 다음 조건을 모두 만족하는 stimulation site만 사용한다.

1. event `status=good`이고 current가 정확히 `6.0 mA`;
2. 같은 site에서 good event가 10개 이상;
3. pair의 두 contact가 모두 `status=good`이고 type이 ECoG 또는 SEEG;
4. 두 contact 모두 finite MNI coordinate가 있음.

동결된 24개 site는 다음과 같다.

`LPS2-LPS3`, `LTG10-LTG11`, `LTG11-LTG12`, `LTG13-LTG14`,
`LTG15-LTG16`, `LTG17-LTG18`, `LTG19-LTG20`, `LTG1-LTG2`,
`LTG20-LTG21`, `LTG22-LTG23`, `LTG23-LTG24`, `LTG25-LTG26`,
`LTG26-LTG27`, `LTG27-LTG28`, `LTG28-LTG29`, `LTG29-LTG30`,
`LTG2-LTG3`, `LTG30-LTG31`, `LTG31-LTG32`, `LTG3-LTG4`,
`LTG4-LTG5`, `LTG5-LTG6`, `LTG6-LTG7`, `LTG9-LTG10`.

Receiver와 stim pair가 contact 하나를 공유하거나 pair-midpoint Euclidean distance가
$15\,\mathrm{mm}$ 미만이면 volume-conduction/artifact control로 제외한다. 남은 unordered
site pair는 245개다.

각 unordered pair는 위에 동결한 24-site **나열 순서**에서 index가 작은 site를 $a$,
큰 site를 $b$로 둔다. 사전식 문자열 정렬은 금지한다. 이 순서로 정한 $(a,b)$에

$$
h_{ab}=\operatorname{SHA256}(
\texttt{ds003708-v1.0.2|}a\texttt{|}b)_0
$$

를 적용한다. $h_{ab}$는 digest의 첫 byte다.

- calibration: $0\le h\le152$, 151 pairs;
- development: $153\le h\le203$, 42 pairs;
- confirmation: $204\le h\le255$, 52 pairs.

각 stimulation site의 good trials은 onset 순으로 정렬하고 0-based even index를 half A,
odd index를 half B에 배정한다. 모든 eligible site는 각 half에 최소 5 trials이 있다.
Calibration/development만 apparatus 판정에 사용하며 confirmation endpoint는 development
gate 통과 뒤 한 번만 계산·직렬화한다.

이번 판본에서는 calibration 151 pairs로 window, threshold 또는 decoder를 고르지 않는다.
그 pair endpoint는 계산·직렬화하지 않으며 metadata allocation 확인에만 남긴다. Raw
BrainVision range는 multiplexed라 다른 receiver channel sample도 함께 반환하지만,
development gate 이전 code path는 confirmation response를 산출하거나 표시하지 않는다.

## 6. 무차원 관측량

BrainVision value는 header resolution $0.1\,\mu\mathrm V$를 적용한다. Trial마다
$[-500,-5]\,\mathrm{ms}$ baseline mean을 뺀 뒤 half 안에서 waveform을 평균한다.
Baseline scale $\sigma_{csh}$는 같은 half의 모든 baseline residual sample의 표준편차다.
Nonfinite 또는 $\sigma_{csh}\le0$이면 해당 edge를 사용하지 않고 apparatus gate를
실패시킨다.

Contact-level early response는

$$
Z_{c\leftarrow s}^{(h)}
=
\max_{10\,\mathrm{ms}\le t\le50\,\mathrm{ms}}
\frac{|\overline V_{c\leftarrow s}^{(h)}(t)|}
{\sigma_{csh}}
$$

로 둔다. Ratio이므로 무차원이다. Receiver node $r=(c_1,c_2)$의 primary A-CAR
response는

$$
A_{r\leftarrow s}^{(h),\rm mean}
=\frac{Z_{c_1\leftarrow s}^{(h)}+Z_{c_2\leftarrow s}^{(h)}}2
$$

다. Bipolar control은 $V_{c_1}-V_{c_2}$를 먼저 만든 뒤 같은 baseline normalization과
early maximum을 적용한 $A^{(h),\rm bip}$다.

Prestimulus matched control은 같은 계산을 $[-250,-210]\,\mathrm{ms}$에 적용한
$P_{r\leftarrow s}^{(h)}$다. 첫 $10\,\mathrm{ms}$는 stimulation artifact 때문에 어떤
endpoint에도 쓰지 않는다. Late $[50,250]\,\mathrm{ms}$ magnitude는 secondary
descriptive output이며 primary 판정을 바꾸지 않는다.

두 nonnegative dimensionless response의 normalized disagreement를

$$
d(x,y)=\frac{|x-y|}{x+y+10^{-12}}
$$

로 둔다. $10^{-12}$도 dimensionless numerical floor다.

## 7. Development apparatus gate

각 readout $m\in\{\mathrm{mean},\mathrm{bip}\}$에서 development directed edges에 대해
다음을 모두 요구한다.

1. half-A/half-B response Spearman correlation $\rho_{\rm rep}^{(m)}\ge0.50$;
2. median early response를 median prestimulus control로 나눈 비가 $\ge1.25$;
3. 모든 planned ranges가 exact byte count와 finite float32 decode를 만족;
4. 42 unordered development pairs 전부에서 양방향 response가 정의됨.

하나라도 실패하면 `APPARATUS_OR_EVOCATION_STOP`으로 닫고 confirmation statistic을
계산하지 않는다. Gate를 본 뒤 window, threshold, reference, site 또는 trial을 바꾸지
않는다.

## 8. Confirmation reciprocity falsifier

각 confirmation unordered pair $\{r,s\}$와 readout $m$에 대해

$$
u_{rs}^{(m)}
=\frac12\left[
d(A_{r\leftarrow s}^{(A,m)},A_{r\leftarrow s}^{(B,m)})
+d(A_{s\leftarrow r}^{(A,m)},A_{s\leftarrow r}^{(B,m)})
\right],
$$

$$
v_{rs}^{(m)}
=\frac12\left[
d(A_{r\leftarrow s}^{(A,m)},A_{s\leftarrow r}^{(B,m)})
+d(A_{r\leftarrow s}^{(B,m)},A_{s\leftarrow r}^{(A,m)})
\right].
$$

$u$는 same-direction split-half disagreement, $v$는 independent-half reciprocal
disagreement다. Primary ratio는

$$
R^{(m)}
=\frac{\operatorname{median}v_{rs}^{(m)}+10^{-12}}
{\operatorname{median}u_{rs}^{(m)}+10^{-12}}.
$$

단순 $R>1.25$는 방향별 trial precision이 다를 때 reciprocal signal도 기각할 수 있다.
따라서 raw $R$은 effect-size tolerance로만 남기고, 각 방향·half의 실제 이분산성을
보존한 restricted-null resampling으로 tail을 교정한다.

각 site와 half의 실제 trial 수를 유지한 채 replacement resample하고, 같은
`(site, half, b)` index draw를 그 site의 모든 receiver에 공유한다. Baseline mean,
$\sigma$, early maximum과 두 readout을 매번 원 code path로 다시 계산하여
$A_e^{(h,m,b)}$를 얻는다. $B=8192$, root seed는 3708이고 site label과 half에서 파생한
결정적 child stream을 사용한다. 선택 index의 SHA-256도 receipt에 기록한다.

모든 raw $A$가 finite positive임을 먼저 확인하고

$$
L_e^{(h,m)}=\log(A_e^{(h,m)}+10^{-12})
$$

로 둔다. $b=1,\ldots,B$에 대해 bootstrap log residual을

$$
\widetilde e_e^{(h,m,b)}
=L_e^{(h,m,b)}-L_e^{(h,m)},
\qquad
e_e^{(h,m,b)}
=\widetilde e_e^{(h,m,b)}
-\frac1B\sum_{b'=1}^{B}\widetilde e_e^{(h,m,b')}
$$

로 정확히 중심화한다. Confirmation unordered pair $q=\{r,s\}$의 restricted-P1
공통 중심은

$$
\bar L_q^{(m)}=
\frac14\sum_{h\in\{A,B\}}
\left(L_{r\leftarrow s}^{(h,m)}+L_{s\leftarrow r}^{(h,m)}\right)
$$

이다. 방향·half별 noise는 그대로 두고 reciprocal location만 같게 만든 null surrogate는

$$
A_{0,e}^{(h,m,b)}
=\exp\!\left(\bar L_q^{(m)}+e_e^{(h,m,b)}\right)
$$

다. 이 surrogate에 위의 $u,v,R$ 정의를 그대로 적용하여 $R_{0,b}^{(m)}$를 얻고

$$
p_R^{(m)}=
\frac{1+\#\{b:R_{0,b}^{(m)}\ge R_{\rm obs}^{(m)}\}}{B+1}
$$

를 계산한다. 이것은 population p-value나 95% confidence interval이 아니라, **이 한
피험자와 동결된 site set에 조건부인 restricted-null resampling tail area**다.

Readout별 기각 indicator를

$$
\phi_m=
\mathbf 1\{R_{\rm obs}^{(m)}>1.25\ \text{and}\ p_R^{(m)}\le0.025\}
$$

로 둔다.

- $\phi_{\rm mean}=\phi_{\rm bip}=1$:
  `REFERENCE_ROBUST_OBSERVED_MAGNITUDE_RECIPROCITY_PROXY_REFUTED`;
- $\phi_{\rm mean}=\phi_{\rm bip}=0$:
  `PROVISIONAL_FIXED_SET_TYPICAL_RECIPROCITY_NOT_REFUTED`;
- 두 값이 다름: `REFERENCE_SENSITIVE_OR_INCONCLUSIVE`.

두 번째 label은 symmetry/self-adjointness의 증거가 아니며 fixed 52-pair typical
disagreement에서 reference-robust 기각이 없었다는 뜻뿐이다. Short/long distance,
late-window raw $R$은 descriptive controls이고 primary verdict를 바꾸지 않는다.

## 9. 구현 전 합성 falsifier

Real signal을 열기 전에 같은 code path가 다음 fixtures를 통과해야 한다.

1. `restricted_null_heteroscedastic`: 동결된 24 sites, list-order 52 confirmation pairs,
   실제 site별 half trial 수, 정확히 reciprocal한 latent early response를 사용한다.
   Direction/site noise SD는 hash로 고정한 geometric $1{:}16$, baseline scale은 독립
   $1{:}8$ 범위이며 Gaussian과 unit-variance centered $t_5$ scenario를 각각 실행한다.
2. 각 scenario에서 outer fixture seed 370800--371055의 256개와 inner restricted-null
   resample 2048개를 사용한다. 적어도 한 fixture/readout에서 uncalibrated raw
   $R>1.25$여야 원 통계의 pathology를 실제로 건드린다. 그런데 calibrated composite
   refutation은 scenario별 최대 7/256이어야 한다. 실패하면
   `STATISTICAL_FALSE_POSITIVE_STOP`이다.
3. `directed_power`: 같은 heteroscedastic noise에서 동결 hash로 선택한 최소 75% edge에
   fixed reciprocal log-gap $\log(1.6)$을 준다. Gaussian과 $t_5$ 각각에서 calibrated
   composite refutation이 최소 205/256이어야 한다. 실패하면
   `STATISTICAL_POWER_STOP`이며 real P1 verdict를 열지 않는다.
4. Early window가 prestimulus와 같은 null fixture에서 development evocation gate STOP;
5. truncated/wrong-length range, metadata hash mismatch, marker/event count 또는 허용된
   $\{-1,0\}$ 밖의 anchor mismatch가 signal decode 전 STOP;
6. confirmation serialization이 development failure 뒤 false임.

Fixture는 baseline correction, resampling, early maximum, contact-average/bipolar와
restricted-null calculation을 실제 분석과 같은 함수로 통과해야 한다. Node count 24,
confirmation pair count 52, root seed 3708은 고정한다. Real confirmation resample에서
단 하나라도 nonfinite, nonpositive $A$, $\sigma\le0$ 또는 invalid surrogate가 나오면
`APPARATUS_OR_RESAMPLING_STOP`이고 $10^{-12}$ floor로 invalid value를 숨기지 않는다.

## 10. 뇌/AGI 필수 필드

- **BIO_STARTING_MECHANISM:** $6\,\mathrm{mA}$, $200\,\mu\mathrm{s}$ biphasic SPES와
  early $10$--$50\,\mathrm{ms}$ CCEP magnitude; human iEEG.
- **CE_DELTA:** aligned finite input/readout에서 observed response가 self-adjoint
  compression처럼 reciprocal하다는 proxy P1.
- **MEASUREMENT_MODEL:** causal response + iEEG readout + A-CAR/bipolar reference +
  stimulation artifact + noise; baseline-normalized magnitude.
- **DATA_PROVENANCE:** OpenNeuro `ds003708` derivative v1.0.2; exact S3 object identity와
  metadata SHA-256 고정.
- **DATA_SPLIT:** metadata-hash 151/42/52 unordered pairs; onset-order even/odd trial halves.
- **OBSERVABLES:** dimensionless early/prestimulus magnitude, split-half Spearman,
  $u$, $v$, raw $R$, heteroscedastic restricted-null $R_0$와 conditional tail $p_R$.
- **RESIDUAL_RULE:** raw reciprocal/split-half ratio를 방향·half별 trial-resampling
  residual이 보존된 reciprocal-location null과 비교; post-hoc scaling/edge deletion 금지.
- **FALSIFIER:** 두 reference 모두 raw $R>1.25$이고 restricted-null $p_R\le0.025$일 때만
  naive observed magnitude reciprocity proxy P1 기각.
- **MATCHED_CONTROLS:** A-CAR contact-average versus bipolar readout, prestimulus window,
  distance strata, late window, split-half repeatability.
- **MODEL_SELECTION:** 없음. Window, site eligibility, split, statistic, fixture와 threshold
  단일 고정. Calibration pair endpoint는 사용하지 않음.
- **REVISION_TRIGGER:** ds003708 결과를 본 뒤 이 run을 retune하지 않는다. 다음 판본은
  다환자 `ds004457`를 새 계약과 독립 split으로 source-lock해야 한다.
- **CLAIM_CEILING:** SINGLE_SUBJECT_HUMAN_CCEP / FINITE_RESTRICTED_OBSERVED_RESPONSE_RECIPROCITY_FALSIFIER / REAL_INTERVENTIONAL_DATA / NO_AMBIENT_OR_INFINITE_DIMENSIONAL_METRIC_RECOVERY / NO_POLARIZATION_TOMOGRAPHY / NO_POPULATION_GENERALIZATION / NO_CONSCIOUSNESS_SELF_HIPPOCAMPUS_OR_AGI_VALIDATION.

## 11. 해석 금지선

1. 이 dataset에는 $s_i+s_j$, $s_i-s_j$ superposition query가 없으므로 BA-OBS-ID2의
   polarization tomography를 검증하지 않는다.
2. 모든 primary eligible event가 $6\,\mathrm{mA}$이므로 amplitude linearity를
   검증하지 않는다.
3. Patient는 임상적으로 electrode가 삽입된 단일 epilepsy subject다.
4. CCEP directionality는 causal neural dynamics와 measurement map을 함께 포함한다.
   비대칭성은 brain metric의 비존재를 뜻하지 않는다.
5. 대칭성 비기각은 equivalence proof나 positive metric identification이 아니다.
6. 어떤 결과도 의식, 자아, 현재-세계 manifold, 해마 hash 또는 AGI를 검증하지 않는다.
