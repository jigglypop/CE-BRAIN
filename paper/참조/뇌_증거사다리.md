# 뇌 생물학 증거 사다리

Status: `CANONICAL_BIO_EVIDENCE_LADDER_V1`

판본일: 2026-08-31

이 문서는 뇌 이론의 `BIO_EVIDENCE_L0`–`L4`를 정의하는 정본이다. 수학적
완결성, 합성 fixture, 코드 정확성, 실제 생물학적 지지와 인과 매개를 서로
바꾸어 세지 않는 것이 목적이다.

## 1. 공통 판정 원칙

1. 등급은 **주장과 명시된 preparation·단위·endpoint의 쌍**에 붙는다. 한
   종·영역·세포형의 결과를 다른 범위로 자동 운반하지 않는다.
2. 통합 사슬의 등급은 필수 화살표 가운데 가장 낮은 등급이다. 서로 다른
   논문의 receptor, spine, myelin, population geometry 결과를 더해 하나의
   `미시변수 → 계량 → 행동` 증거로 만들지 않는다.
3. 상위 등급은 아래 등급의 조건을 누적해서 만족해야 한다. Stage 번호나
   다른 자료 계보의 PASS는 등급을 대신하지 않는다.
4. source/schema 검사, 장치 준비와 합성 수치 PASS는 생물 endpoint를 열기
   위한 장치다. endpoint가 열리지 않았으면 양성도 음성도 아니다.
5. `BLOCKED_INPUT`, `AUTHORIZATION_FALSE`, `EXECUTION_READY_FALSE`, approval
   `PENDING`, runner 부재와 품질관리 탈락은
   정확히 그 정지 이유로 기록한다. 생물 가설의 실패로 바꾸지 않는다.
6. regularization으로 만든 SPD working metric은 raw Fisher rank의 생물학적
   식별 증거가 아니다. raw와 regularized 결과를 분리한다.

## 2. 등급 정의

| 등급 | 최소 필요조건 | 허용되는 표현 | 금지되는 승격 |
|---|---|---|---|
| `L0` 형식·장치 | 정의·정리·공리·합성 fixture, source/schema audit 또는 실행 계약. 실제 생물 endpoint의 방향성·재현·개입은 아직 없음 | “조건부 수식이다”, “구현 witness가 통과했다”, “입력이 열렸다/차단됐다” | “실제 뇌가 이 기전을 쓴다”, “생물학적으로 지지됐다” |
| `L1` 범위고정 관측 | 1차 생물자료 또는 source-locked 재분석, 명시한 종·영역·세포형·단위·endpoint, 관측·제외 규칙과 provenance. 적어도 한 구성요소의 실제 관측 방향을 판정 | “이 preparation에서 이 구성요소가 관찰됐다” | 통합 기전, 일반화, 인과, 매개 |
| `L2` 종단·예측 | 같은 생물 단위의 종단 등록, 독립 calibration, 사전고정 split·null·경쟁모형, held-out 방향·효과의 재현. 누락·검출·readout drift를 대조 | “이 범위에서 변화가 후속 endpoint를 예측한다” | 조작 인과, 계량 매개, 다른 단위·종으로의 일반화 |
| `L3` 기전 개입 | 무작위 또는 동등하게 식별 가능한 선택적 기전 개입, sham·off-target·회복 대조, 사전고정 endpoint와 holdout에서 예측 부호 재현. 조작 충실도와 직접경로를 보고 | “이 preparation에서 개입이 해당 기전 성분과 endpoint를 움직였다” | 동일세포 미시상태→계량→행동의 완전 매개, 보편 뇌 법칙 |
| `L4` 개입 동일성·매개 | 같은 동물과 가능한 같은 세포·접촉의 종단 identity, 미시변수·독립 출력-likelihood 계량·별도 행동 endpoint의 공동 측정, 무작위 mechanism 개입, mediator-specific intervention 또는 검증된 causal-state intervention, positivity·consistency·confounding·exclusion/direct-path 대조, 독립 holdout 또는 복제. selective rescue는 별도 필요조건이지만 단독으로 충분하지 않음 | 명시한 preparation과 endpoint 범위에서만 “뇌가 이 사슬로 동작한다” | 상류 $\Theta$ rescue나 metric·행동 동시회복만으로 매개 확정, 측정하지 않은 종·영역·발달기·행동으로의 보편화 |

## 3. 네 게이트와의 관계

`형식 / 관측 / 개입 / 예측`은 서로 다른 질문이고, 등급은 이 질문을 누적한다.

| 판정 요소 | 최초로 필수인 등급 | 영수증의 최소 내용 |
|---|---|---|
| 형식 폐쇄·단위·정칙성 | `L0` | 판본, 식/코드 hash, 수치 또는 증명 검증 |
| 실제 생물 관측 | `L1` | source 판본, 표본·preparation, 관측·제외 정의 |
| 동일단위 종단·holdout 예측 | `L2` | identity map, split, calibration, null/competition |
| 선택적 개입 | `L3` | randomization, sham/off-target, manipulation check, recovery |
| 통합 매개 동일성 | `L4` | 미시·계량·행동 공동 endpoint, mediator-specific 또는 검증된 causal-state intervention, 단독으로 충분하지 않은 selective rescue, causal assumptions와 독립 검증 |

`통과`, `강함`, `pilot 통과` 같은 계보 내부 어휘는 위 영수증이 없으면
`BIO_EVIDENCE` 등급을 뜻하지 않는다.

## 4. 현재 CE-NPF 통합사슬의 적용

현재 발달 prior, conductance·STP·접촉·myelin 구성요소에는 범위가 제한된 1차
생물자료가 있다. 그러나 같은 동물·세포에서 `ΔΘ → Δg → Δ행동`을 종단 측정하고
선택적으로 개입한 자료가 없으므로, **통합 주장**은
`BIO_EVIDENCE_L0 / BIOLOGICAL_MEDIATION_UNTESTED`다. 구성요소별 L1 근거는
이 통합 등급을 올리지 않는다. 실행계약·서명 payload·fail-closed gate가 통과해도
실제 생물 endpoint의 held-out 방향이 판정되기 전에는 이 등급을 올리지 않는다.
