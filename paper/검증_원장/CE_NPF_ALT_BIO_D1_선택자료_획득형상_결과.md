# CE-NPF 대체 생물학자료 D1 선택자료 획득·형상 결과

## 판정

- 획득: `TRACK2P_SELECTED_DOWNLOAD_PASS`
- 형상: `TRACK2P_SELECTED_SOURCE_SCHEMA_PASS`
- 지위: **준비됨**. 아직 어떤 생물학 endpoint도 계산하지 않았다.

## 획득 영수증

- Zenodo record: `17091226`
- 공급자 ZIP container manifest SHA-256: `3cfb18334b413a0ceaa307cdf328750f3fe3f7b5e2b88b6d4b5e1b178375fc25`
- 선택 파일: 249개
- 선택 바이트: 4,294,515,444
- 검증: 각 member의 공급자 크기와 CRC32가 일치한 후에만 최종 파일로 승격.
- 저장 위치: `data/external/track2p_zenodo_17091226/selected`

## 형상 영수증

- subjects: 6
- sessions: 41 (`jm031` 7, `jm032` 7, `jm038` 7, `jm039` 7, `jm040` 6, `jm046` 7)
- 마우스별 동일행 추적 세포수: 221, 370, 685, 746, 541, 435
- 신경 프레임: 세션당 36,000 또는 54,000
- `spks`, `stat`, `iscell`, motion, timestamps, interframe 배열 형상 일치
- 사람 검증 `ground_truth.csv`: 3개(`jm038`, `jm039`, `jm046`)

일부 세션의 행동 프레임은 신경 프레임보다 1–148개 적었다. README가 지정한 `tstamps.npy`/`interframe_int.npy`로 누락 위치를 복원하는 별도 정렬 게이트를 주효과 전에 실행한다. 이는 장치·좌표 문제이며 생물학적 지지나 반증으로 세지 않는다.
