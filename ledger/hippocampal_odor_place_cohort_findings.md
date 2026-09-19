# 해마 복원 연구: 전체 세션의 단서·행동 관측 범위

2026-09-20. [한 세션의 입력 연결](hippocampal_odor_place_input_findings.md)을 전체
38개 NWB로 넓혔다. 질문은 **부분 단서로 과거의 연결된 내용이 재활성화되는가**다.
이번 단계는 이를 시험할 관측 범위를 확인했다. 새로운 신경 판독이나 해마 복원 기전의
입증을 수행한 단계는 아니다.

## 원래 라벨 전체와 NWB 분석 범위

기존 Figshare v3 라벨53개를 재사용했다. 8마리의 비어 있지 않은 day/epoch90개에
완료된 시행6,935개가 있고, 일반 냄새86구간6,844개와 air4구간91개로 나뉜다.
각 구간의 좌/우 및 정답/오답 분할은 모두 중복 없이 전체를 덮는다. 일반 냄새의
86구간 중77개에는 냄새 좌/우 × 정답/오답 네 칸이 모두 있다.
이6,935개 전체를 DANDI의 신경 분석 표본으로 세지 않는다.

DANDI001539의 고정 판본 `0.250815.1203`에 있는38개 asset의 metadata를 전부
확인했다. 최초 단일 epoch 비교는23개만 일치했다. 나머지15개는 원래 여러 odor
epoch를 순서대로 연결한 NWB였으며, 별도 진단에서 원래 시각을 재정렬하지 않는
epoch 조합을 확인했다. 최초 진단은 유지하고 새 canonical 소스에서 이를 명시했다.

시작 시각만의 유일 연결은38/38개·4,182시행이다. 그러나 전체 trial이 명시된 과제
구간에 속해야 한다는 조건까지 적용하면 **35/38개·3,500시행**이다.
CS42_02/04/05는 이 범위 조건에서 보류했다. 시각이 맞는다는 이유로 경계를 넓히거나
3세션의 실패를 지우지 않는다. 통과한35세션 중33개에 냄새×정오답 네 칸이 모두 있다.

별도 offline 진단에서는 세 세션 모두 원라벨 단일 epoch2와 유일하게 일치했다.
CS42_02의 마지막1개, CS42_04의 마지막1개, CS42_05의 마지막2개 trial 종료가
NWB task stop을 넘으며 최대 초과는 각각1.0562s·0.6561s·3.8979s다. 중복 구간 포함은
없었다. 다른678개 시행은 범위 안이지만 성공 결과를 다시 선별해 덮어쓰지 않았다.
경계를 이렇게 저장한 변환상의 원인은 현재 입력만으로 확정할 수 없다.
진단 소스·결과·manifest는 `data/local/hippocampal-reinstatement/odor-place-task-support-diagnostic-v1`
에 보존했다.

[연결 소스](../verify/Q-NPF-04/hippocampal_reinstatement/odor_place_cohort_labels.py)는
53개 원라벨의 용량·SHA, metadata summary와 참조 표 보충의 SHA를 고정한다.
같은 rat/day/kind 안에서 epoch 순서의 조합을 비교하고 유일한 exact ordered match만
허용한다. 각 시행의 시각·고유 ID·라벨 분할·NWB 보상 일치와 전체 trial의 odorplace
epoch 포함을 검사한다. Air와 일반 냄새를 이어 붙이지 않으며 실패를 삭제하지 않는다.

## 지역 표 참조의 정정: 이름이 없는 객체도 유효하다

모든38개에 unit당 정수 electrode 값 하나가 있고 ragged `electrodes_index`는 없다.
값이 표 행 범위 안이라는 것만으로 행 번호 해석은 보증되지 않는다. 초기 검사에서는 HDF5 `table` 참조를 해석한 객체의 `.name`이
None인11개를 null/unresolvable로 잘못 분류했다. 이는 검사 코드의 오류였다.
2026-09-20 후속 검사에서 기존 캐시만 사용해38개 모두 참조가 존재하고 non-null이며,
dereference한 객체의 ID와 HDF 주소가 예상 electrode 표와 같음을 확인했다.

[정정 소스](../verify/Q-NPF-04/hippocampal_reinstatement/odor_place_region_reference.py)는
객체 동일성, 기존 정수 행/범위 조건, 시행 범위와 네 칸 조건을 함께 적용한다.
과거 소스·결과를 덮어쓰지 않고 [정정 결과](../verify/Q-NPF-04/hippocampal_reinstatement/odor_place_region_reference_result.json)를
추가했다. 날짜가 다른 unit ID를 같은 뉴런으로 연결하지 않는다.

