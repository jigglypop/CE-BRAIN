# CE Codex 하네스 상세 규칙

루트 `../AGENTS.md`가 기본 속도·라우팅 규칙의 정본이다. 이 파일은 `.codex` 내부 작업이나 명시적 CE 연구 run에만 상세 규칙을 보충한다.

## 라우팅

요청을 받으면 먼저 규모를 판단한다. **작은 요청에 run을 파지 않는 것이 속도 규율의 핵심이다.**

| 요청 | 행동 |
|---|---|
| 단순 질문·계산·파일 위치·한 줄 수정 | run 없이 바로 답한다 (spot). 스킬을 로드하지 않는다 |
| 특정 주장 지위·증명 판정 | $ce-closure-gate |
| 식의 차원·무차원 검사 | $ce-dimensionless |
| 테스트·회귀·수치 검증 | $ce-validate |
| 주장·상수·판본·진리값 원장 작성·수정 | $ce-ledger-write + ce-ledger-writer |
| 강의·유도·독자 가이드·논문 원고 작성·수정 | $ce-paper-write + ce-paper-writer |
| 문서 유형 판별·공통 지위 규약 확인 | $ce-doc-write (라우터) |
| 신규 주장 검증·승격 판단·논문화·병렬 연구 | $ce-research (full) |
| 완결 run의 후속·반복 (v8→v9 등) | $ce-research (light, PREDECESSOR 지정) |
| `.codex` 하네스·스킬·역할 카드·실행 정책 수정 | run 없이 대상 파일만 최소 수정 (spot) |

선택한 스킬 하나만 로드한다. 역할 카드는 4장(sourcer, math-verifier, status-auditor, impl-engineer)이며 해당 레인을 실행하는 순간에만 읽는다. 우회 경로 탐색(routes)은 math-verifier 레인에 포함되고, 최종 집필은 역할 카드 없이 $ce-research의 집필 규칙으로 직접 한다.

## 코어 명령

    .codex/hooks/run.sh <cmd> ...     # POSIX
    .codex/hooks/run.cmd <cmd> ...    # Windows (프리빌드 바이너리 직행)

- `init <run-dir>` — 기존 run 재개 또는 새 run 생성. 활성 미완성 run이 있으면 새 폴더 생성이나 다른 기존 run으로의 전환 전에 `REUSE_REQUIRED`로 중단하고 포인터를 보존한다.
- `init --new-contract <run-dir>` — 기존 목표·증거 계보와 독립인 새 연구 프로그램에만 사용한다. 같은 목표의 새 가설·데이터 판본·독립 확인·복구·추가 계산·감사·그림·논문 보완은 기존 `CE_RUN`의 epoch에서 한다.
- `status <run-dir>` — 단계별 상태·Gate·수정 카운트를 한 화면에 출력. **run 현황 파악에 stage 파일을 다시 읽지 말고 이것을 쓴다.**
- `check <run-dir> <contract|lanes|gate|build|final>` — 해당 단계까지 전체 체인 검사.
- `revise <run-dir> <role>` — 구현·측정 계열의 국소 수리 기록. 역할당 3회 상한이며, 한도 소진은 주장 축소나 `BLOCKED`의 근거가 아니다.
- `counterexample <run-dir> <cex-id>` — 실패한 부모 주장과 재현 증인을 같은 run의 음성대조군으로 잠근다.
- `pivot <run-dir> <cex-id> <route-id>` — 구조적으로 다른 기전 경로를 최소 3개 등록한 뒤 선택한 경로를 같은 run에서 연다. 역치·seed·endpoint·decoder만 바꾸는 재조정은 거부한다.
- `gc <workspace>` — `.pin`, 활성 epoch, 외부 참조가 없는 완결 run만 `_archive/`로 옮기고 색인을 남긴다. 참조 경로와 미완성 run은 건드리지 않는다.

## 심각도 어휘 (모든 역할 공통)

- **P0**: 주장을 무너뜨리는 결함 — 완전한 반례, 증명 오류, 수치 불일치가 결론을 바꿈. 해소 전 Gate PASS 불가.
- **P1**: 결론은 유지되나 방치 불가 — 증명 공백, 숨은 공리, 기준선 불일치. revise로 처리하거나 BLOCKED로 기록.
- **P2**: 표기·분량·정리 문제. 최종 보고서에 목록만 남기고 수정 루프를 소모하지 않는다.

## 속도 규율

