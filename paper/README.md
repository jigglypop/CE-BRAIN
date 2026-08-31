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

뇌 주장에는 추가로 증거 사다리 지위(`BIO_EVIDENCE_L0`–`L4`)가 붙는다.
정본은 [뇌 생물학 증거 사다리](../.codex/harnesses/brain_evidence_ladder.md)다.
L4(개입 동일성·매개) 이전에는 범위를 생략한 “뇌가 이렇게 동작한다”를 쓰지
않는다.

## 2. 뇌 이론 (6_뇌)

- [읽기 지도](6_뇌/00_읽기지도.md) — 장 구성과 독자 경로
- [해부학 계층](6_뇌/01_해부학계층.md) · [관측 정의](6_뇌/02_관측정의.md) · [항상성 제어축](6_뇌/03_항상성제어축.md) · [그래프 결합과 이완](6_뇌/04_그래프결합과이완.md)
- [실험 근거](6_뇌/05_실험근거.md) — 입구. 세부는 [05_실험근거/](6_뇌/05_실험근거/) 분할 파일
- [수면과 복구](6_뇌/07_수면과복구.md) · [시냅스 가소성](6_뇌/08_시냅스가소성.md)
- [생명에서 지능까지](6_뇌/09_생명에서지능까지.md) — 입구. 세부는 [09_생명에서지능까지/](6_뇌/09_생명에서지능까지/) (C. elegans→mouse 계통 비교, 원시생명 정리)
- [신경 프로그래밍 언어 역공학](6_뇌/10_신경프로그래밍언어_역공학.md)
- [신경 리만 계량과 문맥 의존 라우팅](6_뇌/11_리만계량_라우팅_논문.md)
- [국소회로에서 상태다양체·흐름·계량으로 가는 조건부 구성](6_뇌/국소회로_상태다양체_흐름_대응/00_논문목차.md) — 21장은 발달 prior와 가소성·지연에서 기능계량 변형으로 가는 통합식을 유도한다.

## 3. AGI 런타임 (7_AGI)

이론·사양 축: [AGI](7_AGI/1_AGI.md) → [Architecture](7_AGI/2_Architecture.md) → [Equation](7_AGI/12_Equation.md) → [BrainRuntimeSpec](7_AGI/14_BrainRuntimeSpec.md) → [CodeMap](7_AGI/18_CodeMap.md). 코드 변경 전 CodeMap을 확인한다.

현재 실제 인간 뇌자료 논문: [인간 해마 세타자극 iEEG 재분석 목차](6_뇌/06_인간해마_세타자극_iEEG_재분석/00_논문목차.md). 공개 객체 18개 전수 계산, 임상 기준 후기 대비 $33.643\ \mu\mathrm V$, 인접 쌍극 기준 반례와 진행 중인 관측연산자 계산을 장별 본문으로 정리한다.

연구 루프 기록(23–42)은 run별 결론 문서다. 후속 연구는 선행 run의 routes·validation과 `_workspace/ce/brain-algorithm-route-ledger.md`를 먼저 읽고, 같은 목표와 증거 계보라면 그 run의 epoch에서 이어간다.

### 연구 run과 논문 완결

같은 연구 질문·데이터 판본·endpoint의 후속 계산, 오류 복구, sensitivity,
감사, 표·그림과 원고 보완은 새 workspace를 만들지 않고 기존 `CE_RUN`에서
계속한다. 기본 `init`은 다른 미완성 run이 있으면 `REUSE_REQUIRED`로 새 폴더
생성을 막는다. 기존 목표·증거 계보와 독립인 연구 프로그램일 때만 명시적인
`--new-contract`를 사용한다. 단, `real_brain_equation_discovery_loop.md`는
현재 checkout에 없다. [하네스 안내](../.codex/README.md)에 기록된 이 부채가
복구되기 전에는 그 하네스를 전제로 새 연구 run이나 주장 승격을 시작하지 않는다.

연구 논문의 정본은 주제 폴더의 `00_논문목차.md`와 그 목차가 순서대로 조립하는 장 파일들이다. 새 결과는 해당 장을 제자리 갱신하며, README에는 목차 링크만 한 번 둔다. `_workspace/`에는 논문 사본·초안·v2·final 사본을 만들지 않고 증거와 짧은 `DOCS_PAPER` 인계만 둔다. 실증·뇌 논문은 제목·초록·연구 질문, 자료·코호트·판본, 측정·전처리·QC, 사전 고정 분석, 주 결과와 모든 대조·민감도·음성 결과, 대안 해석, 주장 상한과 한계, 다음 반증 조건, 재현 경로와 1차 참고문헌을 장별로 포함한다.

