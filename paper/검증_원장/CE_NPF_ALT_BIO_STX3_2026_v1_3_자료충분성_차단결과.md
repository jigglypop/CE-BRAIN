# Stx3 v1.3 자료충분성 차단 결과

Status: `STX3_TRIAL_COUNT_BLOCKED / BIOLOGICAL_ENDPOINT_NOT_EVALUATED`

판정일: 2026-09-02

계약 ID: `CE_NPF_ALT_BIO_STX3_REWARD_ALIGNMENT_XN_v1_3`

## 1. 판정

성체 CA1 Stx3 자료의 confirmatory endpoint는 실행하지 않는다. v1 hard gate는 각
`mouse × day × arm`의 block-5 trial을 시간순 `A,B,H`로 순환 배정하고 각 fold에 최소
4 trial, 즉 arm당 최소 12 trial을 요구한다. 16마리 모두 이 gate를 통과해야 하며 실패한
마우스를 제외해 계속하는 것은 금지돼 있다.

v1.3 full preflight는 `Cre_3/day5/LR=+1`에서 `A/B/H=4/3/3`을 만나 안전 정지했다.

- receipt: `data/external/plitt_kaganovsky_stx3_2026/stx3_reward_alignment_v1_3_full_preflight.json`
- receipt SHA-256: `b058e33bd18e46871c0382ad1ad97d152f2488ae6eea1e9ce2188fac7a9e9c93`
- 저장 상태: `STX3_TRIAL_JOIN_BLOCKED`
- 의미상 세분 상태: `STX3_TRIAL_COUNT_BLOCKED`
- `biological_endpoint_evaluated`: `false`
- runner SHA-256: `cc7c8a8b466728c4da79d95ecc547968b14a2cb5b39988a8c25fb98465ce40c4`
- preflight SHA-256: `6fec9d01e02df44e86799c174eced21a0517a7970a1c4acd5602a8839852b8fd`
- focused test: `35 passed`; test-source SHA-256
  `4462f7e3fbf9e85e8bd86476b175c06f1b3e9c908867e4bd9f401d7aa039dfeb`

attempt marker, execution lock, `G`, `ΔG`, `B`, `ΔB`, 집단검정 및 결합검정은 만들거나
계산하지 않았다. 이 결과는 생물 가설의 양성 또는 음성이 아니라 자료충분성 실패다.

## 2. 32-session 전수 trial-count 감사

아래 값은 NWB annotation `trial_info.block_number`와 `trial_info.LR`만 읽어 계산했다.
신경, lick, reward endpoint는 읽거나 계산하지 않았다. 괄호는 `n (A/B/H)`다.