- 카드·스킬을 선로딩하지 않는다. 필요한 시점에 필요한 것만 읽는다.
- run 현황은 `status`로 본다. stage 파일 재독은 내용을 인용할 때만.
- PREDECESSOR가 있으면 선행 run이 검증한 결론을 재유도·재대조하지 않고 경로만 인용한다.
- 상세 계산·로그·발췌는 artifacts/에 쓰고 stage 파일에는 판정·표·경로만 남긴다.
- 레인 파일은 3–4만 자 재생성이 아니라 판정 중심의 짧은 문서다.
- 상세 논문은 주제에 맞는 `docs/<분야>/<논문>/` 폴더에서 `00_논문목차.md`와 순서가 고정된 장별 Markdown으로 조립한다. 강의·유도도 길어지면 같은 입구+장 구조를 쓴다. `_workspace/`에는 논문 사본·초안·v2·final 사본을 만들지 않으며 `docs/README.md`와 분야 읽기 지도에는 목차 입구만 한 번 연결한다.
- `40-final-report.md`는 `DOCS_PAPER: docs/<분야>/<논문>/00_논문목차.md`와 run 결론·증거 경로·현재 epoch 통합 여부만 적는 짧은 인계 기록이다. 장 본문을 중복하지 않는다.
- `check final`은 앞 단계를 포함한다. 같은 상태에서 contract→lanes→gate→build→final을 연속 재실행하지 말고, 단계 전환에 필요한 check와 마지막 final을 각각 한 번만 실행한다.
- `check final`은 `40-final-report.md`가 가리키는 `docs/` 내부 목차가 `## 논문 조립 순서`에서 장 파일을 순서대로 연결하고, 그 조립 전체가 초록·배경·방법/정의·결과/유도·논의·한계/반증·재현성·참고문헌을 갖추는지 검사한다. 장이 목차 폴더 밖이나 `_workspace/`를 가리키거나 같은 원고를 중복하면 실패한다. 실증 run의 수치 원장은 선택적 `35-result-ledger.md`로 같은 run에 둘 수 있다.

## 실행·캐시 규율

- “검증해줘”, “고쳐줘”, “하네스 개선”은 전체 테스트 실행 권한이 아니다. 기본은 변경 파일에 직접 연결된 가장 작은 검사 **한 개**이며, green이면 멈춘다.
- 관련 회귀 확대는 작은 검사가 실패했거나 공용 API·의존성 경계를 바꿨을 때만 한다. 저장소 전체 pytest·전체 bench·release 검증은 사용자가 `전체`, `full`, `release`, `CI 재현`을 명시한 경우에만 실행한다.
- 코드가 바뀌지 않았는데 같은 green 명령을 다시 실행하지 않는다. 다른 역할의 성공 로그가 현재 byte와 명령을 고정했다면 인용하고 중복 실행하지 않는다.
- Python은 기존 interpreter를 `-B`로 사용하고 child 환경에 `PYTHONDONTWRITEBYTECODE=1`을 둔다. pytest는 `-p no:cacheprovider`와 실행별 고유 `--basetemp`를 사용한다.
- basetemp는 하네스가 만든 고유 소유 경로만 쓰고 성공·실패·중단 모두 `finally`에서 제거한다. 고정 이름 재사용, repo root 임시물, 광역 glob cleanup은 금지한다.
- Ruff는 `--no-cache`를 쓴다. 문법 확인은 source를 메모리에서 `compile()`하고 `compileall`로 pyc를 만들지 않는다.
- 현재 interpreter로 가능한 작업에 새 venv나 `uv run`을 만들지 않는다. dependency resolution이 실제로 필요할 때만 기존 프로젝트 실행기를 사용한다.
- Windows에서는 `.codex/hooks/python.cmd doctor`로 실행기를 먼저 확인하고, focused Python/pytest는 같은 래퍼의 `python`/`pytest` 모드로 실행한다. 프롬프트 입력을 기다리지 않으며, Application Control이 차단한 `.venv`나 uv-managed Python을 우회하지 않는다.
- full 검증을 생략한 것은 실패가 아니다. 최종 보고에는 실행한 최소 검사와 생략한 확대 검증을 각각 명시한다.

## 실측 교정 루프