| 관측 범위 | 세션 수 |
|---|---:|
| Metadata를 읽은 전체 자산 | 38 |
| 원 tetrode 대응에서 CA1+PFC를 모두 가진 후보 | 38 |
| 위 후보 중 canonical 시행/과제 범위 검사까지 통과 | 35 |
| 위35개 중 냄새×정오답 네 칸이 모두 있는 후보 | 33 |
| 신경·위치 및 DIO/NP 원자료를 확보한 적격 세션 | 33 |
| 위33개 중 모든 시행의 실제 선택까지 연결한 세션 | 31 |
| 공통 창과 각 학습 블록의 네 칸 조건까지 통과한 첫 판독 세션 | 27 |

후속 [tetrode 의미 정정](hippocampal_tetrode_region_findings.md)에서 CS39_05에도
CA1 3유닛과 PFC 5유닛이 있음을 확인했다. 이전의 ‘CA1 없음’은 표 행 해석 오류였다.
CS39_06과 CS39_07은 왼쪽 냄새의 오답이 없어
네 칸 조건을 만족하지 않는다. 네 칸이 존재한다는 것만으로 충분한 반복 수·균형·
독립성이 확보됐다고 보지 않는다. 초기23세션 뒤 추가9세션과 CS39_05를 확보했다.
최초23개의 수집은 [입력 원장](hippocampal_neural_behavior_inputs_findings.md), 전체33개와
CS41_01/02 선택182건 미해결 및 실제 판독은 [후속 결과](hippocampal_choice_readout_findings.md)에 둔다.
LFP 값은 아직 받지 않았다.

## 한 세션에서 실제 선택과 단서 종료를 확인했다

