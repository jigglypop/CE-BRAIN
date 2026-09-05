# 필요한 역할 네 개

주 에이전트 Astra가 목표·유도·통합·최종 설명을 담당한다. 아래는 필요한 경우에만 쓰는 보조 역할이다.

| 역할 | 모델 | 하는 일 |
|---|---|---|
| [reader](reader.toml) | Luna | 파일·출처·자료 구조 확인 |
| [implementer](implementer.toml) | Terra | 배정된 구현과 관련 검사 |
| [reviewer](reviewer.toml) | Astra | 핵심 수학·기전·반례 감사 |
| [explainer](explainer.toml) | Terra | 진행 중인 기전 설명·문서 초안 |

생물·일반 역할을 별도로 나누지 않는다. 기존 분류·출처·자료 읽기는 reader, 감사·판정 검토는 reviewer, 문서 작성은 explainer로 합쳤다. 유도와 최종 판정은 주 에이전트가 맡는다.

호출·파일 소유권·설명 주기는 [공통 운영 규칙](../harnesses/agent_policy.md)을 따른다. 네 역할을 매번 모두 호출하지 않는다.