| Subject/day | LR=-1 | LR=+1 | Gate |
|---|---:|---:|---|
| Cre_1 d0 | 22 (8/7/7) | 19 (7/6/6) | PASS |
| Cre_1 d5 | 20 (7/7/6) | 19 (7/6/6) | PASS |
| Cre_2 d0 | 22 (8/7/7) | 18 (6/6/6) | PASS |
| Cre_2 d5 | 19 (7/6/6) | 18 (6/6/6) | PASS |
| Cre_3 d0 | 17 (6/6/5) | 13 (5/4/4) | PASS |
| Cre_3 d5 | 14 (5/5/4) | **10 (4/3/3)** | **FAIL** |
| Cre_4 d0 | 21 (7/7/7) | 17 (6/6/5) | PASS |
| Cre_4 d5 | 15 (5/5/5) | 17 (6/6/5) | PASS |
| Cre_5 d0 | **7 (3/2/2)** | **10 (4/3/3)** | **FAIL** |
| Cre_5 d5 | **10 (4/3/3)** | **8 (3/3/2)** | **FAIL** |
| Cre_6 d0 | 19 (7/6/6) | 21 (7/7/7) | PASS |
| Cre_6 d5 | 17 (6/6/5) | 18 (6/6/6) | PASS |
| Cre_7 d0 | 22 (8/7/7) | 18 (6/6/6) | PASS |
| Cre_7 d5 | 16 (6/5/5) | 15 (5/5/5) | PASS |
| Ctrl_1 d0 | 19 (7/6/6) | 21 (7/7/7) | PASS |
| Ctrl_1 d5 | 19 (7/6/6) | 21 (7/7/7) | PASS |
| Ctrl_2 d0 | 21 (7/7/7) | 19 (7/6/6) | PASS |
| Ctrl_2 d5 | 20 (7/7/6) | 20 (7/7/6) | PASS |
| Ctrl_3 d0 | 20 (7/7/6) | 20 (7/7/6) | PASS |
| Ctrl_3 d5 | 21 (7/7/7) | 19 (7/6/6) | PASS |
| Ctrl_4 d0 | 21 (7/7/7) | 19 (7/6/6) | PASS |
| Ctrl_4 d5 | 21 (7/7/7) | 19 (7/6/6) | PASS |
| Ctrl_5 d0 | 19 (7/6/6) | 21 (7/7/7) | PASS |
| Ctrl_5 d5 | 20 (7/7/6) | 20 (7/7/6) | PASS |
| Ctrl_6 d0 | 20 (7/7/6) | 20 (7/7/6) | PASS |
| Ctrl_6 d5 | 22 (8/7/7) | 18 (6/6/6) | PASS |
| Ctrl_7 d0 | 20 (7/7/6) | 20 (7/7/6) | PASS |
| Ctrl_7 d5 | 20 (7/7/6) | 20 (7/7/6) | PASS |
| Ctrl_8 d0 | 22 (8/7/7) | 18 (6/6/6) | PASS |
| Ctrl_8 d5 | 21 (7/7/7) | 19 (7/6/6) | PASS |
| Ctrl_9 d0 | 21 (7/7/7) | 19 (7/6/6) | PASS |
| Ctrl_9 d5 | 20 (7/7/6) | 20 (7/7/6) | PASS |

요약은 29/32 session PASS, 3/32 session FAIL, 5 arm FAIL이다. 실패는 모두 Cre군에
속한다. 고정 DANDI 001710 manifest에서 `Cre_3/day5`, `Cre_5/day0`, `Cre_5/day5`는
각각 해당 날짜의 `scan0` 하나뿐이며 대체 scan은 없다.

## 3. 금지되는 구제와 다음 허용 행동

- fold 최소치를 4에서 2 또는 3으로 사후 낮추지 않는다.
- Cre 마우스만 완화하거나 `Cre_3/Cre_5`를 제외하지 않는다.
- cycle 위상, day 또는 scan을 결과를 본 뒤 바꾸지 않는다.
- A/B와 H를 중복 사용해 held-out 행동을 가장하지 않는다.
- 이 차단을 Stx3 또는 접힘 가설의 음성 결과로 쓰지 않는다.

원 confirmatory 질문을 다시 열려면 같은 범위의 독립 cohort에서 모든
`day × arm`에 block-5 완료 trial이 최소 12개 있어야 한다. 최소 trial을 낮춘 분석은 완전히
새 이름의 exploratory/secondary estimand일 뿐 원 primary를 구제하거나 증거등급을
올릴 수 없다. 현재 checkout에는 새 연구 run을 정당화할
`real_brain_equation_discovery_loop.md`가 없으므로 그런 후속 run은 시작하지 않는다.

## 4. 원래 질문에 대한 네 판정

1. **원래 질문에 답했는가?** 아니다. Stx3 성분과 보상상대 집단표현·행동의 결합
   endpoint는 표본충분성 gate 전에 차단됐다.
2. **무엇이 반증되었는가?** 생물 가설은 반증되지 않았다. “현재 32-file cohort가 고정된
   A/B/H confirmatory 설계를 실행할 만큼 충분하다”는 준비 가정이 반증됐다.
3. **무엇은 아직 살아 있는가?** 조건부 Fisher--Riemann 수학, 연결·효능·지연이 생성자와
   기능계량을 바꿀 수 있다는 후보식, 별도 preparation의 구성요소 관측은 살아 있다.
4. **다음에 허용되는 행동은 무엇인가?** 청소년기 가설과 무관한 성체 L4 신규실험에서
   같은 동물·세포의 미시변수, 독립 출력-likelihood 계량, 별도 행동, 무작위 기전개입,
   mediator-specific 개입·구제 및 독립 복제를 공동 측정하는 것이다.
