<!-- 도메인: ce-brain-bio -->

# BA-SRM10 연구 계약 — ART10 강건성 실패의 구조적 진단과 bounded-influence 측정 판본

Status: `RESULT_RECORDED / R-A_SURVIVED` (계약 동결 2026-08-30, 결과 기입 2026-08-30)

계보: BA-SRM6 (`INPUT_CONTRACT_STOP`) → BA-SRM7 (`SOURCE_ROOTED_INPUT_STOP`) → BA-SRM8 (`SYNTHETIC_DGP_STOP`) → BA-SRM9 (`SYNTHETIC_F2C_FUTILITY_STOP`) → **BA-SRM10 (이 계약)**.

정본 규약: `.codex/harnesses/real_brain_equation_discovery_loop.md`, `.codex/harnesses/brain_evidence_ladder.md`. 저장 정책상 새 `CE_RUN`·`_workspace/`를 만들지 않으며 이 계약·결과·영수증은 `paper/` 정본과 코드·테스트에 직접 남긴다.

## 0. 경로 선정 근거 (착수 전 기록)

2026-08-30 기준 route ledger(`_workspace/ce/brain-algorithm-route-ledger.md`, 읽기 전용)의 열린 후보와 비교:

| 후보 | 상태 | 기각/보류 사유 |
|---|---|---|
| BA-STAGE3-CCEP-NEXT (Stage 4 해부학 다리) | `STAGE4_UNAUTHORIZED` | 독립 해부학 그래프의 외부 소싱·계약 동결이 선행 조건. 재개 조건 유지, 이번 세션 범위 밖 |
| BA-LCMF 후속 | R0–R3 STOP, 001695 봉인 | 구조적으로 다른 source-locked 계약 필요. 001701 기반 rescue 금지 준수 |
| BA-EMP-IBL | `OPEN_INPUT` | 공식 cache 입력 미확보 |
| BA-CG1 | `OPEN` (합성 전이 과제) | 하네스 §6 우선순위 4 (실데이터 경로 뒤) |
| **BA-SRM9 후속** | `FUTILITY_STOP` + 정확한 후속 규칙 | **선택.** 로컬 실데이터(eLife 66135, SHA 검증) 존재, 이론측 브리지(edge-metric→$d_{\rm eff}$, 2026-08-26 두 run COMPLETE)가 실데이터 endpoint를 대기 중, 이전 STOP이 남긴 정보가 가장 구체적 |

선정 기준(사다리 승급 가능성 · 인과 식별 가능성 · 이전 STOP 정보 · 독립 falsifier · capability dependency) 중 capability dependency와 STOP 정보에서 SRM 계보가 유일하게 즉시 실행 가능하다.

BA-SRM9의 후속 규칙(원장 인용): *"A successor must first source-lock a distinct hypothesis explaining the ART10 failure and its adverse controls, then restart at the appropriate synthetic gate under a new contract."* 이 계약이 그 source-lock이다.

## 1. 질문과 판본 경계

BA-SRM9의 F2-C에서 이월 후보 20개 전원이 ART10 시나리오의 중앙 Spearman $\rho$ 게이트($\ge 0.80$)에 미달했다(관측 범위 $0.6137$–$0.7405$). ART10은 ROT10에 1% 표본 성분에 $\pm 10\,\hat\sigma_{\rm pop}$ 스파이크를 더하는 오염 시나리오다(주입 순서: clean → Gaussian noise → artifact → mask, SRM9 `f2-config.json` 동결).

시험 질문(단일): **[산출 후보]** 오염 관측에서 $Q(t)$ 순위 붕괴의 원인이 모멘트 기반 표준화·비유계 영향함수(관측 이차형식의 오염 민감도)인가 — 즉 bounded-influence 표준화로 교체하면 다른 모든 동결 게이트를 유지한 채 ART10 중앙 $\rho\ge0.80$이 회복되는가.

의식·해마·synaptic edge·인간·AGI·생물학적 리만 계량은 이 판본의 시험 대상이 아니다. 이 판본은 L0 (합성 장치) 계층에 있다.

## 2. 실패 진단 가설 (결과 개봉 전 고정)

표본 성분당 오염 확률 $p=0.01$, 진폭 $A=10\hat\sigma$일 때 오염이 더하는 분산은

$$
\Delta\sigma^2 \approx p\,A^2\hat\sigma^2 = 0.01\times100\,\hat\sigma^2 = 1.0\,\hat\sigma^2,
$$

즉 신호 단위분산과 같은 크기의 백색 분산 마루가 공분산 전 고유값에 더해진다. 두 기전이 순위를 무너뜨린다:

1. **마루 요동**: 창별 오염 개수가 Poisson 요동하므로 $\operatorname{tr}\,\widetilde G(\widetilde G+\lambda)^{-1}$에 신호 변화와 같은 자릿수의 시변 잡음이 더해진다.
2. **prefix 척도 오염**: prefix 표준편차 추정이 $\sqrt{1+\Delta\sigma^2/\sigma^2}\approx\sqrt2$배 부풀어 $z$ 전체가 계통적으로 압축되고, 그 압축률 자체가 prefix 내 오염 개수에 따라 채널별로 요동한다.

