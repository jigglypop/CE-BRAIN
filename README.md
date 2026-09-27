# CE-BRAIN

고정된 뉴런들의 전기적 상호작용과 과거 흔적이 어떻게 기억·학습·현재의 세계모델을 만드는가를
하나의 공통 구조로 설명한다. 뉴런은 고정된 점이고, 변하는 것은 상태와 관계다. 기능적 거리와 변화
비용은 리만 계량으로, 신호가 흐르는 방향은 따로 쓴다.

$$
\dot x=-G(h)^{-1}\nabla E(x;W)+F(x;W,u),\qquad \tau_h\dot h=-h+x,\qquad \dot W=\Phi(x,h)
$$

식과 결과, 판정, 참고문헌은 [논문](paper/CE-BRAIN.md)에 있다.

## 현재 상태 (2026-09-27)

공리는 원장에 등록된 실데이터로 빠르게 계산한 판정이 지지됨일 때만 채택한다.

| 공리 후보 | 상태 |
|---|---|
| C2 고정된 점, 변하는 상태와 관계 | **채택**: 환경이 바뀌어도 머리방향 세포의 고리 위 자리는 고정되고 전체 회전과 발화율만 바뀐다 (R 0.977, 문헌 0.93–0.96) |
| C3 현재 상태에 남는 과거 흔적 | **채택**: 잠들기 직전 방향이 논렘에 남는다. 독립 자료에서 재현되고 자유 확산이 아닌 되돌림이지만, τ는 계마다 다르다(192 s, 896 s) |
| C4 기능적 거리·변화 비용 = 리만 계량 | 미채택: 동시각 공분산 후보는 지형 E를 잰다. 렘 동역학은 확산 모양이나 기울기가 문헌의 0.2–0.4배 |
| C5 계량과 방향의 분리 | **채택**: 방향 성분은 PEN의 PB 경로에만 실린다(연결체 셋, 51–55°) |
| C6 이력에 따른 관계 변화 | **채택**: 트랙 경험이 수면 뒤 CA1 쌍 상관을 바꾼다 (EV 0.108, 문헌 0.15; 시간 역전 0.018) |
| C7 해마 = 주소·검색 | 미채택: 수면 뒤 가까운 주소를 함께 불러내지만 느린 세포 우세 미재현 |
| C8 한 표현의 선택 | 미채택: 갈등하는 두 후보를 섞지 않지만 중간 성분 4%가 남음 |
| C1 공통 구조 | 미채택: 공통 식의 꼴은 세 자료를 맞추고 흔적 우물 깊이(약 3 kT)는 종을 넘어 옮겨 가지만, 이동도·흔적 시간은 계마다 다르다 |

## 구성

| 위치 | 내용 |
|---|---|
| `research/harness.py` | 하네스: 원장 조회·등록, 판정 기준·역증명 기록. 공리는 원장 실데이터 판정이 지지됨일 때만 채택 |
| `research/core.py` | 공통 식: 계량·방향 분해, 최소 비용 평면, 등각 변환 |
| `research/malecns.py` | MaleCNS 적재(파일·해시는 원장에서): 고정 뉴런, 방향 있는 시냅스, 영역별 시냅스, 전달물질 부호 |
| `research/store.py` | 세션 형식(스파이크·단위 열·구간·시계열)으로 원장 파일 읽기, NWB 원격 범위 읽기 추출 |
| `research/fetch.py` | 공개 자료를 세션 형식으로 가져와 원장에 등록: `python -m research.fetch <이름>` |
| `research/fast/` | Rust 핵심 `cefast`(칸 세기, 창 세기, 교차 상관), `uv sync`가 빌드 |
| `ledger/data_registry.jsonl` | 자료 원장: 출처·판본·파일·sha256 |
| `research/c<전제>_<번호>_*.py` | 단계별 검사. 판정 기준은 파일 머리에 실행 전 고정 |
| `research/results/` | 단계 결과 JSON |
| `paper/CE-BRAIN.md` | 논문 정본 |
| `tests/` | 하네스·공통 식·MaleCNS 적재 검사 |
| `data/` | 원자료와 비압축 캐시(git 밖) |

## 실행

```sh
uv sync --python 3.11
.venv/Scripts/python -m research.c3_1_sleep_trace
.venv/Scripts/python -m pytest tests/test_harness.py tests/test_core.py tests/test_malecns.py tests/test_c4_metric.py tests/test_c4_anisotropic.py tests/test_c4_soft_modes.py tests/test_c3_trace.py tests/test_fast.py tests/test_store.py tests/test_c3_replication.py tests/test_c3_restoring.py tests/test_c4_diffusion.py tests/test_c6_reactivation.py tests/test_c7_address.py tests/test_c8_selection.py tests/test_c1_common.py
```
