# CE-NPF 대체 생물자료 R1 소스·스키마 사전검사 v2 결과

## 판정

- 판정: `RANDI_2023_SOURCE_SCHEMA_V2_PASS`
- 지위: **준비됨**. 생물학 endpoint는 아직 검사하지 않았다.
- 원 질문에 답했는가: 아니다. 개입자료가 분석 가능한지만 확인했다.
- 반증된 것: 없음. v1의 좌표계 오독만 교정했다.
- 살아 있는 것: WT--`unc-31` 유효 전파기하 비교.

## 정본과 실행 환경

- WT: 523,093,816 bytes, SHA-256 `d6e7b3d93175b40b7ae17bde2182835e9c2144388142c522ee9be3832f6ce836`.
- `unc-31`: 84,924,311 bytes, SHA-256 `8b99f6610dbb2d6ab0b8dd6ad15646fe1c120da25dd9bb725f36f530b2af321a`.
- 공급자 export code: `leiferlab/pumpprobe` commit `1dbc5e0a2b609d54bc9b1c90c73d4e3bf183d3c7`.
- auditor: `audit_randi_2023_source_schema_v2.py`.
- interpreter: `C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe`, Python 3.11.9.

## 복구된 스키마

| 집단 | 전체 recordings | identity 사용 가능 | 제외 ID | timepoints 범위 | neuron 열 범위 | stimulus 수 범위 |
|---|---:|---:|---|---:|---:|---:|
| WT | 113 | 112 | 11 | 393--5,848 | 80--281 | 3--92 |
| `unc-31` | 18 | 15 | 0, 3, 4 | 550--5,035 | 82--160 | 4--79 |

모든 archive checksum, recording ID 연속성, 6-file 완전성, GCaMP 직사각형, time 행 정렬, stimulus 배열 정렬, sentinel 범위와 빈 label padding 규칙이 통과했다.

## 주장 한계

이 통과는 단일뉴런 자극과 전뇌 칼슘반응을 동물 단위로 분석할 장치가 준비됐다는 뜻이다. 물리 시냅스 가중치, 축삭 전도속도, 발달 중 재배선, 자연행동 매개를 식별하지 않는다.

## 다음 허용 행동

동물 단위 분할, 자극 전 기준선, 자극 후 시간창, autoresponse gate, 기하량, 음성대조와 중단조건을 먼저 고정한 뒤 R1 endpoint를 한 번 실행할 수 있다.