두 기전 모두 이차 모멘트 추정기의 비유계 영향함수($\mathrm{IF}\propto z^2$)에서 나온다. 따라서 교정 후보는 추정기의 영향 경계다.

## 3. 등록 경로 (구조가 서로 다른 3개, 사전 선택 1개)

| 경로 | 구조 변경 (seam) | 판별 예측 | kill condition |
|---|---|---|---|
| **R-A (선택)** | 표준화 연산자 교체: prefix mean/sd → prefix median/$1.4826\cdot\mathrm{MAD}$, 이후 $z\mapsto\operatorname{clip}(z,-4,4)$. truth·estimate 경로에 동일 적용. 다른 모든 단계·후보·게이트 불변 | ART10 잔여 오염 분산 $\le p\,c^2=0.16\,\hat\sigma^2$ (6배 감소) → 중앙 $\rho\ge0.80$ 회복. Gaussian 하 clip 왜곡 $P(|z|>4)\approx6\times10^{-5}$로 무시 가능 → 무오염 시나리오 게이트 유지 | ART10 중앙 $\rho<0.80$ 지속, 또는 JUMP 검출·ISO FAR·MISS30 게이트가 SRM9 동결 문턱을 벗어나면 kill |
| R-B | 측정 마스크 확장: prefix 교정 인과 진폭 규칙으로 오염 표본을 결측 처리 → 기존 ESS 기구가 흡수 | ART10 회복 + JUMP의 구조적 평균이동(수 $\sigma$)은 기각하지 않아야 함 | JUMP 검출 저하 시 kill (SELF1/2/3의 QC 전이 실패 계보를 승계하는 위험 명기) |
| R-C | 스펙트럼 범함수 교체: $\operatorname{tr}$ 기반 $d_{\rm eff}$ → 오염 둔감 분위수 기반 요약 | ART10 회복 | 측정 대상 자체가 바뀌므로 최후 순위. 무오염 시나리오와의 정합 붕괴 시 kill |

R-A를 결과 개봉 전에 선택한다(한 판본 한 구조 변경). R-A가 죽으면 그 실패를 음성대조로 잠근 뒤 R-B, R-C 순으로 새 판본을 연다.

## 4. 계약 필드

| 필드 | 내용 |
|---|---|
| `BIO_STARTING_MECHANISM` | BA-SRM8/9에서 승계 (합성 DGP: 물리시간 불규칙 클록, MCAR/블록 결측, 직교 센서 혼합, ROT/JUMP 상태 전이). 이 판본에서 변경 없음 |
| `CE_DELTA` | 없음 (장치 판본). CE 추가항은 실데이터 endpoint 개봉 이후 판본의 몫 |
| `MEASUREMENT_MODEL` | **단일 구조 변경**: §3 R-A의 robust 표준화 + $c=4$ clip. 그 외 SRM9 `f2-config.json`·`run_f2a.py`/`f2_common.py` 동결 사슬을 바이트 그대로 승계(읽기 전용 import) |
| `DATA_PROVENANCE` | 전량 합성 (SRM9 generator 동결 재사용). 실데이터 미개봉 |
| `DATA_SPLIT` | 신규 seed 블록만 사용: calibration `20262001..20262016`, 평가 패널 `20262101..20262108`. SRM9의 `2026xxxx` 기존 블록은 소진된 것으로 보고 재사용 금지 |
| `OBSERVABLES` | 후보별·시나리오별 truth 대 estimate $Q(t)$의 중앙 Spearman $\rho$와 NMAE; ISO FAR; JUMP 검출 수 |
| `RESIDUAL_RULE` | SRM9 F2 게이트 문면 그대로: 시나리오별 중앙 $\rho\ge0.80$, NMAE $\le0.20$; JUMP 중앙 $\rho\ge0.80$·NMAE $\le0.20$·FAR $\le0.20$·검출 $\ge4/8$; ZERO는 expected abstain |
| `FALSIFIER` | (a) ART10 회복 실패 → R-A kill. (b) 무오염 시나리오(ISO/JUMP/MISS30/BLOCK30) 중 하나라도 SRM9 문턱 대비 퇴행 → R-A kill. (c) clip 문턱 $c$·robust 상수·seed를 결과 확인 후 변경 → 즉시 STOP |
| `MATCHED_CONTROLS` | 동일 seed·동일 후보에서 (i) 무변경 SRM9 표준화(음성대조: ART10 실패 재현 확인), (ii) clip 없는 robust 표준화(성분 분해: 척도 교정만의 기여) |
| `MODEL_SELECTION` | 후보 선택 없음 — SRM9 이월 후보 20개 전원을 동결 정의 그대로 평가. 후보별 재조정 금지 |
| `REVISION_TRIGGER` | R-A 통과 시: 다음 판본에서 같은 robust 장치로 F2-C 이후 단계(F2-D→confirm) 재개 자격. R-A kill 시: R-B 새 계약 |
| `CLAIM_CEILING` | `BIO_EVIDENCE_L0`. 통과해도 "합성 오염 하 장치 순위 안정성"까지만. 생물학·의식·기억·AGI 주장 금지 |

