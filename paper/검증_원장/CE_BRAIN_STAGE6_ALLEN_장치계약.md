# CE-BRAIN Stage 6 Allen 개발자료 장치 계약

Status: `METADATA_ONLY_PRE_ENDPOINT`

## 목표

국소 기하의 성공을 전제하지 않고, 순환 동역학이 미래 예측에 필요한 차원을 설명하는지 검사할 개발 장치를 고정한다. 이 단계는 과학 결과가 아니라 자료 목록·분할·비용을 확정하는 장치 감사다.

## 자료와 봉인

- 개발자료: DANDI `000021@0.251116.2246`, Allen Visual Coding Neuropixels.
- 이 판본은 32개 subject, 32개 session NWB, 182개 probe NWB로 구성된다.
- subject는 salt `CE-BRAIN-STAGE6-ALLEN-V1`의 SHA-256으로 development 60%, calibration 20%, confirmation 20%에 배정한다.
- 이 장치 단계에서는 neural array, spike time, stimulus endpoint, fitted rank, prediction score를 열지 않는다.
- 기존 독립 확인용 DANDI `001695@0.260319.2023`은 계속 봉인하며 이 계약의 개발자료로 사용하지 않는다.

## 실행 전 후보와 대조군

첫 실행 계약은 development/calibration만 사용해 다음을 같은 시간 holdout에서 비교해야 한다.

1. 자극과 현재 상태만 쓰는 비순환 기준선.
2. 과거 population state를 쓰는 저차원 선형 동역학 기준선.
3. 안정한 recurrent mode를 포함한 후보.
4. mode 수는 유지하되 시간·연결 의미를 섞는 cycle-preserving 대조.
5. recurrent mode를 제거하는 cycle-destroying 또는 spectral destruction 대조.

주된 endpoint는 미래 population activity의 held-out predictive loss다. `r_dyn`과 `r_pred`는 train에서만 선택하고, confirmation은 계약·코드·문턱을 봉인한 뒤 한 번만 연다. 해부 connectome이 없는 이 개발자료에서는 `r_graph`를 측정했다고 주장하지 않는다.

## 중단 조건

- 반복 자극과 충분한 영역별 unit coverage를 session NWB에서 확인할 수 없으면 장치 중단한다.
- 입력 누출 없이 strict-past 예측 분할을 만들 수 없으면 장치 중단한다.
- 순환 후보가 단순 history/low-rank 기준선보다 안정적으로 낫지 않으면 `RECURRENT_PREDICTIVE_DIMENSION_NOT_ESTABLISHED`로 닫는다.
- 순환 후보가 이겨도, mode 파괴 대조가 선택적으로 성능을 낮추지 않으면 순환의 인과적·구조적 의미를 주장하지 않는다.

