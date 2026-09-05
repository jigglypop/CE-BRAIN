# CE 연구 하네스 (Claude Code)

## 정본·표적
- 정본: `ledger/`(yaml 원장·큐) `derivations/`(유도·추측 카드) `verify/` `paper/`(제자리 갱신). 시행착오·주차장은 `_workspace/<YYYYMMDD>-<트랙>-<주제>.md`(상한 20개·48KB·640KB·21일, harness가 강제).
- 표적은 `paper/진전_원장.md` §2 하나. 훅이 매 프롬프트에 주입. 첫 메시지에 "이번 세션이 닫을 고리" 한 문장. 무관한 요청은 `[범위변경]`으로 묻고, 표적 변경은 사용자만.
- 떠오른 아이디어는 실행 말고 주차장에 한 줄. 툴 호출 10개마다 `[정렬]`/`[이탈]`, `[이탈]` 2연속이면 표적 복귀.

## 추측 우선 (재발견 금지)
식이 먼저다. 질문에 추측 카드(`derivations/<Q>/F-NN.formula.md`, 예측식 또는 예산식)가 없으면 attempt는 카드 작성이다: 유도 없이 `[공리: 후보]`로 선언, 숫자(또는 장부 항등식)·극한 복원·kill≥2·사다리≤7단 사전등록, sourcer 신규성 필수, judge adopt/refute. 그 뒤 attempt 하나가 사다리 한 단을 닫는다. 재발견(identical·special_case)은 정지가 아니라 확장 신호: 카드는 refute 후 더 강한 카드, 보조정리는 cited로 닫고 다음 단, 질문을 park하지 않는다. 재발견 2회·축소 4단계 소진이면 `force_pivot: conjecture`가 자동으로 붙는다. 틀릴 수 있는 만큼 강하게 세우고, 결과를 본 뒤 숫자·kill·tol을 바꾸지 않는다.

## 도메인 분기 (모든 연구 작업의 0단계)
**메인은 사용자가 정한 모델(Fable)로 두고, 생물 내용은 읽지 않고 위임한다.** `model-gate` 훅이 UserPromptSubmit에서 생물 표지를 보면 메인 문맥 맨 앞에 위임 지시를 넣는다(차단 없음). 메인은 파일 경로만 넘기고 마지막 json만 받는다. 생물 원문을 읽어야 하면 bio-reader에 시킨다.
**답변 용어 예산(Stop 훅이 강제).** 사용자에게 쓰는 글도 전사에 쌓여 매 턴 다시 들어간다. `bio-budget` 훅이 마지막 답변의 도메인 표지를 세어 종류 6·총 14를 넘으면 턴 종료를 막는다. 삭제가 아니라 **환원**으로 고친다. 구체 명칭·측정 서술을 중립어(자료, 구조 변수, 채널, 전담 보고)와 파일 경로로 바꾸고 숫자는 짧은 표로 남긴다. 정보는 파일에 다 있으므로 사용자가 잃는 것은 없다.
**메인 문맥 위생(협상 불가).** 생물 전담이 돌려주는 것은 `{artifact, verdict, numbers, next}` 네 키뿐이고 전체 표·반례·문헌·스키마는 파일에만 둔다. 메인은 그 본문을 읽거나 붙여넣지 않는다. 사용자 요약도 숫자·판정 위주로 짧게 쓰고 자료·기록 절차의 서술을 옮기지 않는다. 본문이 쌓이면 제공자 안전장치가 턴을 끊는다.
**첫 호출은 `domain-classifier`(opus)다.** 이 작업이 생물학인지 판별해 `verify/_routing/<session_id>.json` 영수증을 남긴다. 영수증 없이 연구 역할을 부르면 훅이 막는다. 판별 기준: 실제 생물 자료를 쓰거나 명명 · 생물 기전·생리·가소성을 주장 · 생물 문헌을 증거로 인용 · `BIO_EVIDENCE_*`가 걸린 주장. **섞이면 bio가 이기고, 애매하면 bio다.**

## 에이전트 (위임만 수행, 카드 읽기 금지, 마지막 json만 전달)
| 역할 | nonbio(수학·물리·컴공) | bio(전부 opus) |
|---|---|---|
| 추측·유도 | prover(inherit) | prover-bio |
| 감사 | adversary(inherit) | adversary-bio |
| 판정·원장 | judge(sonnet) | judge-bio |
| 문헌·신규성 | sourcer(haiku) | sourcer-bio |
| 원장→원고 | paper-writer(sonnet) | paper-writer-bio |
| 자료 읽기 | — | bio-reader |

