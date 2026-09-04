# 20260902 brain — 리만접힘 카드 attempt (Q-NPF-01, attempt 1)

## 표적 연결
진전 원장 §2 표적 문장 (1)(2)(3) ↔ Q-NPF-01. 이번 세션이 닫을 고리: F-01 카드 adopt|refute.

## 부트스트랩 (이 세션)
- `ledger/`·`derivations/`·`verify/`·`scripts/`·`paper/진전_원장.md`가 작업 트리에 없었다. `ledger.py add-question`으로 Q-NPF-01 등록, next-question → active, bump-attempt → 1.
- `.codex/hooks/goal_reminder.py` 부재 → §2 주입 훅 침묵. 미수정.

## 환경 실측
- cargo 1.95.0 / rustc 1.95.0, sympy 1.14.0, numpy 2.4.6, scipy 1.17.1. WDAC가 로컬 빌드 unsigned exe 실행을 차단(Loewenstein 계보 기록).
- 저장소 보유 생물자료: `data/external/ottenheimer_2023_figshare_21365598` (3.7GB ZIP + 저자 코드), Stx3(차단), DANDI 000004·001176·001075·001612 등. Loewenstein CSV는 저장소에 없음(live host hash만).

## 진행
- [x] prover(추측) F-01 — card-check PASS, 훅 symbolic·numeric pass, 수정 0회. 식: tr E_fold(u) = −Δτ ∂_u log V_g^pre(u) + O(Δτ²). 예측 β1=1.00±0.30, κ≥0.50, placebo β1=0.00±0.30. kill 4, 사다리 6단(6단 = Ottenheimer 2023 예측시험). 자유 파라미터 1 < 예측 3
- [x] adversary 카드 감사 6종 — status `refute 권고`. P0 2건: (a) 동결 추정기(h=0.30 s 중심차분)가 순수 지연 무잡음 세계에서 β1=1.07–1.49를 내어 참인 카드를 P=0.54로 오기각(β1=1.00은 log V_g가 창 안에서 2차 이하일 때만 정확), (b) placebo kill 2가 정확히 Cauchy(0/0)라 참인 카드를 P=0.29–0.98로 파괴. P1 9건(1단 chart 불변 거짓, 3단 강체 이동 거짓, κ 무판별, kill 3은 Finsler 판별 아님, gate 6/8 vs sign 7/8 불일치, Var(T) 하한 없음, raw rank/λ_min 규칙 없음, 빠진 단 6개, 순수 지연 가정이 formula에 부재). 살아남는 것: 보조정리(u-무관 chart+강체 이동 ⇒ tr E = −Δτ ∂_u log V + O(Δτ²)), 2차 이하면 β1=1 정확, gain-only 기울기 0. 산출물 verify/Q-NPF-01/F-01/adversary/ 9 스크립트
- [x] sourcer 신규성 — identical·special_case 없음(3건 모두 unrelated, 참조는 UNVERIFIED). 1단 Jacobi 공식 인용 후보: Magnus & Neudecker 1999 / Amari 2016
- [x] judge — `refute`, L2, E-20260902-001 (`ledger/entries/20260902-001-npf01-f01-refute.yaml`), validate PASS, check-current 0. pivot/conjecture 제안은 "카드 attempt 분기표에 pivot 없음·사다리 미개설"로 거부
- [x] after-attempt Q-NPF-01 1 → parked (하네스 전이). 진전 원장 §2·§4·§5·§7 갱신
- [x] 계보 질문 Q-NPF-02 등록(origin E-20260902-001, conjecture, priority 1) → active. bump-attempt는 judge 직전에(Stop 훅 함정 회피)

