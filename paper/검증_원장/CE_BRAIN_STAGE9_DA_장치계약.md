# CE-BRAIN Stage 9 dopamine 학습게이트 장치 계약

Status: `METADATA_PREREGISTERED_ENDPOINT_CLOSED`

## 자료와 질문

DANDI `001632@draft`의 현재 전체 목록을 잠근다. 과학 질문은 핵심 30·60·300·600초 조건에서 dopamine 기록이 조건과 과거 행동만 사용한 기준선보다 다음날 학습 변화를 더 잘 예측할 수 있는가이다.

이 계약은 자료·분할·스키마 적격성만 다루며 dopamine 및 행동 수치를 아직 점수화하지 않는다.

## 목록과 분할

1. DANDI API의 모든 pagination을 따라 asset ID·path·size·created·modified를 정렬하고 canonical SHA-256을 계산한다.
2. subject는 path 첫 구성요소로 정의한다.
3. 핵심 조건은 filename prefix의 `30s`, `60s`, `300s`, `600s` 네 개만 쓴다. `D`, `few`, `50percent`, `CSminus`, context, fear-conditioning 변형은 첫 실행에서 제외한다.
4. 각 조건 안에서 `SHA256("CE-BRAIN-STAGE9|" + subject)` 순으로 정렬한다. 앞 60% development, 다음 20% calibration, 마지막 20% confirmation으로 둔다. 각 칸은 최소 1 subject다.
5. confirmation의 NWB endpoint는 development·calibration 계약이 통과하기 전까지 열지 않는다.

## 스키마 게이트

development에서 조건별 첫 subject의 day01 자산 하나씩만 내려받는다. 네 파일 모두에서 다음이 식별되어야 한다.

- trial 또는 event 단위 reward timing/behavior
- dopamine 또는 photometry time series
- session/day 식별자
- 같은 subject의 다음날 자료 존재

하나라도 없으면 `STAGE9_DA_SCHEMA_STOP`이다. 통과할 경우에만 train feature, next-day target, animal holdout, null model과 효과크기를 새 계약으로 고정한다.

Draft inventory가 달라지면 기존 receipt를 덮어쓰지 않고 새 판본 감사를 만든다.
