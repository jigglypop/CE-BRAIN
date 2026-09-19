# Allen 20Hz VC: 전체 전류·명령 확보와 입력 조건

2026-09-19. [이전 source 시각 검토](allen_source_timing_findings.md)에서 확인한
실험 `1574292898.139`의 0–6시행 결손을 채웠다. 목적은 다음 전달·이력 비교에서
실제 입력을 정의하는 것이다. 이번 결과는 측정 자료 확보와 입력 확인이며 반응 적합은 아니다.

## 확보와 보존

- 기존 NWB 부분 캐시 SHA-256
  `dfea65157ac4bfc8af5aae0c08964b6c4258e631655d9cd17a3c4140ff06b15d`는 유지했다.
- 같은 원격 ETag에 대해 HEAD, `If-Match`, HTTP206과 `Content-Range`를 확인하고
  결손 139개 블록, 9,109,504바이트만 별도 overlay에 받았다. 원격 전체는
  837,666,824바이트이며 전량 다운로드하지 않았다. 설정한 추가 수집 상한은 16MiB다.
- 7시행 × 전류 AD9/AD8/AD2 및 명령 DA5/DA4/DA2 = 42개 전체 배열을 확보했다.
  모든 배열은 505,902표본이며 전부 유한값이다. 각 시행의 6채널은 시작시각·100kHz
  표본률·길이가 같다. 전류는 A, 명령은 V로 conversion과 offset을 적용했다.
- overlay는 `data/external/allen_synphys_r21/vc20hz_ranges/1574292898.139`에 있다.
  manifest SHA는 `2780277f58632d68826dc09a892d70f33e15c3cb26370e423faf57ac5f5b5abc`다.
  139개 블록의 크기·해시를 전량 대조했다.

## 실제 입력: 시행별 진폭을 구별한다

아래는 DA 배열의 초기값(0V)에 대한 양의 pulse plateau 차이다. 실제 세포막 전압이나
발화의 관측값이 아니다. 21개 명령 배열의 각 12개 양의 interval을 전부 확인했다.

| 시행 | DA2 / HS2 | DA4 / HS4 | DA5 / HS5(source) |
|---|---:|---:|---:|
| 0–1 | 60mV | 60mV | 60mV |
| 2–4 | 120mV | 120mV | 120mV |
| 5–6 | 120mV | 150mV | 120mV |

정확한 배열 차이는 각각 0.06000000284984708, 0.12000000569969416,
0.1500000071246177V다. 각 양의 interval 안에서 최솟값과 최댓값이 같았다.
각 명령에는 별도로 초기 −10mV test pulse도 포함된다. 앞 단계의 메타데이터 진폭은
실제 배열과 일치했다. 점검 중 0시행의 60mV를 전체로 확대한 중간 보고는 잘못이었으며,
위 전량 계산으로 바로잡았다. 결과 JSON과 NPZ에는 원래부터 실제 시행별 값이 보존돼 있다.

source 전압/AP 채널은 없다. 따라서 이 자료로 평가할 수 있는 대상은 source의
전압 명령에 따른 target clamp-current다. 세 세포 자체 자극의 순서와 과거 전류 상태를
포함해야 하며, IC–VC 차이를 50Hz–20Hz 빈도 효과만으로 읽지 않는다.

## DB의 남은 측정 조건

읽기 전용 조회에서 experiment3337, devices2/4/5의 electrodes26623/26625/26626,
cells18950/18951/18952, sweeps0..6의 sync_rec72618..72624를 확인했다.
medium DB의 보유 부분 캐시는 recording 조회에 필요한 블록382337024가 없어
다음 결합을 완성하지 못했다: `recording → patch_clamp_recording.nearest_test_pulse_id
→ test_pulse.id`. 작은 DB에는 해당 recording/QC 행이 없다.

따라서 이번 0–6시행의 access/input resistance·baseline·QC 값은 아직 미확립이다.
기존 37–56시행의 값을 옮겨 쓰지 않는다. DB의 추가 범위를 받지 않았으며 다음은
필요한 indexed lookup 범위와 실제 test-pulse 측정 상태를 확인하는 것이다.

이 문단은 전체 입력 확보 당시의 상태다. 후속 [측정 상태 결합](allen_vc20hz_measurement_state_findings.md)에서
기존 DB 캐시를 보존하고 결손64KiB만 받아21개 recording/PCR/TP 연결을 완료했다.
모두 embedded TP와 최소 QC가 확인됐으나 C·τ와 hardware compensation은 미확인이다.
DB의 노트 작성 시각과 raw 첫 표본 시각을 구별하고, TP baseline 전류를 써야 보정 전위가
재현된다는 점을 확인했다. 실제 반응·이력 모형의 적합은 이 후속에서도 수행하지 않았다.

## 파일과 검증

- [추출 소스](../verify/Q-NPF-04/allen_synphys/vc20hz_source_inputs.py),
  [검사](../tests/test_vc20hz_source_inputs.py),
  [결과](../verify/Q-NPF-04/allen_synphys/vc20hz_source_inputs_result.json),
  [전체 입력 배열](../data/local/allen-synphys-analysis/vc20hz-inputs-v1/full_inputs.npz).
- 결과 JSON 127,018바이트, SHA-256
  `2f22c6fad05f33ee03ae5d6d39f56d706c883da2207b057692295d8ff333b087`.
- NPZ 11,226,104바이트, SHA-256
  `9222e0ce81471c2452f0e20929b1634b79fa790f120c6a5cd45df00789050a97`.
- source/test SHA는 결과 JSON에 고정했다. `vc20hz-inputs-v1`에 4개 산출물,
  `r2.1-vc20hz-overlay-20260919`에 139개 블록과 manifest를 등록했다.
- 실행기 `C:/dev/ce/ce-agi-runtime-repro-fffd356/.codex/hooks/python.cmd`로
  `pytest tests/test_vc20hz_source_inputs.py -q` 5개 통과 후
  `python verify/Q-NPF-04/allen_synphys/vc20hz_source_inputs.py --allow-download`를 실행했다.
  Python3.11.9, NumPy2.4.6, h5py3.16.0이다. 기본 실행은 offline이고 출력 덮어쓰기를 거부한다.
- 검사는 캐시 손상·판본 불일치·잘못된 HTTP range 거부와 명령 경계를 포함한다.
  별도로 42배열·7공통 clock·139블록·21명령의 전량 검사를 수행했다.

이번 단계로 source 입력의 크기와 전체 관측 결손은 해결했다. 실제 시냅스 전류,
가소성, 리만 계량과 해마 검색의 식별은 아직 이 결과가 입증하는 범위가 아니다.