- 수치 검증이 어긋나면(backend parity FAIL, 기준선 잔차 $|z|>3$, 차원 검사 불일치) 같은 명령을 반복하지 말고 `harnesses/empirical_calibration_loop.md`의 루프를 따른다: 최소 재현 → 첫 분기 중간값 → 원인 분류(차원 D·구현 I·정밀도 P·convention C·기준선 B·이론 T) → 교정 1건 → 최소 재검. 불일치당 3사이클 상한, 사이클당 조치 1건.
- 교정 가능한 것은 구현 코드, 결과를 보기 전에 선언된 자유 파라미터, sourcer가 출처 검증한 기준선 갱신뿐이다. tolerance·fixture·cutoff·acceptance·endpoint·seed는 결과를 본 뒤 바꾸지 않는다.
- 이론 검증의 수치 비교는 예측값·기준선(출처)·오차·잔차 $z$ 4열로 artifacts에 남긴다. $|z|\le1$은 관측 일치(증명 아님), $1<|z|\le3$은 tension(P2, 결론 의존 시 P1), $|z|>3$은 P0 후보로 루프 진입.
- T(이론) 분류는 앞 5개 클래스의 기각 근거가 기록된 뒤에만 쓴다. 이론 잔차를 코드 수정으로 흡수해 green을 만들지 않는다 — T 확정은 실패가 아니라 산출이며 closure-gate로 회부한다.
- **식 개정은 같은 run의 epoch 계약 행위다** (`harnesses/empirical_calibration_loop.md` §8): T 확정 잔차만 근거가 되고, 구 판본은 반례와 함께 음성대조군으로 보존한다. 새 판본은 새 동결 fixture와 강제한 관측 기준선(출처)을 명기한다. 관측 무차원 비율을 falsifier로 먼저 동결하고 자유 파라미터 수 < 재현 비율 수를 요구하며 비율별 개별 재조정을 금지한다.

## 네이티브 성능 경로 (Rust/CUDA)

- 무거운 수치 검증은 Python `float64` oracle → Rust CPU `f64` → CUDA `f64` 순으로 승격하며, 승격 조건은 해당 parity 하네스의 `BACKEND_PARITY_PASS`다. 곡률 진단의 정본 계약은 `harnesses/curvature_backend_parity.md`.
- 승격 후에도 세션마다 무작위 fixture 표본 3개 이상을 Python oracle과 재대조한다. 표본 실패는 즉시 parity FAIL 강등이다. CUDA `f32`는 속도 진단 전용이며 과학 판정에 쓰지 않는다.
- 성능 측정은 정확성 gate 통과 후에만, warm-up·반복 횟수·batch 크기를 고정해 artifacts에 기록한다. fallback 발생이나 native 호출 receipt 0은 성능 수치와 무관하게 parity FAIL이다.
- 빌드 캐시는 `%LOCALAPPDATA%`, 레포 안 `target/` 금지. 훅 이벤트에서 cargo 빌드를 트리거하지 않는다.

## main Git 인계 규율

- Git 상태 변경과 발행은 root/main agent 한 명만 맡는다. 모든 subagent는 `status`·`diff`·hash 같은 읽기 전용 확인만 하며 `add`·`commit`·`fetch`·`pull`·`rebase`·`push`·branch/worktree 변경을 하지 않는다.
- main은 종료 전에 루트·현재 branch·upstream·HEAD·remote tip·변경 경로를 확인하고, 작업 범위가 아닌 dirty path가 하나라도 있으면 자동 정리하거나 함께 stage하지 않는다.
- 발행할 때는 승인된 경로 manifest만 `git add -- <paths>`로 stage하고 staged diff·관련 검증을 확인한 뒤 `.codex/hooks/check-large-data.cmd --commit`을 명시적으로 실행한다. push 직전에는 같은 실행기의 `--push`도 실행한다. 이 gate는 연구 binary 확장자와 95MB 초과 Git blob을 막으며 secret scanner를 대신하지 않는다. `git add .`, `git add -A`, force push, 자동 stash/reset/clean/rebase는 금지한다.
- push 직전 다시 fetch하여 `origin/main`이 preflight base와 같은지 확인하고 fast-forward 일반 push만 사용한다. 완료 후 remote `refs/heads/main`과 local HEAD의 일치, commit SHA, 정확한 경로와 남은 dirt를 보고한다.

## 뇌 알고리즘 경로 선택

