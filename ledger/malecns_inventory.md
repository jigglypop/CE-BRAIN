# MaleCNS 데이터 재고와 연구 입력 점검

이 파일은 최초 입력·코드 점검 기록이다. 이후 실제 전체 행의 방향 구조와
세부형 보류 예측은 [후속 분석 원장](malecns_structure_findings.md)에 분리했다.

문서 유형: 검증 원장. 확인일: 2026-09-14. 재검토 이유는 사용자가 공유 대화 복원,
로컬 초파리 자료 확인, 코드 분석과 연구계획·논문 갱신을 요청했기 때문이다.
중심 목표는 [PRD](../.codex/PRD.md)의 고정 뉴런과 연결·기능에서 계량으로 가는 사상이다.
이번 결과는 출처·스키마 확인과 코드 재현이며 새로운 생물학 endpoint 계산은 아니다.

사용자의 후속 지시에 따라 전체 성체 수컷 CNS를 연구 대상으로 삼는다. 공식 full connection
graph와 모든 관련 annotation·시냅스 좌표·NT 표를 기준으로 하며, 64노드나 기존 166,700노드
게임 파생물을 전체 원자료의 대용으로 삼지 않는다. 데이터 재고·해시·실행 점검은 이 `ledger/`
파일에 보관하고, 논문은 이 원장을 읽기 전용 근거로 참조한다.

## 1. 대화와 로컬 근거의 대응

