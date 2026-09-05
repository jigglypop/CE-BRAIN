# 실제 뇌 식 기반 발견 루프 하네스

Status: `CANONICAL_REAL_BRAIN_DISCOVERY_LOOP_V2`

판본일: 2026-09-02

이 하네스는 실제 뇌에서 확립된 기전식과 측정과정을 출발점으로 삼고, CE의
추가항을 독립 가설로 세워 실제 생물 endpoint에서 반증하는 순서를 고정한다.
장치·문서·다운로드의 양을 연구 진전으로 세지 않으며, 생물학적 증거 등급은
[`brain_evidence_ladder.md`](brain_evidence_ladder.md)를 따른다.

## 1. 목표 정렬 게이트

중심 목표와 완료 조건은 [연구 PRD](../PRD.md)를 따른다. 고정점에서 연결·부가 기능이 메트릭을 표현하는 사상 중 무엇을 검증하는지 먼저 적는다. 평균 반응·수집량을 메트릭 검증으로 바꾸지 않는다. 아래 행동·인과 매개 요구는 그 주장을 하는 단계에만 적용한다. 역할은 [운영 규칙](agent_policy.md)에 따라 필요한 것만 호출한다.

각 사이클을 열기 전에 다음을 한 문장씩 기록한다.

1. **최종 목표:** 어떤 생물 preparation에서 어떤 인과사슬을 판정하려는가.
2. **이번 하위 목표:** 이번 계산·측정이 직접 판정하는 한 가지 질문은 무엇인가.
3. **필요한 이유:** 그 질문이 최종 사슬의 어느 화살표를 여는가.
4. **현재 상태:** 완료·부분완료·실패·미실행과 각각의 영수증은 무엇인가.
5. **다음 gate:** 관측 가능한 PASS·FAIL·STOP·사용자결정 조건은 무엇인가.

현재 행동이 최종 목표를 직접 판별하지 않거나 같은 Stage 번호의 다른 계보를
세고 있거나 선행 gate를 건너뛰면 해석을 중지하고 최소 수정으로 복귀한다.

## 2. 세 층의 분리

모든 실뇌 계약은 다음을 섞지 않는다.

1. **생물 기준식**
   $F_{\mathrm{bio}}$: 정의역·단위·시간척도와 1차 출처가 고정된 막전위,
   receptor, STP, 지연, 가소성, 항상성 등의 기전식.
2. **CE 추가항**
   $\Delta F_{\mathrm{CE}}$: 새 상태·결합·경계조건. `[공리: 모델 선택]`,
   `[경험식]` 또는 `[예측]` 중 하나로 지위를 표시한다.
3. **측정모형**
   $\mathcal H$: 숨은 상태에서 기록값으로 가는 acquisition, sampling,
   indicator kinetics, preprocessing, noise와 censoring.

권장 분해는

$$
dx_t=F_{\mathrm{bio}}(x_t,u_t;\theta)dt
     +\Delta F_{\mathrm{CE}}(x_t,h_t;\phi)dt+G(x_t)dW_t,
\qquad
y_k=\mathcal H(x_{t_k};\psi)+\varepsilon_k
$$

다. 실제 문제가 이 꼴이 아니면 동등한 상태·관측 분해를 계약에 명시한다.

## 3. 계약 필수 필드

결과를 보기 전에 다음을 고정한다.

| 필드 | 필수 내용 |
|---|---|
| `OBJECTIVE_CHAIN` | 최종 인과사슬, preparation, 단위와 주장 상한 |
| `BIO_STARTING_MECHANISM` | 기준 기전식·단위·시간척도·1차 출처 |
| `CE_DELTA` | CE 추가항과 대안모형 |
| `MEASUREMENT_MODEL` | 원신호부터 분석입력까지의 관측·noise·누락 모형 |
| `DATA_PROVENANCE` | DOI/공식 저장소·판본·포함/제외·identity |
| `DATA_SPLIT` | calibration/development/confirmation 또는 train/validation/holdout |
| `OBSERVABLES` | 단위·분모·불확도와 사전고정 endpoint |
| `ESTIMANDS` | 각 무작위 개입의 총효과·경로효과·예측효과 |
| `RESIDUAL_RULE` | likelihood·잔차·적합도와 tension/실패 판정 |
| `FALSIFIER` | CE 항을 죽이는 독립 시험과 adverse control |
| `MATCHED_CONTROLS` | 생물 기준식·단순 대안·동일 정보/자원 대조군 |
| `MODEL_SELECTION` | 복잡도·식별성·자유도·경쟁모형 비교 규칙 |
| `REVISION_TRIGGER` | 어느 잔차가 어느 항의 새 판본을 허용하는가 |
| `CLAIM_CEILING` | 현재 `BIO_EVIDENCE`와 금지되는 승격 |

