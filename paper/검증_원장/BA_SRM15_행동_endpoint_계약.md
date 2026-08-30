<!-- 도메인: ce-brain-bio -->

# BA-SRM15 연구 계약 — 실데이터 행동 endpoint (2단계, 비가역 개봉 포함)

Status: `ENDPOINT_COMPLETE / VALID_NEGATIVE / ALL_FOUR_FALSIFIERS_FIRED` (계약 동결 2026-08-30, 결과 기입 2026-08-30)

계보: BA-SRM7 (endpoint 문면 동결, 미개봉) → BA-SRM8~12 (장치 합성 확증) → BA-SRM13/14 (`NEURAL_INPUT_LOCK_PASS_V3_DEV`) → **BA-SRM15 (이 계약)**.

## 1. 질문과 판본 지위

시험 질문 (SRM7 §1-3 승계): **[예측 후보]** source-locked *C. elegans* calcium에서 확증 연산자의 네 soft spectral feature $(q,\nu,\kappa,\mathcal M)$가 같은 정보·용량의 matched control들보다 held-out future locomotion(`behavior.v`, $h=6$) 예측에 증분값을 갖는가.

**판본 지위**: 이 corpus는 판본 제안(v13·v14 장치 결정)에 사용되었으므로 통과해도 최대 `BIO_EVIDENCE_L3_DEVELOPMENTAL_HELD_OUT`이다(SRM7 §12 승계). 독립 확증은 외부 corpus(WormID/DANDI 또는 IBL)에서 retune 없는 재현으로만 가능하다. 의식·해마·synaptic edge·인간·AGI는 시험 대상이 아니다.

## 2. 동결 문면의 승계와 연산자 사상

SRM7 §7~§12를 **문면 그대로** 승계하되, 이 계보의 유일한 구조 변경(SRM13 §2에서 동결)에 따라 $G_t$의 정의만 확증 연산자로 사상한다. 이 사상은 SRM15의 새 변경이 아니라 SRM13 동결의 일관 적용이다.

| SRM7 기호 | SRM15 정의 |
|---|---|
| $z$ | robust 표준화 causal $I$ (prefix median/$1.4826\cdot$MAD, clip $\pm4$, 결측 0 + mask) — SRM13과 동일 |
| $G_t$ | `causal_q`(`POWER_theta2_p1p5__gamma2__radial_huber_c3`, $D_r=\operatorname{diag}\sqrt{\pi_i}$)의 물리시간 causal 공분산 `covs[t]` |
| $r_{\star,t}$ | `causal_q`의 anchor별 $r_\star$ (유효 양weight 수 기반) |
| $c_G$ | `causal_q`의 calibration prefix median $\operatorname{tr}G/r_\star$ (nonfinite·$\le10^{-12}$면 recording abstain) |
| $q_t$ | `causal_q`의 $Q_t=\sum_k \mu_k/(\mu_k+1)/r_{\star,t}$ ($\lambda=1$ primary; sensitivity grid $\{0.1,0.3,1,3,10\}$ 보고만) |
| $\kappa_t,\nu_t,\mathcal M_t$ | SRM7 §7 식 그대로, $S_{t,1}$은 $\widetilde G_t(\widetilde G_t+I)^{-1}$, $\sigma_\kappa,\sigma_\nu$는 recording prefix anchor RMS |
| anchor 집합 | SRM13 lock(SHA `490bed30…`)의 recording·split별 ID **그대로** — 재계산 금지 |
| 충분성 규칙 | SRM14 §2 (소비 유도: train + 역할 split $\ge100$) |

