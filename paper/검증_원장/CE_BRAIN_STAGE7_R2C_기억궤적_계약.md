# CE-BRAIN Stage 7 R2C 기억궤적 독립 개발 계약

Status: `PREREGISTERED_PRE_R2C_NEURAL_SCORE`

## 질문과 자료

R1과 다른 topdir `ec016.17/ec016.233`에서 위치 encoding과 immobility ripple의 압축 궤적이 재현되는지 묻는다. R2B의 84/84 메타데이터 일치 조건은 score 전에 장치 중단됐고, R2C는 실제 cluster에 존재하며 `.clu/.res`가 일치하는 CA1 pyramidal unit 75개만 사용한다.

원시 위치 유효률은 94.05%, 왕복은 64회이며 양방향 각 32회다. 시간순 분할은 train 38·validation 12·test 14회로 고정한다. ripple·decoder test 점수는 아직 열지 않았다.

## validation-only 해독기 선택

R1의 단일 해독기 오차가 컸으므로 train으로 place-rate를 만들고 validation에서만 다음 16개 후보를 비교한다.

- spatial Gaussian sigma: 0.5, 1, 2, 3 position bin
- decode prior: train occupancy 또는 uniform
- decode time bin: 0.1초 또는 0.2초

위치 bin 30개, movement `speed>0.10`, Poisson 독립 unit likelihood는 R1과 같다. validation median absolute error가 가장 작은 후보 하나를 고정하며 동률은 `(sigma, prior, dt)` 문자열 순서로 푼다. 선택 뒤 test에는 재선택이나 threshold 변경을 하지 않는다.

test encoding 문턱은 R1과 동일하게 median absolute error 0.15 track 이하이면서 train occupancy 정적 기준보다 20% 이상 개선이다.

## ripple과 replay

첫 CA1 electrode group의 첫 LFP channel, zero-based channel 0을 쓴다. 120~250Hz, robust z, peak 3.5·boundary 1.5, 40~400ms, 30ms merge, immobility `<0.02`, 20ms 4-bin 이상, 활성 CA1 unit 5개 이상은 R1과 같다.

선택된 해독기로 event마다 R1과 같은 order·distance를 계산한다. seed `20260909`, event당 time-order shuffle 199회와 cell-template shuffle 199회, event bootstrap 1,999회를 유지한다.

## 판정

R1과 동일하게 다음을 모두 만족할 때만 `DEVELOPMENT_MEMORY_TRAJECTORY_SUPPORTED_REPLICATED`다.

1. test encoding 문턱 통과.
2. 적격 ripple event 20개 이상.
3. order가 두 null보다 각각 0.10 이상 높고 bootstrap 하한 >0.
4. distance가 두 null보다 높고 bootstrap 하한 >0.
5. 이중 유의 event 10% 이상, 5% 귀무율 binomial `p<0.01`.

encoding 실패는 `TRAJECTORY_MEMORY_NOT_ESTABLISHED_REPLICATED`, encoding만 통과하고 replay 실패는 `ENCODING_TRAJECTORY_ONLY_REPLAY_NOT_ESTABLISHED_REPLICATED`, event 부족은 `STAGE7_R2C_REPLAY_COVERAGE_STOP`이다.

이 실행은 R1과 다른 동물의 development 복제이지 최종 확인이 아니다. 통과해도 새 confirmation 자료가 필요하며, 실패해도 해마 replay 일반의 부재로 해석하지 않는다.