## attempt 2 (Q-NPF-02 / F-01, 같은 세션 재추측)
- [x] prover(추측) Q-NPF-02/F-01 — card-check PASS, 훅 symbolic·numeric pass. 추측을 formula에 직접: ĝ_post(u)=e^{2γ}g_pre(u−δ(u)), δ(u)=k_x(a·u_pk+b·u), 예측 (a,b)=(0,1) — 계량장이 평균반응 anchored warp율 k_x를 계수 1로 따름. 예측 3(b1=1.00±0.06, 방향-홀수 shear κ=0.00±0.15, 운동학 판별자 Λ_x median 0.10), kill 5(K1 진폭 CI, K2 리만성, K3 운동학 Λ_x≤−0.10 = F-01 강체지연과 갈리는 판별 사례, K4 placebo primary k_x 재사용, K5 계산), 사다리 6단. 추정기 SG(7,3)+반쪽분할+Gram 감쇠보정(편향 +0.06 명시), gate 7/8 + Var(u_adm)≥0.04 s² + raw λ_min≥0.02, ridge 금지. 합성: N=1000 참 세계 support 0.687/K1 오기각 0.130/STOP 0.103; **N=300이면 참 세계도 STOP_power 0.937** (실제 자료 크기 대비 검토 필요 → adversary에 지시)
- [x] adversary 카드 감사 6종 — `refute 권고`. P0 5: (1) 동결 파이프라인 g=J̄ᵀΣ⁻¹J̄(작동점 z̄(u)에서 평가)에서는 readout 고정·α=1이면 임의의 계량장 4개가 모두 b1≈1(0.973–1.103)을 냄 → b1=1은 계량 예측이 아니라 항등식; (2) 반응 진폭 α≠1이면 b1이 −7.26…+5.71로 흩어짐(미선언 동질성 가정 G(αz)=e^{2γ}G(z)); (3) D7 계약의 N=60 trial/phase에서 카드 자신의 규칙이 참 세계에서도 STOP_power=1.000(N≈1000 필요, 17배) → 명명 자료에서 판정 불가; (4) 카드 식 (a,b)=(0,1) vs (a,0)을 가르는 Ψ는 계산되지만 predicts·kill에 없음(참 세계 95% [−14.7,+17.7]); (5) K1은 강체지연 세계에서 b1≈1.03–1.12(발동 9–12%), K3은 cue-고정 재귀회로에서 F-01 기전이 Λ_x=+0.35/+0.76(예측 −0.35/−0.87 아님). P1 15(K2는 리만성 시험 아님—ĝ 구성상 대칭, Λ_x 예측 비정합, ±0.06 미사용, S_FLOOR 미선언 문턱, λ_min 비불변, recovers 1·3 공허 등), P2 3. 살아남는 것: 1차 전개 보조정리(Jacobi+chain rule = pullback Fisher의 재매개화 공변성), trace-free gain 소거, Gram 퇴화 정지, placebo k_x 재사용 수리. 산출물 verify/Q-NPF-02/F-01/adversary/ a1–a6
- [x] sourcer 신규성(재판정) — Wang 2018 `generalizes`, Williams 2020 `generalizes`; Arsigny 2006은 prior_art에서 빼고 cited_steps(1단)로. 재발견 없음
- **구조적 발견(카드가 아니라 표적 자체에 대한 것):** (i) 저장소 보유 생물자료 Ottenheimer 2023의 trial 예산(60/phase)이 모든 계량 수준 endpoint의 결정 제약 — 어떤 카드든 통계량 선택 전에 N·검정력을 먼저 적어야 함; (ii) 평균반응에서 만든 g로는 "계량이 반응 warp를 따른다"가 readout 고정 시 동어반복, readout 변화 시 일반적으로 거짓 → 집단 활동만으로는 계량 접힘이 평균반응 운동학과 분리되지 않음(21장 §8.3 비식별과 일치); (iii) 재귀회로의 실제 전도지연 변화는 강체 이동도 anchored 팽창도 아님 → 두 카드의 운동학 signature 모두 CE 지연 기전을 시험하지 못함
- [x] bump-attempt Q-NPF-02 → 1; judge `refute`, L2, E-20260902-002 (`ledger/entries/20260902-002-npf02-f01-refute.yaml`), validate PASS, check-current 0
- [x] after-attempt Q-NPF-02 1 → parked. 진전 원장 §2(생물 자료 기준 현재 결론 + 사용자 택일 a/b/c)·§4·§5·§6·§7 갱신
- [x] links: 런처에 모드 없음(위 주차장) → 미실행
- 세션 종료 상태: active 질문 없음, 3번째 카드 금지, 사용자 결정 대기

## 주차장
- (21.54w)–(21.54aa) 수치 witness 부재 → 별도 질문 후보.
- (prover) A1 내부(early→late)보다 A1→A2 세션간 Δτ가 클 수 있어 β1 추정력이 더 높을 가능성 — secondary 보고로만, 이번 카드 predicts에는 넣지 않음.
- goal_reminder.py 복원은 하네스 작업(범위 밖).
- `.claude/hooks/python.cmd links`가 "Unknown mode 'links'"로 실패(현재 `.codex/hooks/python_harness.py`는 doctor·python·pytest만). CLAUDE.md의 `links [--strict]`·`harness`·`source`·`lint` 명령은 이 런처와 불일치 — 하네스 결함, 이 세션에서 고치지 않음.

