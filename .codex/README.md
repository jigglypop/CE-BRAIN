# CE Codex 하네스 안내

이 디렉터리는 논문 본문과 분리된 판정 규칙·실행 하네스의 입구다. 실제 결과와
형식 검증을 같은 증거로 세지 않도록, 각 하네스는 입력 잠금, 실행 영수증,
승격·정지 조건을 명시해야 한다.

현재 정본:

- [뇌 생물학 증거 사다리](harnesses/brain_evidence_ladder.md) —
  `BIO_EVIDENCE_L0`–`L4`의 필요조건과 통합 주장 합성 규칙
- [실제 뇌 식 기반 발견 루프](harnesses/real_brain_equation_discovery_loop.md) —
  생물 기준식·CE 추가항·측정모형, 다운로드 전 eligibility, 실데이터 endpoint와
  L4 매개 판정 순서
- [실측 교정 루프](harnesses/empirical_calibration_loop.md) — 불일치의
  D→I→P→C→B→T 분류와 사후 구제 금지 규칙

현재 실행 진입점:

- Windows Python은 `hooks/python.cmd doctor|python|pytest`를 사용한다. 이미
  허용된 system Python만 선택하며 venv 생성·패키지 설치·정책 우회를 하지 않는다.
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
