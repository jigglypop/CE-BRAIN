# CE-BRAIN Stage 9 DA R2 날짜 스키마 계약

Status: `PRE_ENDPOINT_SCHEMA_MAPPING`

R1 day01 중단 뒤 threshold를 바꾸지 않고, 이미 해시 분할된 development schema subject 네 마리(`30s-F2`, `60s-F1`, `300s-F2`, `600s-F1`)의 day01~day08을 모두 공식 SHA-256으로 검증한다.

이 검사는 dataset array 값을 점수화하지 않는다. HDF5 object path와 shape만 읽어 다음을 확인한다.

1. 각 조건에 event log가 있는 행동 session이 둘 이상 존재.
2. 각 조건에 `specifications` 밖의 실제 photometry/dopamine/fluorescence instance가 하나 이상 존재.
3. 같은 subject 안에서 행동 session과 chemical-recording session을 날짜로 연결할 수 있음.

모두 통과하면 `STAGE9_DA_LONGITUDINAL_SCHEMA_ELIGIBLE`, 아니면 `STAGE9_DA_LONGITUDINAL_SCHEMA_STOP`이다. 통과 후에도 어떤 dopamine feature와 어떤 next-day behavior target을 쓸지는 별도 계약 전까지 열지 않는다.
