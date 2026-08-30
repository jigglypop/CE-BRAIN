# CE-BRAIN Stage 7 DANDI 001701 X-미로 장치 감사

Status: `POSITION_AND_SPIKES_PRESENT / TRIAL_SEMANTICS_MISSING`

기준일: 2026-08-31

## 1. 목표

CRCNS 선형트랙에서 trajectory memory가 두 번 미확립된 뒤, 매뉴얼의 `다른 memory code 탐색` 분기로 이동할 수 있는지 확인한다. 대상은 DANDI 001701의 X-미로 공간 match-to-sample 자료다.

## 2. 고정된 개발 파일

| 파일 | 크기 | SHA-256 | unit 수 |
|---|---:|---|---:|
| `sub-BaggySweatpants_ses-BaggySweatpants-DY15-g1.nwb` | 12,967,760 B | `5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3` | 320 |
| `sub-Franklin_ses-Franklin-DY16-g0.nwb` | 16,239,384 B | `60446690e71448c6228106b09ba669c047ad8cacdf0c1dea6b6cfab73ee0d8b2` | 449 |

두 파일 모두 `session_description = X Maze`이고, unit spike table과 behavior의 Position·head direction을 포함한다.

## 3. 확인된 장치 한계

- 두 NWB 모두 `/intervals`와 trial table이 없다.
- `/acquisition`은 비어 있고, task event·port poke·door open·reward event가 없다.
- 위치에서는 네 팔 끝점과 양쪽 사이의 이동을 복원할 수 있다.
- 위치만으로는 sample arm, match/non-match rule, correct/incorrect, reward를 신뢰성 있게 복원할 수 없다.

공식 논문은 X-미로 시행에서 한쪽 sample door가 열린 뒤 반대쪽 두 문 중 하나를 선택하는 과제를 설명한다. 그러나 공개 변환 코드의 `add_behavior`는 trial export를 `Linear Track`과 `Double-Y Maze`에만 구현하고 `X Maze` 분기가 없다. `Task` 구현에도 `LinearTrackTask`와 `DoubleYMazeTask`만 있고 X-미로 전용 trial class가 보이지 않는다. 따라서 **공개 NWB에서 시행표가 빠진 것은 변환 경로의 미지원과 일치한다**. 원시 Arduino trial 파일을 보지 않고 이를 확정적 원인이라고 단정하지는 않는다.

근거:

- 논문: <https://www.nature.com/articles/s41593-026-02232-0>
- 고정 코드 판본: <https://github.com/emilyasterjones/AeryJones_2025/tree/dfbbde116929d420523421d7bfe5d441eb91568a>
- NWB exporter: `Yggdrasil/NWB/nwb.py`
- task parser: `Yggdrasil/Task/task.py`

## 4. 가능한 질문과 불가능한 질문

### 현재 파일만으로 가능한 개발 질문

> 선택 쪽으로 이동하기 전 신경신호가 위치·머리방향·직전 팔을 넘어 다음 반대편 팔 선택을 예측하는가?

이는 네 끝점 방문과 side-to-side 이동을 위치에서 score-blind하게 추출한 뒤 검사할 수 있다.

### 현재 파일만으로 불가능한 확인 주장

- match-to-sample 규칙을 신경계가 기억했다.
- 선택이 정답 또는 오답이었다.
- reward 결과를 기억했다.
- encoding과 retrieval epoch가 관계형 기하를 보존했다.
- recall과 correction 방향이 분리됐다.

## 5. 판정과 다음 허가

**[장치 판정]** `POSITION_AND_SPIKES_PRESENT / TRIAL_SEMANTICS_MISSING`.

**[허가]** 위치 기반 endpoint 방문과 side-to-side transition 추출기의 score-blind 개발은 허용한다. 신경 endpoint를 열기 전에 최소 방문시간, endpoint 반경, 동일 endpoint 재방문 합치기, 시간순 train/validation/test 분할, 행동 기준선을 고정해야 한다.

**[claim ceiling]** 통과하더라도 `다음 원격 팔 선택과 관련된 신경상태/시간코드 후보`까지만 말한다. `memory retrieval`, `correct choice`, `task rule representation`으로 승격하지 않는다.

**[확인자료 조건]** sample·choice·correct·reward가 명시된 trial table 또는 원시 Arduino task log를 확보한 뒤 별도 계약으로 다시 시작한다.
