# Stx3 의존 가소성·보상상대 집단기하·행동 결합 분석계약 v1

Status: `ANALYSIS_CONTRACT_FROZEN_PRE_OUTCOME / BIOLOGICAL_ENDPOINT_NOT_YET_EVALUATED`

계약 ID: `CE_NPF_ALT_BIO_STX3_REWARD_ALIGNMENT_XN_v1`

고정일: 2026-09-01

## 1. 목표 정렬 게이트

- 최종 목표: 발달 prior, 국소 신경 집단의 기하, 연결·가중치·전달 물리의 가소성이라는 원래 세 가설 중 무엇이 실제 생물학 자료로 지지되는지 마지막 허용 단계까지 판별한다.
- 이번 단계의 하위 목표: 동일 생쥐의 day 0/day 5 CA1 영상에서 Stx3 의존 가소성 조작이 보상상대 집단표현의 기하 변화와 held-out 행동 변화에 함께 연결되는지 검정한다.
- 필요한 이유: 기존 D1–D7은 서로 다른 cohort의 구성요소 관찰이거나 동일세포 성분검사였고, `가소성 기전 → 집단기하 → 행동`을 한 cohort에서 판별하지 못했다.
- 목표 명확성: 명확하다. 다만 이 자료는 실제 연결행렬, 시냅스 가중치, 전도속도 또는 지연을 측정하지 않는다. Stx3 결손은 postsynaptic membrane-fusion 가소성의 상위 조작일 뿐이다.
- 계보 점검: 이 계약은 기존 `ALT_BIO D1–D7`의 다음 Stage 번호를 자칭하지 않는 독립 `STX3_REWARD_ALIGNMENT_XN` 계보다. DANDI 001868의 D8-secondary 계보와 합산하지 않는다.
- 다음 게이트: 아래 source/schema/registration/trial gates를 모두 통과하고 32개 NWB의 SHA-256이 전수 일치할 때만 수치 endpoint를 한 번 실행한다. 하나라도 실패하면 생물학 결과를 계산하지 않고 해당 `BLOCKED` 상태로 정지한다.

현재 상태를 구분하면 다음과 같다.

| 상태 | 항목 | 근거 |
|---|---|---|
| 준비됨 | DANDI 정본, 32개 asset 선택, 대표 NWB 스키마, 16마리 day0/day5 ROI map | 아래 source lock과 preflight 영수증 |
| 검사 중 | 전체 32개 NWB 다운로드·해시·전수 스키마 | 아직 미실행 |
| 지지됨 | 없음 | 생물학 outcome 값을 아직 열지 않음 |
| 실패/미확립 | 실제 `W`, 연결, 전도속도, 지연, mediator intervention/rescue | 이 자료에 측정치가 없음 |

## 2. 질문과 허용되는 주장

주요 신경 질문은 다음이다.

> 서로 다른 Y-maze 팔의 CA1 집단표현이 단순한 좌·우 시각 정체성이 아니라 “보상까지 남은 거리”로 정렬했을 때 선택적으로 가까워지는 변화가 control에서 Stx3 결손군보다 큰가?

행동 질문은 다음이다.

> 신경 계산에 사용하지 않은 trial에서 보상 직전 비섭취성 핥기의 집중도가 control에서 Stx3 결손군보다 더 증가하는가?

완전한 결합 질문은 다음이다.

> 위 두 변화가 같은 생쥐에서 양의 처치군-보정 연관을 보이는가?

모든 게이트가 양성이어도 허용되는 최대 문장은 다음뿐이다.

> 성체 수컷 생쥐 CA1의 동일동물 종단자료에서 Stx3 의존 postsynaptic 가소성 조작은 held-out 보상상대 집단기하 변화 및 분리된 보상예측 행동 변화와 연관되었다.

다음 문장은 금지한다.

- 시냅스 가중치, 연결, 수초, 전도속도 또는 지연이 직접 측정되어 기하를 바꾸었다.
- crossnobis 하나가 매끄러운 리만 다양체 전체 또는 뇌의 물리적 공간 접힘을 입증했다.
- 집단기하가 행동의 인과 매개자다.
- 청소년기에 의미가 고정되거나 뉴런이 의미를 가지고 태어난다.
- Stx3 처치가 무작위 배정되었거나 acquisition batch가 완전히 통제되었다.

