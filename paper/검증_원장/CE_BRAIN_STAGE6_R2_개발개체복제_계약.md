# CE-BRAIN Stage 6 R2 개발개체 복제 계약

Status: `PREREGISTERED_PRE_R2_SCORE_POST_R1`

## 목적

R1의 `HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED`를 본 뒤 수행하는 development replication이다. R1의 unit 품질 필터, 자연영화 분할, rank·ridge 후보, N/D/R/M/P 모형, bootstrap, 판정 문턱을 변경하지 않는다. R2는 새 가설 탐색이 아니라 같은 계산의 개체 간 방향 일치 여부를 검사한다.

## 고정 자료

- DANDI `000021@0.251116.2246`
- subject `740268983`, session `759883607`
- asset `c9fc315f-5145-45a3-8183-3ad8fe499c4d`
- size `1,862,261,144` bytes
- SHA-256 `689b5fdc793343c9b874a1080252ec8c7d08f790274500c1344b925a692cfea2`

schema 사전감사에서 자연영화 900프레임 완전 반복 20회, stimulus block 4·12, 시각영역 unit 746개, 시간 역전 0곳, 양의 interval과 running 신호를 확인했다. neural prediction score는 아직 계산하지 않았다.

subject `719828686`은 시간 역전 2곳 때문에 score 전 `STAGE6_STRICT_PAST_SCHEMA_STOP`으로 격리한다. 행을 정렬하거나 제거해 구제하지 않는다. confirmation 4개체와 DANDI `001695`는 계속 열지 않는다.

## 판정

R1과 동일하게 `R>N` 1%, `R>D` 0.5%, `R>M` 0.5%와 각 bootstrap 하한 양수를 모두 요구한다.

- R2도 `HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED`이면 “두 development 개체에서 history 이득은 반복되지만 교차축 순환은 분리되지 않음”으로 기록한다.
- R2가 완전 지지여도 R1 불일치 때문에 Stage 6 확인 통과로 승격하지 않고 개발 이질성으로 기록한다.
- R2에서 `R>N`도 실패하면 history 일반화 자체가 개발 개체 사이에서 불안정하다고 기록한다.

어떤 결과도 confirmation 개방을 자동 허가하지 않는다. R1·R2 방향이 정리된 뒤 별도 확인 계약을 작성해야 한다.

