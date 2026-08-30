<!-- 도메인: ce-brain-bio -->

# BA-SRM12 연구 계약 — JUMP 검출 게이트 재유도와 새 seed 합성 확증

Status: `SYNTHETIC_CONFIRMED_L0_DEV / 14_OF_14` (계약 동결 2026-08-30, 결과 기입 2026-08-30)

계보: BA-SRM10 (`R-A_SURVIVED`) → BA-SRM11 (`SYNTHETIC_FUNNEL_KILL / GATE_DEFECT_C_CLASSIFIED`) → **BA-SRM12 (이 계약)**.

## 1. 판본 지위 선언 (정직성 조항)

이 판본은 BA-SRM11에서 검출수 $[15,21]/32$를 관측한 **뒤에** 게이트를 재유도하므로 **outcome-informed 개발 판본**이다. 아래 게이트 선택이 관측에 의해 오염될 위험을 다음으로 통제한다:

- 게이트 문면은 관측 수치가 아니라 **SRM8 계약 자체의 동결 규약(F2-A: `detected>=4/8`)에서만** 유도한다 (§2).
- 판정은 SRM11에서 한 번도 열지 않은 **새 seed 블록**에서만 내린다 (§3).
- 대안 게이트(이항 유의성 검정)는 채점에 쓰지 않고 기술 통계로만 병기한다 (§2).

이 판본의 통과는 funnel 자체 용어로의 L0 장치 확증이며, 독립 확증·생물학 주장이 아니다.

## 2. 게이트 재유도 (결과 확인 전 고정)

SRM8 동결 규약에서 JUMP 검출 게이트는 검출률 문턱이다: F2-A는 `detected >= 4/8`, 즉 **관측 검출률 $\ge 50\%$**. confirm의 `32/32`는 같은 통계량에 결정론($100\%$)을 요구해 seed당 확률적 검출과 모순되는 규약 결함(C)이었다 (SRM11 §6.2).

**재유도 게이트(채점용)**: confirm 패널 32 seed에서 검출수 $\ge 16/32$ — F2-A의 관측 검출률 $50\%$ 규약을 통계량·문턱 동일하게 32 seed 규모로 확장한 것이다. 유도에 SRM11 관측치는 사용하지 않았다.

**기술 통계(채점 아님)**: 검출수의 정확 이항 $p$-값($H_0{:}\,p=0.5$, 단측)을 후보별로 병기한다. 참고로 $P(X\ge22\mid32,0.5)\approx0.025$가 유의성 관점의 대안 문턱이며, 채택하지 않은 이유는 F2-A 규약(관측률 문턱, 유의성 검정 아님)과의 비대칭 때문임을 명기한다.

JUMP 외 confirm 게이트는 SRM8 문면 그대로 유지한다: recovery 6종 각각 중앙 $\rho\ge0.90$, 5%분위 $\rho\ge0.75$, 중앙 NMAE $\le0.15$; ISO 중앙 NMAE $\le0.15$, 평균 FAR $\le0.10$, 최대 FAR $\le0.20$.

## 3. 승계·신규 항목 (동결)

| 항목 | 값 |
|---|---|
| 장치 | BA-SRM10 V2 robust 장치 그대로 (`examples/brain/ba_srm10_ra_runner.py`의 `robust_pair`, clip $\pm4$) — 구조 변경 0건 |
| 후보 | SRM11 이월 14개 그대로 (정렬 ID SHA-256 `b139c56b589b54730b88469bf261f76ae382e17f83d5b93dccb1bd0b43366df2`). SRM11의 kill은 결함 게이트 단독 원인이므로 재입장 허용 |
| 단계 | confirm만 재실행 (F2-B·F2-D는 SRM11에서 14/14 통과, 재실행하지 않고 승계) |
| ISO 교정 seed | `20264001..20264016` |
| confirm 패널 seed | `20264101..20264132` (7 시나리오: recovery 6종 + ISO_NULL; ZERO abstain 점검은 `20264101..20264108`) |
| 재사용 금지 | SRM9/10/11의 모든 기존 seed 블록 |

