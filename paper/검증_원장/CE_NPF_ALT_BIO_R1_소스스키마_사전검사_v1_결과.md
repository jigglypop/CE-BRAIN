# CE-NPF 대체 생물자료 R1 소스·스키마 사전검사 v1 결과

## 판정

- 판정: `RANDI_2023_SOURCE_SCHEMA_FAIL`
- 범위: source/schema만 검사했으며 생물학 endpoint는 열지 않았다.
- 원 질문에 답했는가: 아니다. 자료 좌표계 검사가 끝나지 않아 가설 결과를 계산하지 않았다.
- 반증된 것: `stim_neurons`의 모든 음수가 오류이고 `labels` 행 수가 항상 GCaMP 열 수와 정확히 같다는 v1 장치 가정.
- 아직 살아 있는 것: 정본 archive와 개입자료 lane. 두 archive의 byte 수와 SHA-256은 모두 통과했다.

## 통과한 항목

- WT archive: 523,093,816 bytes, SHA-256 `d6e7b3d93175b40b7ae17bde2182835e9c2144388142c522ee9be3832f6ce836`.
- `unc-31` archive: 84,924,311 bytes, SHA-256 `8b99f6610dbb2d6ab0b8dd6ad15646fe1c120da25dd9bb725f36f530b2af321a`.
- 압축 해제 후 WT 113 recordings × 6 files, `unc-31` 18 recordings × 6 files가 존재했다.
- 모든 GCaMP 행은 recording 안에서 같은 열 수를 가졌고, time 행 수와 일치했다.

## 실패 원인

v1 auditor는 `stim_neurons`를 `-1` 또는 현재 GCaMP 열 인덱스로만 해석했다. 공급자 코드의 `Fconn`은 `-1`, `-2`, `-3`을 서로 다른 미식별/제외 상태의 sentinel로 사용한다. 따라서 117건의 보고 중 대부분은 손상이 아니라 좌표계 오독이었다.

세 WT recording에서는 label 파일이 GCaMP 열보다 길었다. 초과분은 모두 빈 문자열이었다. 또한 WT recording 11과 `unc-31` recordings 0, 3, 4는 관측 열 구간에 식별 label이 전혀 없었다. 이들은 세포 identity가 필요한 endpoint에 사용할 수 없다.

공급자 코드 근거는 `leiferlab/pumpprobe` commit `1dbc5e0a2b609d54bc9b1c90c73d4e3bf183d3c7`의 `pumpprobe/Fconn.py`와 `pumpprobe/Funatlas.py::export_to_txt`다.

## 다음 허용 행동

생물학 값을 보지 않은 상태이므로 successor source 계약을 고정할 수 있다. v2는 sentinel을 보존하고, GCaMP 열 구간의 label만 정렬하며, 초과 label은 모두 비어 있을 때만 padding으로 인정한다. identity endpoint의 사용 가능 recording 수는 WT 112, `unc-31` 15로 먼저 고정한다.

