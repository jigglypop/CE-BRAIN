# ce-agi-runtime

CE-AGI 런타임 도메인 레포 — canonical Layer A-F(runtime.py, engine.py, sleep.py),
docs/7_AGI 전체, experiments(run 부산물 76종), 브리지·world-memory 복합체,
봉인 pinned run 2종(agi-world-memory-v1, agi-v18b), Rust 커널을 담는다.

- 이력 출처: ce-monorepo @ bca0df1, git filter-repo (2026-08-23). 타 도메인 대형
  이력 blob(연구 zip/mat, viewer 빌드, guard 벤치 데이터)은 이 레포 이력에서 제거 —
  유일본 이력은 모노레포 아카이브가 보존한다.
- 완결 run 증거: `tests/_run_paths.run_dir` 가 live -> 로컬 _archive -> `CE_RUNS_PATH`
  (기본: 형제 ../ce-runs) 순으로 해석한다.
- **알려진 한계**: run artifact JSON류는 모노레포 .gitignore 정책상 git 이력에 없다
  (디스크 전용). ce-runs에는 stage md만 있으므로, artifact 해시를 대조하는 테스트의
  완전 재현에는 `CE_RUNS_PATH=<모노레포 루트>` (디스크 사본 보유 머신) 또는 데이터
  재취득이 필요하다.
- 타 도메인으로 추출된 모듈(코어 5, 양자 10, 우주론 registry, lab 계열)의 사본이
  과도기적으로 남아 있다 — clarus-core 등 의존성 교체가 후속 작업이다 (MULTIREPO_PLAN.md).
- 뇌 주장 금지: supported_phenomena(ce-brain-bio 발행)에 L4 행이 있을 때만 뇌 문구 인용 가능.

검증: `CE_RUNS_PATH=<...> .claude/hooks/python.cmd pytest tests -p no:cacheprovider -q`