## 4. falsifier와 결과 코드

- 새 seed에서 검출수 $<16/32$이거나 다른 confirm 게이트가 무너지는 후보는 `FUTILITY_KILL`. 14개 전원 kill이면 `SYNTHETIC_FUNNEL_KILL`로 잠그고 후보군 자체(kernel 계열)의 검출력 한계를 음성 결과로 완결한다.
- 1개 이상 통과하면 `SYNTHETIC_CONFIRMED_L0_DEV` — outcome-informed 개발 판본의 확증임을 접미사로 명기. 통과 후보 목록·수치 동결 후 **실데이터 endpoint 계약(SRM7 successor rule 결합) 개설 자격**.
- seed·게이트·상수·후보의 결과 후 변경은 즉시 STOP. `CLAIM_CEILING`: `BIO_EVIDENCE_L0`.

## 5. 결과 (2026-08-30 실행, 동결 seed·게이트 그대로)

**판정: 후보 14/14 `SYNTHETIC_CONFIRMED_L0_DEV`.** 새 seed 블록(`20264xxx`)에서 전 게이트 통과.

| 게이트 | 결과 (후보 14개 범위) |
|---|---|
| recovery 6종 중앙 $\rho\ge0.90$ / 5%분위 $\ge0.75$ / NMAE$\le0.15$ | 전부 통과 — 최저 여유 ART10 중앙 $[0.9318,0.9471]$, 5%분위 $[0.8703,0.9128]$ |
| ISO 중앙 NMAE$\le0.15$·평균 FAR$\le0.10$·최대$\le0.20$ | 전부 통과 — 평균 FAR $[0.0468,0.0504]$ |
| JUMP 검출 $\ge16/32$ (재유도 게이트) | 전부 통과 — 검출수 $[17,24]$ |
| ZERO_NULL expected abstain | 8/8 |

**기술 통계(채점 아님)**: 검출수의 이항 $p$($H_0{:}\,p=0.5$, 단측)는 kernel 계열별로 갈린다 — BIEXP·POWER_theta2 계열 8종은 검출 $21$–$24$($p\in[0.0035,0.055]$)로 유의성 관점 대안 문턱($\ge22$)까지 대체로 넘지만, **POWER_theta8_p2 계열 6종은 검출 $17$–$18$($p\in[0.298,0.430]$)로 검출확률이 $50\%$와 구별되지 않는다.** 게이트 문면상 전원 통과이나, 실데이터 판본에서 검출 민감도가 중요해지면 theta8 계열의 이 한계를 선택 근거에 반영해야 한다(결과 후 후보 제외는 하지 않는다 — 기록만 남긴다).

증거·재현: 러너 스크래치패드 `ba_srm12_confirm_runner.py`(동결 seed 결정론, `examples/brain/ba_srm11_confirm_runner.py` 모듈 재사용), 영수증 SHA-256 `22d188b164777db8528e21867e4d75544ec8c20469d918b9cc80ed71cac5356a`.

### 5.1 다음 의무

§4에 따라 **실데이터 endpoint 계약(BA-SRM13) 개설 자격이 성립**했다. BA-SRM13은 (a) SRM7의 `SOURCE_ROOTED_INPUT_STOP` successor rule(물리시간 causal masked PSD 공분산 + 유효표본수 기권 규칙 + behavior-blind 실배경 주입 검사)을 승계하고, (b) 이 판본까지 확증된 robust 장치를 측정 연산으로 쓰며, (c) SRM7이 동결한 endpoint·split·대조군 문면을 재사용하되 anchor 규칙만 ESS 기권으로 교체하는 단일 구조 변경 계약이어야 한다. 확증 recording은 계속 봉인 유지.
