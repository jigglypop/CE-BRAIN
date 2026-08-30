# CE-BRAIN Stage 6 R1 순환예측 개발 계약

Status: `PREREGISTERED_PRE_SCORE_DEVELOPMENT_ONLY`

## 질문과 주장 상한

같은 자연영화 프레임과 같은 개체에서도 직전 population state의 교차뉴런 동역학이 다음 프레임 반응을 더 잘 예측하는지 묻는다. 이 실행은 development subject 하나의 장치·모형 개발 분석이다. 통과하더라도 해부학적 graph cycle, 기억 용량, 인과적 순환회로 또는 독립 재현을 주장하지 않는다.

## 고정 자료

- DANDI `000021@0.251116.2246`
- subject `707296975`, session `721123822`
- asset `224b57e5-c9a3-46ef-85db-966713f3ccbe`
- size `1,736,516,600` bytes
- SHA-256 `4e284295a1be5c6cca49df84fab52ad38b4749d2361b2edebeb676051cf09921`
- `natural_movie_one`: 900프레임 완전 반복 20회, stimulus block 4와 12

confirmation 4개체와 DANDI `001695`는 열지 않는다.

봉인 manifest에는 실제 실행 interpreter 절대경로, Python·NumPy·h5py 판본을 기록하고 재계산 때 동일성을 검사한다.

## 뉴런과 반응

peak channel 위치가 `VIS`로 시작하고, `quality=good`, `presence_ratio>=0.95`, `amplitude_cutoff<=0.1`, `isi_violations<=0.5`, `firing_rate>=0.1 Hz`인 unit만 사용한다. unit id 오름차순에서 처음 256개로 계산량을 고정한다. 256개 미만이면 있는 적격 unit을 모두 쓰되 128개 미만이면 장치 중단한다.

각 영화 frame의 `[start_time, stop_time)` spike count에 Anscombe 변환 `sqrt(count+3/8)`을 적용한다. 첫 stimulus block의 앞 8회는 train, 뒤 2회는 rank 선택용 validation, 두 번째 block의 10회는 시간적으로 떨어진 development test다. 반복 경계를 가로지르는 lag는 만들지 않는다.

## 후보 모형

train 반복의 frame별 평균을 알려진 자극 기준선 `N`으로 둔다. train residual에 PCA를 적합하고 rank 후보 `{4,8,16,32}`를 비교한다.

- `N`: 영화 frame별 train 평균만 사용한다.
- `D`: 현재 latent coordinate가 자기 자신의 다음 값만 예측하는 diagonal AR(1)이다.
- `R`: 현재 latent population state 전체로 다음 latent state를 예측하는 ridge VAR(1)이다.
- `M`: `R`의 가장 큰 singular mode 상위 25%를 0으로 만든 mode-destruction 대조다.
- `P`: `R`의 행과 열을 서로 다른 고정 permutation으로 섞어 coefficient 수와 singular values는 보존하되 coordinate 의미를 끊는 대조다.

ridge는 `{1e-3,1e-2,1e-1,1}`에서 validation loss가 가장 낮은 값을 rank와 함께 선택한다. seed는 `20260908`이다. 모든 점수는 원래 unit 공간의 다음-frame MSE이며 test 반복별로 계산한다.

## 사전 판정 문턱

test 10회를 단위로 1,999회 bootstrap한다. 다음을 모두 만족할 때만 `DEVELOPMENT_RECURRENT_PREDICTIVE_MODES_SUPPORTED`로 기록한다.

1. `R`이 `N`보다 1% 이상 개선하고 bootstrap 95% 하한이 0보다 크다.
2. `R`이 `D`보다 0.5% 이상 개선하고 하한이 0보다 크다.
3. `R`이 `M`보다 0.5% 이상 개선하고 하한이 0보다 크다.

`R`이 `N`만 이기면 `HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED`, 그 밖에는 `RECURRENT_PREDICTIVE_DIMENSION_NOT_ESTABLISHED`다. `P`는 사전 진단 대조로 보고하되 주 판정을 단독으로 바꾸지 않는다.

## 해석 규율

`R>D`는 개별 latent 자기상관을 넘어선 교차상태 예측 이득을 뜻한다. `R>M`은 그 이득이 일부 강한 population mode에 의존하는지를 묻는다. 둘 다 관측자료의 계산적 제거 대조이며 실제 회로를 개입으로 끊은 결과가 아니다. 따라서 R1 통과는 confirmation 계약을 만들 자격일 뿐 Stage 6 최종 통과가 아니다.
