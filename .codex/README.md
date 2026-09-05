# Codex Astra 하네스

[기본 지침](../AGENTS.md)은 작업 방식, 이 문서는 필요한 도구와 세부 규칙의 입구다. `.claude/`는 별도 실행기 설정이며 그 모델·위임·출력 예산을 Codex에 적용하지 않는다.

[저장소 설정](config.toml)의 기본 모델은 `gpt-6-astra`다. 추론 강도와 권한은 사용자 설정을 따른다. 프로젝트 설정은 신뢰된 저장소에서 적용되며 실행 시 명시한 설정이 우선할 수 있다. 모델 설명은 [공식 Astra 안내](https://developers.openai.com/api/docs/guides/latest-model), 설정 적용 순서는 [공식 설정 안내](https://learn.chatgpt.com/docs/config-file/config-basic)를 참고한다.

연구 목표는 [PRD](PRD.md)에 고정한다. 주 에이전트는 Astra, 단순 확인은 Luna, 일반 구현·초안은 Terra를 사용한다. [에이전트 운영 규칙](harnesses/agent_policy.md)에 호출·승급·설명 기준이 있다. 실제 역할 설정은 `agents/*.toml`이며 생물 작업을 무조건 고비용 모델로 보내지 않는다.

## 자료를 찾거나 다시 검토할 때

[데이터 원장](../ledger/data_registry.md)을 먼저 검색하고 보유 자료를 재사용한다. 없는 자료는 요청 범위 안에서 찾아 받으며, 재다운로드 이유를 남긴다. 재검토·재분석도 허용한다. [데이터 관리 규칙](harnesses/data_policy.md)에 수집·재사용·재검토 기준이 있다.

과거의 `PUBLIC_DATA_SUFFICIENCY_FROZEN`은 해당 계약의 판정이다. 공개자료 전체의 다운로드·재검토 금지가 아니다. 기존 봉인 기록을 보존하며 새 질문과 결과를 구분한다. 성체 L4 연구실 입력·인계 스키마의 통과도 생물학적 결과나 외부 실행 허가가 아니다. 필수 입력이 없으면 해당 결과는 미실행으로 남긴다.

## 필요한 규칙만 읽기

- [실제 뇌 발견 루프](harnesses/real_brain_equation_discovery_loop.md): 연구 계약, 질문별 자료 적격성, 실행과 결과 판정.
- [생물학 증거 사다리](harnesses/brain_evidence_ladder.md): L0–L4 조건과 주장 상한.
- [실측 교정](harnesses/empirical_calibration_loop.md): 구현·측정·이론 오류를 구분하는 절차.
- [문서 정책](harnesses/document_policy.md): 문서 유형, 링크, 원장과 논문, 독자 기준.
- [해시 잠금 소스와 부채](harnesses/known_debt.md): 수정하면 기존 증거가 깨지는 파일과 남은 문제.

## 실행 명령

저장소 루트에서 실행한다. 기본은 관련 검사 하나이며 전체 테스트를 자동 실행하지 않는다.

```powershell
.codex/hooks/python.cmd doctor
.codex/hooks/python.cmd pytest tests/test_data_registry.py
.codex/hooks/python.cmd python .codex/hooks/repository_harness.py
.codex/hooks/python.cmd python .codex/hooks/data_registry.py find DATA_ID
```

네이티브 확장이 필요하면 `.codex/hooks/build-native.cmd`를 사용한다. 없으면 순수 Python 경로로 실행한다. 명시적으로 커밋·배포할 때는 `.codex/hooks/check-large-data.cmd --commit`과 `--push`로 대용량 파일을 검사한다.
