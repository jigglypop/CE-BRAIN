# 해마 복원 연구: 냄새 단서·목표 장소 자료의 연결

2026-09-20. 해마를 ‘복원 포인트’로 보는 질문은 **부분 단서 → 사건 색인 → 연결된 내용의
재활성화**다. [기존 사람 자료](hippocampal_story_transfer_findings.md)에서는 내용 판독의
전이를 지지했지만 같은 내용의 사건 조건 구별은 지지하지 못했다. 이번에는 실제 단서와
행동 결과를 동시 집단 기록에 연결할 수 있는 공개 자료를 확보했다. 신경 판독이나
CE 식의 적합을 수행한 단계는 아니다.

## 자료와 분석할 수 있는 질문

[Symanski 등의 원논문](https://elifesciences.org/articles/79545)은 냄새로 학습한 보상
장소를 선택하는 쥐의 CA1·전전두엽 및 후각망울 기록을 제공한다.
[DANDI 001539 판본 0.250815.1203](https://dandiarchive.org/dandiset/001539/0.250815.1203)의
38개 NWB 중 작은 odor-place 세션을 먼저 확인했다. 선택한 파일은
`sub-Symanski-CS39/sub-Symanski-CS39_ses-06_behavior+ecephys.nwb`,
asset `dd3aaf58-c574-4d84-b918-f060f3663878`, identifier `CS39_06`이다.
자료 전체의 8마리·38세션을 분석한 것으로 세지 않는다.

해당 NWB는 23개 trial의 시작·종료·보상 유무·보상 시각을 제공하지만 냄새·선택·정오답
열은 없다. 보상 유무만으로 정답을 추정하지 않고 저자가 공개한
[Figshare v3 처리자료](https://doi.org/10.6084/m9.figshare.19620783.v3)의 원래 라벨을 찾았다.
두 자료의 사용 조건은 CC BY 4.0이다. Figshare의 다른 판본과 파일을 혼합하지 않았다.

## 정확한 시행 연결

`Figure1-6.zip`의 1,103개 member 목록에서 `odorTriggers` MAT 53개를 추출했다.
모두 ZIP CRC 검사를 통과했다. 그중 `CS39odorTriggers06.mat`의 MATLAB day6·epoch2에
있는 `allTriggers` 23개가 NWB의 `start_time`과 **원래 순서와 수치까지 정확히 일치**했다.
같은 day 안에서 일치하는 epoch는 유일했다.

[연결 소스](../verify/Q-NPF-04/hippocampal_reinstatement/odor_place_trial_labels.py)는
입력 SHA, trial ID 고유성, 유한하고 증가하는 시각, 양의 trial 길이와 task epoch 범위를
검사한다. 좌/우 및 정답/오답 라벨은 각각 중복 없이 전체 시행을 분할해야 한다.
원래 정답 라벨과 NWB 보상의 일치도 확인한다.

| 관측 | 이 세션의 결과 |
|---|---:|
| 정확히 연결된 시행 | 23 |
| 냄새 좌 / 우 | 10 / 13 |
| 정답 / 오답 | 20 / 3 |
| 기록 유닛 | 11 |
| CA1 / PFC 유닛 (원 tetrode 대응으로 정정) | 5 / 6 |

저자의 [라벨 생성 코드](https://github.com/JadhavLab/Jadhav-Lab-Codes-JHB/blob/master/BetaOdorProject/figures1-6Functions/Behavior/cs_getOdorTriggers.m)에서
left/right는 냄새의 방향 라벨이며 실제 선택 팔의 별도 관측값과 같지 않다.
이번 연결은 선택 팔을 추론하지 않는다. 보상과 정답의 일치는 이 epoch에서 확인한
사실이며 다른 NWB 전체에 동일한 변환 규칙을 적용하지 않는다.

이 asset에는 유닛마다 `electrodes` 정수 하나가 있고 `electrodes_index`가 없다.
초기에는 이를 표 행으로 읽어 CA1/PFC 2/9로 잘못 집계했다. 후속
[원 tetrode 대응](hippocampal_tetrode_region_findings.md)에서는5/6이며 초기 JSON은 오류 기록으로 남긴다. 전극 48개를
유닛 48개로 세지 않는다. Spike 시각 배열의 길이는 35,768이지만 그 값은 아직 읽지
않았고 LFP·위치 배열도 분석하지 않았다.

## 실제 보유 범위와 재현

DANDI 보유 폴더는
`data/external/hippocampal_reinstatement/dandi001539_0.250815.1203_header_v1`이다.
API 본문 18,254바이트와 NWB 18개 범위 279,496바이트를 받았으며, 로컬 진단·메타데이터를
포함해 29파일을 보존했다. 전체 NWB 485,835,720바이트는 받지 않았다. API의 전체 SHA를
로컬 전체 파일 검증으로 보고하지 않는다. 범위 응답의 206·Content-Range·ETag를 확인했다.

Figshare 보유 폴더는
`data/external/hippocampal_reinstatement/figshare19620783_v3_labels_v1`이다.
ZIP64 꼬리·중앙목록·작은 라벨 및 별도 MATLAB7.3 파일의 HDF5 root 확인까지
네트워크 본문은 714,575바이트로 2MiB 제한 안이다. 초기 manifest 뒤의 HDF5 확인
131,072바이트를 최종 summary에 더했다. Summary 자신까지 포함한 실제 보존 파일은
183개·1,373,121바이트다. 원래 probe의 Temp 경로와 초기 진단은 보존했다.
전체 5,659,941,080바이트 ZIP과 1,151,664,926바이트 MAT는 받지 않았다.
API의 전체 MD5와 multipart ETag는 로컬 전체 해시 검증을 대신하지 않는다.

새 연결 소스는 저장소 상대 경로를 사용하며 네트워크 없이 실행한다. 성공 결과가
있으면 덮어쓰기를 거부한다. [관련 검사](../tests/test_odor_place_trial_labels.py)는
정상 연결과 시각 불일치·라벨 중복/누락·보상 불일치·trial 중복을 검사해 6개 통과했다.
[결과 JSON](../verify/Q-NPF-04/hippocampal_reinstatement/odor_place_trial_labels_result.json)은
6,711바이트이며 SHA-256은
`64c7755a2524750da996a5fa71bd2a9780ac27569d554b9c68e9aaf623bfa443`이다.

실행기는 `C:/dev/ce/ce-agi-runtime-repro-fffd356/.codex/hooks/python.cmd`다.
`pytest tests/test_odor_place_trial_labels.py` 뒤
`python verify/Q-NPF-04/hippocampal_reinstatement/odor_place_trial_labels.py`를 실행했다.
Python3.11.9·NumPy2.4.6·SciPy1.17.1이며 입력·소스·검사 해시는 결과와
[데이터 원장](data_registry.md)에 남겼다.

## 복원 포인트 가설에서 아직 필요한 관측

이 과제는 냄새와 학습한 목표 방향이 결합돼 있다. 냄새를 신경활동에서 분류하는 데
성공하더라도 그것만으로 감각 반응과 기억 검색을 구별할 수 없다. 이번 단계가 해결한
것은 **단서·정오답과 같은 세션 기록의 정확한 연결**이다. 사건 색인, 내용 복원,
CA1→PFC 인과 방향, 전기 이력에 따른 계량 변화는 미확립이다.

다음은 같은 단서 안의 정답·오답과 선택, 단서 종료 뒤의 활동, 움직임·위치를 실제로
함께 관측할 수 있는지 확인하는 것이다. 이 세션의 CA1 5유닛·오답3회만으로 방향성이나
일반화 성능을 확정하지 않는다. 기존 53개 라벨을 재사용해 다른 세션과 기록 범위를
연결한 후 충분한 독립 시행과 관측이 확보된 범위에서 신경 판독을 설계한다.
자료 준비를 ‘현재 세계의 선택’이나 생물학적 리만 계량의 증명으로 승격하지 않는다.

## 작업 인계

저장소는 `C:/dev/ce/ce-agi-runtime`, branch `main`, upstream `origin/main`이다.
HEAD와 로컬 origin/main 참조는 `fffd356ee4f1f7bf5079f3379cd06e4dc56a444c`다.
Fetch·commit·push를 하지 않았으므로 원격의 실시간 tip은 미확인이다. 기존 `.codex`
삭제와 reality_stone 분리 변경은 보존했다.

이번 입력 확보 단계의 변경 범위는 mixed-clamp 소스·검사·결과 각2개, odor-place 연결
소스·검사·결과 각1개, 새 입력 폴더와 registry, 관련 원장·논문04/11·gitignore 예외다.
각각6·9·6개 한정 검사가 통과했다. 등록7판본268파일의 용량·SHA를 현재 파일과 대조했고
기존 medium/VC 부모 manifest2개도 고정 SHA와 일치했다. 전기 원파형 결합과 해마 신경
판독, 두 축의 생물학적 공통식은 남은 연구다. 라이브러리 분리 작업의 완료 판정을
이 연구 입력 검증으로 대신하지 않는다.

당시 독립 검토는 정수 열의 표 행/tetrode 의미 차이를 검출하지 못했다. 지역 집계는
후속 정정했다. 당시 보존
`repository_harness.py`의 `check_repository(root)`는 분리 작업 전 기준38개와 현재38개가
같았고 added/resolved는 모두0개였다. 기존 삭제 경로 문제를 새 연구 오류로 세거나
복원하지 않았다. 관련 tracked 경로의 `git diff --check`도 통과했다.

## 전체 세션 후속

[전체 세션의 관측 범위](hippocampal_odor_place_cohort_findings.md)는38개 metadata와
원라벨53개를 연결했다. 시작 시각의 ordered epoch 조합은38개 모두 유일하지만,
trial 전체의 task epoch 범위 검사까지 통과한 것은35세션·3,500시행이다. 과제 범위의
보류3개는 유지한다. 초기 ‘null 참조11개’는 이름 없는 객체를 오판한 결과였으며 후속
객체 동일성 검사에서38개 모두 유효한 electrode table 참조임을 확인했다.
CS39_06에서는 실제 선택과 nosepoke 종료를
23/23 연결했으나 Position 값·신경 판독은 아직 수행하지 않았다. 위 절의 단일 세션
보유 상태는 최초 단계의 기록이며 후속 범위와 구별한다.

[실제 신경·행동 입력](hippocampal_neural_behavior_inputs_findings.md)은 별도23세션의
spike·위치와2,454시행의 NP 구간,2,353시행의 실제 선택을 연결했다. 참조 정정 뒤 적격
세션을 당시32개로 집계했다. 후속 원 tetrode 의미 정정은 적격33개를 확인했고 현재
모두 확보했다. [첫 선택 판독](hippocampal_choice_readout_findings.md)은27세션을 평가했으며
기억 내용 복원은 여전히 미확립이다.