## 3. 정본과 바이트 잠금

### 3.1 논문·자료·코드

- 최종 논문: Plitt, Kaganovsky et al., *Neuron* (2026), DOI `10.1016/j.neuron.2026.03.006`.
- DANDI 정본: `DANDI:001710`, published version `0.260213.0329`, DOI `10.48324/dandi.001710/0.260213.0329`, CC BY 4.0.
- 전체 manifest: 139 assets, 78,579,169,148 bytes.
- 전체 `assets.yaml` SHA-256: `8b5bb8e170398307d3c0ca02fb66dbef1a4c47acd5d9bbbeacc249ee3d047288`.
- 선택 receipt: `data/external/plitt_kaganovsky_stx3_2026/dandi_001710_dense_day0_day5_selection.json`.
- 선택 receipt SHA-256: `a2c139cff4312b7c3869465b355aa738552373d119f96c8aab3a5e4dc4982dfa`.
- 선택 범위: dense `Ctrl`/`Cre`의 code day 0과 day 5, 32 assets, 20,006,552,508 bytes.
- 정렬된 `path<TAB>size<TAB>sha256` LF 결합의 canonical SHA-256: `3b2ceb2c5e3715d2f03a030070c06679a1b5d3fadbc63f2ae460f747e6f85663`.
- 공식 코드 commit: `f2ab24db8709a321d38576a1fa674f95035a2fec`.
- `mouse_metadata.py` SHA-256: `2a52a5561de9ea61c379b4e6997aa51429403dd75be58ed3fd99d7c56f58d68a`.
- `session.py` SHA-256: `82938af1cb7689fb9c919b29606fde9a121ac538e2e7db8c4532935cd07488a1`.
- `behavior.py` SHA-256: `e168df23550cae4e5dc1ee92dab7e3346db128fac43e7ae3646cb22c0a45188c`.
- `utilities.py` SHA-256: `cda27c7efe916eaf2ca478ecc574c34da10ea4426c4553367a434d0d68951d76`.
- `reward_overrep.py` SHA-256: `81bfd032d0d10c083a6bbd61dc4e1148306ea3d157b963f4028d82466fabe3e7`.

### 3.2 ROI registration

- Figshare v5 DOI: `10.6084/m9.figshare.31286365.v5`.
- `roi_aligners.zip`: 14,164,344 bytes, provider MD5 `fa3864a15d5e3a191feeb5cb34ba4002`, SHA-256 `d2b593bcfc875696e40f55d51bdc29cf39abd4b1740169b1f6337397574aad34`.
- restricted-unpickle preflight: `data/external/plitt_kaganovsky_stx3_2026/roi_aligner_day0_day5_audit.json`.
- preflight SHA-256: `985dc4b2cc87cd4dadb5af65efa015579fa90fd0c68c68bea233fa06d2d94ae4`.
- 16마리 day0/day5 ordered pair canonical SHA-256: `c5ce0aca6ab6bcf4ac4294bb3b0cae97606d67b53a08333225f4191350149fe5`.
- 확인된 공통 ROI 범위: 마리당 162–1,095개로, 사전 최소값 20을 모두 넘는다.

pickle은 unrestricted `pickle.load`/`dill.load`로 열지 않는다. 허용된 NumPy scalar/dtype 재구성만 받는 restricted unpickler를 사용한다. 매핑 pair는 day0 ROI index 오름차순으로 결정론적으로 정렬한다.

`shuffle_pkls.zip`은 제공자 outcome cache다. SHA-256 `2134a66fe1720b5b531d5b134720b22f13c8ea54b5873c1f12b86c829663f255`만 잠그고 primary 실행 전후 모두 입력으로 열지 않는다.

### 3.3 값 비열람 스키마 영수증