반례는 논문을 줄이는 신호가 아니라 다음 식을 구별할 실험 입력이다. 실패한
식과 증인을 음성대조군으로 고정하고, 같은 run에서 상태·상호작용·측정·개입
구조가 다른 경로를 최소 3개 등록한 뒤 하나를 사전 선택해 계산한다. 좁혀서
참이 된 문장은 보존 결과일 뿐 돌파구 성공으로 세지 않는다.

## 4. 검증 원장 (검증_원장)

- [뇌 검증기준](검증_원장/뇌_검증기준.md) — legacy simplex/graph 계보의 네
  게이트와 일반 반증 원칙; BIO 등급 판정은 위 증거 사다리를 따른다.
- [신경 가소성·기능계량·접힘 주장 원장](검증_원장/신경_가소성_리만접힘_주장원장.md) — 발달 scaffold, conditional/marginal output Fisher, delayed flow-pullback, fixed-itinerary hybrid, marked-path 민감도와 slow Itô--jump metric transport, 공개 저자-catalogued 측방 돌기(필로포디아 미분리) 재관측 입력의 부분 적격성, 인과 매개 미검증 상태 (`BIO_EVIDENCE_L0`)
- [AIND BCI E1 동일세포 개입 계약](검증_원장/CE_NPF_AIND_BCI_E1_동일세포_개입계약.md) — SHA-256 `23fe688c…f22c`로 보존한 불변 사전등록 계약
- [AIND BCI E1 선택 입력 사전검사 결과](검증_원장/CE_NPF_AIND_BCI_E1_선택입력_사전검사_결과.md) — 22-asset source/schema 감사 뒤 epoch·clock A가 `E1_BLOCKED_INPUT`; target·ROI·metric endpoint 미실행
- [Loewenstein 2015 저자-catalogued 돌기 재관측 입력 사전검사 결과](검증_원장/CE_NPF_LOEWENSTEIN_2015_SPINE_생존입력_사전검사_결과.md) — 성체 수컷 GFP-M 청각피질 L5 apical tuft에서 선별한 측방 돌기(필로포디아 미분리)의 4일 재관측 입력만 `PARTIAL_MODEL_ELIGIBILITY`; biological CTMC/PDMP와 animal-heldout은 식별불가
- [Loewenstein V0,V1,V1Z,V2 비교계약](검증_원장/CE_NPF_LOEWENSTEIN_2015_돌기재관측_V0_V2_비교계약.md) · [Rust 수치코어](6_뇌/국소회로_상태다양체_흐름_대응/repro/fit_loewenstein_2015_protrusion_v0_v2.rs) · [wrapper](6_뇌/국소회로_상태다양체_흐름_대응/repro/run_loewenstein_2015_protrusion_v0_v2.ps1) · [authorization=false 실행 잠금](6_뇌/국소회로_상태다양체_흐름_대응/repro/loewenstein_2015_v0_v2_execution_lock.tsv) — 계약·구현 hash 잠금은 존재하지만 실제 fit 미시작, production receipt 없음
- [AGI CloudCell Monad 감사](검증_원장/AGI_CloudCell_Monad_Audit.md)
- [AGI STDP 효능 감사](검증_원장/AGI_STDP_Efficacy_Audit.md)

## 5. 구현 참조 (참조)

- [Reality Stone](참조/Reality_Stone.md) — 기하 백엔드 엔진
- [기하학적 AI 엔진](참조/기하학적_AI_엔진.md)

## 6. 재현

Windows 검증 정본 경로는 `.codex/hooks/python.cmd`지만 현재 checkout에는 그
hook이 없다. 복구 전에는 workspace `.venv`나 과거 `.claude` 경로로
우회하지 않고, 필요한 검증을 정확한 선행조건 부재로 정지한다. hook이 복구되면
변경 파일에 직접 연결된 가장 작은 source/test 검사부터 실행한다.

코드가 방정식을 높은 정밀도로 푸는 것과 그 변수를 실제 뇌·지능의 기전으로 식별하는 것은 다른 검증이다. simulator 성립은 보조 증거이며, 뇌 주장 승격은 증거 사다리와 `검증_원장/뇌_검증기준.md`를 따른다.