구조적·실용적 식별성을 분리한다. 식별되지 않는 파라미터 조합은 개별
생물량으로 해석하지 않는다.

## 4. 데이터 재사용과 질문별 적격성

[데이터 관리 규칙](data_policy.md)에 따라 먼저 원장과 보유 자료를 확인한다. 같은 판본의 파일은 재사용하고, 필요한 자료가 없으면 요청 범위 안에서 공식 출처를 찾아 받는다. 재검토·재분석은 허용하며 질문과 이유를 남긴다.

Methods·README·스키마로 이번 질문에 필요한 변수와 단위를 먼저 확인한다. 전체 인과사슬의 필수 변수가 없으면 그 주장에 대해서만 `NOT_ELIGIBLE_FOR_CHAIN`으로 기록한다. 부분 질문을 판별할 수 있다면 부족한 조건과 주장 상한을 밝히고 진행한다. 필요한 조건을 충족하는 자료가 없으면 미확립으로 남기고 최소 추가 측정·개입을 제시한다.

다운로드는 필요한 파일·부분집합부터 시작한다. 원장에 출처·판본·위치·크기·해시·수집 이유를 남긴다. 기존 원자료를 자동 삭제하지 않는다. 과거 정지 판정은 보존하며, 문턱·제외·분할을 사후 완화해 기존 확인 결과를 구제하지 않는다.

## 5. 한 사이클의 실행 순서

1. **출처 잠금:** 기전식·측정모형·자료판본·intervention을 1차 출처에서 확인한다.
2. **생물 기준선:** CE 항 없이 $F_{\mathrm{bio}}+\mathcal H$가 baseline artifact와
   알려진 입력을 재현하는지 focused 검사 한 번으로 확인한다.
3. **CE 항 사전고정:** 추가항, 초기조건, 자유도, endpoint, falsifier와 대안을
   동결한다.
4. **분리 적합:** calibration/train에서만 적합하고 구조 선택은 validation까지만
   허용한다. confirmation·개입 holdout은 마지막 평가 전 봉인한다.
5. **최소 실데이터 endpoint:** source identity·clock·unit·event 결박이 통과하면
   같은 사이클에 최소 한 생물 endpoint를 계산한다. 장치만 확장하지 않는다.
6. **모델 비교:** CE 항이 기준식과 단순 대안보다 holdout/개입 판별에서 나은지,
   ablation에서 이득이 사라지는지 검사한다.
7. **판본 판정:** `PASS`, `FAIL`, `STOP`, `BLOCKED_INPUT` 또는
   `ENDPOINT_NOT_EVALUATED`를 정확한 범위로 기록한다.

P0, 즉 결과를 뒤집거나 봉인을 깨는 오류만 실데이터 진입을 막는다. P1/P2는
endpoint 편향을 구체적으로 보이지 못하면 병렬 부채로 남긴다. 재검토·재분석은 사용자 요청이나 새 질문·오류·방법 변경을 근거로 허용한다. 이유와 달라진 판정을 기록하고, 목적 없는 반복은 피한다.

## 6. 성체 L4 통합 인과 gate

`미시변수 \Theta → 생물학적으로 조작 가능한 상태 M → 별도 행동 Y`와
`M → 출력-상대 계량 g → 사전고정 요약 m=s_{\mathrm{pre}}(g)`를 명시한
preparation에서 L4로 판정하려면 다음이 모두 필요하다. 여기서 $g$와 $m$은
$M$의 측정량이지, 그 자체에 직접 개입할 수 있다고 가정한 생물 상태가 아니다.

