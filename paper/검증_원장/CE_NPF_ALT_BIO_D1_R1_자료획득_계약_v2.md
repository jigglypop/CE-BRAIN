# CE-NPF 대체 생물자료 D1/R1 자료획득 계약 v2

## 계승과 변경

- 판본: `ALT_BIO_D1_R1_SOURCE_v2`
- v1 계약의 목표, 정본 파일, 주장 한계와 endpoint 미개봉 규칙을 그대로 계승한다.
- 변경 이유: v1 source 감사가 공급자 sentinel과 빈 label padding을 오류로 해석했다.
- 변경 시점: 활동 효과크기, genotype 차이, 발달 추세, 행동 상관을 계산하기 전이다.

## Randi export 좌표계

공급자 정본 코드는 `leiferlab/pumpprobe` commit `1dbc5e0a2b609d54bc9b1c90c73d4e3bf183d3c7`로 고정한다.

1. `gcamp`은 `time × recording-specific neuron` 행렬이다.
2. `t` 길이는 `gcamp` 행 수와 같아야 한다.
3. `stim_volume_i`와 `stim_neurons` 길이는 같아야 한다.
4. `stim_neurons`의 `-1`, `-2`, `-3`은 공급자 sentinel로 허용한다. 0 이상 값만 현재 recording의 GCaMP 열 범위 안이어야 한다.
5. `labels`의 앞 `gcamp` 열 수 항목을 열 정렬 label로 사용한다. 초과 항목은 전부 빈 문자열일 때만 padding으로 허용한다.
6. 앞 구간에 비어 있지 않은 label이 하나도 없는 recording은 identity endpoint에서 미리 제외한다.

## 고정 사용 가능 집단

- WT: 총 113 recordings 중 identity 사용 가능 112. recording 11 제외.
- `unc-31`: 총 18 recordings 중 identity 사용 가능 15. recordings 0, 3, 4 제외.
- 제외는 genotype 효과나 반응값이 아니라 source label 존재 여부만으로 결정한다.
- 미식별 recordings를 population-only 분석에 다시 넣지 않는다.

## v2 source gate

- archive byte/checksum, recording ID 연속성, 6-file 완전성, GCaMP 직사각형, time 정렬, stimulus 배열 정렬이 모두 통과해야 한다.
- 위 좌표계 규칙을 적용한 identity 사용 가능 수가 정확히 WT 112와 `unc-31` 15여야 한다.
- 통과 후에도 이는 `준비됨`일 뿐이다. 별도 분석 계약 전에는 생물학 endpoint를 계산하지 않는다.