- 대표 파일: `sub-Ctrl-2_ses-ymaze-day3-scan0-novel-arm1_behavior+ophys.nwb`.
- 파일 SHA-256: `67655403042cc6a8198dc39eb05286345cd9dad1d6e2b03d72ee2f3f7db31c87`.
- schema receipt: `data/external/plitt_kaganovsky_stx3_2026/schema_sample_audit.json`.
- schema receipt SHA-256: `d3010d31f82a38cea05762cceade2d245606f69f3da6bcaddb4c7572167e9f36`.
- 확인 범위: HDF5 path, shape, dtype, subject identity뿐이며 신경·행동 outcome은 평가하지 않았다.

## 4. cohort와 독립 단위

- primary cohort: `Ctrl_1–Ctrl_9` 9마리, `Cre_1–Cre_7` 7마리.
- 독립 통계 단위: mouse. cell, frame, position bin, trial을 독립 표본으로 세지 않는다.
- 분석일: code day 0과 day 5, 논문 표기의 day 1과 day 6.
- 공통 indicator: dense cohort 모두 `AAV1-hSyn-jGCaMP7f`.
- sparse cohort는 primary 및 행동 결합에서 완전히 제외한다.
- 다른 자유행동 cohort나 행동전용 동물을 결합하지 않는다.

다음 confounding은 계약상 제거되었다고 주장하지 않는다.

- 처치군 무작위 배정이 보고되지 않았다. 무작위화가 명시된 것은 familiar arm 배정이다.
- `Ctrl_1–5`는 980 nm, `Ctrl_6–9`는 920 nm인 반면 Cre는 모두 980 nm다.
- 생년·실험 batch가 처치군과 완전히 교차하지 않는다.
- 모두 수컷이므로 성별 일반화가 불가능하다.
- 공개 aligner를 원 raw/Suite2p 자료에서 독립 재생성할 수 없다.

따라서 양성이어도 strict evidence ceiling은 `L2 same-animal longitudinal/held-out triad`; 기전 개입의 `L3 component`로 기술할 수는 있지만 L3 확정이나 L4 매개로 승격하지 않는다.

## 5. fail-closed hard gates

아래를 순서대로 모두 통과해야 한다.

1. 32개 선택 asset의 path, byte size, SHA-256이 selection receipt와 전부 일치한다.
2. 각 NWB subject identity와 path subject가 `_`/`-` 정규화 뒤 일치하고, day는 path와 정본 metadata에서 일치한다.
3. `F_dff`, fluorescence, neuropil 배열이 같은 `(frames, ROI)` shape이고, 2P-aligned 행동의 길이가 frames와 일치한다.
4. full-resolution 행동에는 `non-consummatory licks`, `reward`, `speed`, `position`, `left or right`, `block`, `trial start/end/number`가 모두 있다.
5. day0/day5 ROI ravel index는 pinned `mouse_metadata.py`와 NWB annotation이 일치한다. 파일명 novel-arm 문자열은 endpoint 정의에 사용하지 않는다.
6. aligner의 day0/day5 index가 각 NWB ROI 열 범위 안에 있고 중복되지 않는다.
7. neural loader와 full-resolution behavior loader의 session-local completed-trial ordinal을 join했을 때 `n_trials`, `LR`, `block_number`가 완전히 일치한다. 자동 offset 보정, fuzzy join, 한쪽 trial 삭제는 금지한다.
8. endpoint session은 두 날 모두 `block_number == 5`만 쓴다. code day0의 blocks 0–4 familiar-only 자료는 noise/nuisance training에만 쓰며 representation mean이나 행동 endpoint에 섞지 않는다.
9. 각 mouse×day×arm의 완료 trial을 시간순으로 `A,B,H,A,B,H,…` 배정한다. 각 cell에 A, B, H가 각각 최소 4 trials여야 한다.
10. day0/day5 공통 ROI 중 아래 모든 필요 ratemap과 공통 precision이 유한한 ROI만 한 번 고정한다. 남는 ROI가 20개 미만이면 실패한다.
11. 16마리 모두 위 gate를 통과해야 confirmatory group permutation을 실행한다. 실패한 마리를 버리고 표본수를 줄여 계속하지 않는다.
12. primary와 두 필수 sensitivity의 모든 mouse statistic이 유한해야 한다. clipping, outlier 제거, group별 제외, 임의 downsampling은 금지한다.