변경 없이 승계되는 것: AR 기준식 $\hat b^{\rm AR}_{t+h}=\alpha+\sum_{\ell\in\{0,1,3,6\}}\beta_\ell b_{t-\ell}$; ridge grid $\{0,0.01,0.1,1,10,100\}$과 tie 규칙; outer split (SRM7 §8 표)과 적합·선택·개봉 절차; 필수 common-row family 9종(`AR`,`CE_SOFT`,`FIXED_D` $d\in\mathcal D$,`FIXED_4`,`PARTICIPATION_RATIO`,`RAW_SPECTRAL`,`CAUSAL_UNWEIGHTED`,`MASK_ONLY`,`RED_CHANNEL`)의 feature map (eigen 값·projector는 $G_t$에서); adverse control 3종(`PHASE_RANDOMIZED`,`TIME_REVERSED`,`CIRCULAR_BEHAVIOR_SHIFT` — 각자 독립 ridge 선택); GFP 11-recording nuisance panel; $\mathcal D=\{d\in\{2,4,8,16,32,48\}:d<\min_r r_{\star,r}\}$과 `PROJECTOR_UNIDENTIFIED` 규칙; primary residual $\Delta R^2_r$ 정의와 두 held-out GCaMP 모두 $\Delta R^2>0$ + RMSE 우위 게이트; falsifier 발동식 $\delta^{\rm GCaMP}_m,\delta^{\rm GFP}_{\rm CE}$ (§11); moving-block bootstrap(60, 2000, seed 20260823) descriptive; window-level p-value·모집단 일반화 금지.

진단 전용 중 `RATIO2_075`(SRM6 규칙 abstention 보고)는 실행한다. `SOURCE_SYMMETRIC`(보관 symmetric interpolation 대조)은 **실행하지 않으며** `NOT_RUN`으로 보고한다 — 비게이트 진단이고 causal 경쟁에 불참하므로 판정에 영향 없음을 명기한다.

## 3. 단계 실행 규율 (비가역 경계)

1. **Stage A (행동 개봉: outer-train만)** — behavior struct의 값은 outer-train 9 recording(GCaMP 7 + GFP train 7 중 소비분)에서만 읽고, 각 family 계수를 pooled outer-train prefix anchor로 적합한다. feature·target 공통 mean·scale도 여기서만 fit.
2. **Stage B (선택)** — outer-validation recording의 middle-20%로 ridge와 `FIXED_D`의 $(d,\mathrm{ridge})$를 선택한다. 선택 후 어떤 계수·family·threshold도 변경 금지.
3. **Stage C (단일 개봉)** — outer-held-out recording의 last-20%를 **조건 없이 한 번** 열어 전 family·adverse control·GFP panel을 채점한다. validation 성능을 이유로 개봉을 취소하지 않는다. Stage C 이후 어떤 재적합·재선택도 금지.
4. 각 stage의 산출(계수 해시, 선택 결과, 점수)을 stage별 영수증으로 남기고 다음 stage 전에 동결한다.

## 4. falsifier와 결과 코드 (SRM7 §11 문면 그대로)

`SOFT_DIMENSION_INCREMENT_NOT_SUPPORTED` / `MEASUREMENT_ARTIFACT_NOT_EXCLUDED` / `TEMPORAL_ALIGNMENT_NOT_IDENTIFIED` / `FIXED4_NOT_SUPPORTED` — 복수 동시 발동 가능, adverse 실패를 다른 score로 덮지 않는다. 어떤 결과든(양·음) §5에 기입하고 음성 결과도 완결한다.

`REVISION_TRIGGER`: D→I→P→C→B→T 분류, 명백한 코드 결함만 역할당 최대 2회 수리, threshold·$W$·$h$·$\lambda$·split·seed·model·ridge·endpoint·pass boundary의 결과 후 변경은 새 계약+독립 corpus 필요.

## 5. 결과 (2026-08-30 실행, 동결 절차 그대로 — 완결된 음성 결과)

**판정: [산출: 유효한 경험적 반증] — falsifier 4종 전부 발동.** 확증 연산자의 네 soft spectral feature $(q,\nu,\kappa,\mathcal M)$는 이 corpus의 held-out locomotion 예측에서 증분값을 갖지 않는다.

### 5.1 단계 이력

- verify: 22/22 recording의 anchor 집합이 SRM13 lock과 SHA 동일 (`anchor_identity_all_match=true`).
- Stage A/B: outer-train 14 + validation 4의 행동값만 개봉. 전 family·adverse의 ridge 선택이 test 개봉 전에 닫힘 (GCaMP 전 family ridge $0$ 선택, `FIXED_D`는 $(d{=}32,\ \mathrm{ridge}\ 0)$). validation 단계에서 이미 CE_SOFT 평균 $R^2$ $0.374$ 대 AR $0.534$의 열세가 보였으나 동결 규율대로 개봉을 취소하지 않았다.
- Stage C: held-out 4 recording(GCaMP 2 + GFP 2)의 last-20%를 조건 없이 1회 개봉.

