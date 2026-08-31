# CE-NPF AIND BCI E1 동일세포 개입 계약

Status: `SOURCE_SCHEMA_AUDIT_PASS_WITH_PROVIDER_METADATA_INVALID / RAW_CHUNK_LOCK_PENDING / VALUE_AUDIT_NOT_RUN`

Claim ceiling before a blind run: `BIO_EVIDENCE_L0`

Parent status: `FORMAL_L0_NUMERICAL_WITNESS_PASS / BIOLOGICAL_MEDIATION_UNTESTED`

Next gate: `AIND_BCI_E1_SELECTED_INPUT_CONTENT_AUDIT`

## 0. 목표, 이번 단계의 이유, 이탈 점검

**최종 목표.** 국소 회로의 물리·시냅스·전도 상태
\(\Theta\)가 출력-상대 리만 계량 \(g\)를 바꾸고, 그 변화가
독립 행동을 매개하는지를 실제 생물학 자료로 판정한다.

**이번 하위 목표.** 학습 전·후 같은 영상 야에서 반복한
단일세포 광자극으로 추정한 **randomized-target effective response contrast**의
변화가, 서로
독립인 trial block에서 추정한 출력 계량 변화를 예측하는지 검사한다.

**왜 필요한가.** 합성 fixture는 식의 계산 가능성만 보였다. 이
단계는 \(\Delta\Theta\to\Delta g\)의 첫 실자료 다리를 시도하되,
축삭 전도속도·물리적 시냅스 weight·행동 매개를 관측했다고
부르지 않는다.

**목표 명료성과 이탈.** 목표는 명확하다. 다만 이 자료는 식
(21.48)의 \(v\)나 식 (21.68)의 인과 매개를 식별하지 못한다.
그러므로 E1은 Stage 10의 다른 계보가 아니며, 양성이어도
`STAGE10_INTEGRATED_MODEL_NOT_IDENTIFIABLE`을 해제하지 않는다.

**다음 gate.** 먼저 22개 behavior-NWB prefix의 전체 object key·크기·opaque
ETag·LastModified inventory를 고정하고 필수 NWB/Zarr schema를 endpoint를 열지 않고
감사한다. 실제 분석에 내려받는 모든 metadata와 chunk는 그다음 content
SHA-256을 별도로 기록한다. pre/post 공통 target·same-ROI·physical clock의
값 수준 검사는 content lock 뒤에만 연다. 어느 gate든 실패하면 모형 적합으로
넘어가지 않는다.

## 1. 출처 잠금과 현재 상태

### 1.1 정본 코호트

정본은 Allen Institute SWDB 2026 BCI v2에 공개된 derived asset
22개, mouse 5마리의 목록이다. 각 asset ID, subject ID, 가변 이름,
S3 위치, `metadata.nd.json`과 behavior-NWB Zarr의 consolidated
`.zmetadata` 크기·ETag을 다음 manifest에 고정했다.