생물 도메인은 전담이 맡는다. 도메인이 bio인데 비-생물 역할을 부르거나, 프롬프트에 생물 내용이 있는데 전담·opus가 아니면 차단이다. bio 카드들은 `.claude/agents/<역할>.md`의 계약을 읽고 그대로 따르되 생물 전용 규칙(estimand 선언, 채널 식별 인증서, 위약 1급, 선택·대비 분리, N 선등록, 관측량·영점, 모든 상수 카드 이관)을 더한다.

## 루프
한 세션 = 한 attempt. 카드 attempt: prover(추측)→adversary(카드 감사)→sourcer(신규성)→judge(adopt|refute). 사다리 attempt: prover(유도·수치)→adversary→(sourcer)→judge(promote 단 닫힘|continue|pivot|refute kill). Stop 훅이 원장 항목을 요구(3회 후 INCOMPLETE).
L0~L4(evidence-ladder). **L3 이상만 논문 인용.** 반례는 축소 pivot(partial→alt_derivation→reformulate→weaken), 재발견은 확장 pivot(conjecture→generalize). 탐색 fail-open, 논문 fail-closed.

## 라우팅
spot(단순 질문·한 줄 수정·하네스 최소 수정, 스킬 없음) · /attempt · /conjecture · /paper · /explain-plan · /audit /dim /validate · /status /gc. 코드(examples·tests)는 메인이 직접, 가장 작은 검증 하나.

## 명령 (정책 허용 시스템 Python만, `.venv`·uv·pip install·대화형 프롬프트 금지)
    .claude\hooks\python.cmd doctor|harness|source <p>|pytest <t> -q|links [--strict]|lint
    .claude\hooks\python.cmd python .claude\hooks\lib\ledger.py summary|validate <f>|check-current|next-question|bump-attempt <Q>|after-attempt <Q> <N>|ladder <Q>|card-check <f>|reindex
    scripts\research-loop.cmd [--max-iters N] [--question Q] [--dry-run]
전체 pytest는 사용자가 `전체`/`full` 명시 때만. sympy 없으면 symbolic skipped(최고 L2).

## 운영 (Fable 5.1 지침 반영, 2026-09-04)
서브에이전트를 띄운 뒤 **블로킹으로 기다리지 않는다.** 독립 작업을 계속하고 결과는 알림으로 받는다. 독립적인 도구 호출은 한 응답에 묶는다. 파일은 전체 재작성 대신 필요한 부분만 수정한다. 요청 범위 밖의 정리·최적화·추가 테스트는 하지 말고 마지막에 제안만 한다. 다음 단계를 설명만 하고 턴을 끝내지 않는다. 이미 정한 단계는 실행한다. 압축 요약에는 제약·결정·정확한 숫자·미해결 항목을 원문 표현으로 보존한다.

## 정직성 (협상 불가)
서브에이전트 프롬프트·문서·명령은 `safety-screen` 훅이 먼저 본다. **도메인 판별 영수증 없이 연구 역할을 부르면 차단**이고, **생물학 내용은 생물 전담(opus)으로만 간다**(`subagent_type: *-bio`·`bio-reader` 또는 `model: opus`). 표적 밖 위험 범주와 모델 내부 추출 요구는 차단(우회 없음), 과대 프롬프트는 경고다. 긴 근거는 프롬프트에 붙이지 말고 `verify/` 경로로 넘긴다.
실패를 통과로 쓰지 않는다. 안 돌린 검증을 돌렸다고 쓰지 않는다. 기계 문자열(pass/PASS)을 `paper/`에 지위처럼 쓰지 않는다.
지위는 정의·정리·공리·산출·경험식·미완성·예측 7종뿐(채택 카드는 `[공리: 후보]`, 그 숫자는 `[예측: 사전등록]`, 사다리 완주 뒤 `[정리]`). 관측 근접은 증명이 아니다. 진전은 예측(카드 채택)·닫힘·기각·축소 넷(새 장·항목·게이트 분할은 개시·정리). 하위 게이트 3개 초과면 §2에 택일 기록 후 진행. tolerance·fixture·seed·예측 숫자·kill은 결과 본 뒤 안 바꾼다.

## 한국어·논문
툴 호출 사이 한국어 1–3문장. 판단 설명은 목표 계약→1학년 LaTeX→비유→정렬→지위. `paper/`는 결과 먼저, 과정·식별자 금지, 영어는 첫 등장 병기 후 한국어, 장 머리 세 줄 상자. 종료 전 진전 원장 §2·§7 갱신 + `links`.

## Git
루트 `AGENTS.md` main-only. subagent는 commit/push 금지. 발행은 명시 지시 때만, `check-large-data.cmd --commit/--push`. force push 금지. 메시지 `<종류>: <항목> — <한 줄>`(예측·닫힘·기각·축소·개시·정리·하네스), "new" 금지.