### 5.2 발동한 falsifier와 수치

| 결과 코드 | 근거 수치 (held-out) |
|---|---|
| `SOFT_DIMENSION_INCREMENT_NOT_SUPPORTED` | $\Delta R^2$: `20200309_162140` $=-0.0505$, `20200310_142022` $=-0.1018$ (둘 다 $\le0$). CE_SOFT $R^2$: $0.6963/-0.2586$ 대 최선 대조군(AR $0.7468/-0.1568$대 RAW 등). bootstrap 기술 구간 $[-0.172,-0.009]$ 전체 음수 |
| `MEASUREMENT_ARTIFACT_NOT_EXCLUDED` | $\delta^{\rm GFP}_{\rm CE}=+0.0281>\delta^{\rm GCaMP}_{\rm CE}=-0.0490$ — CE 특징의 효과가 GFP nuisance와 구별되지 않음. $\delta_{\rm MASK}=-0.0246$, $\delta_{\rm RED}=-0.0043$도 $\delta_{\rm CE}$ 이상 |
| `TEMPORAL_ALIGNMENT_NOT_IDENTIFIED` | 위상무작위·시간역전·순환이동 대조가 두 held-out 모두에서 CE_SOFT $R^2$ 이상 (예: TIME_REVERSED $0.7117/-0.1763$) |
| `FIXED4_NOT_SUPPORTED` | validation이 $d=32$를 선택, $d=4$는 선택도 우세도 아님 |

부가 관찰: 두 번째 held-out 동물(`20200310_142022`)은 **AR 포함 전 모델이 음의 $R^2$** — 그 구간의 locomotion 자체가 이 특징 공간에서 예측 불가. 이는 CE 특징의 실패와 별개의 데이터 속성으로 기록한다.

### 5.3 증거·재현

verify/stage-a/stage-b/stage-c 영수증 SHA-256: `cac85dbcfdf7d270db96db4295800f58790084d59549d2d34458af0f994f1d25` / `2355c5cbaacb97cf451e530e97d4262954512a72b019aba1350618502e3ab543` / `2a047dc1cf42f77220aaa1373a06c5864ebc84a3070976ab6d0c73f74d5eb123` / `5fc6fe3ac1fd850c7751933f939fc437fe130a192a73d2017cebc5759c6be1df`. 러너: `examples/brain/ba_srm15_endpoint.py`·`ba_srm15_stages.py`·`ba_srm15_run_stages.py` (결정론; 재실행으로 영수증 재생성 가능). `SOURCE_SYMMETRIC`은 계약대로 NOT_RUN.

### 5.4 지위와 재개 조건 (계보 완결)

- **보존되는 좁은 주장**: (a) SRM10~12의 L0 장치 확증(오염 강건 순위 안정성)은 이 음성 결과로 무효화되지 않는다 — 장치는 성립하고, 그 장치가 읽는 양이 이 행동 endpoint에 무익함이 확정된 것이다. (b) SRM13/14의 입력 계약 성립. (c) 이 반증 자체 — 유효차원 soft 특징의 행동 예측 무증분 — 는 후속 경로의 음성대조군이다.
- **소진**: 이 corpus의 GCaMP held-out 2개는 개봉·소진되었다. 이 corpus 위에서의 어떤 CE 특징 재조정·재시도도 독립 확증이 될 수 없다.
- **재개 조건**: (i) 구조적으로 다른 readout 가설(특징이 아니라 상태·결합·개입 seam이 다른 후보 3개 등록 후 1개 사전 선택)과 새 corpus, 또는 (ii) 외부 corpus(WormID/DANDI, IBL)에서 retune 없는 독립 시험. 관측 근접·부분 양성 수치로 이 판정을 재해석하지 않는다.
- `CLAIM_CEILING` 최종: 이 계보 전체에서 "뇌가 이렇게 동작한다"급 주장 없음. 유효차원은 관측 분석자 양이며, 의식·기억·해마·AGI와의 연결은 미시험으로 남는다.
