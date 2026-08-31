# CE-NPF 대체 생물자료 D1 선택자료획득 계약 v2

## 지위와 이유

- 판본: `ALT_BIO_D1_SELECTED_SOURCE_v2`
- Track2p parent archive와 과학 질문은 `CE_NPF_ALT_BIO_D1_R1_자료획득_계약.md`를 계승한다.
- Zenodo의 9.86 GB 단일 archive 병렬 range 요청에서 504가 반복되어, 공급자가 공식 제공하는 ZIP-container member API로 전환한다.
- 이는 결과를 본 뒤 고른 변수가 아니다. 생물학 endpoint를 열기 전에 README가 선언한 분석 변수만 고정한 source 획득 최적화다.

## 고정 선택 규칙

Zenodo container manifest SHA-256은 `3cfb18334b413a0ceaa307cdf328750f3fe3f7b5e2b88b6d4b5e1b178375fc25`다. 다음 member만 선택한다.

1. 모든 session의 `suite2p/plane0/spks.npy`
2. 모든 session의 `suite2p/plane0/stat.npy`
3. 모든 session의 `suite2p/plane0/iscell.npy`
4. 모든 session의 `move_deve/motion_energy_glob.npy`
5. 모든 session의 `move_deve/tstamps.npy`
6. 모든 session의 `move_deve/interframe_int.npy`
7. 존재하는 모든 subject-level `ground_truth.csv`

선택 결과는 6 subjects, 41 sessions, 249 files, 4,294,515,444 bytes로 고정한다. 각 member의 byte 수와 CRC32는 container manifest 값을 사용한다.

## 배제와 주장 한계

- `F.npy`, `Fneu.npy`: 이번 질문은 공급자 처리 spike proxy `spks.npy`로 고정하므로 제외한다.
- `ops.npy`: 평균 영상 등 대형 중간 산출물이며 동일행 추적과 활동--행동 분석에 필수적이지 않아 제외한다.
- 선택 자료는 시냅스, 축삭, 전도속도, 분자 세포형을 포함하지 않는다.
- source gate는 다운로드·CRC·배열 shape·동일 subject 내 행 수만 검사한다. 발달 효과나 행동 상관은 별도 계약 전까지 계산하지 않는다.

## 다음 게이트

249개 모두 byte/CRC를 통과하고, 정확히 6 subjects와 41 sessions가 복구되며, 각 subject 안에서 `spks`의 세포 행 수가 날짜 간 같을 때만 D1 분석 계약을 연다.

