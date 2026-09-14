# 데이터 원장

다운로드 전에 여기서 보유 자료를 찾는다. [원장 본체](data_registry.jsonl)는 한 줄에 등록 기록 하나를 저장한다. 기록은 삭제하지 않으며 같은 자료·판본·파일·경로의 마지막 기록을 조회한다. 이 원장은 보유 상태를 관리한다. 과학적 적격성은 각 질문의 분석 기록에 남긴다.

기존 폴더는 위치만 등록했다. 원자료·코드·결과만 있는 폴더가 섞여 있으므로 파일 보유나 분석 가능성을 보장하지 않는다. [기존 재고 조사](../verify/Q-NPF-03/local_data_inventory.md)는 당시 질문에 대한 참고 기록이다. Randi OSF 자료의 두 폴더는 같은 자료 ID로 묶었으나 파일 단위 동일성은 아직 확인하지 않았다.

저장소 루트에서 실행한다.

```powershell
# 출처·자료 ID·판본·파일명·해시·경로 검색
.codex/hooks/python.cmd python .codex/hooks/data_registry.py find allen_synphys

# 필요한 파일만 해시 재검증
.codex/hooks/python.cmd python .codex/hooks/data_registry.py find synphys_r2.1_small.sqlite --verify

# 새 파일 등록: 실제 경로·출처·이유로 바꿔 실행
.codex/hooks/python.cmd python .codex/hooks/data_registry.py register --dataset DATA_ID --version VERSION --asset FILE --path LOCAL_FILE --source SOURCE_URL --reason "처음 수집"
```

폴더 또는 미완료 파일의 위치를 남길 때는 `register`에 `--location-only`를 붙인다. 판본이나 출처를 확인하지 못했으면 `unknown`으로 명시하고 후속 확인 때 새 기록을 남긴다. 같은 자료·판본·파일에 다른 해시는 자동 덮어쓰지 않는다. 먼저 손상이나 판본 변경을 확인한다. 원장 쓰기는 주 에이전트가 직렬로 수행한다.

| 조회 상태 | 뜻과 다음 행동 |
|---|---|
| `location_only` | 위치만 확인. 폴더 안 목록·수집 영수증을 먼저 확인 |
| `partial` | 미완료 파일 있음. 실행 중인지 확인하고 중복 다운로드 금지 |
| `unchanged_metadata` | 등록 당시 해시가 있고 현재 크기·수정시각이 같음. 현재 해시 일치를 재검증한 것은 아님 |
| `hash_match` | 이번 조회에서 등록 해시와 일치 확인 |
| `changed` | 파일 변경 감지. 사용 전에 판본·무결성 확인 |
| `missing` | 등록 경로가 없음. 다른 위치를 먼저 찾은 뒤 필요하면 재수집 |

도구는 네트워크 접속·다운로드·삭제를 하지 않는다. `find` 결과가 없더라도 다른 이름의 자료와 미등록 파일을 확인한다. 동일 해시 검색으로 다른 이름·위치의 복사본도 찾을 수 있다. 서버가 제공한 체크섬과 별도로 대조하지 않았다면 로컬 해시 등록만으로 서버 원본과의 일치를 주장하지 않는다.

## MaleCNS 보유 자료 (2026-09-14)

`.gitignore`의 `/data/` 때문에 일반 `rg --files`에서 빠지지만 실제 로컬 자료는 있다.
자료 ID `malecns`, 판본 `v1.0`으로 네 위치와 11개 파일을 등록했다. 새 다운로드는 없다.

| 위치 | 보유 내용 | 사용 전 구분 |
|---|---|---|
| `data/local/malecns-v1.0` | annotation, NT prediction, segment 연결표와 source lock | 원본 3개 해시를 기존 lock과 대조 |
| `data/local/malecns-v1.0-flat-connectome` | 공식 객체 11개, 31,318,683,398 bytes, generation별 manifest | 파일 존재·크기와 중복 핵심 3개 해시 확인; 31 GB 전량 재해시는 하지 않음 |
| `data/local/malecns-full` | 199,713개 non-Glia annotation의 incoming CSR | 미분류 body 포함, 게임용 부호 가정 |
| `data/local/malecns-neurons166k` | superclass가 지정된 166,700개 노드의 incoming CSR | 좌표 없음, 0 부호는 미확정 효과이며 연결 부재가 아님 |

