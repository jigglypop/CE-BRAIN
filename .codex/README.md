# CE Codex 하네스 안내

이 디렉터리는 논문 본문과 분리된 판정 규칙·실행 하네스의 입구다. 실제 결과와
형식 검증을 같은 증거로 세지 않도록, 각 하네스는 입력 잠금, 실행 영수증,
승격·정지 조건을 명시해야 한다. `.claude/`는 이 디렉터리의 얇은 미러이며 규칙 본문을
갖지 않는다.

현재 정본:

- [뇌 생물학 증거 사다리](harnesses/brain_evidence_ladder.md) —
  `BIO_EVIDENCE_L0`–`L4`의 필요조건과 통합 주장 합성 규칙
- [실제 뇌 식 기반 발견 루프](harnesses/real_brain_equation_discovery_loop.md) —
  생물 기준식·CE 추가항·측정모형, 다운로드 전 eligibility, 실데이터 endpoint와
  L4 매개 판정 순서
- [실측 교정 루프](harnesses/empirical_calibration_loop.md) — 불일치의
  D→I→P→C→B→T 분류와 사후 구제 금지 규칙
- [문서 정책](harnesses/document_policy.md) — 링크 정책(깨진 링크 제거, `_workspace`
  링크 금지), 수기 누적 문서의 논문화(`00_논문목차.md` 폴더), 문서 유형과 처음 읽는
  독자 게이트, direct 모드 소유권

현재 실행 진입점:

- Windows Python은 `hooks/python.cmd doctor|python|pytest`를 사용한다. 이미
  허용된 system Python만 선택하며 venv 생성·패키지 설치·정책 우회를 하지 않는다.
- 저장소 배치·문서 정책 검사기는 `hooks/repository_harness.py`다
  (`python.cmd python .codex/hooks/repository_harness.py`;
  `tests/test_canonical_document_policy.py`가 같은 검사를 단언한다).
- 커밋·푸시 전 대용량 blob 게이트는 `hooks/check-large-data.cmd --commit|--push`다
  (`hooks/check_large_data.py`, 95 MB 초과 또는 `_workspace/` 아래 데이터 확장자를 차단).
- 선택적 네이티브 확장 빌드는 `hooks/build-native.cmd`다. 두 pyo3 크레이트
  (`reality_stone/` → `reality_stone._rust`, `reality_stone/python/reality_stone/clarus/core/`
  → `reality_stone.clarus._rust`)를 cargo로 빌드해 패키지 옆에 놓는다. 빌드하지 않으면
  모든 소비자가 순수 Python 경로로 동작한다.
- 성체 L4의 첫 lab gate는
  [`adult_l4_same_contact_tool_development_schema_v1.json`](../paper/6_뇌/국소회로_상태다양체_흐름_대응/repro/adult_l4_same_contact_tool_development_schema_v1.json)과
  [`preflight_adult_l4_same_contact_tool_development_v1.py`](../paper/6_뇌/국소회로_상태다양체_흐름_대응/repro/preflight_adult_l4_same_contact_tool_development_v1.py)다.
  입력이 없을 때는 `DEVELOPMENT_SCHEMA_PASS_LAB_INPUT_REQUIRED`까지만 허용한다.
  이 계보는 `PUBLIC_DATA_SUFFICIENCY_FROZEN`이다. 사용자가 특정 자료와 목적을 다시
  승인하기 전에는 신규 공개자료 다운로드·자료 충분성 재감사를 하지 않는다.
  외부 연구실 인계 정본은
  [`adult_l4_same_contact_lab_handoff_v1.json`](../paper/6_뇌/국소회로_상태다양체_흐름_대응/repro/adult_l4_same_contact_lab_handoff_v1.json)과
  [`validate_adult_l4_same_contact_lab_handoff_v1.py`](../paper/6_뇌/국소회로_상태다양체_흐름_대응/repro/validate_adult_l4_same_contact_lab_handoff_v1.py)다.
  `LAB_HANDOFF_SCHEMA_PASS_EXTERNAL_ACTION_REQUIRED`는 실행허가나 생물학적 결과가 아니다.
- 하네스가 없거나 실행 영수증이 재현되지 않으면 `미실행` 또는 `장치 차단`으로
  기록하며, 생물 가설의 양성·음성 결과로 바꾸지 않는다.

## 해시 잠금 소스 (수정 금지)

`artifacts/**/*.json`과 `experiments/preregistration/*.json` 영수증이 SHA-256을 기록한
파일은 내용을 바꾸면 증거 사슬이 끊긴다. 리팩터링·중복 제거 대상에서 제외한다.

- `reality_stone/python/reality_stone/clarus/`: `sparse_causal_bridge.py`,
  `latent_causal_bridge.py`, `free_rollout_bridge.py`, `reliability_rollout_bridge.py`,
  `parent_anchored_rollout_bridge.py`, `episodic_ltm_dream_bridge.py`,
  `episodic_ltm_dream_bridge_v2.py`, `agi_world_memory_integration_v3.py`, `local_memory.py`,
  `quantum.py`, `constants.py`, `dual_scc_basal_ganglia.py`, `dual_scc_controller.py`,
  `dual_scc_probe_benchmark.py`, `causal_recurrent_geometry_benchmark.py`