## 하네스 (사용자 지시, 세션 중간)
- 계기: 카드 감사 서브에이전트가 제공자 안전장치(`reasoning_extraction`)로 조기 종료 → 보내기 전에 저장소에서 막는다.
- 추가: `.claude/hooks/safety-screen.cmd` + `lib/safety_screen.py` + `tests/test_safety_screen.py`(21 passed), settings.json PreToolUse 첫 항목(matcher `Agent|Task|Write|Edit|MultiEdit|Bash`).
- 차단 2범주(우회 없음): 표적 밖 생물학적 위험(능력 상향·에어로졸·무기화·합성 경로·생물보안 우회), 모델 내부 추출(사고과정·추론 흔적·시스템 프롬프트를 그대로 내놓으라는 요구). 경고 1: Agent 프롬프트 12000자 초과 → 긴 근거는 `verify/` 경로로.
- 예외: Write/Edit로 훅 자신의 정의 파일과 시험 파일을 고칠 때만(자기잠금 방지). Agent·Bash에는 예외 없음.
- 실측: cmd 래퍼가 차단 payload에 exit 2 + 메시지, clean payload에 exit 0. 단 Claude Code는 세션 시작 시 훅을 읽으므로 **이 세션에서는 아직 비활성**, 다음 세션부터 적용.
- 부작용: 이 세션의 auto 모드 분류기가 차단 문구를 담은 Bash 명령 자체를 거부한다. 훅 시험 자료는 예외 경로(Write/Edit)로만 고칠 수 있다.

## attempt 3 (Q-NPF-03, 사용자 "최선으로 전부 진행")
- 질문 등록: Q-NPF-03(origin E-20260902-002, conjecture, priority 1) → active, attempt 0.
- 세 갈래 동시: (1) 비동어반복 카드(반응 진폭 α에 대한 계량 응답, N=60에서 판정 가능해야), (2) 저장소 보유 자료 재고조사(다운로드 없음), (3) 후보 공개자료 메타데이터 조사(payload 없음).

### (3) 후보 공개자료 메타데이터 조사 결과 (sourcer, 다운로드 없음)
- 저장소가 이미 다룬 자료 외에서 네 조건(동일세포 종단 · phase당 ~1000 trial · 별도 행동 endpoint · 동기 clock/holdout)을 **메타데이터만으로 모두 만족한다고 확인된 자료는 없다.**
- Allen Visual Behavior 2P: 동일세포 종단 추적 명시(FOV당 3–11 세션), 행동 endpoint 완비(go/no-go change detection, lick·reward·running). 82–107 mice, 551–703 세션, 34,619–50,476 뉴런. **phase당 trial 수 UNVERIFIED**(시간 기반 세션), 학습 전/후 설계 증거 미확인. 최소 탐색 sample: 세션 1개 메타데이터 + NWB 헤더 약 2–5MB. 라이선스 open, AllenSDK 직접 접근.
- IBL Brain-Wide Map 2025: 459 세션·139 subject·12 lab, 621,733 raw unit(75,708 curated), CC-BY 4.0, AWS S3. 다중 동물 holdout 가능. **동일세포 세션 간 동일성 미문서화, trial 수 UNVERIFIED, 학습이 주 조작 아님**(일회성 의사결정 과제). 최소 sample 5–20MB.
- DANDI 일반 수집: 네 조건을 만족하는 특정 데이터셋을 메타데이터 검색으로 찾지 못함. MICrONS는 trial 기반 행동이 없음.
- 판정: 두 후보 모두 **최소 탐색 sample 없이는 trial 수 조건을 판정 불가**. 추가 확인 요청 보냄(Allen VB 2P의 session당 trial 수·novel/familiar 구조·세포 동일성 필드, Allen VB Neuropixels 판본).
- 추가 확인 결과: Allen VB 2P는 학습이 imaging 전 3021 훈련세션에서 끝나므로 familiar/novel은 학습 전후가 아님(요건 1 불충족). trial 수는 NWB trial table 없이는 UNVERIFIED. 탐색 sample 약 500MB(100MB 규칙 초과, 승인 필요). VB Neuropixels는 세션 간 unit 동일성 미문서화.

### (2) 보유 자료 재고조사 결과 (다운로드 없음)
- 36개 디렉터리 약 93GB, 계량 endpoint 적격 자료 없음. 정본 표 `verify/Q-NPF-03/local_data_inventory.md`.
- 가장 가까운 후보 Hattori 2023 OFC: trial 충분(220/세션 x 40-85세션), choice/reward 행동, 그러나 공개 npz에 세션 간 세포 등록 키 없음, 로컬 imaging npz 1개, imaging/개입 마우스 disjoint.
- 차선 Ottenheimer 2023: 등록·행동·clock 충족, trial 60/phase만(필요량의 약 1/17).
- 정리 문서: `verify/Q-NPF-03/data_sufficiency.md`(요건 4, 보유/외부 표, 승인 요청 A/B/C).

