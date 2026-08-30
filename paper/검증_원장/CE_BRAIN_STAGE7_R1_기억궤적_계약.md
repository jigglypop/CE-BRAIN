# CE-BRAIN Stage 7 R1 기억궤적 개발 계약

Status: `PREREGISTERED_PRE_REPLAY_SCORE_DEVELOPMENT_ONLY`

## 질문과 주장 상한

선형 트랙을 달릴 때 형성된 CA1 위치 순서가 멈춤 중 ripple 안에서 짧게 압축된 정방향 또는 역방향 궤적으로 다시 나타나는지 묻는다. 같은 뉴런 집합이 켜지는 정적 vector 설명과, 시간 순서까지 보존되는 trajectory 설명을 직접 경쟁시킨다.

이 분석은 hc-3 development session 하나의 관측 분석이다. 통과해도 특정 기억 내용, 학습 인과, 장기기억 저장, 순환차원 또는 국소 기하를 확립하지 않는다.

## 고정 자료

- CRCNS hc-3 `ec013.40/ec013.719`
- 공식 archive MD5 `32517ed8114e1b930df7925da6f2bb68`
- session duration 1,202.176초
- CA1 pyramidal unit 43개, electrode group 5~8
- position 39.0625Hz, LFP 1,250Hz, spikes 20kHz
- ripple 검출 채널: CA1 첫 group의 첫 channel, zero-based channel 32

## 위치와 encoding template

두 LED 좌표의 평균을 위치로 사용한다. 모든 좌표가 음수인 sample은 결측으로 두고, 0.5초 이하의 내부 결측만 선형 보간한다. 0.10초 Gaussian smoothing 뒤 PCA 첫 축에 투영하고 유효 위치의 1·99 percentile을 `[0,1]` track coordinate로 고정한다.

속도는 track length/초 단위로 계산한다. `speed>0.10`을 movement, `speed<0.02`를 immobility로 고정한다. 한 traversal은 한쪽 끝 `<0.15`에서 반대쪽 끝 `>0.85`까지 1~30초 안에 도달하고 위치 유효률이 80% 이상인 구간이다. 방향별 traversal을 시간순으로 60% train, 20% validation, 20% encoding-test로 나눈다. 방향별 traversal 5개 미만 또는 전체 12개 미만이면 장치 중단한다.

train movement에서 30개 위치 bin, Gaussian sigma 1 bin으로 CA1 unit별 Poisson firing-rate template를 만든다. 위치 decoder는 100ms bin을 사용한다. encoding-test의 median absolute position error가 0.15 track 이하이고 occupancy-prior 정적 기준선보다 20% 이상 좋아야 replay 해석을 허가한다.

## ripple과 replay 후보

채널 32 LFP를 4차 Butterworth 120~250Hz로 zero-phase filtering하고 Hilbert envelope를 계산한다. immobility 구간 envelope의 median/MAD로 robust z-score를 만든다.

- peak `z>=3.5`
- 경계 `z>=1.5`
- duration 40~400ms
- 30ms 미만 간격은 병합
- event center의 speed `<0.02`
- 20ms bin 4개 이상, 5개 이상의 CA1 pyramidal unit 활성

조건을 만족하는 event가 20개 미만이면 표본수 장치 중단이며 과학 음성으로 세지 않는다.

## trajectory 점수와 대조

train place-rate template로 각 20ms bin의 위치 posterior를 계산한다. event마다 다음을 계산한다.

1. `order_score`: 시간과 posterior mean 위치의 Spearman 상관 절댓값. 정·역방향 모두 허용한다.
2. `distance_score`: 모든 시간-bin 쌍에서 시간 간격과 decoded 위치 간격의 Spearman 상관.
3. `jump`: 인접 decoded 위치의 평균 절대 차이.

두 대조를 seed `20260909`로 event당 199회 만든다.

- `T`: event 안의 20ms time-bin 순서를 섞는다. aggregate spike vector는 같고 trajectory만 파괴한다.
- `C`: unit과 place-field template 대응을 섞는다. 시간별 spike 수는 같고 공간 내용만 파괴한다.

event는 order score가 T와 C 각각의 95 percentile을 모두 넘을 때 이중 유의로 센다. event 단위 bootstrap 1,999회로 실제와 각 대조의 median order·distance 차이를 평가한다.

## 사전 판정

다음을 모두 만족할 때만 `DEVELOPMENT_MEMORY_TRAJECTORY_SUPPORTED`다.

1. encoding decoder 문턱 통과.
2. 적격 ripple event 20개 이상.
3. 실제 median order score가 T와 C median보다 각각 0.10 이상 높고 두 bootstrap 하한이 0보다 크다.
4. distance score도 T와 C보다 높고 두 bootstrap 하한이 0보다 크다.
5. 이중 유의 event 비율이 10% 이상이며, 5% 귀무율에 대한 단측 binomial `p<0.01`이다.

encoding은 통과하지만 replay 문턱이 실패하면 `ENCODING_TRAJECTORY_ONLY_REPLAY_NOT_ESTABLISHED`, encoding부터 실패하면 `TRAJECTORY_MEMORY_NOT_ESTABLISHED`다. event 부족은 `STAGE7_REPLAY_COVERAGE_STOP`이다.

## 해석 규율

선형 트랙 자체가 1차원이라 topology는 별도 고차 위상 증거가 아니다. 통과 결과는 “행동 중 위치 순서와 관계된 압축 trajectory가 immobility ripple에서 정적 vector 대조보다 자주 나타난다”까지로 제한한다. retrieval과 correction 분리는 Stage 8의 새 자료·새 계약이 필요하다.