1. 같은 성체 동물과 가능한 같은 세포·접촉의 종단 identity.
2. proxy가 아닌 직접 $\Theta$ 또는 독립 calibration을 통과한 proxy.
3. actuator command $a$, 독립 측정한 neural-state chart $z$, 행동값을 정의에 넣지
   않은 미래 output likelihood $p(O_{\mathrm{future}}\mid z,h,c;M)$와 동물별 raw
   Fisher field의 분리. $I_a[p(O\mid a)]$만 있으면 actuator--response pullback이지
   내재적 neural-state 계량이 아니다.
4. common support, 매끈함, constant rank·균일 SPD, 좌표 공변성 및
   Riemann/Finsler/stratified 경쟁.
5. 별도의 행동 endpoint.
6. 무작위 mechanism intervention, sham·off-target·recovery와 fidelity check.
7. tensor 자체의 불가능한 `do(g)`나 계산된 scalar에 대한 `do(m)`가 아니라,
   사전고정한 생물학적 상태 $M$에 대한 무작위 assigned-target intervention
   $Z_M$. $M$, $g$, $m=s_{\mathrm{pre}}(g)$를 따로 기록하고 $Z_M\to M\to m$의
   조작 충실도를 확인한다. $m$만 측정했거나 controller가 출력분포 전체를 직접
   맞춘 경우에는 metric-specific mediation이 식별되지 않는다.
8. `RESTORE > OFF`와 `ORTHOGONAL \simeq OFF`를 동시에 요구하는 대조, nuisance
   transition-kernel equivalence, positivity·consistency·mediator--outcome
   confounding·exclusion/direct-path 감사와 독립 동물 holdout 또는 복제.
9. 같은 identified contact에서의 가역 mechanism intervention과 selective rescue,
   sham rescue 및 passive-recovery 대조. 상류 상태와 계량·행동의 동시 회복만으로
   매개를 확정하지 않으며, 동일접촉 rescue가 불가능하면 L4를 STOP한다.

하나라도 빠지면 통합 등급은 가장 약한 화살표에 머문다. 양성 결과라도 다음
Stage를 자동 허가하지 않는다.

## 7. 식 개정과 반례

- 한 판본·한 사이클에는 구조 변경 한 건만 허용한다.
- 차원(D), 구현(I), 정밀도(P), convention(C), 기준선/측정(B)을 기각한 뒤에만
  이론(T) 잔차로 분류한다.
- 결과를 본 뒤 tolerance, rank cutoff, endpoint, seed, 제외, window를 바꾸지
  않는다.
- 확인자료를 본 수정은 개발용 `[경험식]`이며 새 독립 확인 전 `[예측]`이 아니다.
- 실패식·정의역·증인을 음성대조로 보존하고, 상태·상호작용·측정·개입 구조가
  다른 후보를 최소 3개 만든 뒤 결과 개봉 전에 하나를 선택한다.

## 8. 결과 영수증

각 실행 뒤 반드시 기록한다.

1. 원래 질문에 답했는가.
2. 무엇이 반증되었는가.
3. 무엇이 살아 있는가.
4. 다음에 허용되는 행동은 무엇인가.
5. 생물 endpoint가 실제 평가되었는가.

형식 정리, synthetic witness, source/schema 준비는 `L0`다. 실제 관측은 L1,
동일단위 종단·holdout 예측은 L2, 선택적 기전 개입은 L3, 동일성·매개 폐쇄는
L4다. 물리적 Lorentz 시공간과 출력-상대 신경 정보기하는 별도 주장이다.

## 9. 저장·재사용

같은 질문·자료판본·endpoint의 보완은 기존 계보에서 이어간다. 완결된
`C:/dev/ce/ce-runs` archive는 읽기 전용이며 수정하지 않는다. 이 저장소에서는
새 `_workspace/`를 기본 생성하지 않고, 저장 정책이 요구하면 계약·코드·테스트·
영수증을 `paper/` 정본에 직접 둔다. 논문 산출물은 주제의 `00_논문목차.md`가
조립하는 장 파일을 갱신하며 별도 final 사본을 만들지 않는다.
