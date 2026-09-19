# 해마 지역 연결 정정: 참조 객체와 전극 번호의 의미

2026-09-20. 앞선 `.name=None` 정정은 HDF 참조가 실제 electrode 객체를 가리킨다는
점만 확인했다. 그 표를 어떻게 읽어야 하는지는 별도 문제였다. 기존 원장과 소스가
`/units/electrodes` 값을 0-based 표 행으로 사용해 지역을 잘못 집계했다.

## 원자료에서 확인한 대응

전극 표에는 같은 `tetrodeN`이 Ref OFF/ON 두 행으로 반복된다. Unit의 정수 값은
표 행보다 **1-based tetrode 번호**로 해석할 때 원 cellinfo·tetinfo의 area와 맞는다.
예를 들어 CS33의 값31은 `tetrode31`의 CA1에 대응하지만 행31은 `tetrode23`의 PFC다.
전체1,423유닛 중684개의 지역이 두 해석 사이에서 달라진다.

기존 ZIP에서 원 cellinfo/tetinfo 16개를 확보해 모든 유일 과제 연결 세션의 원 epoch와
비교했다. 처음 진단은 CS41 day7의 단일 epoch가 squeeze된32-tetrode 배열을32 epochs로
오해했다. 원자료의 축과 Preprocess_CS41의 `[7,1]` 과제 지정을 함께 확인한 보충 결과로
이를 정정했다. 해당24유닛도 원 cellinfo/tetinfo area가 일치한다.

정정 후 **35개 과제 연결 세션의1,305유닛**에서 원 지역 자료가 일치한다. 전체38개에는
CA1 915·PFC508유닛이 있고, 과제 경계가 맞지 않는3개는 원 epoch 연결 미확인을 유지한다.
이 전체 지역 집계는 tetrode 대응에 따른 재구성이며 모든38개의 과제 연결 성공을 뜻하지 않는다.

| 범위 | 기존 잘못된 행 해석 | 원 tetrode 대응 |
|---|---|---|
| 최초23세션967유닛 | CA1 398 / PFC494 / OB75 | CA1 677 / PFC290 / OB0 |
| 전체38세션1,423유닛 | CA1 540 / PFC752 / OB131 | CA1 915 / PFC508 / OB0 |
| 과제·CA1/PFC·냄새×정오답 네 칸 충족 | 32세션 | 33세션 |

새로 포함된 세션은 CS39_05 하나이고 기존32개는 모두 남는다. 이 세션도 필요한 값을
확보했으므로33개 전체의 입력이 있다. 확보 집합은 **1,284유닛(CA1 847/PFC437)**이다.
이전 원장과 frozen JSON의 지역 수치는 과거 오류를 포함한 기록으로 남기고 새 결과로 대체한다.

추가로 원 ZIP의 `CS33spikes03.mat` 하나를 받아 NWB CS33 day1–4의113유닛,
1,179,435개 spike를 원 MATLAB의 day/tetrode/cell과 대조했다. 전부 해당 day의
task epoch2에서 단일 cell과 정확히 일치했다. 초 단위 float64 배열에 정렬·shift·연결·
단위 변환을 하지 않았고 최대 잔차는0s다. 113개 모두 NWB 정수가 원 MAT의
1-based tetrode 번호와 같았다. 이는 CS33 네 날의 직접 event 근거이며 다른 rat이나
다른 epoch의 cell 동일성을 직접 검증한 것은 아니다.

변환기 구현 자체를 고정해 읽지는 못했다. 다른 rat의 정수 값 해석은 원자료 지역과 전극
group의 교차 확인에 따른 추론이다. 지역 일치만으로 epoch 사이 같은 뉴런의 추적,
unit별 연속 관측을 입증하지 않는다. 원논문의 OB는 LFP만 기록했다는 설명과도
교정된 집계가 맞으며, OB 발화 유닛을 새 생물학적 발견으로 취급하지 않는다.

## 재현과 보존

[정정 소스](../verify/Q-NPF-04/hippocampal_reinstatement/odor_place_tetrode_regions.py)는
고정 metadata에서 tetrode group을 독립적으로 재구성하고 원 cellinfo/tetinfo의 지역
집합, 원 epoch, unit ID 순서를 비교한다. 같은 group의 서로 다른 지역, 없는 tetrode,
잘못된 번호와 불완전한 원자료 증거는 거부한다.
[검사](../tests/test_odor_place_tetrode_regions.py)9개 통과 후 한 번 실행했다.
[결과](../verify/Q-NPF-04/hippocampal_reinstatement/odor_place_tetrode_regions_result.json)의
SHA는 `30c74fb53563a56a190469a62143f4c5ce0bef427307b7bc14c275820e4b7891`이다.

원 MAT16개·범위 영수증·최초 매핑 진단은
`data/external/hippocampal_reinstatement/odor_place_cell_tet_info_v1`,
단일 epoch 축 보충과 실패본은
`data/local/hippocampal-reinstatement/odor-place-cs41-source-axis-v1`에 있다.
CS41_07의 초기 누락을 성공으로 덮어쓰지 않았다. 이름 없는 HDF 객체의 동일성 확인은
여전히 유효하지만 그것만으로 정수 열의 의미가 검증됐다는 해석은 철회한다.

CS33 원 event 수집·대조7파일은
`data/external/hippocampal_reinstatement/odor_place_cs33_spike_identity_v1`에 보존했다.
새 network body는17,371,935B/2범위이며206·Content-Range·ETag·길이·CRC32를 확인했다.
대조 JSON SHA는 `4720a246c89384ed55a8f60f3c9c6bb3c3c159168e4273f7bf13d29736aea7df`다.

수집 이력도 정정한다. 최초 cellinfo/tetinfo collector는 도구 timeout 뒤 실제로 완료됐는데
중단으로 오인하고 다시 수집했다. 실제 본문은559,112B+559,112B=1,118,224B이고
559,112B는 중복이다. 최초16 MAT와 receipt가 보존본19파일과 SHA까지 일치한다.
‘receipt 작성 전 중단’이라고 쓴 초기 status는 사실과 다르며 덮어쓰지 않았다.
정정 helper·JSON은 `data/local/hippocampal-reinstatement/odor-place-cell-tet-attempt-correction-v1`에 있다.
이후 CS33 수집은 단일 실행만 사용했고 재시작은 없었다.
