# Clarus-Equation Codex rules

## Default: direct implementation

- For ordinary code, test, documentation, and harness work: inspect the target, make the smallest scoped change, and run one focused validation.
- 문서 정본 입구는 `paper/README.md`, 하네스 구조와 부채는 `.codex/README.md`에서 확인한다.
- Do not create a CE research run, preregistration, audit bundle, or full report unless the user explicitly asks for research, a new scientific claim, formal closure, preregistration, or release evidence.
- Do not run bare `pytest`, the full suite, all benchmarks, or packaging by default. Use the narrowest changed test or a source-only check first.
- Keep one implementation owner. Use subagents only for independent read-only mapping or research, and audit a stable snapshot after the implementation owner stops editing.
- 논문형 문서(강의·유도·논문 원고·독자 가이드)를 작성·수정할 때는 `.codex/harnesses/document_policy.md`의 문서 유형 규칙, 링크 정책, 처음 읽는 독자 게이트를 적용한다. 태그 블록만 나열한 논문형 문서는 완성으로 보고하지 않는다.
- 깨진 링크는 제거하고 `_workspace/` 링크는 만들지 않는다. 수기 누적 논문형 문서(200 KB 초과 또는 run별 절 누적)는 `00_논문목차.md` 폴더로 논문화한다. 검사기는 `.codex/hooks/repository_harness.py`이고 `tests/test_canonical_document_policy.py`가 위반 0을 단언한다.
- 문서 소유권은 direct 모드에서 순서로 분리한다. 원장(`paper/검증_원장`)과 논문형 문서가 함께 바뀌면 원장을 먼저 안정화하고, 논문형 문서는 그 원장을 읽기 전용으로 사용하며 같은 변경에서 두 유형을 동시에 수정하지 않는다.
- `artifacts/`와 `experiments/preregistration/` 영수증이 SHA-256으로 잠근 소스·테스트·게이트는 수정하지 않는다. 목록은 `.codex/README.md`의 부채 절에 있다.

## Plan orchestrator: 목표 정렬 게이트

여러 단계 작업이나 연구 사다리를 계획·갱신할 때 오케스트레이터는 다음 내용을 사용자에게 쉬운 말로 먼저 설명한다.

1. 최종 목표, 이번 단계의 하위 목표, 이번 단계가 최종 목표에 필요한 이유를 각각 한 문장으로 구분한다.
2. 현재까지 완료·부분완료·실패·미실행인 항목과 그 근거 파일 또는 검증 영수증을 구분한다.
3. 다음 행동 전에 `목표가 명확한가`, `현재 실험이 그 목표를 직접 판별하는가`, `같은 Stage 번호의 다른 계보를 잘못 세고 있지 않은가`, `선행 게이트를 건너뛰지 않는가`를 점검한다.
4. 목표 이탈·계보 혼동·계약 불일치를 발견하면 결과 해석을 계속하지 말고 안전 정지한 뒤, 무엇이 어긋났고 어떤 최소 수정으로 복귀하는지 보고한다.
5. 각 실행 결과 뒤에는 `원래 질문에 답했는가`, `무엇이 반증되었는가`, `무엇은 아직 살아 있는가`, `다음에 허용되는 행동은 무엇인가`를 기록한다.
6. 양성 결과라도 사전 조건이나 필수 데이터(recovery, holdout, blind ground truth 등)가 빠졌다면 다음 Stage를 자동 허가하지 않는다.

## Validation tiers

- FAST (default, target <=15 s): source parse/compile or one focused test file/node.
- STANDARD (explicitly useful, target <=60 s): the changed subsystem and its adjacent integration test.
- FULL/LOCK (explicit request only): full pytest, release gates, scientific stages, or irreversible V5 workflows.

For pytest, disable the cache provider and use a unique temporary basetemp outside the repository. Never run an irreversible scientific stage as a routine validation.

## Codex plan orchestration

For every multi-step task, the plan update must make the following four items explicit in plain language:

1. **Goal:** what concrete outcome the user is asking for.
2. **Why this step:** how the current step contributes to that goal.
3. **Goal clarity and drift:** whether the goal is clear, whether the work is still aligned, and any evidence of drift risk.
4. **Next gate:** the observable pass, fail, stop, or user-decision condition that controls the next branch.

Do not label apparatus preparation, data acquisition, or coordinate registration as a hypothesis result. If a planned action no longer contributes to the stated goal, stop that branch, record the mismatch, and replan before continuing. When explaining progress to a nontechnical reader, separate `준비됨`, `검사 중`, `지지됨`, `실패/미확립` so that implementation progress is not mistaken for scientific confirmation.

## Windows Python execution

