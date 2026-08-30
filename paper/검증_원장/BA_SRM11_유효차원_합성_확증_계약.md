<!-- 도메인: ce-brain-bio -->

# BA-SRM11 연구 계약 — robust 장치의 F2-B/F2-D/합성 확증 완결

Status: `SYNTHETIC_FUNNEL_KILL / GATE_DEFECT_C_CLASSIFIED` (계약 동결 2026-08-30, 결과 기입 2026-08-30)

계보: BA-SRM8 → BA-SRM9 (`SYNTHETIC_F2C_FUTILITY_STOP`) → BA-SRM10 (`R-A_SURVIVED`, `paper/검증_원장/BA_SRM10_유효차원_강건성_계약.md`) → **BA-SRM11 (이 계약)**.

## 1. 질문과 판본 경계

BA-SRM10은 bounded-influence 표준화(R-A)가 ART10 강건성 실패를 교정함을 보였으나, SRM8 funnel의 F2-B 시나리오(ROT10·MISS30), F2-D(REVERSE), 그리고 합성 확증 단계는 아직 robust 장치로 평가되지 않았다. 이 판본은 **구조 변경 없이** (R-A 장치 그대로) 남은 합성 funnel 단계를 완결한다.

시험 질문(단일): **[산출 후보]** SRM10의 생존 장치가 SRM8이 동결한 나머지 funnel 게이트(F2-B, F2-D, confirm) 전체를 통과하는가. 통과 시 이 장치는 L0 합성 계층에서 확증된 것으로 기록되고, 실데이터 endpoint 계약(SRM7 successor rule)의 개설 자격이 생긴다.

구조 변경 0건: 후보·robust 상수·clip·게이트 문면·시나리오 정의를 전부 승계한다. 새 자유도는 seed 블록뿐이며 결과 확인 전에 아래에 동결한다.

## 2. 승계 항목 (동결)

| 항목 | 값 |
|---|---|
| 장치 | BA-SRM10 V2 (median/$1.4826\cdot$MAD 표준화 + $z$ clip $\pm4$), 구현 `examples/brain/ba_srm10_ra_runner.py`의 `robust_pair` |
| 후보 | SRM10 V2 전 게이트 통과 14개 (BIEXP_theta1_1_theta2_8_a_0p5 γ1 2종, POWER_theta2_p1p5 γ1/γ2 6종, POWER_theta8_p2 γ1/γ2 6종; 정렬 ID 목록 SHA-256 `b139c56b589b54730b88469bf261f76ae382e17f83d5b93dccb1bd0b43366df2`) |
| 시나리오 정의 | SRM8 `f2-config-v4.json` 문면 그대로 (ROT10, MISS30, REVERSE, ART10, BLOCK30, ISO_NULL, JUMP, ZERO_NULL; MISS50은 descriptive only로 이번에도 게이트 아님) |
| 게이트 문면 | F2-B: 시나리오별 중앙 $\rho\ge0.80$, NMAE $\le0.20$. F2-D: REVERSE $\rho\ge0.80$, NMAE $\le0.20$ 그리고 ISO 평균 FAR $\le0.20$. confirm: 모든 recovery 시나리오(ROT10·MISS30·BLOCK30·ART10·REVERSE·JUMP)에서 중앙 $\rho\ge0.90$, 5% 분위 $\rho\ge0.75$, 중앙 NMAE $\le0.15$; ISO 중앙 NMAE $\le0.15$, 평균 FAR $\le0.10$, 최대 FAR $\le0.20$; JUMP 검출 32/32 |
| 단계 진행 | 후보별 F2-B → F2-D → confirm 순. 앞 단계 kill이면 뒤 단계를 열지 않는다 |

## 3. 신규 seed 블록 (결과 확인 전 동결, 기존 블록 재사용 금지)

| 용도 | seed |
|---|---|
| ISO 교정 ($\theta$, 후보별 95% 분위) | `20262501..20262516` |
| F2-B 패널 (ROT10·MISS30) | `20262201..20262208` |
| F2-D 패널 (REVERSE·ISO FAR·ZERO abstain 점검) | `20262301..20262308` |
| confirm 패널 (7 시나리오 전부) | `20263001..20263032` |

SRM9의 `2026xxxx` 원 블록과 SRM10의 `202620xx`/`202621xx` 블록은 소진분으로 재사용하지 않는다.

## 4. falsifier와 결과 코드

- 후보 14개 전원이 confirm 이전 단계에서 죽으면 `SYNTHETIC_FUNNEL_KILL` — R-A 장치의 일반화 실패로 잠그고, 원인 분류(D→I→P→C→B→T) 후 구조적으로 다른 후속(R-B 마스크 확장 등)만 허용.
- 일부가 confirm까지 통과하면 `SYNTHETIC_CONFIRMED_L0` — 통과 후보 목록·수치를 동결하고 실데이터 endpoint 계약 개설 자격 부여. **이것은 L0 확증이며 생물학적 주장이 아니다.**
- seed·게이트·상수·후보를 결과 확인 후 바꾸면 즉시 STOP.
- ZERO_NULL은 전 단계에서 expected abstain이어야 한다 (위반 시 `INVALID_KILL`).