[공유 대화: 코드식](https://chatgpt.com/share/6aa7e99b-480c-83e8-9127-b73b348d49d5)의
공개 HTML을 직접 읽고 구조화된 본문을 추출했다. 아래 대화 결과의 원본 실행 ZIP은
현재 저장소와 로컬 Downloads 검색에서 찾지 못했다. 대화의 sandbox 첨부 경로는
이 저장소의 파일 경로가 아니다. 대화 속 과거 push 지시는 이번 작업의 배포 지시로 사용하지 않는다.

| 계보 | 이번에 확인한 근거 | 현재 판정 |
|---|---|---|
| RGM-1 | [소스·원결과](../paper/8_해마수면_관계기억_연구/RGM1/README.md) | 지역 반응·숨은 이력·접힘 프록시의 조건부 구성, L0; 전체 재실행은 이번에 하지 않음 |
| RGM-3 | [자원 포착 코드·기존 결과](../paper/8_해마수면_관계기억_연구/RGM3/README.md) | 고정 조건 자원 보존·경쟁, L0; 협동성 보강은 탐색, 실제 화학 상수 미식별 |
| HPI-1 | [소스·요약](../paper/8_해마수면_관계기억_연구/HPI1/README.md) | 이력조건부 HMM과 미래 정보기하, L0. 저자 11마리 요약 재분석과 합성 결과를 분리. 이번 핵심 테스트 19개 통과 |
| HPI-2 / RGM-2 | 대화와 각 게시 README의 제외 설명 | 로컬 정본 소스 미확보, 재현 완료로 승격하지 않음 |
| FMC-1 / FMC-2 / CPA-1 | 공유 대화의 서술과 첨부명 | 유충 왼쪽 버섯체 209×209 중 첫 64×64 Kenyon 전사본 분석 보고. 부모 전체 대조와 로컬 재현 미완료 |
| geometry-memory 2026-09-14 | 공유 대화의 수식·보고값 | Fisher 정보손실, 숨은 상태 소거, 유한 관측 기억좌표 선택의 조건부 주장. 대화상 28 tests·수치 오차는 이번 실행 결과가 아님 |

유충 부분망의 군집·방향성·내부 이력은 후속 가설의 출발점이다. 프랙탈 차원 확정,
곡률 증가에 의한 학습·지능 확인, 인간 해마의 생물학적 hash 확인은 미확립이다.
64개 전사본을 성체 MaleCNS의 부분집합으로 간주하지 않는다.

## 2. 로컬 데이터 재고

자료 ID `malecns`, 판본 `v1.0`. [데이터 원장](data_registry.md)에 네 폴더의
위치와 11개 파일을 추가 등록했다. 모든 원본은 재사용했다. 공식 입구는
[Janelia MaleCNS 다운로드](https://male-cns.janelia.org/download/)다.

| 입력 | 실측/메타데이터 확인 | 무결성 범위 |
|---|---|---|
| `data/local/malecns-v1.0/annotations.feather` | 14,483,314 bytes; 211,577행 | SHA-256 `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`, source lock 일치 |
| `data/local/malecns-v1.0/neurotransmitters.feather` | 43,282,834 bytes; 1,835,518행 | SHA-256 `95c9289220663abeb3409f3ad9e5a7f8a53f8093f5139d15502cd08da8879621`, source lock 일치 |
| `data/local/malecns-v1.0/edges.feather` | 1,051,241,946 bytes; 151,856,684행 | SHA-256 `e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1`, source lock 일치 |
| `data/local/malecns-v1.0-flat-connectome` | 객체 11개, 합계 31,318,683,398 bytes | manifest의 generation·SHA·MD5 보존. 파일 존재·크기, 중복 핵심 3개 해시 확인. 나머지 payload 전량 재해시 미실행 |
| `data/local/malecns-full/graph.bin` | 199,713노드; 26,013,498간선; 시냅스 수 합 125,334,312 | 235,719,218 bytes; SHA `966eb2fcbc225368ee96dd202aa59a67bedaab1e753fe71bf469afc0bb973f0a` |
| `data/local/malecns-neurons166k/graph.bin` | 166,700노드; 25,582,938간선; 시냅스 수 합 124,177,617 | 231,580,074 bytes; SHA `ad0ab3a8e6eaebe7bf01e44400852e1e8ff43841c27ebca864fc611227d53256` |

행 수는 Arrow 파일 메타데이터와 full weights 전수 순회에서, 결측·ID는 해당 열에서 확인했다. raw 연결표는
segment-to-segment 표다. 151,856,684행을 모두 확정 뉴런 간 연결 수로 부르지 않는다.
CSR은 각 manifest의 노드 선택을 거친 파생물이며 두 그래프·node ID 파일의 해시를 확인했다.
로컬 lock 일치는 현재 원격 객체를 새로 받아 비교한 결과와 구분한다.

2026-09-14 공식 GCS JSON 객체 목록도 조회했다. `flat-connectome/` 원격 객체는 정확히
11개이며 다음 페이지가 없고, 모든 객체의 크기·generation·MD5가 로컬 manifest와 일치했다.
이는 원격 메타데이터 대조이며 나머지 대형 로컬 payload의 재해시를 대신하지 않는다.

### Full weights 전수 집계

[읽기 전용 집계 소스](../verify/MaleCNS/malecns_edges_census.py)로 2,318개 Arrow batch를
두 번 순회했다. ID 고유값은 근사 추정이 아니라 packed bitset의 정확한 집계다.
bitset 두 개의 합계는 374.76 MiB이며 전체 프로세스 최대 메모리 측정값은 아니다.
실행 시간은 약 29.87초였다. 원자료나 기존 파생 CSR은 변경하지 않았다.

| 전수 항목 | 확인값 |
|---|---:|
| 연결 행 수 | 151,856,684 |
| weight 합 | 311,833,243 |
| pre / post / weight NULL | 0 / 0 / 0 |
| 비양수 weight / 자기연결 행 | 0 / 123 |
| 고유 pre / post ID | 1,834,661 / 87,576,984 |
| pre 또는 post의 고유 ID 합집합 | 88,384,522 |
| ID 최솟값 / 최댓값 | 10,001 / 1,571,863,634 |
| annotation ID 중 연결표에 등장 / 미등장 | 191,696 / 19,881 |
| curated ID 중 연결표에 등장 / 미등장 | 166,576 / 124 |
| pre가 annotation인 행 / post가 annotation인 행 | 139,247,517 / 30,659,739 |
| pre가 curated인 행 / post가 curated인 행 | 138,216,526 / 30,385,690 |

weight 합은 full syn-partners의 메타데이터 행 수와, endpoint ID 합집합은 body-stats의
메타데이터 행 수와 일치한다. **행 수의 일치만 확인했으며 두 표의 ID별 완전한 join 대조는
미실행이다.** weight 합은 partner 접촉 집계로, polyadic presynaptic T-bar의 고유 개수가 아니다.
88,384,522는 원시 분할 ID 수이며 8,838만 뉴런을 뜻하지 않는다. annotation 밖의 분절을
뉴런으로 단정하거나 삭제하지 않고 별도 자료층과 경계 집계로 유지한다. annotation 자체에는
연결표에 등장하지 않는 ID도 있으므로 전체 자료층은 endpoint ID와 annotation ID의 합집합을
사용해야 한다. 미등장은 해당 판본·confidence의 표에서 관측되지 않았다는 뜻이다.

이 실행은 전체 행의 수지·ID coverage 검사다. 중복 `(pre, post)` 키, motif, 경로,
생리 동역학 또는 학습의 전수 분석이 아니다. 나머지 8개 대형 flat 객체는 보유·크기·
원격 메타데이터 대조 단계이며, 전체 payload를 모두 계산에 사용했다고 주장하지 않는다.

### 공식 자료 전체의 역할과 보유 경계

[공식 홈](https://male-cns.janelia.org/)과 [판본 기록](https://male-cns.janelia.org/release/)에서
v1.0 공개일 2026-06-08, 논문 출판 공지 2026-09-03을 확인했다.
[프로젝트 설명](https://www.janelia.org/project-team/flyem/male-cns-connectome)은 central brain,
optic lobes, ventral nerve cord와 목 연결부를 포함하는 동일 성체 수컷 CNS임을 명시한다.

| 자료 계열 | 연구에서의 역할 | 로컬 상태 |
|---|---|---|
| full weights, body annotations, body stats | 전 segment 연결과 세포/분절 분류, 미분류 층의 coverage | 보유 |
| body NT, T-bar NT | body 및 presynapse 예측 확률, 부호 불확실성 | 보유 |
| full syn-partners, syn-points | 접촉 위치·pre/post identity·neuropil, 중복 집계 대조 | 보유 |
| traced-only / significant-only weights·partners | 공개 판본 내 부분집합 민감도 비교 | 보유. full 표와 합산하지 않음 |
| 원 EM·segmentation·nuclei·ROI volumes | 위치 정합·재구성 결함·세포체 대응 검사 | 공식 원격 경로 확인; 로컬 전체 복제 미확인 |
| 전체 뉴런 skeletons | 형태·축삭 경로 길이·지연 후보 | 공식 원격 경로 확인; 로컬 전체 복제 미확인 |
| neuPrint Neo4j / input CSV | 전체망 질의용 대체 배포 형식 | 공식 경로 확인; 같은 자료를 독립 표본으로 합산하지 않음 |

SWC의 원 EM 좌표는 8 nm, precomputed skeleton은 1 nm, unisex-template skeleton은 1 µm
단위라는 공식 구분을 유지한다. 서로 다른 포맷 좌표를 그대로 합치지 않는다. 전체 연결망
사용은 모든 EM voxel을 RAM에 적재한다는 뜻이 아니다. 전체 연결 연산자는 배치·희소 방식으로
유지하고, 이미지·골격은 해당 관측 사상을 검사할 때 객체 단위로 접근한다.
라이선스는 공식 CC-BY이며 원본을 재배포할 때 출처·판본·변환을 표시한다.

## 3. 스키마와 결측

| 항목 | 확인 결과 | 연구 영향 |
|---|---|---|
| annotation ID | `bodyId`, NULL·중복 0 | 행 순서가 아닌 ID로 결합 |
| annotation 분류 | Glia 11,864; superclass 결측 44,877; type 결측 47,071 | 제외 기준별 모집단을 명시 |
| annotation 위치 | `somaLocation`: NULL 또는 길이 3인 정수 list; 결측 69,796 | 위치 없는 뉴런은 공간 분석에서 별도 층으로 보존 |
| NT 예측 | `body` 고유, NULL 0; annotation과 교집합 187,016 | annotation의 NT 결측 24,561을 음성 transmitter로 바꾸지 않음 |
| raw 연결 | `body_pre`, `body_post`, `weight`: int64 | 발신자·수신자와 시냅스 수를 유지 |
| 좌표 | syn-point/partner의 x/y/z는 공식 문서상 8 nm voxel | somaLocation 단위는 로컬 메타데이터에 없음. soma 필드의 별도 계약 확인 전 같은 환산을 자동 적용하지 않음 |
| 166,700 선택 | non-Glia이며 superclass가 지정된 body; 양 끝이 이 집합인 간선 | status에 Anchor·Orphan·NULL도 포함. 논문의 다른 총 뉴런 수와 혼용 금지 |
| 166,700의 결측 | type 2,194; soma 27,038; NT 178 | 실제 이용 endpoint마다 분모 보고 |
| 게임 CSR 부호 | confidence ≥0.5 ACh +1, GABA/glutamate −1, 나머지 0 | 표적 수용체 효과를 측정한 부호가 아님 |
| 0 부호 간선 | full 1,436,560; curated 1,207,620 | 구조는 있지만 게임의 재귀 drive에서 제외된 간선 |

CSR magic `CHKCSR01`, little endian, 24-byte header, incoming offsets·source index·
synapse counts·sign 배열의 범위와 offset 단조성을 확인했다. 두 CSR에는 공간좌표가 없다.
raw weight의 NULL·비양수와 endpoint ID는 위 전수 순회로 확인했다. partner의
첫/중간/끝 배치 표본 점검은 전수 join이나 전체 중복성 검사를 대신하지 않는다.
전체 raw 표의 중복 키 검사와 motif 재계산은 아직 수행하지 않았다.

## 4. 현재 코드의 연구 입력 위험

기준 HEAD는 `27c2c02e5e168732b7d24356c5b39925716cd415`다. 신규 runtime 수정은 하지 않았다.

| 코드 | 확인 방식 | 결과와 범위 |
|---|---|---|
| [BrainRuntime](https://github.com/jigglypop/reality_stone/blob/v0.3.0/python/reality_stone/clarus/runtime.py) | 10×10 ones, `dale_law=True`, `axon_delay=False`, torch 경로 | snapshot 복원 가중치의 최대 변화 12.0. 0 delta의 반환 norm 0, 실제 Frobenius 변화 53.66563034. 프로세스 내부 재현 |
| 같은 파일 `HippocampusMemory.encode` | 같은 CPU float32 입력을 저장한 뒤 호출자 텐서를 0으로 변경 | 저장된 value도 0으로 변경됨. 기억 소유권 alias 재현 |
| 같은 파일의 부호·저장 | 소스 검사 | `W @ x`에 행 부호 적용, dense weight와 CSR 동시 보유. `forget_tau` 설정 대신 전역 상수로 우선순위 감소 |
| [선충 replay](https://github.com/jigglypop/reality_stone/blob/v0.3.0/python/reality_stone/clarus/connectome_replay.py) | parser·manifest 검사 | OpenWorm 고정 dataset ID와 CSV 규격. MaleCNS loader로 사용할 수 없음 |
| [HPI-1](../paper/8_해마수면_관계기억_연구/HPI1/predictive_core.py) | 코드 읽기·`test_predictive.py` 실행 | 고정 방출 슬롯, 학습 전이, 결측 marginalization. 19 tests 통과. 온라인 HPI-2 또는 원뇌 학습 검증이 아님 |
| [HPI 경로 계량](../paper/8_해마수면_관계기억_연구/HPI1/path_geometry.py) | 수식·입출력 확인 | 주어진 선형계와 전체 관측 공분산으로 Gaussian 계량 계산. 실제 회로 추론 모듈이 아님 |

166,700² float32 가중치 하나는 111,155,560,000 bytes다. 현재 dense 생성자를 전체
MaleCNS 분석의 선행조건으로 두지 않는다. 구조 연구는 sparse 연산자로 시작하고,
runtime의 저장·부호 계약은 별도 수정 뒤 해당 경로 실험을 열어야 한다.

## 5. 기존 MICrONS 작업의 재확인

[완료한 EM 연구 원장](../paper/검증_원장/고정뉴런_EM위치와_연결기록_보류예측.md)의 1,348노드·15블록
결과는 기존 증거로 유지한다. 이후 `microns_radial_direction_observation_blocks.jsonl`은
현재 14행, block 0–13만 있다. 기록된 코드 SHA와 실제 소스 SHA는
`c5bbd21cf268d2f518f1a0182d4d3cd59e865c615ff58c176d959cfda6212bda`로 일치한다.
최종 result JSON과 arrays NPZ는 없다. 따라서 15블록 완료·전체 방향성 결과로 인용하지 않는다.
기존 파일과 미추적 render 코드는 보존했으며 이 작업에서 계산을 재개하지 않았다.

## 6. 검증과 인계

`.codex/hooks/python.cmd doctor`가 Python 3.11.9 경로에서 통과했다.
HPI1 폴더에서 절대 경로의 `.codex/hooks/python.cmd pytest test_predictive.py -q`를 실행해
19개가 통과했다. runtime 세 가지 문제는 별도 임시 프로세스에서 재현했고 원자료에 쓰지 않았다.
문서 검사 `.codex/hooks/python.cmd python .codex/hooks/repository_harness.py`는
`REPOSITORY_HARNESS_PASS`였다. 같은 검사기의 `check_links`를 별도 데이터 원장 두 파일에도
적용해 깨진 링크 0개를 확인했다. 집계 코드의 AST 구문 검사와 실행 당시 소스 해시 대조도
통과했다. 변경 범위의 `git diff --check`는 오류 없이 종료했다.

전수 집계에 사용한 별도 실행기는 이미 설치된 `CE_PYTHON` 선택 경로의 Python 3.14.4,
PyArrow 25.0.1이었다. 실행은 동일한 승인 wrapper를 통과했으며 설치·정책 우회는 하지 않았다.
기본 doctor의 Python 3.11.9 환경과 구별한다. 당시 선택 경로는
`C:/Users/dongh/AppData/Local/uv/cache/archive-v0/-7582xpefQo_Gdq3/Scripts/python.exe`다.
집계 소스 SHA-256은 `8cf1d2b823a3a406a2abcffc63b9e4f411dcd5ff39a1b31397bce9fd39cb8ec7`이다.
다음은 NumPy·PyArrow가 있는 승인된 실행기를 `CE_PYTHON`으로 선택한 뒤 루트에서 쓰는 명령이다.

```powershell
.codex/hooks/python.cmd python verify/MaleCNS/malecns_edges_census.py `
  --edges data/local/malecns-v1.0/edges.feather `
  --annotations data/local/malecns-v1.0/annotations.feather `
  --curated-ids data/local/malecns-neurons166k/node_ids.txt `
  --max-bitset-mib 512
```

이 스크립트는 위 해시로 확인한 비어 있지 않은 int64·NULL 없는 MaleCNS 입력의 재현용이다.
임의의 손상 파일·다른 스키마·음수 ID에 대한 일반 수집 어댑터나 fail-closed 검증기는 아니다.

저장소 `C:/dev/ce/ce-agi-runtime`, branch `main`, upstream `origin/main`.
이번 조회에서 HEAD·upstream·`git ls-remote origin refs/heads/main`이 모두 위 SHA와 같았다.
커밋·push는 하지 않았다. 기존 `AGENTS.md` 수정, `.claude/` 삭제, MICrONS 미추적 두 파일은
이번 작업 전부터 있던 변경이다. 현재 연구 등급은 준비·형식 L0이며, MaleCNS로 실제
방향별 기능 반응·학습·기억을 지지하는 새 생물학적 결과는 아직 없다.

이번 변경은 `ledger/data_registry.md`, `ledger/data_registry.jsonl`, 이 원장,
`verify/MaleCNS/malecns_edges_census.py`, 논문 13번 주제 폴더의 다섯 장,
`paper/README.md`, 뇌 읽기지도, 해마수면 연구 README, `.codex/PRD.md`다.
데이터 어댑터·runtime 결함 수정·전체망 대리 동역학은 후속 작업이며 원본 파일을 수정하지 않았다.