## 하네스 2 (사용자 지시: 생물학 부분만 전부 opus)
- `agents/bio-reader.md` 신설(model opus, 생물 자료·문헌 읽기 전담, ledger/paper 쓰기 금지, 산출물은 verify/ 아래). 에이전트 5종 → 6종.
- `safety_screen.py`에 `bio_routing` 범주 추가: Agent·Task 프롬프트에 생물 표지(도메인어 + 이 저장소가 쓰는 자료명)가 있으면 `model=opus` 또는 `subagent_type=bio-reader`가 아닌 한 exit 2. Write·Edit·Bash에는 적용 안 함.
- 기존 시험 계약 변경: "도메인 표현은 통과"를 "opus 라우팅을 만족시킨 뒤 위험·내부추출 범주에 안 걸린다"로 갱신. 39 passed.
- 실측: 생물 프롬프트에 model 없음 → exit 2 + 사유, opus → 0, bio-reader → 0, 수학 전용 → 0.
- 이 규칙 적용 후 Q-NPF-03 감사·신규성 두 호출을 모두 opus로 재실행(이전 것은 사용자 인터럽트로 종료).

### attempt 3 진행 (Q-NPF-03/F-01)
- [x] prover 카드 — card-check PASS, symbolic 7/7·numeric 15/15+5/5. 축약계량 Phi = I/m^2 = CV^-2 + p^2/2, gain 응답 지수 R=(2-p)(1-rho), 대비식 dlogPhi = 2L + Lambda(R-2)L, 예측 Lambda=1.00±0.24, Gamma=2-R=1.46±0.50, 자유 파라미터 0, kill 5, 사다리 7단. 동어반복 세계 지지율 0.006(Lambda 중앙 -0.017), 참 세계 N=60 검정력 0.911·오기각 0.089, W_hist kill 0.994. 산출물 verify/Q-NPF-03/F-01/.
- [x] sourcer(opus) 신규성 — 카드 전체 identical/special_case 없음. generalizes 3(Abbott & Dayan 1999: 2항 Fisher·p=2 극한, Goris 2014: 멱법칙 인스턴스, Ma 2006/Poisson Fisher: p=1 극한), unrelated 4(Churchland 2010은 반증원, Kanitscheider 2015·Moreno-Bote 2014·Gu 2011/Ni 2018은 다른 estimand). **1단은 identical → ladder_cited(Abbott & Dayan 1999)**. 신규성은 p 전 구간 보간 + (1-rho) 인자 + 종단 Lambda에 걸림(CV^-2 단독은 d'^2 재서술). 서지 오류: Kanitscheider 2015 'PNAS' 표기는 PLoS Comput Biol 11(6):e1004218과의 혼합(claim 변경 아님). 정리 번호는 UNVERIFIED(1차 출처 미열람).
- [x] adversary(opus) 감사 — `refute 권고`. P0 4: (1) **위약 붕괴** — 학습 없는 세계(late=early)에서 게이트 0.933·K2 지지 0.783·지지 0.683·Lam_hat 1.177·Gamma_hat 1.44, K1은 0.133만 발동. 원인은 bin 선택이 pooled |L|이라 반쪽교차 IV 외생성이 깨지고 표본 요동이 참 과정과 같은 멱법칙 위에 놓여 Lam_hat->1; (2) recovers 넷째 극한 공허 — 전도속도 단독·효능 단독 모두 선택 bin 0개, 인용된 lam_true=0.988 전부가 내재 gain 채널; (3) 표적 치환 — estimand 미선언((21.41) 대 (21.41a))으로 Gamma 1.06 대 1.46, m^2 나눗셈이 궤적 속도(=접힘) 삭제; (4) 명명 자료 판정 불가 — dF/F 기저차감 시 480/480 폐기, 영점 이동으로 Gamma 0.948~2.577. P1 6·P2 2. 산출물 verify/Q-NPF-03/F-01/adversary/ a1~a9 + audit_report.json
- [x] judge — `refute`, L2, E-20260903-001, validate PASS, check-current 0, ladder_cited 1단(Abbott & Dayan 1999)
- [x] after-attempt Q-NPF-03 1 -> parked. 진전 원장 §2·§4·§5·§7 갱신
- **살아남은 것(별도 질문으로만)**: 보조정리 dlogPhi/dlogmu=(2-p)(1-rho)+2rho q(L1); 경험 명제 "학습 전후 변동-평균 멱지수 불변"(Lam=1 <=> p_cross=p, IV 편의 <=0.10으로 실측 가능). 확정 수리: bin 선택을 독립 분할 L로 -> 위약 지지 0.783->0.017, 참 세계 0.950->0.917

## 하네스 3 (2026-09-03, 사용자 지시 두 번)
- "생물학 버전/아닌 버전 분류, 생물은 opus 전담": `domain-classifier`(opus) 0단계 + 생물 전담 5종(`prover-bio`·`adversary-bio`·`judge-bio`·`sourcer-bio`·`paper-writer-bio`, 전부 opus). 훅 `classify_first`(영수증 없는 연구 역할 호출 차단, bio 도메인의 비-생물 역할 차단). 생물 전용 규칙 8개를 `verify/Q-NPF-04/spec.md`와 카드에 명문화.
- "메인은 Fable로 두라": 첫 판본의 프롬프트 차단(`/model opus` 요구)을 철회하고 **위임 지시**로 교체. `model-gate`는 항상 exit 0, 생물 프롬프트에 메인이 opus가 아니면 "원문 읽지 말고 전담에 위임"을 문맥 맨 앞에 넣는다.
- 테스트: `test_safety_screen.py` 70 + `test_model_gate.py` 18 = 88 passed. ACCEPTANCE §9.3 갱신은 auto 모드 분류기가 편집을 막아 미반영(문구가 첫 판본 그대로) — 다음 세션에서 고칠 것.
- 라우팅 영수증: `verify/_routing/870ccf52-e14f-4026-af42-39b8f4c7184a.json`, domain=bio, confidence high. 분류기 단서: 라우팅 단위(세션)와 증거등급 단위(주장)는 다르다 — 합성 검증은 생물 자료 개봉 전까지 `BIO_EVIDENCE_L0` 사전조건일 뿐.

## attempt 4 (Q-NPF-04, 사용자 "식 더 정교하게 만들어서 실행")
- 사용자 명시 허가로 4번째 카드 진행(진전 원장 §4에 기록). 명세 `verify/Q-NPF-04/spec.md`: P1 estimand 선언, P2 관측량·영점, P3 채널 식별 인증서(효능·지연·gain 단독), P4 phase 내 위약 1급, P5 선택·대비 분할 독립, P6 N·검정력 선등록, P7 모든 상수 카드 이관, P8 유한 대비 선형화. P3/P6 실패 시 카드 없이 실패 보고.
- prover-bio 1차 실행은 인터럽트로 종료(산출물 없음). 2차 실행은 forward model `fwd.py`와 채널 CRB 인증서까지 만들고 중단됨 — 중간 결과: 단일세포 통계량은 지연 채널 z≈0.12(CRB 하한에서도 식별 불가), gain–효능 post-fit 상관 −0.91. 자료 N=60·세포 17–63 기준.
- **사용자 아이디어(2026-09-04): 계량이 아니라 크리스토펠·측지선, 뉴런별 실측.** 명세 §"우선 후보"에 반영. 구조적 근거: 계량은 점의 내적이라 요약이 평균반응 재서술로 흐르지만 접속은 이동 시 방향 변화이고, 계량(출력 우도)과 궤적(활동)이 독립 축약이라 동어반복을 피함. 측지선 잔차 R = z̈ + Γ ż ż − F, 예측 계수 1, 귀무 평탄 접속, 뉴런별 잔차 투영 r_i.
- 출력 계약 변경(플래그 원인 제거): 전담 에이전트는 전체 보고를 파일에 쓰고 메인에는 {artifact, verdict, numbers, next}만 반환. 3차 실행(접속·측지선 후보) 진행 중, 보고 파일 `verify/Q-NPF-04/F-01/prover_card_report.json`.

## 세션 종결 상태 (2026-09-03)
- 카드 3장 연속 refute(E-20260902-001/002, E-20260903-001). active 질문 없음, 4번째 카드 금지.
- 누적 결론: 집단 활동만으로 만든 통계량은 (위약과 분리) 또는 (표적 기전에 민감) 둘 중 하나만 가능. 21장 §8.3 비식별과 일치.
- 사용자 결정 대기: `verify/Q-NPF-03/data_sufficiency.md`의 A(Allen VB 2P 약 500MB 탐색 표본, 100MB 규칙 초과) / B(Hattori 2023 등록 키 판본 문의) / C(endpoint 격하) 또는 표적 재정의.