저자의 [원래 행동 처리 코드](https://github.com/JadhavLab/Jadhav-Lab-Codes-JHB/blob/88d5f8d2bb39796b8656dc42bd42969a7bbe8697/BetaOdorProject/figures1-6Functions/Behavior/cs_getNosepokeWindow.m)를
확인했다. 냄새는 nosepoke 동안 제시되며 nosepoke 종료가 단서 종료 기준이다.
`odorTriggers`의 left/right는 냄새 라벨이다. 실제 선택은 이어지는 좌/우 reward-well
DIO 입력으로 따로 확인해야 한다. 관련9개 코드 파일은 논문 당시 commit과 현재
확인한 commit 사이에 byte가 같았으며 두 판본을 보존했다.

CS39 day6의 DIO·nosepokeWindow·rewards 작은 MAT3개만 추가 확보했다.
기존23개 시행 모두에서 nosepoke 종료 이후 첫 reward-well 진입을 연결했다.
냄새는 좌10/우13이지만 실제 선택은 좌13/우10이다. 오답3개(trial ID9/14/20)는 모두
오른쪽 냄새 뒤 왼쪽 선택이며 원라벨 incorrect와 NWB rewarded=false에 일치한다.
Nosepoke 종료에서 선택 well 진입까지는1.570–3.077s다. 보상 유무에서 선택 방향을
역추정한 결과가 아니다. 이 세션도 위치 값은 아직 읽지 않아 운동 통제 완료로 세지 않는다.

저자의 [원논문](https://elifesciences.org/articles/79545)은 냄새 표본화 때 CA1·PFC·OB의
리듬 협응과 선택 관련 신경활동을 보고한다. 단서와 학습한 목표는 결합돼 있고 단서
종료 뒤에는 움직임이 시작된다. 따라서 냄새 분류나 단서 종료 뒤 활동만으로 기억
복원을 판정할 수 없다. 같은 단서의 정답·오답, 실제 선택, 위치·속도·회전과 시간의
관계를 함께 관측해야 한다. 완료되지 않은 조기 이탈은 원래 완료 trial 라벨에서 빠진다.

## 부분 보유와 보존

초기 라벨/코드 범위 진단49파일은
`data/external/hippocampal_reinstatement/odor_place_observation_scope_v1`에 있다.
초기 `observation_scope_report.json`의 ‘단일 NWB만 연결’ 및 ‘행동 값 미수집’은
그 보고 시점의 상태다. 이후 행동3파일 수집 receipt가 추가됐으며 초기 보고를 고쳐
새 단계가 처음부터 완료된 것처럼 만들지 않았다.

행동3파일은2026-09-20 KST01:24:38–01:24:46에 기존5.66GB ZIP에서 범위로 받았다.
6개 응답의 합계32,028바이트이고 CRC 및 각 MAT SHA를 확인했다. 수집 helper는
206·Content-Range를 본문 수신 전에 검사하며 If-Match를 전송한다. 응답 ETag는
receipt에 보존했다. 본문 수신 전에 ETag까지 명시적으로 비교하는 구현은 아니다.
후속 로컬 검산에서는6개 응답 ETag가 If-Match와 모두 정확히 일치했다.

전체 세션 metadata·범위·보충 진단670파일은
`data/external/hippocampal_reinstatement/dandi001539_0.250815.1203_cohort_metadata_v1`
에 Temp와 SHA가 같은 복사본으로 보존했다. CS39_06은 앞서 고정한 캐시만 재사용했다.
나머지37개와 API의 신규 network body는9,388,755바이트이며 전체16MiB·자산별2MiB
상한 안이다. 범위576개는 모두206·정확한 Content-Range·ETag를 확인했다.
전체 NWB를 받은 것은 아니며 API의 전체 SHA를 로컬 전체 파일 검증으로 대체하지 않는다.

최초 summary SHA는 `9c98884de317bce80605e70d0bd1dddfb4ecd065dc081ce6e734168687badacc`,
참조 표 보충은 `2479493841cccd87b1165bc68117ff53ac88412fb2ad9589218065025a33962c`,
실제 선택 보충은 `6acc556098e03545e3b3decc7ae1a32a7fff9bc894008f5c5d376479d843a5e8`다.
초기 manifest와 이후 supplement manifest를 구분하며 정확한 보존 파일별 해시는
[데이터 원장](data_registry.md)에 둔다. 탐색 helper의 Temp 경로는 원래대로 보존했고
새 canonical 연결 소스는 저장소 상대 경로로 네트워크 없이 실행한다.

[관련 검사](../tests/test_odor_place_cohort_labels.py)는 단일/복수 epoch, 순서·유일성,
air 혼합 거부, 보상·범위 불일치와 저장된 참조 상태의 분기를 검사해8개 통과했다.
이 초기 검사는 `.name=None` 오판을 검출하지 못했다. 후속
[참조 검사](../tests/test_odor_place_region_reference.py)7개는 이름 없는 동일 객체의 수용,
잘못된 객체/주소의 거부와 기존 과제·네 칸 조건 보존을 확인했다.
[Canonical 결과](../verify/Q-NPF-04/hippocampal_reinstatement/odor_place_cohort_labels_result.json)는
833,080바이트, SHA `304968b35ba65a7831ca3a4742e07500efa679834bfee362baa768e6c87b21e3`다.
실행기는 `C:/dev/ce/ce-agi-runtime-repro-fffd356/.codex/hooks/python.cmd`이며
`pytest tests/test_odor_place_cohort_labels.py` 뒤
`python verify/Q-NPF-04/hippocampal_reinstatement/odor_place_cohort_labels.py`를 한 번 실행했다.
Python3.11.9·NumPy2.4.6·SciPy1.17.1이고 결과의 기존 파일 덮어쓰기는 거부한다.

## 다음 진행 조건

23세션의 spike·위치와 행동 입력은 후속 단계에서 결합했다. 다음은 추가9세션의 확보와
단서 전후 분석창의 관측지원 및 내용 판독이다. 사용 가능한 세션은 효과 크기가 아닌 지역 참조,
관측지원과 행동 대조의 가능성으로 정한다. 같은 cue에서 선택을 예측하는지와
단서에 없는 학습 내용을 복원하는지는 별도 질문으로 유지한다. 같은 rat/session에
속한 많은 시행과 유닛을 독립 동물 수처럼 세지 않는다.

해마를 ‘주소 지정·검색 구조’로 해석하는 공통 목표는 계속 열려 있다. 이번 입력 연결은
리만 계량이나 CA1→PFC 인과 방향, 전기 이력에서 기억 복원으로 이어지는 공통식을
입증하지 않는다. 현재 단계는 **관측 입력 준비**, 신경 복원 가설은 **미확립**이다.

## 작업 인계

저장소 `C:/dev/ce/ce-agi-runtime`, branch `main`, upstream `origin/main`이다.
HEAD와 로컬 origin/main 참조는 `fffd356ee4f1f7bf5079f3379cd06e4dc56a444c`다.
Fetch·commit·push는 하지 않았으므로 원격 실시간 tip은 미확인이다. 기존 `.codex`
삭제와 reality_stone 분리 변경은 유지했다. 이번 변경은 mixed-clamp raw/audit/state 및
cohort 연결 소스·검사·결과, 그림 생성기/그림, 새 입력 보존 폴더, 데이터 원장과
후속 원장·논문04/11·gitignore다. 관련 테스트는 각각12·7·7·8개 통과했다.
다음 연구는 전기 상태를 포함한 전달 예측과 해마의 실제 신경·움직임 결합이며,
라이브러리 분리나 전체 연구 목표의 완료 판정은 이 입력 검증과 별도다.

이번11판본1,129파일의 등록 용량·SHA를 실제 파일과 모두 대조했고 기존 raw/medium/
VC overlay/라벨 부모 manifest4개도 고정 SHA와 일치했다. 독립 수치·해석 검토에서
전기 보정식의 첫 항을 실제 `PCR baseline_potential`로 명확히 했으며 해마 원장의
당시 검토에서는 오류를 발견하지 못했다. 위 참조 오류는 이후 객체 동일성 검사로 정정했다.
당시 보존 문서 harness의 기준38개와 현재38개가 같아 추가/해결은0개였다.
관련 로컬 링크의 새 오류도 없었으며 기존 삭제 경로는 복원하지 않았다.