- Agent runs are non-interactive. Never wait for a `uv`, Python selector, security, or package-install prompt; use explicit arguments or stop with the exact prerequisite.
- On this repository, use `.codex/hooks/python.cmd doctor|python|pytest` as the Windows Python entry point (Claude Code sessions may call the `.claude/hooks/python.cmd` mirror, which delegates to it). It prefers an already working non-venv system interpreter, sets the repository `PYTHONPATH`, disables bytecode/cache output, and gives pytest a unique owned basetemp.
- Do not invoke the workspace `.venv` or a uv-managed Python after Windows Application Control rejects it. Do not weaken or bypass Windows Application Control. `uv` is reserved for an explicitly required dependency-resolution step after its cache and execution policy are separately repaired.
- The direct-system-Python fallback is the default for focused source/tests only. A sealed scientific one-shot must also freeze and record the selected interpreter path, version, and dependency versions in its contract or manifest.
- Native extensions are optional. Build them with `.codex/hooks/build-native.cmd` (cargo only, no venv or pip); without them every consumer uses the pure-Python fallbacks and `reality_stone._has_rust_ext` / `reality_stone.clarus.has_native_kernels()` report `False`.

## Main-agent Git ownership

- The root/main agent alone owns branch changes, staging, commits, fetch/pull, and pushes. Subagents may inspect `git status`, `git diff`, and object IDs read-only, but must never change Git state or publish.
- Before a handoff, the main agent records repository root, branch, upstream, HEAD, remote tip, exact changed-path manifest, validation command, and remaining unrelated dirt. Never use `git add .`, `git add -A`, stash, reset, clean, checkout, or an automatic rebase to make a dirty tree look clean.
- Publishing requires the user's explicit publish instruction or an already explicit publish workflow. Fetch first, require `main` tracking `origin/main`, require a fast-forward, stage only the approved path manifest, run `.codex/hooks/check-large-data.cmd --commit` and then `--push` to scan staged and outgoing blobs, run `.codex/hooks/repository_harness.py` when documents changed, and use an ordinary non-force push. A mismatch, remote advance, hook failure, or branch-protection rejection is a stop condition, not permission to force or rewrite history.
- After a push, verify that `refs/heads/main` at the remote equals local `HEAD`, then report the commit SHA, exact published paths, validation evidence, and any local changes that remain.
- Commit messages describe the change. Do not reuse a placeholder subject such as `new`.

## Theory analysis and explanation (서사-우선 독해 규약)

CE 뇌·AGI 이론 전체를 분석·요약·설명하라는 요청(예: "논문 전체 분석", "어떤 이론인지 설명")을 받으면 다음 규약을 따른다.

1. `paper/README.md` 1절(형식 출처 표지)과 `paper/6_뇌/00_읽기지도.md`의 읽기 순서를 먼저 읽고, 루트 `README.md`의 네 층 — **생물 전기식(출발 모형) → CE 가설(history 상태·후보 계량·현재-세계 특권화) → 측정 모형(관측 quotient·식별 한계) → AGI Bridge(공학적 대응)** — 을 분석의 골격으로 삼는다. 결과 수치나 PASS/FAIL 목록만 떼어 이론을 특징짓지 않는다.
2. 태그 체계가 물리 사상을 `[공리]`/`[미완성]`으로 격리하는 것은 약점의 자백이 아니라 **의도된 감사 규율**이다. 분석 보고는 항상 네 층을 함께 제시한다: 동기 서사(공리 묶음) / 조건부 정리 / 채택 공리 / 미완성 다리. 뇌 주장에는 `BIO_EVIDENCE_L0`–`L4` 등급을 함께 적는다.
3. 관측 근접을 증거로 승격하지 않되, 메커니즘 서사를 생략한 채 경험식 목록만으로 이론을 "수치 우연의 모음"으로 특징짓지도 않는다. 두 방향 모두 오독이다.

## CE research

연구급 작업(새 계약, 사전등록, 감사 묶음, 정식 폐쇄, 배포 증거)은 사용자가 명시적으로 요청할 때만 시작하며 `.codex/harnesses/real_brain_equation_discovery_loop.md`의 계약 → 경로 → 감사 → 구현 순서와 `.codex/harnesses/brain_evidence_ladder.md`를 따른다. 새 `CE_RUN`이나 `_workspace/`는 만들지 않고, 기존 run 증거는 형제 저장소 `ce-runs`(`CE_RUNS_PATH`)에서 읽기 전용으로 참조한다. 일상 수정은 이 워크플로를 거치지 않는다.

V5 source lock and one-shot execution must use a fresh independent clone outside OneDrive/reparse-backed paths.