성체 수컷 CNS 자료다. 공유 대화의 유충 Kenyon 64개 전사 부분망과 같은 표본으로 합치지 않는다.
파일·스키마·결측 및 전체 CNS 입력의 적격성은 별도 [MaleCNS 원장](malecns_inventory.md)에 정리했다.

## MaleCNS 후속 분석 (2026-09-14)

자료 ID `malecns-analysis`로 전체 행의 범주 집계 배열, 구조 결과, type source-LOO,
48회 label 대조, 실행 notebook·HTML·그림 3개를 등록했다. 원자료의 새 다운로드가 아니라
보유 MaleCNS v1.0에서 계산한 파생물이다. 배열은 `data/local/malecns-analysis/`,
작은 결과·소스·그림은 `verify/MaleCNS/`에 있다. 질문·수식·양성/음성 관측·해석 한계는
[별도 분석 원장](malecns_structure_findings.md), 서술은 [논문 결과 장](../paper/6_뇌/13_MaleCNS_전체망_기하와기억/05_실제전체망_첫관측.md)에 둔다.

후속 `raw-dyad-return-v1`은 전량 고유 dyad·역방향 연결·실제 ID 두 단계 경로를 계산한
캐시 3개, 결과 JSON, 실행 notebook·HTML·그림 2개를 보관한다. 중복 dyad는 0개이며
모든 원시 분절은 정렬 캐시에 남아 있다. 방법·분모·해석 한계는
[ID 경로 원장](malecns_dyad_return_findings.md)에 별도로 둔다.

2026-09-15 등록한 `hidden-walk-v1`은 같은 전량 연결의 active 희소 전이·terminal 경계·
source 사상·27쌍 probe 궤적의 NPZ 4개와 완료 JSON이다. `hidden-walk-companion-checked-v1`에
실행 notebook·HTML·검수 그림 3개를 따로 등록했다. 초기 그림의 공유 y축 잘림은 원자료나
수치 결과를 바꾸지 않고 교정했으며, 기존 5개 산출물은 `hidden-walk-companion-initial-v1`에
현재 읽기본으로 부적합한 이유와 함께 보존한다. 해시 등록은 파일 정체성 확인이지 과학적
적격성 판정이 아니다. 수치·음성 사례·관측 범위·검수 이력은
[숨은 경유와 미래 정보 원장](malecns_hidden_walk_findings.md)에 별도로 둔다.

같은 날 `observation-memory-v1`에 60출력·투영 기억의 결과 JSON과 NPZ를 등록했다.
검수 notebook·HTML·그림 3개는 `observation-memory-companion-checked-v1`, 초기 눈금
겹침을 보존한 읽기본 5개는 `observation-memory-companion-initial-v1`로 구별한다.
전량 관측 재현·이력 길이·초기항·음수 예측의 실패는
[관측과 이력 축약 원장](malecns_observation_memory_findings.md)에 둔다. 추가 원자료
다운로드는 없으며 기존 raw 연결·흡수 경계 연산자를 그대로 재사용했다.

후속 `connection-fisher-v1`에는 고정 초기분포에서 세 공유 log-efficacy 좌표를 바꾼
전량 Jacobian·endpoint Fisher·여섯 유한차분 대조의 완료 JSON과 NPZ를 등록했다.
정규화의 공통 배수 영방향, 관측별 수치 rank, terminal 압축 셀 수의 필드명 한계와
과학적 주장 범위는 [연결 효능 원장](malecns_connection_fisher_findings.md)에 둔다.
전체 연결을 보존한 세 좌표의 L0 분석이며 모든 연결을 독립 파라미터로 탐색한 것은 아니다.
검수 notebook·HTML·명칭을 명확히 한 summary·그림 3개는
`connection-fisher-companion-v1`에 등록했다. 코드 셀 4개와 PNG 시각 검수는 완료했지만,
사용 가능한 브라우저가 없어 HTML 브라우저 레이아웃 검증은 하지 않았다.

재다운로드는 누락·손상·다른 판본·재개 불가 등 이유를 기록하고 진행할 수 있다. 재검토도 가능하며 질문·이유·데이터 ID·이전/새 결과를 분석 기록에 남긴다. 자세한 기준은 [데이터 관리 규칙](../.codex/harnesses/data_policy.md)을 따른다.