- `clarus/experiments/`: `runtime_metric_intervention(_benchmark).py`,
  `runtime_metric_sufficiency(_benchmark).py`, `runtime_metric_memory_diagnostic.py`,
  `runtime_prediction_guided_metacontrol.py` (자기 소스를 freeze manifest에 해시)
- `origin_life_*.py` (`inspect.getsource` 자기 해시)
- `examples/agi/*_gate.py`, `examples/brain/ce_brain_*.py`, `tests/test_ce_brain_*.py`,
  `tests/test_*_bridge.py`, `tests/test_episodic_ltm_dream_bridge*.py`,
  `tests/test_agi_world_memory_integration*.py`, `tests/test_dual_scc_*.py`
- `.gitattributes`가 `eol=lf`로 고정한 체인 전체

## 부채 (2026-09-02 정리 후 남은 항목)

Rust

- 두 크레이트 모두 pyo3 0.21의 GIL-Ref API(deprecated)를 쓴다. `reality_stone/src/lib.rs`는
  `#![allow(deprecated)]`로 경고를 숨기고, `clarus/core`는 경고를 그대로 낸다. Bound API
  이행은 미착수다.
- `reality_stone/src/ops/metrikey.rs`는 입력 검증을 `assert!`(약 35곳)로 하므로 잘못된
  입력이 Python `PanicException`으로 나온다. 바인딩 계층 검증으로 옮겨야 한다.
- `reality_stone/src/layers/cuda/*.cu` 안의 `geodesic_topk_attention_fp16_kernel`,
  `spline_gemm_fp16_kernel`, `poincare_riemannian_adam_cuda`는 launch 코드가 없다.
  nvcc가 없는 환경이라 CUDA 빌드 전체가 미검증이다.
- `reality_stone/src/layers/rsulf.rs` forward의 인과 계량 어텐션은 O(N²d²) 삼중루프다.

Python

- `clarus/experiments/runtime_{metric_intervention,metric_sufficiency}_benchmark.py`,
  `runtime_metric_memory_diagnostic.py`, `runtime_prediction_guided_metacontrol.py`,
  `realdata_transport_composition.py`는 `_workspace/ce/...` 계약 파일을 읽는다. 해당
  모듈이 freeze manifest에 자기 해시되어 있어 경로를 바꾸면 봉인이 깨진다. `ce-runs`가
  있을 때만 실행되는 fail-closed 동작으로 둔다.
- `verified_*`·`quantitative_*` 95개 파일의 `if __package__:` import 관용구와 자체 해시·
  유리수 파서 헬퍼 중복은 테스트 로더(`spec_from_file_location`) 구조 때문에 유지한다.
  해시 잠금 모듈의 ridge·해시 헬퍼 중복도 봉인 때문에 통합하지 않는다.
- `models/hierarchical_sentence_topic_llm.py`는 기본값으로 HF `klue/bert-base`를
  내려받고, `clarus/sleep.py:74`는 HF 데이터셋 이름을 하드코딩한다.
- `reality_stone/tests/`의 CUDA·네트워크 테스트(gpt2 다운로드, Qwen opt-in)가 루트
  `testpaths`에 포함된다.
- `experiments/preregistration/cosmology_future_holdout_v*.json`은 2026-08-23 물리 트랙
  분리로 사라진 `examples/physics/` 입력을 동결하고 있다. 자기 해시 때문에 편집할 수 없어
  `tests/test_holdout_preregistration.py`의 두 검사를 `xfail(strict=True)`로 기록했다.
- `tests/test_ba_obs_hpc3_author_qc_transaction.py`가 읽는 hpc3 run은 `ce-runs`의
  `_archive`에도 없다. 모듈 수준 skip으로 두었고, 증거가 복원되면 자동으로 다시 실행된다.
- `clarus/core` 크레이트의 `cargo test` 실행 파일은 이 머신의 Windows Application Control이
  차단한다(os error 4551). 컴파일은 통과하며 우회하지 않는다.

문서

- `paper/7_AGI` 번호 21·22·32–40이 비어 있다. 21은 `검증_원장/AGI_STDP_Efficacy_Audit.md`,
  22는 `검증_원장/AGI_CloudCell_Monad_Audit.md`로 옮겨진 것으로 보이며 32–40의 행방은
  기록이 없다.
- 2026-08-23에 삭제된 물리 트랙 경로(`examples/physics/`, `examples/ai/`, `scripts/`)의
  백틱 인용이 본문에 약 40건 남아 있다. 링크가 아니므로 검사기는 잡지 않는다.
- `paper/7_AGI/19_OOD_Generalization.md` 본문 수치는 `experiments/RESULTS_ood_length.md`
  재현과 어긋난다. 상단에 재현 결과 주석만 두었고 본문은 원 run 기록으로 남겼다.
- DISC2R 환자 수가 `README.md`(74명)와 `검증_원장/BA_CCEP_경로트리.md`(73명)에서 다르다.
- `paper/6_뇌/12_리만부분공간_의식순간_강화/`는 1차 구조 전환만 끝났다. 2차 서사
  재작성과 처음 읽는 독자 게이트가 남아 있다. `검증_원장/리만부분공간_의식순간_주장원장.md`
  (333 KB)는 수기 누적 원장이며 스크립트 생성이 아니다.

Git

- 커밋 304건 중 164건의 제목이 `new`다. 이력은 재작성하지 않고, 앞으로의 커밋만
  의미 있는 제목을 쓴다.