실패 상태는 `STX3_SOURCE_BLOCKED`, `STX3_SCHEMA_BLOCKED`, `STX3_REGISTRATION_BLOCKED`, `STX3_TRIAL_JOIN_BLOCKED`, `STX3_NUMERICAL_BLOCKED`로 구분한다. 이는 생물학 가설의 음성 결과가 아니다.

## 6. 고정 전처리와 trial 분리

### 6.1 위치와 보상창

- 30개 1-unit bin: edges `13,14,…,43`, centers `13.5,…,42.5`.
- crossnobis에는 첫·끝 bin을 제외한 interior 28 bins만 쓴다.
- pinned `session.py`의 Catmull–Rom 경로와 reward-zone 식으로 얻는 front는 다음과 같다.
  - early/left: `tfront = 32.67690445738824`
  - late/right: `tfront = 39.83365218636522`
- source 구현의 `floor(tfront - offset - first_bin)` 규칙을 사용한 보상 직전 5-bin window는 full 30-bin index로 left `14..18`, right `21..25`다.
- 각 NWB annotation에 reward-zone 값이 있으면 위 값과 `1e-9` 이내에서 일치해야 한다. 일치하지 않으면 schema blocked다.

각 trial×bin의 신경값은 그 bin에 들어온 frame의 `F_dff` 평균이다. fold ratemap은 먼저 trial별 bin 평균을 만든 뒤 trial들을 동일 가중 평균한다. frame 수가 많은 trial에 추가 가중치를 주지 않는다.

### 6.2 A/B/H 분리

각 arm 안에서 block 5 완료 trial을 시작시간 순으로 정렬하고 1번째 A, 2번째 B, 3번째 H, 이후 반복한다.

- A/B: 신경 집단기하에만 사용.
- H: full-resolution 행동에만 사용.
- H trial은 neural mean, whitening, nuisance coefficient 적합에 사용하지 않는다.
- blocks 0–4는 whitening과 nuisance coefficient에만 사용하며 A/B/H endpoint에는 사용하지 않는다.

10% reward-omission trial만 쓰는 분석은 작은 기대 표본 때문에 primary가 아니다. omission-only 행동은 arm별 최소 2 omission H trials가 있을 때 방향성 sensitivity로만 기록하며 PASS를 만들거나 구제하지 않는다.

## 7. 공통 metric basis와 crossnobis

### 7.1 공통 ROI와 diagonal precision

각 mouse에서 aligner가 지정한 day0/day5 공통 ROI만 사용한다. 두 날 blocks 0–4의 모든 완료 trial을 pool하되 각 `day×LR×position_bin` 평균을 먼저 제거한다. cell별 residual sample variance를 `v_c`라 한다.

분산 floor는

\[
v_{floor}=10^{-3}\operatorname{median}_{c:v_c>0,\ finite}(v_c)
\]

로 고정하고, mouse별 하나의 공통 diagonal precision을

\[
W_i=\operatorname{diag}\{1/\max(v_c,v_{floor})\}
\]

로 만든다. day별 precision을 따로 만들거나 full covariance/ridge를 사후 선택하지 않는다. 이 basis는 day0/day5 변화량에 공통이다.

### 7.2 true alignment와 wrong-shift null

interior 좌표를 `I={0,…,27}`로 다시 번호화한다. left와 right의 같은 reward-front offset `k=1,…,5`에 대해 A/B fold의 공통-ROI 평균 차이를 각각 `δ^A_{d,k,s}`, `δ^B_{d,k,s}`라 한다. right window만 circular shift `s`만큼 옮긴다.

\[
d_{d,s}=\frac{1}{5}\sum_{k=1}^{5}
\frac{(\delta^A_{d,k,s})^\top W_i\delta^B_{d,k,s}}{p_i}.
\]

true alignment는 `s=0`이다. right true window와 한 bin도 겹치지 않는 wrong shift 집합은 결과와 무관하게

