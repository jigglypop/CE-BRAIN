<!-- 도메인: ce-brain-bio -->

# BA-SRM13 연구 계약 — 확증 장치의 실데이터 신경 입력 재감사 (1단계, 행동 봉인)

Status: `SOURCE_ROOTED_INPUT_STOP_V2 / 21_OF_22_PASS` (계약 동결 2026-08-30, 결과 기입 2026-08-30)

계보: BA-SRM7 (`SOURCE_ROOTED_INPUT_STOP`) → BA-SRM8~12 (합성 funnel, `SYNTHETIC_CONFIRMED_L0_DEV` 14/14) → **BA-SRM13 (이 계약)**.

## 1. 질문과 판본 경계

BA-SRM7은 실제 *C. elegans* GCaMP 22 recording에서 archive·schema·clock·unit eligibility를 전부 통과했으나, **행동과 무관한 common-anchor lock**(엄격 $W$-창·gap 규칙 anchor가 split마다 $\ge100$)이 4개 recording에서 실패(`214/42/33`, `372/107/48`, `23/8/0`, `555/53/159`)해 endpoint를 열지 못했다. 원장의 successor rule은 "물리시간 causal masked PSD 공분산 + 유효표본수 기권 규칙을 source-lock하고, 합성 검사를 먼저 통과한 뒤, 신경 lock을 재감사하라"였다 — **BA-SRM8~12가 정확히 그 합성 검사 사슬이었고 14/14로 확증되었다.**

시험 질문(단일, 행동 봉인): **[산출 후보]** SRM12 확증 장치를 anchor 적격성 연산으로 교체하면, SRM7과 같은 데이터·같은 split·같은 최소 100 anchor 규칙 아래에서 22개 recording 전부의 신경 입력 lock이 통과하는가.

이 판본은 behavior 값·모델·score를 열지 않는다 (`behavior_values_scored=false`). 통과해도 "입력 계약 성립"까지다.

## 2. 단일 구조 변경 (결과 확인 전 고정)

SRM7 `input_audit.py`(동결 SHA `a5bd9961c867d8f4707a41649cc865558f7570626abf7feb6186911b41f40b27`)에서 **anchor 적격성 연산 하나만** 교체한다:

- (구) 엄격 $W{=}60$ 연속 창 — 창 안 모든 gap $\le$ `GAP_FACTOR`·중앙값, 창 밖 제외구간 무접촉 — 를 만족하는 anchor만 유효.
- (신) SRM12 확증 장치의 물리시간 causal 공분산: 운반 후보 **`POWER_theta2_p1p5__gamma2__radial_huber_c3`** (SRM8 manifest 동결 정의; kernel $(1+u/2)^{-1.5}$, quality 지수 $\gamma=2$, radial huber $c=3$) 로 `funnel_core_v2.causal_q`를 실행하고, **해당 anchor에서 공분산이 유효한($n_{\rm eff}\ge8$, $n_+\ge2$, 유한) 경우** 유효 anchor로 센다. 입력 $z$는 SRM10 확증 robust 표준화(prefix median/$1.4826\cdot$MAD + clip $\pm4$, 결측은 mask 0)로 만든다.

후보 선택은 SRM8부터 동결된 funnel 랭킹 규칙(E 오름차순 → R 내림차순 → ISO FAR → runtime → ID)을 SRM12 영수증에 적용한 결정론적 결과다(E·R·FAR 1위 동률 2건은 runtime 항으로 해소; 동률 상대는 `…gamma2__identity`).

**변경하지 않는 것**: 데이터 byte-lock 3종과 22 recording split(SRM7 §8), 공식 cut·manual exclusion, photobleach·red→green regression·causal convolution·prefix 규율(§6), split 60/20/20 경계·EMBARGO·GUARD, fixed-$d$ eigengap 규칙(단, 고유값은 신 연산의 공분산에서 취함), **split별 최소 100 feature-common anchor 문턱**, staged lock 순서(신경 lock 후에만 behavior schema, 값은 봉인).

## 3. falsifier와 결과 코드