`CLAIM_CEILING`: `BIO_EVIDENCE_L0`. 의식·기억·해마·synaptic edge·인간·AGI 주장 금지.

## 5. 실행·검증 계획

FAST: SRM10 focused 테스트(4개, 기존 green)를 장치 불변의 근거로 승계하고, 이번 판본은 REVERSE/confirm 경로의 장치 smoke 1회 + 본 평가 1회만 실행한다. 결과는 §6에 제자리 기입한다.

## 6. 결과 (2026-08-30 실행, 동결 seed·게이트 그대로)

**판정: `SYNTHETIC_FUNNEL_KILL` — 후보 14/14 confirm 단계 kill.** 단, 실패 하위 게이트는 전 후보에서 **JUMP 검출 32/32 단 하나**였고, 원인 분류는 장치가 아니라 게이트 규약 결함(C)으로 확정되었다.

### 6.1 단계별 수치 (후보 14개 범위)

| 단계 | 게이트 | 결과 |
|---|---|---|
| F2-B | ROT10·MISS30 중앙 $\rho\ge0.80$, NMAE$\le0.20$ | **14/14 통과** (ROT10 중앙 $\rho$ $[0.9825,0.9910]$) |
| F2-D | REVERSE $\rho\ge0.80$·NMAE$\le0.20$, ISO FAR$\le0.20$ | **14/14 통과** (REVERSE 중앙 $\rho$ $[0.9776,0.9875]$) |
| confirm — 순위·오차 | 6개 recovery 시나리오 중앙 $\rho\ge0.90$, 5%분위 $\rho\ge0.75$, NMAE$\le0.15$ | **14/14 전 시나리오 통과** (최저 여유: ART10 중앙 $\rho$ $[0.9334,0.9562]$, BLOCK30 5%분위 $[0.8640,0.9555]$) |
| confirm — ISO | 중앙 NMAE$\le0.15$, 평균 FAR$\le0.10$, 최대 FAR$\le0.20$ | **14/14 통과** (평균 FAR $[0.0490,0.0521]$, 최대 $0.0776$) |
| confirm — JUMP 검출 | **32/32** | **0/14 통과** — 검출수 범위 $[15,21]/32$ |

### 6.2 원인 분류 (empirical calibration loop, D→I→P→C→B→T)

최소 재현 대조 진단(게이트·seed 무변경): 같은 confirm seed·같은 $\theta$ 교정 절차에서 **무변경 V0 기준선 장치도 검출 18·21·18/32**로 동일하게 미달했다(V2: 16·21·16). 따라서 검출 부족은 R-A 장치의 퇴행(I)이 아니다. seed당 검출확률 $\approx0.5$–$0.65$는 DGP·$\theta$ 규칙·후보 kernel의 고유 속성이고, 이 확률에서 32연속 검출 확률은 $\lesssim10^{-7}$이다. F2-A의 같은 검출 규칙 게이트가 $\ge4/8$(50%)이었던 것과 정합적으로, **confirm의 32/32는 검출 결정론을 암묵 가정한 규약 결함(C)** 이다. 선행 run(SRM8·9)이 confirm에 도달한 적이 없어 이 게이트는 이번에 처음 시험되었다.

### 6.3 보존·재개 조건

- **보존되는 좁은 관찰**: robust 장치는 confirm 수준의 모든 순위·오차·FAR 게이트를 전 후보·전 시나리오에서 통과했다. 이것은 확증이 아니라 관찰이다(게이트 문면상 kill 유지).
- 이 계약 안에서 32/32를 완화하는 것은 금지된 사후 게이트 변경이므로 하지 않는다. kill은 유지된다.
- **재개 조건**: 후속 계약은 JUMP 검출 게이트를 결과 확인 전 새 문면으로 재유도해야 한다 — 예: F2-A의 50% 규약과 정합하는 이항 하한(검출확률 $p_0$에 대한 사전 고정 가설검정), 또는 검출확률 자체를 estimand로 한 신뢰구간 게이트. 이 재유도는 본 run의 검출수를 본 뒤 제안되므로 **outcome-informed 개발 판본**이며, 그 통과는 독립 확증이 아니다. 확증 지위는 게이트 동결 후 새 seed 블록에서만 가능하다.
- 증거·재현: 러너 스크래치패드 `ba_srm11_confirm_runner.py`(동결 seed 결정론), 영수증 SHA-256 `451ef9cc542d0c58c4593dcafbbc5e4c023dc3367357bd0efc5fada6b2672044`, 이월 ID SHA-256 `b139c56b…`(§2). 진단 대조(V0)는 게이트 판정에 사용되지 않았다.

`CLAIM_CEILING` 유지: `BIO_EVIDENCE_L0`, 생물학·의식·기억·AGI 주장 없음.
