# CE-AGI 런타임 문서 안내

이 레포는 뇌·AGI 런타임 도메인(ce-agi-runtime)이다. 문서는 뇌 이론(6_뇌), AGI 런타임 이론·사양(7_AGI), 검증 원장, 구현 참조로 구성된다. 물리 트랙(우주론·QFT·핵융합·GR·flavor) 문서와 원장은 2026-08-23 멀티레포 분리 정리로 이 레포에서 제거됐다 — git 이력과 `MULTIREPO_PLAN.md` 진행 기록을 참조한다.

독자는 문서의 수식·관측 비교·코드 검증이 서로 다른 지위를 가진다는 점에서 출발하며, 한 경로의 통과를 다른 경로의 증명으로 읽지 않는다.

## 1. 형식 출처

각 문장은 정의·정리·공리·산출·경험식·미완성·예측 중 어디에서 오는지 구분해야 한다. 형식 출처 표지는 외부 데이터나 코드 실행을 수학적 증명으로 바꾸지 않는다.

| 표지 | 의미 |
|---|---|
| **[정의]** | 기호·대상·정의역 |
| **[정리]** | 적힌 전제에서 증명된 명제 |
| **[공리]** | 모형·가지·경계조건·물리 사상의 선택 |
| **[산출]** | 정리와 공리를 대입한 직접 결과 |
| **[경험식]** | 자료·보정·유효계수를 사용하는 관계 |
| **[미완성]** | 작용·사상·증명 또는 자료가 더 필요한 항목 |
| **[예측]** | 입력과 판정 기준을 미리 고정한 독립 관측량 |

관측 적합성은 수학적 정리의 진위를 결정하지 않는다. 완전한 반례가 있는 부모 명제는 활성 문서에 보존하지 않지만, 전제를 좁혀 참이 되는 정리와 정확한 no-go는 보존한다.

뇌 주장에는 추가로 증거 사다리 지위(`BIO_EVIDENCE_L0`–`L4`)가 붙는다. 정본 규정은 `.codex/harnesses/brain_evidence_ladder.md`이며, L4(개입 동일성) 이전에는 "뇌가 이렇게 동작한다"를 쓰지 않는다.

## 2. 뇌 이론 (6_뇌)

- [읽기 지도](6_뇌/00_읽기지도.md) — 장 구성과 독자 경로
- [해부학 계층](6_뇌/01_해부학계층.md) · [관측 정의](6_뇌/02_관측정의.md) · [항상성 제어축](6_뇌/03_항상성제어축.md) · [그래프 결합과 이완](6_뇌/04_그래프결합과이완.md)
- [실험 근거](6_뇌/05_실험근거.md) — 입구. 세부는 [05_실험근거/](6_뇌/05_실험근거/) 분할 파일
- [수면과 복구](6_뇌/07_수면과복구.md) · [시냅스 가소성](6_뇌/08_시냅스가소성.md)
- [생명에서 지능까지](6_뇌/09_생명에서지능까지.md) — 입구. 세부는 [09_생명에서지능까지/](6_뇌/09_생명에서지능까지/) (C. elegans→mouse 계통 비교, 원시생명 정리)
- [신경 프로그래밍 언어 역공학](6_뇌/10_신경프로그래밍언어_역공학.md)
- [신경 리만 계량과 문맥 의존 라우팅](6_뇌/11_리만계량_라우팅_논문.md)

## 3. AGI 런타임 (7_AGI)

이론·사양 축: [AGI](7_AGI/1_AGI.md) → [Architecture](7_AGI/2_Architecture.md) → [Equation](7_AGI/12_Equation.md) → [BrainRuntimeSpec](7_AGI/14_BrainRuntimeSpec.md) → [CodeMap](7_AGI/18_CodeMap.md). 코드 변경 전 CodeMap을 확인한다.

연구 루프 기록(23–42)은 run별 결론 문서다. 새 run 전에 선행 run의 routes·validation과 `_workspace/ce/brain-algorithm-route-ledger.md`를 읽는다.

## 4. 검증 원장 (검증_원장)

- [뇌 검증기준](검증_원장/뇌_검증기준.md) — 뇌 주장 판정 기준의 정본
- [AGI CloudCell Monad 감사](검증_원장/AGI_CloudCell_Monad_Audit.md)
- [AGI STDP 효능 감사](검증_원장/AGI_STDP_Efficacy_Audit.md)

## 5. 구현 참조 (참조)

- [Reality Stone](참조/Reality_Stone.md) — 기하 백엔드 엔진
- [기하학적 AI 엔진](참조/기하학적_AI_엔진.md)

## 6. 재현

Windows에서는 `.claude/hooks/python.cmd doctor`로 환경을 확인하고 같은 래퍼의 `pytest` 모드로 실행한다. 변경 파일에 직접 연결된 가장 작은 검사 하나만 먼저 실행한다.

    .claude/hooks/python.cmd pytest tests/test_dimensionless.py -q
    .claude/hooks/python.cmd pytest tests/test_convergence.py -q
    .claude/hooks/python.cmd pytest tests/test_layer_a.py -q

코드가 방정식을 높은 정밀도로 푸는 것과 그 변수를 실제 뇌·지능의 기전으로 식별하는 것은 다른 검증이다. simulator 성립은 보조 증거이며, 뇌 주장 승격은 증거 사다리와 `검증_원장/뇌_검증기준.md`를 따른다.