- 22개 recording 전부 통과 → `NEURAL_INPUT_LOCK_PASS_V2` — 2단계(행동 endpoint, SRM7 §10 문면 그대로) 계약 개설 자격. 이 판정 자체는 생물학적 결과가 아니다.
- 하나라도 split $<100$ anchor → `SOURCE_ROOTED_INPUT_STOP_V2` — recording별 정확한 counts를 잠그고, threshold·split·recording 변경 없이 닫는다. SRM7의 실패 4 recording과의 count 비교를 음성대조표로 남긴다.
- 100 문턱·gap·EMBARGO·후보·clip·MAD 상수를 결과 확인 후 바꾸면 즉시 STOP.
- `CLAIM_CEILING`: 입력 감사 지위만. `BIO_EVIDENCE_L1` 이상 주장 금지, 의식·기억·AGI 금지.

## 4. 실행·검증 계획

FAST: SRM7 감사기의 신경 파이프라인을 바이트 승계(읽기 전용 import 또는 최소 복제)하고, 교체 연산의 focused 검사(합성 불규칙 clock에서 구 규칙 대비 anchor 수 증가 방향성, ESS 기권 발동) 1회 + 본 감사 1회. 임시 산출은 스크래치패드, lock 영수증 요약·SHA만 §5에 기입.

## 5. 결과 (2026-08-30 실행, 동결 규칙 그대로)

**판정: `SOURCE_ROOTED_INPUT_STOP_V2`.** 22개 recording 중 21개가 전 split $\ge100$ anchor를 통과했으나, `BrainScanner20200310_141211`(gcamp, outer-validation)의 **test split이 66** ($<100$; train 281, validation 109는 통과)으로 동결 문턱에 미달했다. 계약 §3에 따라 threshold·split·recording 변경 없이 닫는다.

- archive 3종 byte-lock PASS, schema 22/22 PASS, unit eligibility 22/22 PASS, robust-scale 제외 unit 0개 (전 recording).
- focused preflight PASS: 합성 40$\tau$ 갭 dead zone(60 anchor)에서 구 엄격 창 규칙 0개 대 신 연산 36개 유효, ESS 기권 106회 발동.
- 음성대조 (SRM7 대비): SRM7의 실패 4개 recording 중 3개가 이번에 통과로 전환됐다 — `20200130_105254` `214/42/33`→`403/120/123`(smoke에서 424/113/125로 재현 확인, 본 실행 수치가 정본), `20200309_151024` 계열 등 전 train recording이 수백 anchor대로 회복. 유일한 잔존 실패 `20200310_141211`도 test split $48\to66$으로 개선됐으나 문턱 미달. anchor 부족의 원인은 이 recording의 manual exclusion 2구간과 후반부 결측 밀도다.
- 행동 봉인 유지: `behavior_loaded=false`, `behavior_values_scored=false`, endpoint 미개봉.
- 증거: lock 영수증 SHA-256 `490bed3044bc74ffc475e5455a8372ca319c0cd18f4107bcc239cc551678752b`, 감사기 스크래치패드 `ba_srm13_input_audit.py` (SRM7 감사기 `a5bd9961…` 바이트 승계 + §2 단일 교체).

### 5.1 관찰과 후속 재개 조건 (outcome-informed 명기)

**구조적 관찰**: 미달한 split은 endpoint가 소비하지 않는 구간이다. SRM7 §8의 endpoint 설계상 outer-train recording은 first-60% anchor만, outer-validation recording은 middle-20%만, outer-held-out recording은 last-20%만 모델 적합·선택·채점에 쓴다. `20200310_141211`은 outer-validation이므로 endpoint가 읽는 것은 validation split(109, 통과)뿐이고, 실패한 test split(66)은 어떤 단계에서도 소비되지 않는다. 즉 "모든 recording의 모든 split $\ge100$" 규칙은 endpoint의 실제 소비보다 엄격한 over-coverage였다.

**후속 규칙**: BA-SRM14는 anchor 충분성 규칙을 SRM7 §8의 소비 구조에서 재유도할 수 있다 — outer 역할별로 endpoint가 실제 소비하는 split만 $\ge100$을 요구. 이 재유도는 본 판본의 counts를 본 뒤 제안되므로 **outcome-informed 개발 판본**이며, 근거는 관측 수치가 아니라 SRM7 §8 문면임을 계약에 명기해야 한다. 실데이터는 고정되어 합성 판본과 달리 새 seed 검증이 불가능하므로, SRM14 통과 시에도 그 지위는 "입력 계약 성립(개발)"이고 과학적 결과는 여전히 봉인된 행동 endpoint의 몫이다. 행동값은 SRM14에서도 신경 lock 통과 전 읽지 않는다.
