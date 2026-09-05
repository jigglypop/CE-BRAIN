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

재다운로드는 누락·손상·다른 판본·재개 불가 등 이유를 기록하고 진행할 수 있다. 재검토도 가능하며 질문·이유·데이터 ID·이전/새 결과를 분석 기록에 남긴다. 자세한 기준은 [데이터 관리 규칙](../.codex/harnesses/data_policy.md)을 따른다.