\[
S=\{5,6,\ldots,23\}
\]

의 19개로 고정한다. modulo wrap은 물리적 이웃이라는 주장이 아니라 label-shift null일 뿐이다. 값이나 동물에 따라 shift를 더 빼지 않는다.

보상상대 접힘 proxy는

\[
G_{i,d}=\operatorname{median}_{s\in S}d_{d,s}-d_{d,0},
\qquad
\Delta G_i=G_{i,day5}-G_{i,day0}.
\]

양의 값은 임의의 잘못 정렬보다 실제 보상상대 정렬에서 좌·우 집단표현이 더 가까워졌다는 뜻이다. 이는 population-output의 유한 metric proxy이며 리만 다양체 전체를 증명하지 않는다.

## 8. held-out 행동 endpoint

H trial의 full-resolution `non-consummatory licks`만 쓴다. 각 arm에서 reward front 직전 3 units, 즉 `[tfront-3,tfront)`의 lick event 수를 해당 arm H trial의 whole-track `[13,43)` lick event 수로 나눈다.

- arm 전체 lick 수가 0이면 결측이나 제외가 아니라 `B_arm=0`이다.
- left/right arm을 trial 수와 무관하게 동일 가중한다.
- 보상 전달 이후 lick은 포함하지 않는다.

\[
B_{i,d}=\tfrac12(B_{left}+B_{right}),
\qquad
\Delta B_i=B_{i,day5}-B_{i,day0}.
\]

같은 H trials에서 whole-track mean speed를 계산하고 `Δspeed_i`를 필수 motor sensitivity의 보정변수로 기록한다.

## 9. 세 가지 confirmatory 검정

방향은 모두 사전 고정한다.

1. 신경: `mean(ΔG_Ctrl) > mean(ΔG_Cre)`.
2. 행동: `mean(ΔB_Ctrl) > mean(ΔB_Cre)`.
3. 결합: 처치군을 보정한 `ΔG–ΔB` 순위 연관이 0보다 크다.

신경과 행동은 16마리 중 9마리를 Ctrl로 놓는 `C(16,9)=11,440`개 label 배치를 전수 열거한다. 통계량은 `mean_Ctrl - mean_Cre`, 동률은 `>=`로 세는 one-sided exact permutation이다.

결합 통계량은 전체 16마리의 midrank를 만든 뒤 각 rank에서 실제 처치군 내 평균 rank를 빼고 두 residual rank의 Pearson correlation을 구한 partial Spearman이다. null은 `ΔB` rank를 실제 처치군 안에서만 섞는다. PCG64 seed `20260901`, 정확히 99,999회, one-sided Monte Carlo p는 `(1 + count(T_perm >= T_obs))/100000`이다.

\[
p_{joint}=\max(p_G,p_B,p_{assoc}).
\]

primary conjunction은 세 관측 방향이 모두 맞고 `p_joint<=0.05`일 때만 통과한다. component 하나의 양성으로 conjunction을 선언하지 않는다.

## 10. 필수 confound sensitivity

두 분석은 선택 사항이 아니며 primary와 함께 항상 실행·보고한다.

### 10.1 `S_rate`: global population gain 제거

모든 trial×bin population vector에서 같은 시점/표본의 공통 ROI 평균을 cell 축으로 뺀다. blocks 0–4 residual에도 같은 변환을 적용해 `W_i`를 새로 추정하고 7–9절 전체를 다시 계산한다.

### 10.2 `S_motor`: speed/lick coupling 제거

두 날 blocks 0–4만 training 자료로 사용한다. mouse별 training speed와 lick을 각각 고정 평균/SD로 z-score한다. speed SD가 0이면 sensitivity는 numerical blocked다. lick SD가 0이면 `gamma_c=0`으로 고정한다.

각 cell에 대해 다음 OLS를 적합한다.

\[
x_c \sim C(day\times LR\times position\_bin)+\beta_c z_{speed}+\gamma_c z_{lick}.
\]