- **최우선 과제는 실제 뇌 식 기반 발견 루프다.** 실제 뇌에서 확립된 기전식과 측정모형을 출발점으로 고정하고, CE 가설을 명시적 추가항·새 상태·경계조건으로 분리한 뒤 실제 뇌 데이터의 held-out 잔차와 개입 falsifier로 판정한다. 식 개정은 데이터에 맞춘 사후 조정이 아니라 `harnesses/real_brain_equation_discovery_loop.md`와 `harnesses/empirical_calibration_loop.md`에 따른 새 판본 계약으로만 수행한다.
- 뇌/AGI `00-contract.md`는 최소한 `BIO_STARTING_MECHANISM`, `CE_DELTA`, `MEASUREMENT_MODEL`, `DATA_PROVENANCE`, `DATA_SPLIT`, `OBSERVABLES`, `RESIDUAL_RULE`, `FALSIFIER`, `MATCHED_CONTROLS`, `MODEL_SELECTION`, `REVISION_TRIGGER`, `CLAIM_CEILING`을 결과 확인 전에 고정한다. 실제 데이터·기전식·측정모형의 핵심 입력이 `UNVERIFIED`이면 채점 구현으로 진행하지 않는다.
- **주축은 두 질문이다: (1) 실제 뇌가 그 연산을 쓰는가, (2) 실제 뇌 데이터로 반증을 시도했는가.** 시뮬레이터 성립은 보조 증거다. 정본은 `harnesses/brain_evidence_ladder.md` — 증거 사다리 L0(합성)→L1(관측 비율)→L2(창발 통계)→L3(실데이터 예측)→L4(개입 동일성)와 원시 연산 허용 목록을 따르고, 모든 뇌 run 기계 상태에 `BIO_EVIDENCE_Lx`를 명기한다.
- **L4 이전에 "뇌가 이렇게 동작한다"를 쓰지 않는다.** L1–L3는 "정합"이다. 비허용 원시 연산(부호 자유 W, 알고리즘적 WTA, 전역 열거, 생물 대응 없는 supervisory 신호)을 쓴 run은 추상 알고리즘 트랙으로 강등하고 뇌 주장을 금지한다.
- 새 뇌/기억/의식 run은 직전 실행의 `12-routes.md`, `31-validation.md`, `40-final-report.md`가 가리키는 `docs/` 조립 목차와 필요한 장, 그리고 `_workspace/ce/brain-algorithm-route-ledger.md`를 먼저 읽는다. 연결 기록이 없으면 가장 늦은 numbered audit와 원장 행을 사용하고 closure 부재를 계약에 기록한다. 전체 artifact를 재독하거나 실패한 실험을 endpoint·threshold·seed만 바꿔 재시도하지 않는다.
- 오케스트레이터는 양성처럼 보이는 수치가 아니라 사다리 승급 가능성, 인과 식별 가능성, 기존 STOP이 남긴 정보, 독립 반증 대조군, capability dependency 순서로 다음 후보를 고른다. 선택 근거와 기각·퇴역 경로를 00-contract에 고정한 뒤 레인을 연다.
- simulator 결과는 실제 뇌의 증거로 자동 승격하지 않는다. L1 비율·L3 데이터는 sourcer 검증 기준선만 쓰고 UNVERIFIED 수치는 게이트에 넣지 않는다. 전역 원장은 후보·의존성·증거 경로·상태·다음 falsifier만 관리하고, 서사나 의식 동일시를 기록하지 않는다.

## 끈질김 (진취성 규율)

- **BLOCKED는 최후 수단이다.** 한 후보식의 반례나 역할별 수리 한도만으로 쓰지 않는다. 반례를 잠근 뒤 서로 다른 상태·상호작용·측정·개입 구조의 경로를 최소 3개 만들고, 각 경로의 판별 예측·음성대조·봉인 split·중단 조건을 시험한다. 명시적 모델 클래스 no-go, 필요한 외부 자료의 부재, 또는 세 경로의 중단 조건이 모두 충족된 경우에만 재개 조건과 함께 쓴다.
- ABANDONED는 명시한 모델 클래스의 구조적 불가능이나 증거 원천의 확정적 부재가 있을 때만 쓴다. 한 식의 반례, 분량·피로·세션 길이는 사유가 아니다.
- 부정 결과도 완결한다. 반례·기각은 `docs/` 조립 논문의 해당 장과 짧은 `40-final-report.md` 인계 기록에 반영한다. 죽은 경로 확인은 실패가 아니라 산출이다.
- revise 한도 소진은 run 포기나 목표 축소 사유가 아니다. 실패식을 음성대조군으로 고정하고 `counterexample → 세 기전 경로 → pivot`으로 전환한다. 좁혀서 참이 된 명제는 보존 결과일 뿐 돌파구 성공으로 세지 않는다.

## 데이터 반출 게이트

- Claude의 PreToolUse와 main의 필수 수동 preflight는 Windows 네이티브 `check-large-data.cmd`를 사용한다. POSIX `check-large-data.sh`는 같은 좁은 정책의 미러다. 95MB 초과 Git blob과 `_workspace/` 아래 지정 연구 binary 확장자를 차단하며, 일반 secret/source scanner는 아니다.
- 연구 데이터 원본은 커밋하지 않는다. 매니페스트·코드·요약 산출만 커밋하고 원본은 문서화된 DOI에서 재취득한다 (.gitignore가 정본).
- 게이트에 걸리면 우회(-f, --no-verify)하지 말고 `git rm --cached`로 언트래킹한 뒤 .gitignore 패턴을 보강한다.

## 정직성 (협상 불가)

- 실패를 통과로 표현하지 않는다. 실행하지 않은 검증을 실행했다고 쓰지 않는다.
- 기계 검사 상태 문자열(PASS 등)을 이론 지위처럼 문서에 복사하지 않는다.
- ce-closure-gate 기록 없이 "유도됨·제1원리·닫힘"을 쓰지 않는다.
- 관측 근접은 증명이 아니다. 형식 지위는 정의·정리·공리·산출·경험식·미완성·예측 7종뿐이다.