## 5. 실행·검증 계획

1. 구현은 세션 스크래치패드에서 SRM9 artifacts를 읽기 전용 import하여 수행하고, 생존 시 재현 러너·테스트만 저장소 코드로 옮긴다.
2. 검증 등급 FAST: robust 표준화의 focused 단위검사(무오염 Gaussian에서 moment 표준화와의 일치, clip 영향 경계) 1회 + 본 평가 1회.
3. 결과(통과·kill 불문)는 이 문서의 §6에 제자리 추가하고, route ledger 반영은 ce-ledger-write 레인으로 넘긴다.

## 6. 결과 (2026-08-30 실행, 동결 seed·게이트 그대로)

**판정: R-A 생존.** ART10 순위 붕괴의 원인이 이차 모멘트 추정기의 비유계 영향함수라는 §2 가설이 지지되었다.

focused preflight (계약 §5-2): 무오염 Gaussian에서 robust 대 moment 표준화 중앙 절대차 $0.00962$, clip 비율 $0$, +10σ 오염 20표본 하 척도 이동 $0.0067$ — 전부 사전 경계 안, PASS.

| 변형 | PASS / KILL / ABSTAIN | ART10 중앙 $\rho$ 범위 (후보 20) | 해석 |
|---|---|---|---|
| V0 무변경 (음성대조) | 0 / 20 / 0 | $[0.6130,\,0.7291]$ | SRM9의 ART10 실패($[0.6137,0.7405]$)를 **새 seed 블록에서 재현** — 유효한 음성대조 |
| V1 robust 표준화만 (clip 없음) | 0 / 20 / 0 | $[0.6186,\,0.8302]$ | 척도 교정(§2 기전 2)만으로 불충분 — 지배 기전은 마루 요동(§2 기전 1) |
| **V2 R-A (robust + clip ±4)** | **14 / 6 / 0** | $[0.9243,\,0.9746]$ | **후보 20/20이 ART10 게이트($\rho\ge0.80$, NMAE$\le0.20$) 통과** |

무오염 게이트 유지 (falsifier (b) 판정):

- BLOCK30: V2 중앙 $\rho$ 범위 $[0.9425, 0.9754]$, 전 후보 통과. ISO 평균 FAR 범위 $[0.0500, 0.0567]\le0.20$, 전 후보 통과.
- V2의 kill 6건은 전부 JUMP 검출 게이트($\ge4/8$) 미달이며, **같은 6개 후보가 V0에서도 같은 seed에서 같은 게이트를 실패**했다(전부 quality exponent $\gamma=2$ 계열: EXP_theta10 3종 검출 3→3, BIEXP 3종 검출 3→2). 게이트 지위의 퇴행이 없으므로 falsifier (b)는 발동하지 않는다. BIEXP 3종의 원시 검출수 3→2 감소는 관찰로 남긴다(이 후보들은 기준선에서도 이미 게이트 미달).
- ZERO_NULL은 세 변형 모두 8/8 expected abstain (robust 경로는 MAD 소멸로 fail-closed).

증거·재현: 러너 `examples/brain/ba_srm10_ra_runner.py`(스크래치패드 원본 SHA-256 `d61a8828ab65de545955401fad11ec56243ee5cd36ee5cd8e93386e3d247fc18`), 영수증 SHA-256 `44e9594a3f5d795395f5110890e126ad36ffe260b09c8ecf7e5a56978e6d37a6`, 후보 manifest SHA-256 `58280bb9759549b9f285e95135b5320e44f1d317adf347a065319f367a3e6a0c`. 전 계산은 동결 seed에서 결정론적이므로 러너 재실행으로 영수증이 재생성된다.

지위: **[산출] `BIO_EVIDENCE_L0`** — "합성 오염 하 bounded-influence 표준화가 장치 순위 안정성을 회복한다"까지만. 생물학·의식·기억·AGI 주장 없음 (§4 `CLAIM_CEILING` 유지).

### 6.1 다음 의무 (REVISION_TRIGGER 발동)

1. R-A 통과에 따라 다음 판본은 같은 robust 장치로 F2-D→confirm 단계를 재개할 자격을 갖는다. V2 통과 14후보가 이월 대상이다(γ=2 계열 6후보는 JUMP 검출 미달로 이월 불가).
2. confirm 통과 시 SRM7 successor rule(물리시간 causal masked PSD + ESS 기권 + behavior-blind 주입)과 결합해 실데이터(*C. elegans*, eLife 66135 로컬 보존분) endpoint 재도전 계약을 연다.
3. `_workspace/ce/brain-algorithm-route-ledger.md`는 현행 정책상 읽기 전용이므로 BA-SRM10 정규화 행은 이 문서가 정본이다.