- [AIND BCI v2 source catalog](../6_뇌/국소회로_상태다양체_흐름_대응/repro/aind_bci_v2_source_lock.tsv)
- [BCI metadata and exact v2 asset list](https://allenswdb.github.io/physiology/ophys/BCI/BCI-metadata.html)
- [BCI NWB/Zarr fields](https://allenswdb.github.io/physiology/ophys/BCI/BCI-dataset.html)
- [pre/post photostimulation and BCI task](https://allenswdb.github.io/physiology/ophys/BCI/BCI-stimuli.html)
- [AIND public read-only metadata API](https://aind-data-access-api.readthedocs.io/en/latest/UserGuide.html)

공식 문서의 접근일은 2026-08-31이다. manifest 파일 자체의 SHA-256은
`80602529d57a673f58e0659344566fd0165080793e31f5cb106b5611d1f1ef38`이다.
manifest의 7-field canonical row
`asset_id|subject_id|asset_name|metadata_bytes|metadata_etag|nwb_zmetadata_bytes|nwb_zmetadata_etag\n`
22개를 manifest 순서로 이은 SHA-256은
`2f6247ea984eff10fd45db717c98ed256aaf5e73d15f63aeec577bbd0576aa66`이다.
이 값은 local manifest row commitment이지 API 응답 자체의 hash가 아니다.
auditor는 별도로 live provider의 `_id`, `name`, `location`, 두 subject ID가
manifest와 모두 같은지 검사한다. 정확한 object key는 각 행에서
`{asset_name}/metadata.nd.json`과
`{asset_name}/{asset_name에서 _processed_ 이하를 제거}_behavior_nwb/.zmetadata`
로 유일하게 생성하고, `s3_location`은 정확히
`s3://aind-open-data/{asset_name}`이어야 한다.

ETag는 여기서 opaque object identifier로만 취급한다. multipart 여부를
확인하지 않고 MD5나 SHA-256으로 해석하지 않는다. 현재 잠금은
**source catalog lock**이지 모든 array chunk의 byte lock이 아니다. 따라서
`RAW_CHUNK_LOCK_PENDING`을 유지한다.

읽기 전용 source/schema auditor와 영수증은 다음과 같다.

- [`audit_aind_bci_v2_source_schema.ps1`](../6_뇌/국소회로_상태다양체_흐름_대응/repro/audit_aind_bci_v2_source_schema.ps1)
- [`source/schema receipt`](../../artifacts/brain/ce_npf_aind_bci_e1_source_schema_v1/receipt.json)

auditor SHA-256은
`d07f02c386cf72afee9f101cdfd83b598f4ab888c1dfc60ca777f4066e2371b1`,
receipt SHA-256은
`cbc317f1c2173f364c7aede595bccf6ec15d4c424e3482daed52e8bebdd26d17`다.
22개 behavior prefix의 88,186 object, 160,509,574,918 byte
(149.486191 GiB)를 열거했고, manifest 순서의 per-asset inventory summary
SHA-256은
`cdda8cbb9df5442299e73d0bf20ed23359ea8965781e275d9d3457e9d639cd27`이다.
auditor는 이 object 수·byte 수·summary hash를 expected constant와 비교하므로
원격 inventory drift는 새 값을 기록하며 통과할 수 없다. 22/22에서 56개 필수
consolidated metadata key와 네 table의 required `colnames`, dF/F--region--ROI
세 축 일치, 양의 sampling rate, 엄격한 object-key 정렬을 확인했다. 이는
**장치·schema 통과**이지 array 값이나 생물 endpoint 통과가 아니다.

중요한 제한도 잠근다. provider의 `metadata.nd.json`은 22/22 모두
`metadata_status=Invalid`이고, behavior NWB의 running/locomotion/speed/wheel
key는 0/22다. 이를 보정하거나 `zaber_step_times`로 대치하지 않는다. 코호트는
두 genotype/indicator 계열(3 animals 대 2 animals)이고 일부 session의 FOV
metadata가 비어 있거나 달라지므로 분석은 session-nested로만 수행하며 세션 간
same-cell을 만들지 않는다. 계열 차이는 cohort-limited sensitivity로 보고하고
5 animals에서 보편 genotype 효과를 추정하지 않는다.

### 1.2 원 논문과 이 계약의 관계

Daie et al.은 두광자 광자극과 calcium imaging으로 mouse motor
cortex L2/3의 학습 관련 effective causal connectivity 변화를 보고했다.
현재 판본은 2026-03-05 게시된 **peer review 전 v1 preprint**이다.

- [Daie et al., *Functional reorganization of motor cortex connectivity during learning*](https://doi.org/10.64898/2026.03.03.709199)

원 논문의 결과를 이 계약의 새 계량 가설 성공으로 이식하지 않는다.
이 계약은 공개 v2 22-session subset에서 별도로 blind 평가한다.

## 2. 자료가 식별하는 것과 못하는 것

| 채널 | 자료의 관측 | E1에서 허용하는 이름 | 사용 금지 해석 |
|---|---|---|---|
| same population | 한 session의 같은 ROI table에서 pre/post | 동일 ROI 집합 | 세션 간 same-cell lineage |
| perturbation | 반복 단일세포 2P photostimulation | randomized-target effective response contrast | 무자극 대비 효과·monosynaptic weight |
| activity | dF/F, ROI mask, epoch·trial clock | calcium population response | spike rate의 무편향 직접측정 |
| time | 약 58 Hz imaging과 stimulus timestamp | calcium response lag | axonal conduction velocity |
| behavior | trial/reward/threshold clock; dynamic threshold | schema·clock QC와 비추론적 기술 | `hit` endpoint·독립 causal mediator endpoint |
| geometry | 출력 likelihood에서 추정 | output-relative functional metric | 피질 물리공간 metric·topology |

NWB에 raw conditioned-neuron fluorescence threshold \(F_L,F_U\)가 없고 실험 중
threshold가 변경되었다는 공식 주석 때문에 `hit`는 outcome, score, nuisance,
exclusion 어느 곳에도 쓰지 않는다. 공식 문서가 기술 오류를 경고한 threshold
crossing 이후의 `zaber_step_times`도 쓰지 않는다. trial duration, reward time,
threshold-crossing time은 schema·clock QC와 명시적인 비추론적 기술에만
허용하고, 새 행동 매개 결론에는 사용하지 않는다.

## 3. 색인, 공통 support와 입력 gate

\(a\)는 animal, \(s\)는 session, \(e\in\{0,1\}\)은 pre/post
photostimulation epoch, \(g\)는 stimulated target/group, \(n\)은 반복 trial,
\(i\)는 responder ROI, \(t\)는 NWB physical time이다. 관측 dF/F를
\(Y_{asegni}(t)\)로 둔다.

selected-input content audit은 값 누출을 줄이기 위해 순차 실행한다.

1. **A: epoch/clock preflight.** epoch 여섯 column, dF/F
   `starting_time`과 independent `imaging_rate`만 VersionId·compressed
   content SHA-256으로 잠그고 pre/BCI/post 존재, frame 범위와 1-frame
   synchronization을 검사한다.
2. **B: target/ROI join.** A가 cohort gate를 통과한 경우에만
   PhotostimTrials design column, dF/F ROI region, soma QC column을 연다.
3. **C: endpoint byte lock.** B까지 통과한 경우에만 사전지정 dF/F response
   chunk를 잠근다.

A 또는 B의 하드 gate가 실패하면 그 뒤의 chunk를 요청하지 않고
`E1_BLOCKED_INPUT`으로 끝낸다. 이 fail-closed 중단은 미실행 endpoint를
실패한 생물 가설로 세지 않기 위한 것이다.

세션 포함 표시자는

\[
\begin{aligned}
I_{as}=\mathbf 1\{&\text{source inventory and downloaded content hashes match},\
\text{pre, BCI, post epochs exist},\\
&f_s>0,\ \text{physical timestamps are monotone},\
\text{ROI and PhotostimTrials tables are joinable}\}
\end{aligned}
\tag{E1.1}
\]

로 고정한다. 결과값을 본 뒤 포함 예외를 만들지 않는다. dF/F의
`starting_time`을 \(t_0\), `starting_time/.zattrs`의 rate를 \(f_s\),
frame index를 \(k\)라 하면 input clock을

\[
t^{\rm frame}(k)=t_0+\frac{k}{f_s},\qquad
|t^{\rm table}-t^{\rm frame}(k)|\le f_s^{-1}
\]

로 잠근다. epoch, PhotostimTrials와 BCI Trials의 start/stop time·frame은
모두 finite이고 frame이 dF/F 범위 안에 있어야 하며 위 오차를 start와 stop에
각각 통과해야 한다. \((\text{start\_time},\text{id})\)로 정렬했을 때
start time은 엄격히 증가하고 대응 frame은 비감소하며 각 stop은 start보다
뒤여야 한다. 이는 table row 순서를 시간 순서라고 가정하지 않는 검사다.

pre/post 공통 target과 responder는

\[
\mathcal G_{as}=\mathcal G_{as0}\cap\mathcal G_{as1},\qquad
\mathcal R_{as}=\{i\in\{0,\ldots,N_{\rm ROI}-1\}:
\operatorname{is\_soma}_i=1,\ 
0\le\operatorname{soma\_probability}_i\le1,\ 
\operatorname{soma\_probability}_i\text{ is finite}\}
\tag{E1.2}
\]

이다.

selected-input content audit에서 epoch와 table index를 다음처럼 유일하게
해석한다. `intervals/epochs/stimulus_name`의 exact UTF-8 값
`photostim`과 `photostim_post`가 각각 정확히 한 번,
`BCI`가 한 번 이상 있어야 한다. 공식 schema가 허용하는 반복 `BCI`
row는 모두 같은 task epoch 집합으로 보존하며 첫 row만 고르지 않는다.
\(e=0\)은 `photostim`, \(e=1\)은 `photostim_post`다.
\(g\)는 `PhotostimTrials/group_index`, \(n\)은 같은 row의 원래
`PhotostimTrials/id` 정수값이다. table row 안의 모든 column 길이가 같고
ID가 유일해야 한다.

ROI join도 사후 선택하지 않는다. `roi_table/id`와 dF/F
`DynamicTableRegion rois`가 둘 다 정확한 integer sequence
\((0,\ldots,N_{\rm ROI}-1)\)여야 하며, `closest_roi`는 이 공통 ID로
해석한다. 따라서 식 (E1.2)의 soma QC와 pre/post 공통 responder가 유일하다.
각 \((e,g)\) 안에서 `closest_roi`가 하나뿐이고
같은 \(g\)의 pre/post 값도 같아야 한다. target의 laser \(x,y\), power,
duration은 유한하고 power·duration은 양수여야 한다. 이 값이 trial마다
달라질 때 쓰는 median은 IEEE finite 값의 오름차순에서 표준 sample median으로
정한다. `hit`, `lick_L`, `reward_time`, `threshold_crossing_times`,
`zaber_step_times`의 chunk는 이 input audit에서 요청하거나 decode하지 않는다.

\(g\notin\mathcal G_{as}\), \(i\notin\mathcal R_{as}\)인 값을 imputation하지
않는다. 직접 광학 artifact를 피하고 output support를 target마다 바꾸지 않도록
모든 공통 target의 `closest_roi(g)`를 responder 전체에서 먼저 제외한다.

\[
\mathcal R^{\rm resp}_{as}=\mathcal R_{as}\setminus
\{\operatorname{closest\_roi}(g):g\in\mathcal G_{as}\},
\qquad
\mathcal R^{\rm resp}_{as}=\mathcal R^Z_{as}\dot\cup\mathcal R^O_{as}.
\]

`SHA256(asset_id|roi_id|CE_NPF_AIND_BCI_E1_ROI_V1)`를 unsigned byte
lexicographic order로 정렬하고 hash 동률은 integer `roi_id`로 끊는다.
\(N_{\rm resp}=|\mathcal R^{\rm resp}_{as}|\),
\(N_Z=\lfloor0.75N_{\rm resp}\rfloor\)라 할 때 rank 앞 \(N_Z\)개는
state/chart \(\mathcal R^Z\), 나머지는 metric output \(\mathcal R^O\)로
고정한다. 두 집합은 pre/post에서 동일하고 역할을 겹치지 않는다.

하드 입력 중단은 다음이다.

- 고정한 22 asset 중 5 animal을 모두 보존할 수 없음
- 분석 가능 세션이 animal당 2개 미만이거나 전체 15개 미만
- 세션당 pre/post 공통 target 30개 미만 또는 target당 각 epoch 20 trial 미만
- physical clock 역전, stimulus/activity 동기 오차 1 frame 초과
- source catalog 변경, 필수 field 누락, 또는 analysis environment 미고정
- 식 (E1.11)의 네 role 중 target·epoch별 최소치 \((8,4,4,4)\) 미달
- \(|\mathcal R^Z_{as}|<10d\) 또는
  \(|\mathcal R^O_{as}|<\max(50,5d)\)

하나라도 해당하면 `E1_BLOCKED_INPUT`으로 멈추고 수치 결과를 내지
않는다. 이 문턱은 자료를 보기 전 고정한 feasibility 문턱이다.

## 4. artifact 제거와 표적--반응 대조 관측식

각 trial의 stimulus onset/offset을 \(t^{\rm on}_{egn},t^{\rm off}_{egn}\),
다음 trial onset을 \(t^{\rm next}_{egn}\)로 둔다. baseline과 response
window를 결과와 무관하게

\[
\mathcal B_{egn}=[t^{\rm on}_{egn}-0.50,\ t^{\rm on}_{egn}-0.10],
\tag{E1.3}
\]

\[
\mathcal W_{egn}=\left[t^{\rm off}_{egn}+0.05,\
\min\{t^{\rm off}_{egn}+0.55,t^{\rm next}_{egn}-0.05\}\right]
\tag{E1.4}
\]

로 고정한다. \(|\mathcal W|<0.25\,\mathrm s\)인 trial은 제외한다. 기저선
window와 response window가 모두 dF/F physical clock 범위 안에 있어야 한다.
\(t^{\rm next}\)는 같은 epoch의 PhotostimTrials row를
\((\text{start\_time},\text{id})\)로 정렬했을 때 바로 다음 row의 onset이다.
같은 epoch에 successor가 없는 마지막 row는 이 계약에서 eligible하지 않다.
이 조건들을 통과한 원래 `PhotostimTrials/id`만 eligible trial이며, 아래
\(N_{aseg}\)과 \(n\)은 각각 그 수와 그 원래 ID를 뜻한다. 보정 response
amplitude는

\[
B_{asegni}=\operatorname{median}_{t\in\mathcal B_{egn}}Y_{asegni}(t),
\qquad
A_{asegni}=\frac1{|\mathcal W_{egn}|}
\int_{\mathcal W_{egn}}[Y_{asegni}(t)-B_{asegni}]\,dt
\tag{E1.5}
\]

이다. 수치적분은 실제 timestamp의 trapezoid rule로 고정하고 frame
index를 시간으로 오독하지 않는다.

한 epoch의 randomized target order와 baseline, 실제로 기록된 비행동
nuisance만 사용한다. target마다 고정된 power·duration은 target과 분리해
식별할 수 없으므로 별도 nuisance 열로 넣지 않고 해당 자극 protocol의 target
contrast에 포함한다. trial order는 아래 spline에만 한 번 넣는다. 각 session
\((a,s)\)의 pre/post 공통 integer target ID를 오름차순
\(g_1<\cdots<g_G\)으로 고정한다. epoch별 one-hot design을 \(Z_e\), 두 epoch를
합친 공통 target weight를
\(n^\star_j=(Z_0^T\mathbf1)_j+(Z_1^T\mathbf1)_j\),
\(S^\star_j=\sum_{k=1}^j n^\star_k\)라 한다. session-common weighted Helmert
basis는

\[
H_{kj}=\begin{cases}
(S_j^\star)^{-1},&k\le j,\\
-(n_{j+1}^\star)^{-1},&k=j+1,\\
0,&k>j+1,
\end{cases}
\qquad
C^{as}_{kj}=\frac{H_{kj}}
{\sqrt{(S_j^\star)^{-1}+(n_{j+1}^\star)^{-1}}},
\quad j=1,\ldots,G-1
\]

로 pre/post response 값을 열기 전에 한 번만 고정한다. 그러면
\((n^\star)^TC^{as}=0\),
\((C^{as})^T\operatorname{diag}(n^\star)C^{as}=I\)다. target contrast design과
각 responder의 coefficient를

\[
T_e=Z_eC^{as},\qquad W^{\rm eff}_{ase,i}=C^{as}\beta_{ase,i}
\]

로 두어 \(W_g\)와 \(G-1\)개 자유 coefficient의 대응을 고정한다. constant를
제외한 raw nuisance와 piecewise-linear spline design을 \(B\)라 하고,
metadata만으로 \(\widetilde B=(I-P_{[\mathbf1,T_e]})B\)를 만든 뒤

\[
A_{asegni}=\alpha_{asei}+W^{\rm eff}_{ase,ig}
+\gamma_{asei}^{\!T}\widetilde B_{asegn}+\varepsilon_{asegni}
\tag{E1.6}
\]

를 적합한다. spline 절점과 규제화 계수는 inner training fold에서만 고른다.
모든 연속 nuisance와 spline 열은 epoch 안에서 중심화되고 target/constant
공간에 직교하므로 target-fixed protocol 차이를 제거했다고 해석하지 않는다.
전체 design \(X_e=[\mathbf1,T_e,\widetilde B]\)는 endpoint를 열기 전에
\(\operatorname{rank}(X_e)=\dim X_e\)와
\(\sigma_{\min}(X_e)/\sigma_{\max}(X_e)\ge10^{-8}\)을 모두 통과해야 한다.
실패하면 열을 사후 삭제하지 않고 `E1_BLOCKED_INPUT`으로 멈춘다. 모든 target이
자극 trial인 설계에서 intercept와 target 효과를 분리하기 위해

\[
\sum_{g\in\mathcal G_{as}}n^\star_{asg}W^{\rm eff}_{ase,ig}=0,
\qquad
\mu^{\rm stim}_{ase,ig}=\alpha_{asei}+W^{\rm eff}_{ase,ig}
\]

를 강제한다. \(W^{\rm eff}_{ig}\)는 randomized target 사이의 **effective
response contrast**이고 \(\mu^{\rm stim}_{ig}\)가 baseline-corrected total
photostimulation response다. 무자극·laser-only sham이 없으므로 어느 것도
무자극 대비 효과로 부르지 않는다. multisynaptic route·state dependence·opsin
variability를 포함할 수 있으므로 시냅스 conductance나 \(\bar w\)도 아니다.

\[
\Delta W^{\rm eff}_{as}=\widehat W^{\rm eff}_{as1}
-\widehat W^{\rm eff}_{as0}
\tag{E1.7}
\]

은 학습 전·후 연관 변화이다. learning을 무작위 배정한 sham
arm이 없으므로, 이 차이자체를 “학습이 인과적으로 만든 시냅스
변화”라고 쓰지 않는다.

calcium response centroid

\[
\tau^{\rm Ca}_{ase,ig}=
\frac{\int_{\mathcal W}(t-t^{\rm off})[Y_i(t)-B_i]_+dt}
{\int_{\mathcal W}[Y_i(t)-B_i]_+dt}
\tag{E1.8}
\]

는 measurement/filter를 포함한 response lag이다. E1에서는

\[
\delta v_{ig}=0,\qquad \delta\tau^{\rm ax}_{ig}=0,
\qquad \tau^{\rm Ca}_{ig}\not\equiv \ell_{ig}/v_{ig}
\tag{E1.9}
\]

를 하드 잠금한다. 식 (21.48)의 속도 미분은 E1의 경험 판정
대상이 아니다. \(\tau^{\rm Ca}\)는 E1의 \(\Phi,J,G,\theta^{\rm E1}\)에 들어가지
않으므로 기술적 secondary로만 보고하고 frozen-lag 경쟁 loss를 만들지 않는다.

## 5. 정보 누수를 막는 분할

각 \((a,s,e,g)\) 층의 trial 수를 \(N=N_{aseg}\)라 하고 endpoint를 열기 전

\[
h_{asegn}=\operatorname{SHA256}_{\rm UTF8}(
\texttt{asset\_id|e|g|n|CE\_NPF\_AIND\_BCI\_E1\_V2}),
\qquad
r_{asegn}=\operatorname{rank}(h_{asegn})
\tag{E1.10}
\]

\[
\begin{gathered}
N_\Theta=\lfloor0.4N\rfloor,\quad
N_T=\lfloor0.2N\rfloor,\quad
N_R=\lfloor0.2N\rfloor,\\
r\le N_\Theta:\mathcal D_\Theta,\quad
N_\Theta<r\le N_\Theta+N_T:\mathcal D_T,\\
N_\Theta+N_T<r\le N_\Theta+N_T+N_R:\mathcal D_R,\quad
\text{나머지}:\mathcal D_{\rm blind},\\
(|\mathcal D_\Theta|,|\mathcal D_T|,|\mathcal D_R|,
|\mathcal D_{\rm blind}|)\ge(8,4,4,4).
\end{gathered}
\tag{E1.11}
\]

로 hash-rank 층화 할당한다. `asset_id`는 lowercase UUID 문자열, \(e,g,n\)은
leading zero가 없는 canonical decimal integer, 구분자는 literal ASCII `|`로
직렬화한다. SHA-256 digest는 unsigned byte lexicographic order로 정렬하고
동률은 integer \(n=\) `PhotostimTrials/id`로 끊는다.
\(\mathcal D_\Theta\)는 target-response contrast·flow,
\(\mathcal D_T\)는 factorized terminal likelihood,
\(\mathcal D_R\)는 독립 marginal reference metric,
\(\mathcal D_{\rm blind}\)는 raw-output 최종 점수에 쓴다. 어떤 trial도 역할을
겹치게 하지 않으며, 동률 hash는 원래 integer trial ID로 끊는다.

outer split은 leave-one-animal-out이다.

\[
\mathcal A=\mathcal A_{\rm train}^{(-a)}\dot\cup\{a_{\rm blind}\},
\qquad a_{\rm blind}\in\{731015,740369,754303,766719,767715\}.
\tag{E1.12}
\]

이 split은 **LOAO hyperparameter 선택 + held-out-animal local calibration**이다.
outer training animal은 \(d\), polynomial degree, 규제화, shrinkage family와
cutoff만 고른다. 서로 ROI 수와 정체성이 다른 animal의 population vector를
합치지 않는다. held-out animal에서는 \(\mathcal D_\Theta\)의 pre epoch만으로
local \(\mu,D,P\)를 endpoint-blind calibration하고, \(\mathcal D_\Theta\)와
\(\mathcal D_T\)로 frozen family의 local coefficient만 추정한다.
\(\mathcal D_R\)와 \(\mathcal D_{\rm blind}\)는 이 calibration에 들어가지 않는다.

intervention holdout은 animal·session 안에서 \(target\_id=g=\)
`PhotostimTrials/group_index`로 두고
`SHA256(asset_id|target_id|CE_NPF_AIND_BCI_E1_TARGET_V1)`를 정렬한 뒤
앞의 \(\lceil0.2|\mathcal G_{as}|\rceil\)개 target으로 고정한다. 동률은
integer target ID로 끊는다. 최소 6개 target이 아니면 `E1_BLOCKED_INPUT`이다.
held-out target의
\(\mathcal D_\Theta,\mathcal D_T\)는 candidate fit에서 숨기고,
\(\mathcal D_R\)은 candidate를 동결한 뒤 reference metric에만,
\(\mathcal D_{\rm blind}\)는 raw-output score에만 연다. 따라서 이 계약을
held-out animal을 전혀 보지 않는 population transfer라고 부르지 않는다.

## 6. chart, 상태의존 표적--반응 대조와 flow

outer training animal에서 선택한 차원 \(d^{(-a)}\)를 고정한 뒤, held-out
animal·session의 비-holdout target, pre-\(\mathcal D_\Theta\)만으로 mean
\(\mu_{as0}\), positive diagonal scale \(D_{as0}\), orthonormal chart
\(P_{as,d}\)를 적합하고

\[
z=P_{as,d}^{T}D_{as0}^{-1}(Y_{\mathcal R^Z_{as}}-\mu_{as0})
\tag{E1.13}
\]

로 둔다. \(d\in\{2,3,4,6,8\}\)은 outer-training inner-animal reconstruction
log score의 one-standard-error rule로 가장 작은 값을 고른다. held-out animal의
post 자료, \(\mathcal D_R\), \(\mathcal D_{\rm blind}\), 행동과
\(O^{\rm metric}\)은 chart 선택에 사용하지 않는다.

target holdout을 예측할 수 있도록 \(u_g\)는 one-hot ID가 아니라 response를
쓰지 않은 고정 feature다. laser \((x,y)\), protocol power·duration과 target
soma probability만 사용하며, trial마다 값이 다르면 response를 보지 않고 해당
target 전체 metadata의 median으로 고정한다. ROI mask 값이나 response amplitude는
쓰지 않는다. 변환과 표준화 계수는 outer training metadata에서만 정한다.
state-dependent raw-dF/F impulse operator를

\[
K^Y_{ase}(z)=K^{Y,0}_{ase}+\sum_{c=1}^{d}z_cK^{Y,c}_{ase}
\tag{E1.14}
\]

로 근사한다. horizon \(H=0.60\,\mathrm s\)의 reduced flow는

\[
\Phi_{ase,H}(z;u_g)=F_{ase}z+b_{ase}
+P_{as,d}^{T}D_{as0}^{-1}K^Y_{ase}(z)u_g,
\tag{E1.15}
\]

\[
J_{ase,H}(z;u_g)=F_{ase}
+\begin{bmatrix}
P_{as,d}^TD_{as0}^{-1}K^{Y,1}_{ase}u_g&\cdots&
P_{as,d}^TD_{as0}^{-1}K^{Y,d}_{ase}u_g
\end{bmatrix}.
\tag{E1.16}
\]

\(K^Y\)는 식 (E1.6)의 time-resolved target-contrast 확장을
\(\mathcal D_\Theta\)에서 적합한 현상론적 response operator다. 명시적인
\(D^{-1}\)가 raw dF/F와 standardized chart의 단위를 맞춘다. 식 (21.44)의
일반 RFDE flow와 같다고 선언하지 않는다.

## 7. terminal Fisher과 pullback metric

metric 출력 \(O^{\rm metric}\)은 **행동이 아닌** 독립 ROI role
\(\mathcal R^O_{as}\)의 자극 후 response vector다. \(\mathcal D_T\)에서

\[
O^{\rm metric}\mid \zeta,u_g,e
\sim\mathcal N\!\left(m_e(\zeta,u_g),\Sigma_e(\zeta,u_g)\right)
\tag{E1.17}
\]

를 적합한다. \(m_e\)는 \(\zeta\)의 2차 polynomial이고 log-variance
\(\ell_e\)는 1차 polynomial이다. covariance field는 유일하게

\[
\Sigma_{ase}(\zeta,u)=S_{ase}(\zeta,u)R_{ase}S_{ase}(\zeta,u),
\qquad
S_{ase}=\operatorname{diag}\exp\{\ell_{ase}(\zeta,u)/2\}
\]

로 조립한다. \(R_{ase}\succ0\)는 \(\mathcal D_T\)에서 적합한 Ledoit--Wolf
shrinkage correlation이고 state에 대해 고정한다. shrinkage family와
hyperparameter는 outer-training inner-animal fold에서만 선택한다.

Gaussian terminal Fisher는

\[
\begin{aligned}
G^o_{ase,rq}(\zeta;u_g)
=&(\partial_r m_{ase})^T\Sigma_{ase}^{-1}(\partial_qm_{ase})\\
&+\frac12\operatorname{tr}\!\left(
\Sigma_{ase}^{-1}(\partial_r\Sigma_{ase})
\Sigma_{ase}^{-1}(\partial_q\Sigma_{ase})\right)
\end{aligned}
\tag{E1.18}
\]

이고, 현재 상태의 horizon pullback은

\[
g^H_{ase}(z;u_g)=J_{ase,H}(z;u_g)^T
G^o_{ase}(\Phi_{ase,H}(z;u_g);u_g)
J_{ase,H}(z;u_g)
\tag{E1.19}
\]

이다. 이 계약은 terminal response likelihood와 deterministic mean flow를 분리한
factorization에만 pullback을 적용한다. 미래를 이미 marginalize한
Fisher에 다시 pullback하지 않는다.

candidate를 모두 동결한 뒤 \(\mathcal D_R\)만으로 별도 marginal likelihood와
reference Fisher를 적합한다.

\[
\begin{aligned}
\pi^{\rm ref}_{ase,H}(o\mid z,u_g)
&=p(O^{\rm metric}_{t+H}=o\mid z_t=z,u_g,e;\mathcal D_R),\\
G^{\rm ref}_{ase,H}(z;u_g)
&=\mathbb E_{\pi^{\rm ref}}
[\nabla_z\log\pi^{\rm ref}\nabla_z\log\pi^{\rm ref\,T}].
\end{aligned}
\]

reference family와 smoothing은 outer training에서 고정하고, held-out animal에서는
그 coefficient만 \(\mathcal D_R\)에 적합한다. factorized candidate와 reference가
같은 trial로 적합되지 않게 한다. 독립 test patch도 endpoint를 보지 않고 다음과
같이 고정한다. pre-epoch \(\mathcal D_R\)의 artifact-free baseline frame 중 양쪽
epoch의 candidate-training state cloud에 대한 최근접거리 모두가 outer-training
95% support cutoff 안인 frame만 남긴다. 각 frame을 UTF-8 literal
`asset_id|frame_id|CE_NPF_AIND_BCI_E1_PATCH_V1`의 SHA-256으로 정렬하고 앞의

\[
K_{as}=\min\{256,N^{\rm eligible}_{as}\},\qquad K_{as}\ge64
\]

개 chart state를 \(\mathcal Z_{as\star}\)로 둔다. `frame_id`는 leading zero 없는
canonical decimal이다. \(\mathcal D_R\)는 같은 hash 규칙으로 두 fold로 나누고,
각 patch point의 reference는 그 point가 속한 fold를 제외해 적합한다. 따라서
patch state와 해당 reference fit row는 겹치지 않는다. \(K_{as}<64\)이면
`E1_BLOCKED_INPUT`이다.

수치·측정 floor도 endpoint 개봉 전에 고정한다. \(\mathcal D_R\)의 두 독립
same-epoch half-fit을 \(G^{\rm ref,(1)},G^{\rm ref,(2)}\), nested
trial/animal bootstrap replicate를 \(b\)라 쓴다. AIRM을 계산하기 전에 모든
사전지정 bootstrap replicate, \(h\in\{1,2\}\), \(e,z,g\)에서

\[
\lambda^{{\rm half,num}}_{as,h,b}(e,z,g)
=10^4\epsilon_{\rm mach}
\max\{1,\|\widehat G^{{\rm ref},(h,b)}_{ase,H}(z;u_g)\|_2\},
\]

\[
\operatorname{rank}\widehat G^{{\rm ref},(h,b)}_{ase,H}=d_{as},\qquad
\lambda_{\min}(\widehat G^{{\rm ref},(h,b)}_{ase,H})
>\lambda^{{\rm half,num}}_{as,h,b}
\]

를 먼저 요구한다. 하나라도 실패하면 해당 bootstrap draw를 버리지 않고 전체를
`E1_FUNCTIONAL_METRIC_NOT_ESTABLISHED`로 중단하며 matrix log나 아래 quantile을
계산하지 않는다. 통과한 뒤 familywise functional을

\[
\begin{aligned}
\lambda^{\rm meas}_{as}
&=Q_{0.99}^{b}\!\left[
\max_{e,z,g}\left\|
\widehat G^{{\rm ref},(1,b)}_{ase,H}(z;u_g)
-\widehat G^{{\rm ref},(2,b)}_{ase,H}(z;u_g)
\right\|_2\right],\\
D^{\rm meas}_{as}
&=Q_{0.95}^{b}\!\left[
\max_{e\in\{0,1\}}
\frac1{|\mathcal Z_{as\star}||\mathcal G_{as,\rm hold}|}
\sum_{z,g}\frac1{d_{as}}d_{\rm AI}^2\!\left(
\widehat G^{{\rm ref},(1,b)}_{ase,H}(z;u_g),
\widehat G^{{\rm ref},(2,b)}_{ase,H}(z;u_g)
\right)\right]
\end{aligned}
\]

로 정확히 고정한다. 모든 max와 sum은
\(z\in\mathcal Z_{as\star},g\in\mathcal G_{as,\rm hold}\) 위에서 계산한다.

\[
\begin{aligned}
\lambda^{\rm num}_{as}
&=10^4\epsilon_{\rm mach}\max_{e,z,g}
\{1,\|G^{\rm ref}_{ase,H}(z;u_g)\|_2,\|g^H_{ase}(z;u_g)\|_2\},\\
\lambda_{{\rm floor},as}&=\max\{\lambda^{\rm meas}_{as},
\lambda^{\rm num}_{as}\},\qquad
\delta_{\rm num}=10^4\epsilon_{\rm mach}.
\end{aligned}
\]

이 값들은 outer-training에서
family를 고정한 뒤 held-out animal의 \(\mathcal D_R\) calibration replicate로만
계산한다. factorization 적합성은 모든
\((e,z,g)\in\{0,1\}\times\mathcal Z_{as\star}\times
\mathcal G_{as,\rm hold}\)에서 먼저
\(\lambda_{\min}(G^{\rm ref}),\lambda_{\min}(g^H)>
\lambda_{{\rm floor},as}\)를 통과한 뒤에만 계산한다. 실패하면 pseudoinverse나
ridge로 거리를 만들지 않고 즉시 `E1_FUNCTIONAL_METRIC_NOT_ESTABLISHED`로
보낸다. 통과한 경우

\[
\max_{\substack{e\in\{0,1\},\ z\in\mathcal Z_{as\star}\\
g\in\mathcal G_{as,\rm hold}}}
\frac1{\sqrt d}d_{\rm AI}\!\left(
G^{\rm ref}_{ase,H}(z;u_g),g^H_{ase}(z;u_g)\right)
\le0.10,
\quad
d_{\rm AI}(A,B)=\|\log(A^{-1/2}BA^{-1/2})\|_F
\tag{E1.20}
\]

을 통과해야 한다. 실패하면 reference marginal Fisher만 보고하고
\(\Delta W^{\rm eff}\to\Delta g^{\rm pb}\) branch를 중단한다.

## 8. pre/post 접힘과 선형 민감도

한 session에서 ROI index가 공유되고 chart를 pre calibration에서 고정하므로
primary transport는 identity다. 보조 calibration-only Procrustes \(T\)를
사용할 때도 output·behavior를 적합에 쓰지 않는다. 방향을
\(T_{0\to1}:Z_0\to Z_1\)로 고정하고

\[
\widetilde g_{as1}(z;u_g)
=(DT_{0\to1,z})^Tg_{as1}(T_{0\to1}z;u_g)DT_{0\to1,z}
\tag{E1.21}
\]

로 pre tangent space에 옮긴다.
독립 reference field에도 같은 transport를 적용해
\(\widetilde g^{\rm ref}_{as1}:=T_{0\to1}^{*}g^{\rm ref}_{as1}\)로 둔다.

식 (E1.21)--(E1.23)의 \(g_{as0},g_{as1}\)은 \(\mathcal D_\Theta,
\mathcal D_T\)만으로 적합한 nonlinear full candidate이고
\(g^{\rm ref}\)가 아니다. 경험 적합성은 식 (E1.24)에서 따로 검사한다.
먼저 독립 reference의 변화량

\[
D^{\rm ref}_{as}=\frac1{|\mathcal Z_{as\star}||\mathcal G_{as,\rm hold}|}
\sum_{z\in\mathcal Z_{as\star}}
\sum_{g\in\mathcal G_{as,\rm hold}}\frac1{d_{as}}d_{\rm AI}^2
(\widetilde g^{\rm ref}_{as1}(z;u_g),g^{\rm ref}_{as0}(z;u_g))
\]

의 animal-bootstrap 95% 하한이 \(D^{\rm meas}_{as}\)를 넘어야 한다. 아니면
`E1_NO_DETECTABLE_METRIC_CHANGE`로 중단한다.

E1의 미분 좌표는 함수 이름이 아니라 공통 finite coefficient vector

\[
\theta^{\rm E1}=\bigl(\operatorname{vec}K^{Y,0:d},
\operatorname{vec}F,b,\operatorname{coef}m,
\operatorname{coef}\ell,\operatorname{vech}\operatorname{chol}R\bigr)
\]

다. 식 (21.53)의 E1 제한판은

\[
\widehat{\Delta g}_{as}^{\rm lin}(z;u_g)
=D_\theta g(\widehat\theta_{as0})
[\widehat\theta_{as1}-\widehat\theta_{as0}]
\tag{E1.22}
\]

이다. 여기서 \(\delta K^Y\)는 effective response 항,
\(\delta m,\delta\ell,\delta R\)는
출력/readout·noise 직접항이다. 속도 항은 식 (E1.9)로 고정된다.

SPD cone의 affine-invariant exponential을

\[
\operatorname{Exp}_{G}(U)=G^{1/2}
\exp(G^{-1/2}UG^{-1/2})G^{1/2}
\]

로 정의한다. 선형화 오차는 transport된 post field와 모든 predeclared
patch·held-out target을 animal·session 안에서 균형 있게 합쳐

\[
R_{\rm lin,as}^{2}=
\frac{\sum_{z\in\mathcal Z_{as\star}}\sum_{g\in\mathcal G_{as,\rm hold}}
d_{\rm AI}^2\!\left(\widetilde g_{as1}(z;u_g),
\operatorname{Exp}_{g_{as0}(z;u_g)}
[\widehat{\Delta g}_{as}^{\rm lin}(z;u_g)]\right)}
{\sum_{z\in\mathcal Z_{as\star}}\sum_{g\in\mathcal G_{as,\rm hold}}
d_{\rm AI}^2\!\left(\widetilde g_{as1}(z;u_g),g_{as0}(z;u_g)\right)}
\tag{E1.23}
\]

로 보고한다. 이 full-candidate 분모를
\(|\mathcal Z_{as\star}||\mathcal G_{as,\rm hold}|d_{as}\)로 나눈 값이
\(\delta_{\rm num}\) 이하이면
선형화 비율이 정의되지 않으므로 같은 중단 판정을 쓴다.
\(R_{\rm lin,as}\le0.20\)가 모든 LOAO fold에서 성립해야 식 (21.53)의
1차 경험 예측이 살아남는다. 실패해도 nonlinear predictive model은 별도로
남을 수 있지만 연속 민감도 주장은 기각한다.

## 9. 경쟁 모형과 블라인드 점수

모든 후보는 같은 trial, row, chart, likelihood family, outer animal fold를
사용한다.

| 후보 | 고정/제거하는 항 | 답하는 질문 |
|---|---|---|
| full-effective | \(\Delta K^Y,\Delta F,\Delta m,\Delta\ell,\Delta R\) | effective response와 출력항을 모두 필요로 하는가 |
| frozen-target-response | \(K^Y_1=K^Y_0\) | target-response 변화가 필요한가 |
| rate/gain-only | diagonal gain·offset만 post 허용 | 단순 활성 크기로 충분한가 |
| output-only | \(J_1=J_0\), \(G_1\) 변화만 허용 | geometry 변화가 readout/noise뿐인가 |
| shuffled-target | animal·session·거리 bin 내 target 열 순열 | edge identity가 필요한가 |
| static Euclidean | \(g=I\) | data-dependent metric이 필요한가 |

primary raw blind score는 candidate를 동결한 뒤 \(\mathcal D_{\rm blind}\)에서
계산한 animal-balanced negative log predictive density \(\ell_M\)다.
독립 \(\mathcal D_R\)의 reference metric에 대한 score는

\[
\mathcal L_M=
\frac1{|\mathcal A|}\sum_{a\in\mathcal A}
\frac1{|\mathcal S_a|}\sum_{s\in\mathcal S_a}
\frac1{|\mathcal Z_{as\star}||\mathcal G_{as,\rm hold}|}
\sum_{z,g}\frac1{d_{as}}d_{\rm AI}^2\!\left(
g^{\rm ref}_{as1}(z;u_g),g^M_{as1}(z;u_g)\right)
\tag{E1.24}
\]

이다. \(g^{\rm ref}\)의 coefficient·sampling uncertainty는 \(\mathcal D_R\)
내부 cross-fit과 animal-cluster bootstrap에 전파한다. full 통과는 다음을
**모두** 요구한다.

\[
\mathcal L_{\rm full}\le0.95
\min\{\mathcal L_{\rm frozen},\mathcal L_{\rm gain},
\mathcal L_{\rm output},
\mathcal L_{\rm shuffle},\mathcal L_{\rm Euclid}\},
\tag{E1.25}
\]

- leave-one-animal-out 5개 fold 전부에서 같은 개선 부호
- 두 genotype/indicator 계열의 개선 부호가 반대이면 cohort-wide 판정을 금지하고
  `E1_FAMILY_HETEROGENEOUS`로 제한
- animal-cluster bootstrap 95% lower bound \(>0\)
- 10,000회 target shuffle randomization \(p\le0.01\)
- blind output log score가 state-independent null과 대응 likelihood control보다
  좋고 animal-bootstrap 개선 하한 \(>0\)
- 사전고정 test patch의 모든 점에서 rank \(d_{as}\),
  \(\lambda_{\min}(g)\) bootstrap 하한 \(>\lambda_{{\rm floor},as}\),
  \(\kappa_2(g)<10^4\)
- 고정 선형 rechart의 line-element 상대오차 \(<10^{-3}\)
- 식 (E1.20)과 (E1.23) 통과

ridge를 늘려 rank/SPD gate를 사후적으로 통과시키지 않는다.

## 10. E1의 정확한 성공·실패 판정

| 결과 | 판정 | 주장 상한 |
|---|---|---|
| 입력 gate 실패 | `E1_BLOCKED_INPUT` | 장치 준비 중단; 가설 결과 아님 |
| metric/rank/factorization 실패 | `E1_FUNCTIONAL_METRIC_NOT_ESTABLISHED` | Riemann 다리 미확립 |
| detectable metric 변화 없음 | `E1_NO_DETECTABLE_METRIC_CHANGE` | 선형화·접힘 크기 판정 불가 |
| 두 indicator/genotype 계열의 부호 반대 | `E1_FAMILY_HETEROGENEOUS` | family 한정 결과만 허용 |
| full이 control과 동률/열세 | `E1_TARGET_RESPONSE_CONTRAST_BRIDGE_FAIL` | \(\Delta W^{\rm eff}\to\Delta g\) 반증 |
| 예측은 성공, 선형화는 실패 | `E1_NONLINEAR_ONLY` | 식 (21.53) 경험 주장 불가 |
| 모든 gate 통과 | `E1_TARGET_RESPONSE_CONTRAST_GEOMETRY_ASSOCIATION_PASS` | 해당 자료·출력·calcium scale에 한정한 연관 다리 |

E1 양성으로도 다음은 계속 `false`다.

\[
\begin{gathered}
\texttt{physical\_synaptic\_weight\_identified=false},\\
\texttt{conduction\_velocity\_identified=false},\\
\texttt{learning\_caused\_metric\_change=false},\\
\texttt{behavioral\_mediation\_identified=false},\\
\texttt{stage10\_identified=false}.
\end{gathered}
\tag{E1.26}
\]

## 11. 성체 미시기전--계량--행동 다리를 위한 별도 E2 계약

E1은 공개자료로 실행 가능한 부분 검증이다. 사용자가 요구한
“연결·가중치·속도가 공간을 접어 행동을 바꾸는가”의 성체 인과
결론은 다음 prospective E2 계약을 별도로 충족해야 한다. E2만으로
발달 prior까지 닫히지는 않으며 §11.9의 D1 계약도 별도로 필요하다.

E2부터 index를 다시 고정한다. \(a\)는 animal, \(b\)는 animal 안의
randomization cluster, \(e=(j\to i)\)는 directed edge, \(s\)는 longitudinal
visit, \(q\)는 같은 axon 위 stimulation position, \(n\)은 pulse/trial,
\(r\)은 receptor subtype, \(k\)는 edge 안의 contact다. 따라서 E2의 \(e\)는
E1의 pre/post epoch가 아니다.

### 11.1 무작위 기전·구제 배정

개입 cluster \(b\)를 animal \(a\)에 nested하고 synaptic/efficacy 개입
\(I^W\), conduction/myelin 개입 \(I^v\)를 2\(\times\)2로 무작위화한다.

\[
I_{ab}=(I^W_{ab},I^v_{ab})\in\{0,1\}^2,
\qquad P(I^W=1)=P(I^v=1)=\tfrac12.
\tag{E2.1}
\]

sham, synaptic-only, conduction-only, combined arm과 post 측정 후 별도
\(R^W,R^v\) rescue를 준비한다. animal 전체 spillover가 있으면
\(b=a\)로 두고 cell 수를 독립 표본으로 세지 않는다.

### 11.2 endpoint-blind same-cell/contact matching

\[
C_{ii'}^{c,as}=\|A_{as\to0}r_{ais}-r_{ai'0}\|_{\Sigma_r^{-1}}^2
+\lambda_m d_m(f_{ais},f_{ai'0})
+\lambda_l d_l(i,i'),
\tag{E2.2}
\]

\[
\begin{aligned}
p(M^c,M^e\mid C^c,C^e,\mathcal C_{\rm fid})
&=Z^{-1}\mathbf1_{\Pi_c}(M^c)\mathbf1_{\Pi_e}(M^e)
\mathbf1_{\rm parent}(M^c,M^e)\\
&\quad\times\exp\!\left[-\frac12\sum_{ii'}M^c_{ii'}C^c_{ii'}
-\frac12\sum_{\kappa\kappa'}M^e_{\kappa\kappa'}C^e_{\kappa\kappa'}
-\lambda_c\sum_iM^c_{i\varnothing}
-\lambda_e\sum_\kappa M^e_{\kappa\varnothing}\right],\\
(M^{c\star},M^{e\star})&=\arg\max_{M^c,M^e}p(M^c,M^e\mid
C^c,C^e,\mathcal C_{\rm fid}),\\
M^e_{(j,i,k),(j',i',k')}
&\le M^c_{jj'}M^c_{ii'}.
\end{aligned}
\tag{E2.3}
\]

\(\Pi_c,\Pi_e\)는 unmatched state를 포함한 one-to-one cell/contact matching이고,
\(\kappa=(j,i,k)\)는 contact와 두 parent cell을 함께 가리킨다.
\(\mathbf1_{\rm parent}\)가 마지막 inequality를 모든 contact에 강제한다.
\(\mathcal C_{\rm fid}\)는 두 cost scale, posterior temperature와 unmatched
penalty를 고정하는 blinded fiducial calibration이다. contact cost \(C^e\)에는
bouton/spine morphology와 ultrastructure fiducial만 쓴다. activity, metric
output, behavior는 어느 cost에도 넣지 않는다. posterior marginal은

\[
p^c_{ii'}=\sum_{M^c,M^e}M^c_{ii'}p(M^c,M^e\mid\cdot),\qquad
p^e_{\kappa\kappa'}=\sum_{M^c,M^e}M^e_{\kappa\kappa'}p(M^c,M^e\mid\cdot)
\]

로 각각 계산한다. downstream likelihood와 uncertainty는 이 joint posterior에
합을 취하고 MAP match 하나만 참으로 간주하지 않는다. blinded fiducial
false-match 상한 1%, cell/contact별 posterior
\(\ge0.99\), baseline cell과 contact 유지율 각각 80% 이상, arm 간 유지율
차이 10 percentage point 이하를 모두 요구한다.

### 11.3 분해된 관측 likelihood

\[
\begin{aligned}
p(D\mid X,\Theta)=&\ p(Y^{\rm pop}\mid X,\psi_{\rm meas})
p(Y^{\rm PSC}\mid\Theta^{\rm syn})\\
&\times p(Y^{\rm lat}\mid\ell,v,\tau^{\rm syn},\tau^{\rm meas})
p(Y^{\rm morph}\mid\zeta,\boldsymbol\mu)\\
&\times p(Y^{\rm beh}\mid X,\Theta,C).
\end{aligned}
\tag{E2.4}
\]

식 (E2.4)는 각 calibration·state를 조건으로 한 working conditional
factorization이다. training residual의 cross-channel dependence가 사전고정
상한을 넘으면 곱을 유지하지 않고 joint observation model을 다시
사전등록하며, 같은 blind endpoint에서 고쳐 맞추지 않는다.

calcium/voltage observation kernel은

\[
Y^{\rm pop}_{aisn}(t)=b_{ais}+c_{ais}
\int k^{\rm meas}_{as}(r)x_{ai}(t-r)dr+\epsilon_{aisn}(t)
\tag{E2.5}
\]

로 분리하고 calibration pulse 또는 동시 전기생리로
\(k^{\rm meas}\)를 training data에서만 추정한다.

### 11.4 경로길이·전도속도·지연 분리

같은 axon/target에 서로 다른 자극 위치 \(q\ge3\)개를 사용해

\[
\begin{pmatrix}\widehat L_{abesq}\\ \widehat\ell_{abesq}\end{pmatrix}
\sim\mathcal N\!\left[
\begin{pmatrix}\alpha_{abes}+\beta_{abes}\ell_{abesq}\\
\ell_{abesq}\end{pmatrix},\Sigma^{L\ell}_{abesq}\right],
\qquad \beta_{abes}=v_{abes}^{-1}>0,
\tag{E2.6}
\]

\[
\widehat v_{abes}=\widehat\beta_{abes}^{-1},\qquad
\widehat\tau^{\rm ax}_{abes}
=\widehat\ell_{abesq_\star}\widehat\beta_{abes},
\tag{E2.7}
\]

\[
\begin{aligned}
\alpha={}&\tau^{\rm hardware}+\tau^{\rm meas}+\tau^{\rm release}
+\tau^{\rm receptor/group}+\tau^{\rm integration},\\
\tau^{\rm syn,eff}:={}&\tau^{\rm release}
+\tau^{\rm receptor/group}+\tau^{\rm integration},\\
\widehat\tau^{\rm syn,eff}={}&\widehat\alpha
-\widehat\tau^{\rm meas}-\widehat\tau^{\rm hardware}.
\end{aligned}
\tag{E2.8}
\]

slope는 axial delay, intercept는 release·receptor/group·integration·measurement
delay를 담는다. \(q_\star\)는 terminal target까지의 full traced path를 주는
사전지정 위치다. 각 \((a,b,e,s,q)\)에서 독립 timing calibration pulse와 서로
blinded한 tracing replicate를 각각 3회 이상 얻어, blind physiology/behavior를
열기 전에 \(\Sigma^{L\ell}_{abesq}\)의 두 분산과 공분산을 고정한다. replicate가
없거나 covariance가 singular이면 EIV slope를 적합하지 않고 속도 branch를
중단한다. release-specific independent calibration이 없으면 full receptor-ODE
delay branch를 `E2_FULL_DELAY_BLOCKED`로 닫고 reduced model만 사용한다. 이때

\[
\tau^{\rm red}=\tau^{\rm ax}+\tau^{\rm syn,eff}
\]

다. blind 개봉 전 amendment에서 release calibration을 통과한 경우에만

\[
\tau^{\rm full}=\tau^{\rm ax}+\tau^{\rm release}
\]

를 쓰며 receptor/group와 integration delay는 full ODE state evolution 안에서
생성하고 additive term으로 다시 넣지 않는다. 따라서 aggregate
\(\tau^{\rm syn,eff}\)와 full receptor ODE를 같은 candidate에서 함께 쓰지 않는다.
path-length 상대 표준오차 5% 초과, clock jitter가 최소
검출 지연의 10% 초과, \(\beta>0\) 99% cluster 하한 실패,
frozen-\(v\) 대비 held-out latency RMSE 개선 10% 미만이면 속도 branch를
중단한다.

### 11.5 receptor·STP·efficacy 분리

receptor별 voltage-clamp train은

\[
I^{\rm PSC}_{abesnr}(V_h)=
\sum_{k:\zeta_{abesk}=2}\bar g_{ekr}a^H_{ir,s}\bar w_{ek,s}
s^{(r)}_{ek,n}(U,\tau_{\rm fac},\tau_{\rm rec})
B_r(V_h)(V_h-E_r)+\epsilon
\tag{E2.9}
\]

로 적합한다. receptor마다 3개 이상의 holding voltage로 IV curve를 적합하고,
독립 측정한 operating voltage \(V_i^\star\)에서 평가한 signed current
coefficient를 \(c^I_{ekr,s}(V_i^\star)\,[\mathrm A]\)라 한다. fitted reversal
potential이 calibration \(E_r\)의 95% interval을 벗어나거나 sign gate

\[
\operatorname{sign}c^I(V_i^\star)
=\operatorname{sign}(V_i^\star-E_r)=-\varsigma_j
\]

가 성립하지 않으면 그 receptor branch를 중단한다. 여기서
\(\varsigma_j\in\{-1,+1\}\)는 chapter 21과 같은 Dale sign이며
양의 conversion factor가 아니다. 식
(21.28)에 들어가는 nonnegative dimensionless coefficient를

\[
c_{ekr,s}:=-\frac{\varsigma_jc^I_{ekr,s}(V_i^\star)}
{g_{\rm cal}|V_{\rm cal}|}
=\frac{|c^I_{ekr,s}(V_i^\star)|}
{g_{\rm cal}|V_{\rm cal}|}\ge0,\qquad
|c^I_{ekr,s}(V_i^\star)|
=c_{ekr,s}g_{\rm cal}|V_{\rm cal}|
\]

로 명시적으로 정의한다. receptor density, homeostatic scale, reference gain을
다음 calibration likelihood로 묶는다.

\[
p(D_{\rm cal}\mid\bar g,a^H,g_{\rm cal},E_r)
=p(Y^{\rm receptor}\mid\bar g)
\,p(Y^{H}\mid a^H)
\,p(Y^{\rm reference}\mid g_{\rm cal},E_r)
\]

오른쪽은 calibration residual 검사를 통과해야 하는 조건부 독립
factorization이다. \(g_{\rm cal},V_{\rm cal}\)은 reference conductance·voltage,
\(E_r\)은 receptor reversal calibration이며 모두 별도 standard와 unit으로
잠근다. 장비의 positive source conversion이 필요하면 \(\kappa_j>0\)로 별도
보정하고 \(\varsigma_j\)와 합치지 않는다.
독립 calibration과 식 (21.28)의 contact-to-edge recovery
\(\mathcal R_e^{x^\star}\)가 모두 잠겼을 때만

\[
\begin{aligned}
\widehat{\bar w}_{ek,s}
&=\frac{|\widehat c^I_{ekr,s}(\widehat V_i^\star)|}
{\widehat{\bar g}_{ekr}\widehat a^H_{ir,s}
B_r(\widehat V_i^\star)|E_r-\widehat V_i^\star|}
=\frac{\widehat c_{ekr,s}g_{\rm cal}|V_{\rm cal}|}
{\widehat{\bar g}_{ekr}\widehat a^H_{ir,s}
B_r(\widehat V_i^\star)|E_r-\widehat V_i^\star|},\\
\widehat{\bar W}_{e,s}
&=\mathcal R_e^{x^\star}(\{\widehat c_{ekr,s}\}_{kr}),\\
E^{\rm composite}_{e,s,\mathcal P}
&=\bar W_{e,s}\bar p_{e,s,\mathcal P},\qquad
\bar p_{e,s,\mathcal P}=N_{\mathcal P}^{-1}
\sum_{n\in\mathcal P}p_{e,s,n}.
\end{aligned}
\tag{E2.10}
\]

을 사용한다. 모든 항의 SI unit cancellation과 reference-standard residual을
먼저 검사한다. \(\bar g,a^H,g_{\rm cal},E_r,V_i^\star\) 중 하나라도 독립 보정되지
않거나 denominator 상대오차가 20%를 넘으면 \(\bar w\), \(\bar W\)와
\(E^{\rm composite}\)를 모두 보고하지 않는다. 이때 남길 수 있는 것은 직접
측정한 protocol-specific PSC charge

\[
Q^{\rm PSC}_{e,s,\mathcal P}=\frac1{N_{\mathcal P}}
\sum_{n\in\mathcal P}\int_{\mathcal W_{\rm PSC}}
[I^{\rm PSC}_{esn}(t)-I^{\rm base}_{esn}]\,dt
\]

뿐이며, 이를 물리 가중치나 release probability로 분해하지 않는다.
PSC held-out NRMSE \(>0.15\) 또는 90%
predictive interval coverage가 \([0.85,0.95]\) 밖이면 branch를 중단한다.

### 11.6 독립 metric과 mediator

animal split을

\[
\mathcal A=\mathcal A_{\rm train}\dot\cup
\mathcal A_{\rm validation}\dot\cup\mathcal A_{\rm blind}
\tag{E2.11}
\]

로 완전 분리한다. outer training/validation animal은 chart 차원, family,
regularization과 cutoff를 고르고, blind animal의 pre-intervention calibration
block은 서로 다른 ROI 수에 맞는 local chart coefficient만 적합한다. blind
metric·행동 endpoint는 local calibration에 들어가지 않는다. 식
(21.41)--(21.53)의 terminal Fisher, flow와 pullback도 E1처럼 mechanism,
terminal, reference, blind role로 분리한다. calibration-only
\(T_{0\to s}:Z_0\to Z_s\)로

\[
\widetilde g_{as}(z)
=T_{0\to s}^{*}g_{as}(z)
=(DT_{0\to s,z})^Tg_{as}(T_{0\to s}z)DT_{0\to s,z}
\tag{E2.12}
\]

를 만든다. common support와 SPD/eigenvalue gate는 mediator를 계산하기 전에
통과해야 한다. 행동과 독립인 training-only nonzero tangent field
\(\xi_\star(z)\)를 고정하고 primary mediator를

\[
m^g_{ab}=\frac1{|\mathcal Z_{ab\star}|}
\sum_{z\in\mathcal Z_{ab\star}}\frac12\log
\frac{\xi_\star(z)^T\widetilde g_{ab,\rm post}(z)\xi_\star(z)}
{\xi_\star(z)^Tg_{ab,\rm pre}(z)\xi_\star(z)}
\tag{E2.13}
\]

로 고정한다. \(\xi_\star\)는 conduction velocity \(v\)와 다른 기호이며
\(O^{\rm metric}\), calibration input만으로 정한다. volume과 shear는
secondary다. \(O^{\rm metric}=Y^{\rm beh}\)이거나 어느 alignment·direction
선택에도 \(Y^{\rm beh}\)가 들어가면 매개분석을 삭제한다.

### 11.7 full/ablated 미시기전 경쟁

\[
\widehat{\Delta g}^{\rm lin}=D_\vartheta g(\widehat\vartheta_{\rm pre})
[\widehat\vartheta_{\rm post}-\widehat\vartheta_{\rm pre}],
\qquad
\widehat g_{\rm post}^{\rm full}
=\mathcal G(\mathcal F(\widehat\vartheta_{\rm post})).
\tag{E2.14}
\]

여기서 primary reduced 계약의 \(\vartheta\)는
\(\{\bar w,U,\tau_{\rm fac},\tau_{\rm rec},v,\ell,
\tau^{\rm syn,eff},\text{intrinsic},\text{readout/noise}\}\) 같은 primitive
parameter이고 \(\mathcal F\)가 \(p(t)\), \(\bar Wp\),
\(\tau=\ell/v+\tau^{\rm syn,eff}\) 등 모든 derived quantity를 다시 만든다.
release-specific calibration gate를 통과한 amendment에서만
\(\tau^{\rm syn,eff}\)를 제거하고 \(\tau^{\rm release}\)와 calibrated receptor
kinetics를 primitive로 넣는다. calibration이 없으면 full branch 자체가 없으며
aggregate 안의 release를 임의로 빼지 않는다.
primitive channel \(k\)의 ablation은

\[
\begin{aligned}
\vartheta_{\rm post}^{(-k)}
&=(\vartheta_{{\rm pre},k},\vartheta_{{\rm post},-k}),\\
\Theta_{\rm post}^{(-k)}&=\mathcal F(\vartheta_{\rm post}^{(-k)}),
\qquad g_{\rm post}^{(-k)}=\mathcal G(\Theta_{\rm post}^{(-k)}),\\
\tau_{\rm post}^{(-v)}
&=\ell_{\rm post}/v_{\rm pre}+\tau_{\rm post}^{\rm syn,eff}
\quad\text{(reduced)},\\
\tau_{{\rm full,post}}^{(-v)}
&=\ell_{\rm post}/v_{\rm pre}+\tau_{\rm post}^{\rm release}
\quad\text{(release-calibrated full)}.
\end{aligned}
\tag{E2.15}
\]

로 고정한다. 물리 \(\bar w\)가 식 (E2.10)의 calibration gate를 통과하지 못하면
\(\bar w\)와 \(p\)를 따로 ablate하지 않는다. \(Q^{\rm PSC}\)는 별도 predictive
measurement block으로만 둘 수 있고 물리 primitive ablation을 대신하지 못한다.
E2는 E1의 independent reference metric, AIRM 전 SPD gate,
animal-balanced loss와 reference uncertainty propagation을 그대로 상속한다.
각 primary \(k\)에서
\(\mathcal L_{\rm full}\le0.8\mathcal L_{-k}\), cluster-bootstrap 개선 하한
\(>0\), within-animal/cell-type/distance-bin edge-shuffle \(p\le0.01\)을
모두 요구한다. 또한 식 (E1.23)의 detectable-change denominator와
\(R_{\rm lin}\le0.20\)을 통과하지 못하면 nonlinear 결과만 남기고 식
(21.53)의 1차 매개 주장을 기각한다.

### 11.8 hierarchy, missingness, 행동 매개

\[
Q_{abhs}=\mu_s+\beta_WI^W_{ab}+\beta_vI^v_{ab}
+\beta_{Wv}I^WI^v+u_a+u_{ab}+u_{abh}+\epsilon_{abhs}.
\tag{E2.16}
\]

여기서 \(h\)는 endpoint마다 사전지정한 biological unit이다. edge endpoint면
\(h=e\), cell endpoint면 \(h=i\), contact endpoint면 \(h=(e,k)\)이며 visit
\(s\)가 그 아래 반복된다. 한 unit이 여러 cluster와 연결되면 한 cluster에
중복 복제하지 않고 crossed-unit effect와 randomization-cluster sandwich를 쓴다.
inference의 최상위 단위는 animal 또는 실제 randomization cluster다. cell 수를
animal 수로 세지 않는다. \(b=a\)이면 중복되는 \(u_{ab}\)를 삭제한다. cluster
처치가 animal-level 행동에 spillover할 때는 사전고정한 exposure mapping과
partial-interference 경계를 쓰며, 같은 행동값을 cell마다 복제하지 않는다.
관측 indicator \(R_{abhs}\), propensity \(\pi\), stabilized weight \(w\)를

\[
\begin{aligned}
\pi_{abhs}
&=P(R_{abhs}=1\mid\bar R_{s-1},I,C_0,
\bar Y_{\rm observed,s-1}),\\
w_{abhs}
&=\prod_{u\le s}
\frac{P(R_u=1\mid\bar R_{u-1},I,C_0)}{\pi_{abhu}},\\
W_{ab}&=\frac1{|\mathcal H_{ab}|}\sum_{h\in\mathcal H_{ab}}
\frac1{|\mathcal S_{abh}|}\sum_{s\in\mathcal S_{abh}}w_{abhs},\\
ESS_{\rm cl}&=\frac{(\sum_{ab}W_{ab})^2}{\sum_{ab}W_{ab}^2}
\ge0.70N_{\rm cluster},\qquad
\max_{ab}W_{ab}\le10,\quad\max_{abhs}w_{abhs}\le10
\end{aligned}
\tag{E2.17}
\]

로 고정하고 \(W_{ab}\)의 cluster 평균을 1로 정규화한다. 이는 관측 history에
대한 MAR와 positivity를 가정한다. cell/contact
identity 자체는 imputation하지 않고 처치 관련 dropout도 결과로 보고한다.
missingness odds ratio 1.5의 MNAR sensitivity만으로 결론이 뒤집히면
`E2_INCONCLUSIVE_MISSINGNESS`다.

예측 매개모형은

\[
Y^{\rm beh}_{ab}=\alpha+u_a+\beta_I^TI_{ab}
+\gamma m^g_{ab}+\xi^T\Delta\Theta_{ab}+\delta^TC_{ab}+\epsilon_{ab}
\tag{E2.18}
\]

로 시작하되, 이것만으로 인과 매개를 선언하지 않는다. mediator
contrast는
\(c_W(j):(0,j)\to(1,j)\),
\(c_v(j):(j,0)\to(j,1)\), \(j\in\{0,1\}\)로 고정하고 interaction은 두
stratum effect의 difference-in-differences다. 각 contrast
\(i_0\to i_1\)에서

\[
\begin{aligned}
\mu_Y^{\rm do}(i,m,c)
&=\mathbb E[Y^{\rm beh}\mid do(I=i),do(m^g=m),C=c],\\
\mu_Y^{\rm pred}(i,m,c)
&=\mathbb E[Y^{\rm beh}\mid I=i,m^g=m,C=c],\\
\operatorname{IIE}^{\rm do}_{i_0\to i_1}
&=\int \mu_Y^{\rm do}(i_1,m,c)
\left[dF_m(m\mid do(I=i_1),c)-dF_m(m\mid do(I=i_0),c)\right]dF_C(c),\\
\Omega(c)&=\int\min\{f_m(m\mid I=i_1,c),f_m(m\mid I=i_0,c)\}dm
\ge0.80.
\end{aligned}
\tag{E2.19}
\]

를 사전지정한다. consistency, randomized cluster treatment, 위의
partial-interference mapping, mediator positivity와 mediator--outcome
exchangeability가 모두 필요하다. 마지막 조건을 자료만으로 보장하지 못하면
\(I_m^{\rm specific}\)의 실제 무작위 개입 없이는 predictive mediation으로만
남긴다. fitted primitive를 splice해 channel \(k\)를 ablate한 mediator
distribution \(F_{m^{(-k)}}\)는 먼저 **model-based predictive ablation**으로
정의하고

\[
\begin{aligned}
\operatorname{IIE}^{\rm full,pred}
&=\int\mu_Y^{\rm pred}(i_1,m,c)
\left[dF_m(m\mid i_1,c)-dF_m(m\mid i_0,c)\right]dF_C(c),\\
\operatorname{IIE}^{(-k),\rm pred}
&=\int\mu_Y^{\rm pred}(i_1,m,c)
\left[dF_{m^{(-k)}}(m\mid i_1,c)-dF_m(m\mid i_0,c)\right]dF_C(c),\\
\Delta\operatorname{IIE}^{\rm pred}_k
&=\operatorname{IIE}^{\rm full,pred}-\operatorname{IIE}^{(-k),\rm pred},\\
I_\Theta&\Rightarrow\Delta\Theta\Rightarrow\Delta g_{\rm blind}
\Rightarrow\Delta Y,\\
I_m^{\rm specific}&\Rightarrow\Delta Y,
\qquad
R_\Theta\Rightarrow(\Theta,g,m^g,Y)\text{ recovery}.
\end{aligned}
\tag{E2.20}
\]

을 모두 요구한다. \(k\) 자체가 무작위화되고 consistency, exclusion, off-target
gate를 통과한 경우에만 splice 분포 대신 실제 \(do(I_k)\)에서 관측한 mediator
분포와 \(\mu_Y^{\rm do}\)를 넣은 값을
\(\Delta\operatorname{IIE}^{\rm causal}_k\)라 부른다. 별도
개입이 없는 intrinsic, readout/noise와 그 밖의 channel은
\(\Delta\operatorname{IIE}^{\rm pred}_k\)로만 남고 인과 매개사슬의 고리로 세지
않는다. \(I_m^{\rm specific}\)은 measured direct route와 off-target의 90% CI를
\(\pm0.2\) baseline SD 안에 두어야 한다. 인과 자격을 얻은 각 IIE와
\(\Delta\operatorname{IIE}^{\rm causal}_k\), 나머지 predictive ablation은 서로
분리해 보고하며 각각의 cluster-bootstrap 95% CI가 0을 제외하고 표준화 크기가
0.2 이상이어야 한다. rescue의 \((\Theta,g,m^g,Y)\) recovery
90% CI도 각각 \(\pm0.2\) baseline SD 안에 있어야 한다. 한 고리라도 실패하면
전체 매개사슬을 지지하지 않는다. rescue는 필요조건이지 충분조건이 아니다.

### 11.9 발달 prior와 관계적 의미를 위한 별도 D1 계약

E1과 E2는 성체 회로의 미시기전--계량 다리이며 “뉴런이 의미를 갖고
태어나 청소년기에 고정된다”를 검사하지 않는다. 재구성한 2번은 같은
species·region·cell type·projection에서 age \(\rho\), material scaffold
\(\mathcal D\), 접촉상태 \(\zeta\), 연속 생물변수 \(\mathbf y\)를 측정하는
별도 animal-locked D1 cohort로 검사한다. 모든 age group과 blind animal에서
같은 biological definition과 calibration을 갖는 공통 feature support
\(\mathcal F_\star\)를 endpoint 개봉 전에 고정하고 그 차원을 \(p\)라 한다.
animal마다 다른 feature를 채워 넣어 차원을 맞추지 않는다. 식 (21.15)의
parameter를 \(\eta(\rho,\mathcal D)=\{\bar{\mathbf y}_{\rm dev},Q_{\rm dev},
\pi^{\rm dev}\}\)라 두면 proper joint density는

\[
\begin{aligned}
-\log P_{\rm dev}(\Theta\mid\mathcal D,\rho;\eta)
={}&\tfrac12(\mathbf y-\bar{\mathbf y}_{\rm dev})^T
Q_{\rm dev}(\mathbf y-\bar{\mathbf y}_{\rm dev})\\
&-\tfrac12\log\det Q_{\rm dev}+\tfrac p2\log(2\pi)\\
&-\sum_{ijk}\sum_{r=0}^{2}\mathbf1[\zeta_{ijk}=r]
\log\pi^{\rm dev}_{ijk,r},\\
Q_{\rm dev}&\succ0,\qquad \pi^{\rm dev}_{ijk,r}>0,
\quad\sum_r\pi^{\rm dev}_{ijk,r}=1.
\end{aligned}
\tag{D1.1}
\]

로 둔다. \(Q_{\rm dev}=D_\rho+U_\rho U_\rho^T\)에서 \(D_\rho\)는 positive
diagonal, low-rank 차원은 training animal에서만 고른다. 각 사전지정 age
window의 training animal-equivalent 표본이 \(\max(10p,100)\) 미만이거나
\(\kappa_2(Q_{\rm dev})\ge10^4\), replicate-derived eigenvalue floor를 넘지
못하면 D1 prior branch를 중단한다.

longitudinal matching과 dropout을 잠근다는 문장만으로는 충분하지 않다.
observation model을 먼저

\[
\begin{aligned}
p(D^{\rm obs}_{as},R_{as}\mid\Theta,M^c,M^e,\psi_{\rm obs})
={}&p(D^{\rm obs}_{as}\mid\Theta,M^c,M^e,R_{as},\psi_Y)\\
&\times p(R_{as}\mid\bar R_{s-1},\bar D^{\rm obs}_{s-1},
I,C_0,\psi_R)
\end{aligned}
\]

로 분해하고 관측자료 likelihood를

\(\lambda=(\eta,\psi_Y,\psi_R)\)로 묶어

\[
p(D^{\rm obs}_{as},R_{as}\mid\mathcal D_a,\rho_{as};\lambda)
=\sum_{M^c,M^e}\int p(D^{\rm obs}_{as},R_{as}\mid
\Theta,M^c,M^e,\psi_{\rm obs})
P_{\rm dev}(\Theta\mid\mathcal D_a,\rho_{as};\eta)
p(M^c,M^e\mid C^c,C^e,\mathcal C_{\rm fid})\,d\Theta
\]

로 고정한다. 즉 same-cell/contact posterior를 적분하고 관측 indicator \(R\)의
dropout likelihood도 점수에 포함하며, MAP match나 mean imputation으로
대체하지 않는다. primary 식별 가정은 training-only history에 대한 MAR

\[
R_s\perp D_s^{\rm mis}\mid
(\bar R_{s-1},\bar D^{\rm obs}_{s-1},I,C_0),\qquad
\pi_R\ge0.05
\]

이고 cluster-aggregate weight의 \(ESS_{\rm cl}\ge0.70N_{\rm cluster}\), 최대
weight \(\le10\)을 E2와 같이 요구한다. blind data에서 dropout family를 다시
고르지 않는다. 확인 불가능한 MNAR에 대해서는 training에서 고정한 standardized
missing-value projection \(D^{\rm mis}_\star\)에

\[
\operatorname{logit}P(R_s=1\mid H_s,D_s^{\rm mis})
=\operatorname{logit}\pi_R(H_s)+\delta_R D^{\rm mis}_\star,
\qquad \delta_R\in[-\log2,\log2]
\]

를 적용한다. 이 범위 어느 값에서든 age-prior 또는 stability 판정이 뒤집히면
`D1_INCONCLUSIVE_DROPOUT`으로 멈춘다. identified refreshment/validation sample이
없다면 이 sensitivity를 MNAR 식별로 승격하지 않는다. \(\eta\), observation
family, \(\psi_Y,\psi_R\)의 모든 coefficient와 age smoothing은 training-animal
cross-fit에서만 추정해 \(\widehat\lambda\)로 동결하고 animal·age holdout의
negative log predictive density를

\[
\mathcal L_{\rm dev}=-\frac1{|\mathcal A_{\rm blind}|}
\sum_{a\in\mathcal A_{\rm blind}}\frac1{|\mathcal S_a|}
\sum_s\frac1{N^{\rm obs}_{as}}
\log p(D^{\rm obs}_{as},R_{as}\mid
\mathcal D_a,\rho_{as};\widehat\lambda)
\tag{D1.2}
\]

로 둔다. \(N^{\rm obs}_{as}\)는 해당 session의 실제 continuous primitive,
contact-state와 dropout indicator의 수이며 cell/contact 수가 다른 animal을
균형화한다. 이를 age-invariant, cell-type-only, age-shuffled prior와 같은
support·parameter budget에서 비교한다. full이 각 control보다 10% 이상 낮고
animal-bootstrap 개선 하한이 0보다 커야 한다. continuous primitive의 90%
posterior predictive coverage가 \([0.85,0.95]\) 안이어야 하고, categorical
contact는 coverage와 섞지 않고 held-out log score와 multiclass Brier score가
각 control보다 좋아야만 age-dependent prior를 지지한다.

“성숙=완전 고정” 대신 adult intervention까지 포함한 slow dynamics

\[
d\mathbf y_S=\left[-K_{\rm dev}\nabla U_{\rm dev}
+\Gamma(\rho,I,B)P_{\rm exp}(X,M)+P_{\rm homeo}(X,\mathbf y)\right]dS
+\Sigma_{\mathbf y}^{1/2}dB_S
\tag{D1.3}
\]

로 둔다. \(S\)의 단위는 day이고 \(\mathbf y\)는 calibration SD로 표준화한다.
\(U_{\rm dev}\)는 dimensionless, \(K_{\rm dev}\succeq0\)는 day\(^{-1}\),
\(\Gamma(\rho,I,B)\in[0,1]\)은 dimensionless gate, 두 \(P\)항은
standardized-unit/day,
\(\Sigma_{\mathbf y}\succeq0\)는 standardized-unit\(^2\)/day다. 이를 다음
서로 다른 null과 경쟁시킨다.

- adult experience-gate-off: \(\Gamma_{\rm adult}=0\)지만 복귀력, 항상성,
  process noise는 남긴다.
- complete-freeze: adult에서 전체 drift와 \(\Sigma_{\mathbf y}\)를 모두 0으로
  두어 \(d\mathbf y_S=0\)으로 만든다.
- age-invariant \(K_{\rm dev}\)와
  no-brake \(\Gamma(\rho,I,B)\equiv1\) control.

\(Q_{\rm cal}=\widehat\Sigma_{\rm tech}^{-1}\succ0\)는 training-only independent
technical replicate의 common-support covariance에 사전지정 shrinkage를 적용해
고정한다. intervention mechanism으로 endpoint 개봉 전에 정한 방향 \(a_\star\)와
부호 \(s_\star\in\{-1,1\}\)는
\(a_\star^TQ_{\rm cal}^{-1}a_\star=1\)로 정규화한다. scalar contrast와
equivalence margin을

\[
\Delta y_\star=a_\star^T(\mathbf y_{\rm post}-\mathbf y_{\rm pre}),\qquad
\delta_y=Q_{0.95}\!\left(
|a_\star^T(\mathbf y_{\rm tech,1}-\mathbf y_{\rm tech,2})|
\right)
\]

로 사전고정한다. complete-freeze를 기각하려면 slow model의 blind predictive
NLL이 10% 이상 낮고 animal-bootstrap 개선 하한이 0보다 크며,
\(s_\star\Delta y_\star\)의 95% CI 하한이 \(\delta_y\)보다 커야 한다.
\(\Delta y_\star\)의 CI 전체가 \([-\delta_y,\delta_y]\) 안이면 freeze와
equivalent하다고만 보고한다. adult experience-specific update를 주장하려면
slow model의 blind predictive NLL이 같은 parameter budget의
experience-gate-off \(\Gamma_{\rm adult}=0\) control보다 10% 이상 낮고,
animal-cluster bootstrap 개선 하한이 0보다 커야 한다. 이 gate가 실패하면
adult experience-specific update는 식별하지 않는다. complete-freeze 기각만으로
그 변화가 경험 때문이라고 말하지 않는다.

발달 brake를 주장하려면 slow model이 같은 parameter budget의 no-brake
\(\Gamma\equiv1\)와 age-invariant \(K_{\rm dev}\) 각각보다 blind NLL이 10%
이상 낮고, 각각의 animal-cluster bootstrap 개선 하한이 0보다 커야 한다.
no-brake gate만 실패하면 age-dependent brake 해석을, \(K\) gate만 실패하면
age-dependent restoring-force 해석을 금지하며 다른 통과한 dynamics 결과까지
자동 기각하지 않는다.

의미 endpoint는 세포 label이 아니라 별도 output \(O\)와의 age-indexed 관계로

\[
\begin{aligned}
\mathfrak M_{S_0,c,H}(\rho)
&=I(X_{S_0,t};O_{t+H}\mid h_t,C=c,\rho),\\
\pi_{\rho,c,H}(o\mid z,h)
&=p(O_{t+H}=o\mid z_t=z,h_t=h,C=c,\rho),\\
\pi^\star_{\rho,c,H}(o\mid z^\star,h)
&:=\pi_{\rho,c,H}\!\left(
o\mid T_{\rho\to\star}^{-1}z^\star,h\right),\\
\Delta_{\rm do}(x;\rho,c)
&=\mathbb E[\varphi(O)\mid do(X_{S_0}=x),\rho,c]\\
&\quad-\mathbb E[\varphi(O)\mid do(X_{S_0}=x_{\rm sham}),\rho,c],\\
D^{\nu_\star}_{{\rm sem},c,H}(\rho_1,\rho_2)
&=\int D_{\rm JS}\!\left[
\pi^\star_{\rho_1,c,H}(\cdot\mid z^\star,h),
\pi^\star_{\rho_2,c,H}(\cdot\mid z^\star,h)\right]
d\nu_\star(z^\star,h)
\end{aligned}
\tag{D1.4}
\]

고정한다. \(T_{\rho\to\star}:Z_\rho\to Z_\star\)는 output·행동을 보지 않은
anatomy/calibration 자료만으로 training animal에서 적합해 endpoint 개봉 전에
동결한 정준 alignment다. 독립 anatomical landmark·cell type·projection anchor,
적합 family와 동률 해소 순서도 manifest에 먼저 잠가 동치인 좌표변환 중 결과에
유리한 것을 고르지 않는다. age \(\rho\)의 사전고정 analysis support를
\(\mathcal S_\rho\)라 할 때 제한 map

\[
T_{\rho\to\star}\!\mid_{\mathcal S_\rho}:\mathcal S_\rho
\overset{C^1\text{-diffeomorphism}}{\longrightarrow}
\mathcal I_\rho:=T_{\rho\to\star}(\mathcal S_\rho)
\]

이 image 위 전역 일대일 대응이어야 한다. Jacobian rank가 모든 retained 점에서
\(d\)이고, 그 \(C^1\) inverse가 존재하며, 독립 calibration line element의
상대오차가 \(10^{-3}\) 미만이어야 한다. 아래 support를 만든 뒤에도
\(\operatorname{proj}_{z^\star}\Omega_\star\subseteq
\bigcap_\rho\mathcal I_\rho\)를 요구한다. 하나라도 실패하면
`D1_INCONCLUSIVE_ALIGNMENT`로 멈추며 \(\pi^\star\)나 \(D_{\rm sem}\)을
계산하지 않는다.

mouse의 primary age windows는 early postnatal P7--P14, adolescent P28--P42,
adult P70--P120로 고정하고 다른 species는 raw endpoint를 열기 전 homologous
milestone amendment가 필요하다. training animal에서 각 age-window의 \((z,h)\)
law를 \(\nu_\rho^{\rm tr}\)라 하고, 먼저 같은 정준 좌표로

\[
\bar\nu_\rho^{\rm tr}
:=(T_{\rho\to\star},\operatorname{Id}_h)_\#\nu_\rho^{\rm tr}
\]

처럼 push-forward한다. 세 \(\bar\nu_\rho^{\rm tr}\) 모두가 사전고정 kNN density
cutoff를 넘는 **정준 \((z^\star,h)\) 좌표에서만** 교집합 support
\(\Omega_\star\)를 만든다. blind feature로 support 경계를 다시 적합하지 않는다.
support gate는 pooled mass만 보지 않는다. role
\(q\in\{\mathrm{tr},b_1,\ldots,b_B\}\)는 training과 사전지정 blind animal
fold를 뜻한다. output을 열지 않은 transformed feature의 animal별 empirical
law를 \(\widehat\nu_{a\rho q}\)라 하고

\[
\begin{aligned}
m_{a\rho q}&:=\widehat\nu_{a\rho q}(\Omega_\star),\qquad
n^\Omega_{a\rho q}:=\sum_{i\in a,\rho,q}
\mathbf1[x_i^\star\in\Omega_\star],\\
\mathcal A^\Omega_{\rho q}
&:=\{a:m_{a\rho q}\ge0.25,\ n^\Omega_{a\rho q}\ge20\},\\
\frac1{|\mathcal A_{\rho q}|}\sum_{a\in\mathcal A_{\rho q}}m_{a\rho q}
&\ge0.50,\qquad |\mathcal A^\Omega_{\rho q}|\ge10
\quad\text{for every }(\rho,q).
\end{aligned}
\]

여기서 \(\mathcal A_{\rho q}\)는 그 age·role의 전체 독립 animal 집합이다.
이 첫 gate가 실패하면 `D1_INCONCLUSIVE_COMMON_SUPPORT`로 멈추고 조건부
기준측도를 만들지 않는다. 통과한 뒤에만 prevalence와 무관한 equal-age
target law를

\[
\nu_\star=\frac13\sum_{\rho\in\{\rm early,ado,adult\}}
\bar\nu_\rho^{\rm tr}(\,\cdot\mid\Omega_\star)
\]

로 endpoint 개봉 전에 고정한다. 각 role의 push-forward law를
\(\bar\nu_{\rho q}\)라 하고
\(\bar\nu_{\rho,\mathrm{tr}}=\bar\nu_\rho^{\rm tr}\)로 둔다.
\(\nu_\star\ll\bar\nu_{\rho q}\)와 positivity를

\[
\operatorname*{ess\,sup}_{x\in\Omega_\star}
\frac{d\nu_\star}{d\bar\nu_{\rho q}}(x)\le10
\quad\text{for every }(\rho,q)
\]

으로 먼저 요구하고 다음 support ratio·cluster weight를 계산한다.

\[
\begin{aligned}
r_{i\rho q}&:=\mathbf1[x_i^\star\in\Omega_\star]
\frac{d\nu_\star}{d\bar\nu_{\rho q}}(x_i^\star),
\qquad 0\le r_{i\rho q}\le10,\\
W_{k\rho q}&:=\frac1{n^\Omega_{k\rho q}}
\sum_{i\in k,\,x_i^\star\in\Omega_\star}r_{i\rho q},\\
ESS^\Omega_{{\rm cl},\rho q}
&:=\frac{(\sum_{k\in\mathcal K^\Omega_{\rho q}}W_{k\rho q})^2}
{\sum_{k\in\mathcal K^\Omega_{\rho q}}W_{k\rho q}^2},\qquad
A_{a\rho q}:=\sum_{k\in a\cap\mathcal K^\Omega_{\rho q}}W_{k\rho q}.
\end{aligned}
\]

여기서 \(x_i^\star=(T_{\rho\to\star}z_i,h_i)\),
\(\mathcal K^\Omega_{\rho q}\)는 \(\mathcal A^\Omega_{\rho q}\)에 속하면서
\(\Omega_\star\)에 실제 관측이 남은 독립 cluster 집합이다. density-ratio
family·bandwidth와 상한은 training-only nested cross-fit으로 고정하고, blind
fold에서는 output-free \((z^\star,h)\) calibration만 허용한다. \(r>10\)인
관측을 10으로 잘라 통과시키지 않으며 하나라도 상한을 넘거나 ratio가 존재하지
않으면 실패다. 모든 age와 모든 role마다

\[
ESS^\Omega_{{\rm cl},\rho q}\ge0.70|\mathcal K^\Omega_{\rho q}|,\qquad
\max_{a\in\mathcal A^\Omega_{\rho q}}
\frac{A_{a\rho q}}{\sum_{a'}A_{a'\rho q}}\le0.20
\quad\text{for every }(\rho,q)
\]

을 모두 통과해야 한다. 이 \(ESS^\Omega\)는 dropout weight ESS와 별개이며
\(\Omega_\star\)에 남은 관측으로 다시 계산한다. 어느 하나라도 실패하면
`D1_INCONCLUSIVE_COMMON_SUPPORT`로 멈추고 조건부 기준측도나 의미 거리를
계산하지 않는다. context와 horizon도 D1 manifest의 finite set
\(\mathcal P_\star=\mathcal C_\star\times\mathcal H_\star\)로 잠그며 사후 선택하지
않는다. 각 \((c,H)\)의 same-age independent-animal
\(D^{\nu_\star}_{{\rm sem},c,H}\) 95% quantile을
\(\varepsilon_{{\rm sem},c,H}\)으로 고정한다. global stabilization 판정은
\(\mathcal P_\star\)의 **모든** pair에서 다음을 요구한다.

- nested animal cross-fit으로 계산한 adolescent--adult
  \(D^{\nu_\star}_{{\rm sem},c,H}\)의 bootstrap 95% 상한
  \(\le\varepsilon_{{\rm sem},c,H}\)
- early-postnatal--adolescent \(D^{\nu_\star}_{{\rm sem},c,H}\)의 bootstrap
  95% 하한 \(>\varepsilon_{{\rm sem},c,H}\)
- held-out relational output NLL이 fixed-neuron-label과 age-shuffle control보다
  각각 10% 이상 낮고 animal-bootstrap 개선 하한 \(>0\)
- blind predictive MI bias-corrected 하한 \(>0\), age-stratified permutation의
  Holm familywise-adjusted \(p\le0.01\)

한 pair라도 실패하면 global stabilization을 선언하지 않고 사전지정 pair별
결과만 남긴다.

\(\Delta_{\rm do}\)는 실제 randomized pattern/sham support, consistency,
exclusion과 off-target gate가 있을 때만 causal meaning으로 보고하고, 없으면
\(\mathfrak M\)의 predictive relation만 남긴다. longitudinal same-cell/contact
posterior와 registration dropout은 위 observed-data likelihood에 적분한다.
D1 양성은
발달 prior와 관계적 의미를 지지할 뿐 개별 뉴런의 선천적 의미 label을
지지하지 않는다. D1과 E2가 서로 다른 종·회로·과제이면 둘을 이어 최종
매개사슬로 세지 않는다. 동일 biological system의 overlap cohort 또는
blind하게 검증된 hierarchical bridge까지 통과해야만 통합 gate를 열 수 있다.

## 12. 현재 결론과 허용된 다음 행동

1. AIND BCI v2 22-asset source catalog은 고정되었다.
2. 전체 behavior-prefix object inventory와 consolidated schema 감사는
   `PASS_WITH_PROVIDER_METADATA_INVALID`다. 이것은 준비 결과이며 생물 가설
   결과가 아니다.
3. 아직 endpoint-blind selector, 선택 object의 VersionId·content SHA-256,
   epoch 값, common target, same-ROI 값, clock monotonicity와 role별 trial 수를
   감사하지 않았다.
4. 따라서 E1 가설은 미실행이고 증거 상한은 계속
   `BIO_EVIDENCE_L0`다.
5. 다음에 허용된 유일한 행동은
   `AIND_BCI_E1_SELECTED_INPUT_CONTENT_AUDIT`이다. 이것은 장치·입력 준비
   판정이지 생물학 가설 결과가 아니다.
6. E1이 양성이어도 E2의 전도속도, physical weight/STP, sham,
   mediator-specific intervention, rescue와 D1의 발달 prior가 없으면 최종
   결론을 내리지 않는다.