구현은 joint category 안에서 `x`, `z_speed`, `z_lick`을 demean한 뒤 Frisch–Waugh–Lovell OLS를 사용한다. ridge, 변수선택, 상호작용 추가는 금지한다. block 5에는 spatial/intercept 계수를 적용하지 않고 nuisance 항만 뺀다.

\[
x'_c=x_c-\beta_cz_{speed}-\gamma_cz_{lick}.
\]

그 뒤 cell-axis 평균을 제거하고, 변환된 blocks 0–4로 공통 `W_i`를 다시 추정하여 전체 신경 endpoint를 계산한다. H trial의 행동값은 바꾸지 않는다. 결합 연관에서는 `Δspeed` rank와 처치군을 함께 보정한 partial Spearman을 사용하며, `ΔB` rank를 군내 순열할 때마다 같은 보정을 다시 계산한다.

### 10.3 confound 판정

- claim-ready PASS에는 primary, `S_rate`, `S_motor` 모두 같은 세 방향과 `p_joint<=0.05`가 필요하다.
- 어느 sensitivity에서든 `mean ΔG_Ctrl - mean ΔG_Cre <= 0`이면 `STX3_GLOBAL_RATE_OR_MOTOR_CONFOUND_COMPATIBLE_FAIL`이다.
- 방향은 유지하지만 sensitivity `p_joint>0.05`이면 `STX3_PRIMARY_ONLY_CONFOUND_SENSITIVE_NO_EVIDENCE_ELEVATION`이다.
- non-wrapping wrong-shift, omission-only 행동, 980-nm-only `Ctrl_1–5` 대 `Cre_1–7`은 보고용 sensitivity이며 primary를 구제하지 않는다.

## 11. 고정 결과 상태

- `STX3_REWARD_ALIGNMENT_BEHAVIOR_CONJUNCTION_CONFOUND_ROBUST_SUPPORTED`: 모든 hard gate와 primary·S_rate·S_motor conjunction 통과.
- `STX3_PRIMARY_ONLY_CONFOUND_SENSITIVE_NO_EVIDENCE_ELEVATION`: primary는 통과하지만 필수 sensitivity의 방향은 같고 conjunction은 실패.
- `STX3_GLOBAL_RATE_OR_MOTOR_CONFOUND_COMPATIBLE_FAIL`: 필수 sensitivity에서 신경 방향이 0 또는 역전.
- `STX3_GEOMETRY_COMPONENT_ONLY`: 신경 component만 통과하고 행동 또는 결합 component가 실패.
- `STX3_COMPONENT_CONJUNCTION_NOT_SUPPORTED`: hard gate는 통과했으나 primary 세 component 중 하나 이상이 실패하고 위 좁은 component 상태에도 해당하지 않음.
- 앞서 정의한 `*_BLOCKED`: source/schema/registration/trial/numerical gate가 endpoint 전에 실패.

primary 실패를 다른 window, cell pooling, 다른 p-value, 다른 shift, 사후 outlier 제거로 구제하지 않는다. 새 정의는 새 이름의 후속 탐색계약으로만 허용한다.

## 12. 증거 사다리 귀속

성공 시 구성요소별 귀속은 다음과 같다.

- source-locked CA1 population observation: `L1`.
- 동일동물 common-ROI 종단·trial-heldout 집단기하 및 행동 triad: 최대 `L2`.
- Stx3 결손이라는 기전 조작: `L3 component`로 기술 가능하지만 비무작위 배정, wavelength/batch confounding, rescue 부재 때문에 L3 확정 아님.
- 실제 `W/STP/연결/전도속도/지연 → g`: 측정 부재로 실패/미검정.
- `g → behavior` 인과 매개: mediator-specific intervention/rescue 부재로 `BIOLOGICAL_MEDIATION_UNTESTED`.
- 원래 통합 사슬 등급: 가장 약한 화살표를 따르므로 이 결과 하나로 `BIO_EVIDENCE_L0`에서 자동 승격하지 않는다.

실행 뒤에는 반드시 다음 네 질문에 답한다.

1. 원래 질문에 답했는가?
2. 무엇이 반증되었는가?
3. 무엇은 아직 살아 있는가?
4. 다음에 허용되는 행동은 무엇인가?
